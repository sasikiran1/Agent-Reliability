"""Controlled concurrent live-agent study; no production/prevalence claim.

Reuses the submitted private application and model loop; keeps new evidence separate.
Inference is explicitly serialized, while agent sessions and application I/O overlap.
"""
import concurrent.futures
import hashlib
import json
import platform
import random
import sqlite3
import statistics
import subprocess
import threading
import time
import uuid
import sys
import argparse
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import psutil
os.environ['LANGSMITH_TRACING']='false'
os.environ['LANGCHAIN_TRACING_V2']='false'
from local_lab import JobStore, Trace, serve
from pilot_worker import Loop, request

ROOT = Path(__file__).resolve().parents[1]
INFERENCE = threading.Lock()


def ollama(endpoint, body=None):
    req = Request('http://127.0.0.1:11434/api/'+endpoint,
                  None if body is None else json.dumps(body).encode(),
                  {'Content-Type': 'application/json'})
    with urlopen(req, timeout=120) as response:
        return json.load(response)


class Session(Loop):
    def __init__(self, args, scenario):
        super().__init__(args)
        self.scenario, self.injected = scenario, False
        self.interface=getattr(args,'interface','native')
        self.output_path='native' if self.interface=='native' else 'json-action'
        if scenario=='nominal_existing':
            self.messages=[dict(role='user',content='Ensure exactly one pending job titled "Check dataset manifest" with normal priority exists. Check existing jobs first. If it already exists, do not create another. Verify and report its ID.')]
        if self.interface in ('json-action','portable'):
            self.max_calls=8
            self.messages.insert(0,dict(role='system',content='Complete the task using simulated local job tools. '
                'Return exactly one JSON action per reply: {"action":"tool_name","arguments":{...}}. '
                'Tool results arrive in user messages. To finish, put your final report and requested record IDs in '
                '{"action":"finish","arguments":{"result":"your report"}}. '
                'Available tools: '+json.dumps([s['function'] for s in self.schemas])))
        if getattr(args,'prompt_text',None) is not None:
            self.messages[-1]['content']=args.prompt_text

    def model(self):
        queued = time.perf_counter()
        with INFERENCE:
            self.trace.emit('inference_queue_wait', seconds=time.perf_counter()-queued)
            if time.perf_counter()>getattr(self,'deadline',float('inf')):
                raise TimeoutError('Session exceeded 300 seconds including inference queue wait')
            if psutil.virtual_memory().available < 1024**3:
                raise RuntimeError('RAM guard below 1 GiB')
            if self.interface=='native':
                super().model()
            else:
                if self.model_calls>=self.max_calls:
                    raise RuntimeError('Model-call budget exhausted')
                self.last_request_id=str(uuid.uuid4())
                schema=dict(type='object',properties=dict(action=dict(type='string',enum=[s['function']['name'] for s in self.schemas]+['finish']),
                    arguments=dict(type='object')),required=['action','arguments'],additionalProperties=False)
                body=dict(model=self.args.model,messages=self.messages,format=schema,stream=False,keep_alive='5m',
                    options=dict(num_ctx=4096,num_predict=1024,
                        temperature=getattr(self.args,'temperature',0),seed=getattr(self.args,'seed',20261029)))
                if self.args.model.startswith('gpt-oss'):
                    body['think']='low'
                elif self.args.model.startswith(('qwen','gemma','hf.co/unsloth/DeepSeek')):
                    body['think']=False
                self.trace.emit('model_request',task_id=self.args.goal,request_id=self.last_request_id,request=body)
                self.model_calls+=1;response=request('http://127.0.0.1:11434/api/chat',body,120)
                self.trace.emit('model_response',task_id=self.args.goal,request_id=self.last_request_id,response=response)
                self.messages.append(response['message'])
                if self.interface=='portable' and response['message'].get('tool_calls'):
                    self.output_path='native';self.finished=False
                    self.pending=response['message']['tool_calls']
                else:
                    self.output_path='json-action'
                    action=json.loads(response['message']['content'])
                    self.finished=action['action']=='finish'
                    self.pending=[] if self.finished else [dict(id=self.last_request_id+'-json',function=dict(name=action['action'],arguments=action['arguments']))]
                self.trace.emit('action_decode',request_id=self.last_request_id,output_path=self.output_path)

    def tools(self):
        for call in self.pending:
            if self.tool_calls >= 12:
                raise RuntimeError('Tool budget exhausted')
            self.tool_calls += 1
            function = call['function']
            logical_key = hashlib.sha256(json.dumps([self.args.goal,function],sort_keys=True).encode()).hexdigest()
            inject = (self.scenario.startswith('lost_ack') and not self.injected
                      and function['name'] == 'create_job')
            self.injected |= inject
            result = None
            for retry in range(2 if self.scenario.startswith('lost_ack') else 1):
                body = dict(goal_id=self.args.goal, attempt_id=str(uuid.uuid4()),
                    parent_attempt=self.last_request_id, provider_tool_call_id=call.get('id'),
                    retry_source='explicit_transport_retry' if retry else 'model_requested',
                    tool=function['name'], arguments=function['arguments'],
                    intervention='drop_reply_after_commit' if inject and not retry else None,
                    idempotency_key=logical_key if (self.scenario=='lost_ack_idempotent' or
                        (getattr(self.args,'ordinary_control',None)=='idempotency' and function['name']=='create_job')) else None)
                self.trace.emit('tool_request', **body)
                try:
                    result = request(self.args.service+'/tools', body, 5)
                except HTTPError as exc:
                    result = dict(error=exc.read().decode(), status=exc.code)
                except Exception as exc:
                    self.trace.emit('tool_transport_error',attempt_id=body['attempt_id'],error=repr(exc))
                    if not retry and self.scenario.startswith('lost_ack'):
                        continue
                    result = dict(error=repr(exc))
                self.trace.emit('tool_response',attempt_id=body['attempt_id'],result=result)
                break
            message=(dict(role='user',content='Tool '+function['name']+' result: '+json.dumps(result))
                     if self.output_path=='json-action' else
                     dict(role='tool',tool_name=function['name'],content=json.dumps(result)))
            if call.get('id') and self.output_path=='native':
                message['tool_call_id']=call['id']
            self.messages.append(message)
        self.pending=[]

    def run(self):
        if self.interface not in ('json-action','portable'):
            return super().run()
        if self.args.runner=='minimal':
            while not self.finished:
                self.model()
                if self.pending:
                    self.tools()
        else:
            from typing import TypedDict
            from langgraph.graph import StateGraph,START,END
            class State(TypedDict):
                finished: bool
            def model(state):
                self.model();return dict(finished=self.finished)
            def tools(state):
                self.tools();return dict(finished=False)
            graph=StateGraph(State)
            graph.add_node('model',model,retry_policy=None)
            graph.add_node('tools',tools,retry_policy=None)
            graph.add_edge(START,'model')
            graph.add_conditional_edges('model',lambda s:END if s['finished'] else 'tools')
            graph.add_edge('tools','model')
            graph.compile(checkpointer=None).invoke(dict(finished=False),
                config=dict(recursion_limit=2*self.max_calls+2))


