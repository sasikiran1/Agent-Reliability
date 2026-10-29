"""Bounded local tool loop; parent supervisor owns cancellation and SQL adjudication."""
import argparse
import json
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from local_lab import Trace

TOOLS = [
    dict(type='function', function=dict(name='create_job', description='Create a persistent pending job.', parameters=dict(
        type='object', properties=dict(title=dict(type='string'), priority=dict(type='string', enum=['normal', 'high'])),
        required=['title', 'priority'], additionalProperties=False))),
    dict(type='function', function=dict(name='list_jobs', description='List jobs created for the current task.',
         parameters=dict(type='object', properties={}, required=[], additionalProperties=False))),
]


def request(url, body, timeout):
    with urlopen(Request(url, json.dumps(body).encode(), {'Content-Type': 'application/json'}), timeout=timeout) as response:
        return json.load(response)


class Loop:
    def __init__(self, args):
        self.args = args
        self.trace = Trace(Path(args.output) / 'model-tools.jsonl')
        self.messages = [dict(role='user', content='Create one pending job titled "Check dataset manifest" with priority "normal". Report its job ID when finished.')]
        self.schemas = list(TOOLS)
        self.max_calls = 4
        if args.task_id:
            fixture = next(t for t in json.loads((Path(__file__).resolve().parents[1]/'data/workflow-pilot-tasks.json').read_text()) if t['id']==args.task_id)
            self.messages = [dict(role='user', content=f'Find the existing job titled "{fixture["target"]}". Raise its priority to high, then create one follow-up job titled "{fixture["followup"]}" linked to that parent. Leave other existing jobs unchanged. Verify the resulting records before reporting completion.')]
            self.max_calls = 8
            self.schemas = [TOOLS[1],
                dict(type='function',function=dict(name='update_job',description='Change priority of an existing job.',parameters=dict(type='object',properties=dict(job_id=dict(type='string'),priority=dict(type='string',enum=['normal','high'])),required=['job_id','priority'],additionalProperties=False))),
                dict(type='function',function=dict(name='create_followup',description='Create one pending follow-up linked to an existing parent. Parent must already have high priority.',parameters=dict(type='object',properties=dict(parent_job_id=dict(type='string'),title=dict(type='string')),required=['parent_job_id','title'],additionalProperties=False)))]
        self.model_calls, self.tool_calls = 0, 0
        self.pending = []
        self.finished = False
        self.last_request_id = None

    def model(self):
        if self.model_calls >= self.max_calls:
            raise RuntimeError('Model-call budget exhausted')
        self.last_request_id = str(uuid.uuid4())
        body = dict(model=self.args.model, messages=self.messages, tools=self.schemas, stream=False, keep_alive='2m',
                    options=dict(num_ctx=4096, num_predict=512, temperature=0, seed=20261028))
        if self.args.model.startswith('qwen'):
            body['think'] = False
        self.trace.emit('model_request', task_id=self.args.goal, request_id=self.last_request_id,
                        retry_source='none', request=body)
        self.model_calls += 1
        response = request('http://127.0.0.1:11434/api/chat', body, 120)
        self.trace.emit('model_response', task_id=self.args.goal, request_id=self.last_request_id, response=response)
        self.messages.append(response['message'])
        self.pending = response['message'].get('tool_calls', [])
        self.finished = not bool(self.pending)

    def tools(self):
        for call in self.pending:
            if self.tool_calls >= 12:
                raise RuntimeError('Tool-call budget exhausted')
            self.tool_calls += 1
            attempt = str(uuid.uuid4())
            function = call['function']
            body = dict(goal_id=self.args.goal, attempt_id=attempt, parent_attempt=self.last_request_id,
                        provider_tool_call_id=call.get('id'), retry_source='model_requested',
                        tool=function['name'], arguments=function['arguments'], intervention=None,
                        idempotency_key=None)
            self.trace.emit('tool_request', task_id=self.args.goal, **{k: v for k, v in body.items() if k != 'goal_id'})
            if function['name'] not in {s['function']['name'] for s in self.schemas}:
                result = dict(error='Unknown tool')
            else:
                try:
                    result = request(self.args.service + '/tools', body, 5)
                except HTTPError as exc:
                    result = dict(error=exc.read().decode(), status=exc.code)
            self.trace.emit('tool_response', task_id=self.args.goal, attempt_id=attempt, result=result)
            message = dict(role='tool', tool_name=function['name'], content=json.dumps(result))
            if call.get('id'):
                message['tool_call_id'] = call['id']
            self.messages.append(message)
        self.pending = []

    def run(self):
        if self.args.runner == 'minimal':
            while not self.finished:
                self.model()
                if self.pending:
                    self.tools()
        else:
            from typing import TypedDict
            from langgraph.graph import StateGraph, START, END
            class State(TypedDict):
                finished: bool
            def model(state):
                self.model()
                return dict(finished=self.finished)
            def tools(state):
                self.tools()
                return dict(finished=False)
            graph = StateGraph(State)
            graph.add_node('model', model, retry_policy=None)
            graph.add_node('tools', tools, retry_policy=None)
            graph.add_edge(START, 'model')
            graph.add_conditional_edges('model', lambda s: END if s['finished'] else 'tools')
            graph.add_edge('tools', 'model')
            graph.compile(checkpointer=None).invoke(dict(finished=False), config=dict(recursion_limit=12))

    def warmup(self):
        body=dict(model=self.args.model,messages=[dict(role='user',content='Reply READY.')],stream=False,
                  keep_alive='2m',options=dict(num_ctx=4096,num_predict=8,temperature=0,seed=20261028))
        if self.args.model.startswith('qwen'):
            body['think']=False
        self.trace.emit('warmup_request',request=body)
        response=request('http://127.0.0.1:11434/api/chat',body,120)
        self.trace.emit('warmup_response',response=response)
        Path(self.args.output,'warmup.json').write_text(json.dumps(response,indent=2))


def main():
    parser = argparse.ArgumentParser()
    for name in ('model', 'service', 'goal', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--runner', choices=['minimal', 'langgraph'], default='minimal')
    parser.add_argument('--task-id')
    args = parser.parse_args()
    # Never opt in to external tracing or hosted model fallbacks.
    os.environ['LANGSMITH_TRACING'] = 'false'
    os.environ['LANGCHAIN_TRACING_V2'] = 'false'
    loop = Loop(args)
    status, error = 'finished', None
    main_start=None
    try:
        if args.task_id:
            loop.warmup()
        main_start=time.perf_counter()
        loop.run()
    except Exception as exc:
        status, error = 'worker_error', repr(exc)
        loop.trace.emit('worker_error', error=error)
    finally:
        Path(args.output, 'worker-result.json').write_text(json.dumps(dict(status=status, error=error,
            model_calls=loop.model_calls, tool_calls=loop.tool_calls,
            task_duration_s=None if main_start is None else time.perf_counter()-main_start,
            warmup_completed=main_start is not None), indent=2))


if __name__ == '__main__':
    main()