def adjudicate(db_path, goal, fixture):
    with sqlite3.connect(f'file:{db_path.as_posix()}?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        jobs=[dict(r) for r in db.execute('SELECT * FROM jobs WHERE goal_id=?',(goal,))]
        effects=[dict(r) for r in db.execute("SELECT * FROM effects WHERE goal_id=? AND attempt_id!='seed'",(goal,))]
        deps=[dict(r) for r in db.execute('SELECT d.* FROM dependencies d JOIN jobs j ON j.job_id=d.child_id WHERE j.goal_id=?',(goal,))]
    children=[j for j in jobs if not j['job_id'].startswith('seed-')]
    if fixture:
        original=[j for j in jobs if j['job_id'].startswith('seed-')]
        correct=(len(original)==3 and all(j['priority']==('high' if j['title']==fixture['target'] else 'normal')
            and j['state']=='pending' for j in original) and len(children)==1
            and children[0]['title']==fixture['followup'] and children[0]['state']=='pending'
            and children[0]['priority']=='normal' and len(deps)==1
            and deps[0]['parent_id']==next(j['job_id'] for j in original if j['title']==fixture['target'])
            and deps[0]['child_id']==children[0]['job_id'])
    else:
        correct=(len(jobs)==1 and jobs[0]['title']=='Check dataset manifest'
                 and jobs[0]['priority']=='normal' and jobs[0]['state']=='pending')
    parent_by_child={d['child_id']:d['parent_id'] for d in deps}
    relevant=children if fixture else jobs
    identities=Counter((j['title'],j['priority'],j['state'],parent_by_child.get(j['job_id'])) for j in relevant)
    duplicates=sum(max(0,n-1) for n in identities.values())
    if fixture:
        intended_parent=next((j['job_id'] for j in jobs if j['title']==fixture['target'] and j['job_id'].startswith('seed-')),None)
        unplanned=sum(not (j['title']==fixture['followup'] and j['priority']=='normal' and j['state']=='pending'
                          and parent_by_child.get(j['job_id'])==intended_parent) for j in children)
    else:
        unplanned=sum(not (j['title']=='Check dataset manifest' and j['priority']=='normal' and j['state']=='pending') for j in jobs)
    return dict(state_correct=correct, duplicate_effects=duplicates,unplanned_records=unplanned,
                committed_effects=len(effects), jobs=jobs, effects=effects, dependencies=deps)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--models',nargs='+',default=['qwen3.5:4b','llama3.1:8b'])
    parser.add_argument('--interface',choices=['native','json-action','portable'],default='native')
    parser.add_argument('--agent-counts',nargs='+',type=int,default=[1,2,4])
    parser.add_argument('--runners',nargs='+',choices=['minimal','langgraph'],default=['minimal','langgraph'])
    parser.add_argument('--scenarios',nargs='+',default=['nominal_create','nominal_workflow','lost_ack_retry','lost_ack_idempotent'])
    cli=parser.parse_args()
    output=ROOT/'results'/('multiagent-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir()
    scenarios=cli.scenarios
    plan=[dict(model=m,runner=r,agents=n,scenario=s) for m in cli.models
          for r in cli.runners for n in cli.agent_counts for s in scenarios]
    random.Random(20261029).shuffle(plan)
    manifest=dict(track='controlled_constructed',natural_usage=False,inference_parallelism=1,
        plan=plan,batches=len(plan),agent_tasks=sum(p['agents'] for p in plan),
        scenarios=scenarios,interventions=['researcher_created_tasks_and_application',
        'declared_ack_loss_in_lost_ack_arms','one_transport_retry_in_lost_ack_arms'],
        interface=cli.interface,platform=platform.platform(),python=platform.python_version(),models=ollama('tags'),
        settings=dict(context=4096,output_cap=1024 if cli.interface in ('json-action','portable') else 512,
                      max_model_calls='8 for JSON; native follows submitted task budgets',max_tool_calls=12),
        task_fixtures=json.loads((ROOT/'data/workflow-pilot-tasks.json').read_text()),
        runtime=ollama('version'),ram_bytes=psutil.virtual_memory().total,
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [Path(__file__),ROOT/'src/local_lab.py',ROOT/'src/pilot_worker.py']})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (output/'source').mkdir()
    for p in [Path(__file__),ROOT/'src/local_lab.py',ROOT/'src/pilot_worker.py']:
        (output/'source'/p.name).write_bytes(p.read_bytes())
    print('MULTIAGENT_OUTPUT',output,flush=True)
    if ollama('ps')['models']:
        raise RuntimeError('Existing model loaded; do not interrupt another session')
    fixture=json.loads((ROOT/'data/workflow-pilot-tasks.json').read_text())[0]
    all_rows=[]
    for index,condition in enumerate(plan):
        batch=output/f'batch-{index:03d}';batch.mkdir()
        store=JobStore(batch/'application.sqlite'); trace=Trace(batch/'application.jsonl')
        resources=Trace(batch/'resources.jsonl'); probes=Trace(batch/'probes.jsonl')
        done=threading.Event()
        with serve(store,trace) as url:
            def monitor():
                while not done.is_set():
                    started=time.perf_counter()
                    try:
                        request(url+'/tools',dict(goal_id='probe',attempt_id=str(uuid.uuid4()),
                            tool='list_jobs',arguments={},retry_source='constant_probe'),2)
                        probes.emit('probe',ok=True,seconds=time.perf_counter()-started)
                    except Exception as exc:
                        probes.emit('probe',ok=False,seconds=time.perf_counter()-started,error=repr(exc))
                    resources.emit('resource',available_ram=psutil.virtual_memory().available,
                                   cpu_percent=psutil.cpu_percent())
                    done.wait(.5)
            # Warm model before launching measured sessions.
            ollama('chat',dict(model=condition['model'],messages=[dict(role='user',content='Reply READY.')],
                stream=False,keep_alive='5m',options=dict(num_ctx=4096,num_predict=8)))
            thread=threading.Thread(target=monitor,daemon=True);thread.start()
            barrier=threading.Barrier(condition['agents'])
            def execute(agent):
                goal=str(uuid.uuid4());folder=batch/f'agent-{agent}';folder.mkdir()
                task_fixture=fixture if condition['scenario']=='nominal_workflow' else None
                if task_fixture:
                    with store.connect('seed') as db:
                        for i,title in enumerate(fixture['records']):
                            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)',
                                (f'seed-{goal}-{i}',goal,title,'normal','pending'))
                elif condition['scenario']=='nominal_existing':
                    store.create(goal,dict(title='Check dataset manifest',priority='normal'),'seed')
                args=SimpleNamespace(model=condition['model'],runner=condition['runner'],
                    task_id='manifest-review' if task_fixture else None,output=str(folder),goal=goal,service=url,
                    interface=cli.interface)
                loop=Session(args,condition['scenario']);barrier.wait();start=time.perf_counter();error=None
                loop.deadline=start+300
                try:
                    loop.run()
                except Exception as exc:
                    error=repr(exc)
                state=adjudicate(store.path,goal,task_fixture)
                (folder/'oracle.json').write_text(json.dumps(state,indent=2))
                row=dict(batch=index,agent=agent,goal=goal,**condition,error=error,
                    interface=cli.interface,
                    duration_s=time.perf_counter()-start,model_calls=loop.model_calls,tool_calls=loop.tool_calls,
                    state_correct=state['state_correct'],duplicate_effects=state['duplicate_effects'],
                    unplanned_records=state['unplanned_records'],
                    committed_effects=state['committed_effects'],intervention_exercised=loop.injected)
                (folder/'result.json').write_text(json.dumps(row,indent=2))
                return row
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=condition['agents']) as pool:
                    rows=list(pool.map(execute,range(condition['agents'])))
                all_rows.extend(rows)
            finally:
                done.set();thread.join(timeout=5)
                ollama('generate',dict(model=condition['model'],keep_alive=0))
        (output/'results.json').write_text(json.dumps(all_rows,indent=2))
        print(json.dumps(dict(batch=index,**condition,correct=sum(r['state_correct'] for r in rows),
                              duplicate_effects=sum(r['duplicate_effects'] for r in rows))),flush=True)
    print('MULTIAGENT_COMPLETE',len(all_rows),flush=True)


def validate():
    """Known-answer collector controls; explicitly no model inference."""
    output=ROOT/'results'/('multiagent-validation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir();checks=[]
    for scenario,expected in [('nominal_create',1),('lost_ack_retry',2),('lost_ack_idempotent',1)]:
        folder=output/scenario;folder.mkdir();store=JobStore(folder/'application.sqlite')
        with serve(store,Trace(folder/'application.jsonl')) as url:
            args=SimpleNamespace(model='qwen3.5:4b',runner='minimal',task_id=None,
                output=str(folder),goal='known-goal',service=url)
            loop=Session(args,scenario);loop.last_request_id='constructed-validation-packet'
            loop.pending=[dict(function=dict(name='create_job',arguments=dict(title='Check dataset manifest',priority='normal')))]
            loop.tools();state=adjudicate(store.path,args.goal,None)
            assert len(state['jobs'])==expected and state['duplicate_effects']==expected-1
            assert state['state_correct']==(expected==1)
            checks.append(dict(scenario=scenario,commits=expected,passed=True))
    folder=output/'semantic_counterexamples';folder.mkdir();store=JobStore(folder/'application.sqlite')
    store.create('g',dict(title='Check dataset manifest',priority='normal'),'first')
    store.create('g',dict(title='Different unrequested job',priority='normal'),'second')
    state=adjudicate(store.path,'g',None)
    assert not state['state_correct'] and state['duplicate_effects']==0 and state['unplanned_records']==1
    checks.append(dict(scenario='different_extra_record_is_unplanned_not_duplicate',passed=True))
    store.reset();store.create('g',dict(title='Check dataset manifest',priority='normal'),'seed')
    state=adjudicate(store.path,'g',None)
    assert state['state_correct'] and state['committed_effects']==0 and state['duplicate_effects']==0
    checks.append(dict(scenario='existing_desired_state_needs_no_new_commit',passed=True))
    store.create('g',dict(title='Check dataset manifest',priority='normal'),'duplicate')
    assert adjudicate(store.path,'g',None)['duplicate_effects']==1
    checks.append(dict(scenario='duplicate_of_existing_record_detected',passed=True))
    report=dict(live_model=False,track='constructed_collector_validation',checks=checks)
    (output/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':
    validate() if '--validate-only' in sys.argv else main()
