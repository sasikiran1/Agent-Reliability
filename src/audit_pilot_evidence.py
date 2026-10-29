"""Reconstruct model->attempt->commit->state chains; never score agent prose."""
import csv
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def events(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()] if path.exists() else []


def seconds(value):
    return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()


def main():
    rows=[]
    for run in sorted((ROOT/'results').glob('live-local-*')):
        if not (run/'result.json').exists():
            continue
        result=json.loads((run/'result.json').read_text())
        manifest=json.loads((run/'manifest.json').read_text())
        oracle=json.loads((run/'oracle.json').read_text())
        model=events(run/'model-tools.jsonl');app=events(run/'application.jsonl')
        requests={e['request_id']:e for e in model if e['kind']=='model_request'}
        tool_requests={e['attempt_id']:e for e in model if e['kind']=='tool_request'}
        tool_responses={e['attempt_id']:e for e in model if e['kind']=='tool_response'}
        app_attempts={e['request']['attempt_id']:e for e in app if e['kind']=='application_request'}
        committed={e['effect_id']:e for e in oracle['effects']}
        represented=[effect for e in app for effect in e.get('committed_effect_ids',[])]
        errors=[]
        chains=[]
        attempt_chains=[]
        model_responses={e['request_id']:e for e in model if e['kind']=='model_response'}
        for attempt,tool in tool_requests.items():
            parent=tool['parent_attempt']
            response=model_responses.get(parent)
            calls=response['response']['message'].get('tool_calls',[]) if response else []
            matched=any(call.get('id')==tool.get('provider_tool_call_id') and
                        call['function']['name']==tool['tool'] and call['function']['arguments']==tool['arguments'] for call in calls)
            execution=app_attempts.get(attempt)
            returned=tool_responses.get(attempt)
            if not (parent in requests and matched and execution and returned):
                errors.append('Unlinked execution attempt '+attempt)
            elif not (execution['request']['parent_attempt']==parent and
                      seconds(tool['utc'])<=seconds(execution['utc'])<=seconds(returned['utc'])):
                errors.append('Execution identity/timeline mismatch '+attempt)
            attempt_chains.append(dict(model_request_id=parent,provider_tool_call_id=tool.get('provider_tool_call_id'),
                execution_attempt_id=attempt,tool=tool['tool'],requested_utc=tool['utc'],
                application_response_utc=execution['utc'] if execution else None,
                http_status=execution.get('http_status') if execution else None,
                committed_effect_ids=execution.get('committed_effect_ids',[]) if execution else [],
                final_state_sha256=oracle['final_state_sha256']))
        if len(tool_requests)!=sum(e['kind']=='tool_request' for e in model):
            errors.append('Repeated execution-attempt identity in tool trace')
        if len(app_attempts)!=sum(e['kind']=='application_request' for e in app):
            errors.append('Repeated execution-attempt identity in application trace')
        if set(app_attempts)!=set(tool_requests):
            errors.append('Application execution attempts differ from issued tool requests')
        for effect_id,effect in committed.items():
            attempt=effect['attempt_id']
            tool=tool_requests.get(attempt)
            execution=app_attempts.get(attempt)
            response=tool_responses.get(attempt)
            parent=requests.get(tool['parent_attempt']) if tool else None
            linked=bool(parent and tool and execution and response and effect_id in execution['committed_effect_ids'])
            # SQLite UTC commit timestamps have millisecond precision; allow rounding tolerance.
            ordered=bool(linked and seconds(parent['utc'])<=seconds(tool['utc']) and
                         seconds(tool['utc'])-.002<=seconds(effect['committed_utc'])<=seconds(execution['utc'])+.002 and
                         seconds(execution['utc'])<=seconds(response['utc']))
            if not linked or not ordered:
                errors.append(f'Unlinked/unordered effect {effect_id}')
            chains.append(dict(model_request_id=tool.get('parent_attempt') if tool else None,
                               provider_tool_call_id=tool.get('provider_tool_call_id') if tool else None,
                               execution_attempt_id=attempt,effect_id=effect_id,
                               committed_utc=effect['committed_utc'],job_id=effect['job_id'],
                               final_state_sha256=oracle['final_state_sha256'],linked=linked,timestamps_ordered=ordered))
        if set(represented)!=set(committed) or len(represented)!=len(committed):
            errors.append('Application receipt effects disagree with independently audited committed effects')
        if result.get('worker_status')=='finished' and set(tool_requests)!=set(tool_responses):
            errors.append('Missing tool response in a supposedly finished task')
        for name,sha in manifest.get('source_sha256',{}).items():
            path=run/'source/src'/name
            if not path.exists():
                path=run/'source'/name
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
                errors.append('Source snapshot missing or mismatched: '+name)
        source=run/'source/src/local_lab.py'
        if not source.exists():
            source=run/'source/local_lab.py'
        if source.exists() and hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']['local_lab.py']:
            spec=importlib.util.spec_from_file_location('saved_local_lab',source)
            saved=importlib.util.module_from_spec(spec);spec.loader.exec_module(saved)
            recomputed=(saved.workflow_audit(run/'application.sqlite',result['task_id'],manifest['task_fixture'])
                        if manifest.get('task_fixture') else saved.audit(run/'application.sqlite',result['task_id'],'Check dataset manifest'))
            if recomputed!=oracle:
                errors.append('Recomputed SQL oracle differs from saved final state')
        responses=[e['response'] for e in model if e['kind']=='model_response']
        caps=sum(r.get('done_reason')=='length' for r in responses)
        resource=events(run/'resources.jsonl')
        if result['supervisor_status'].startswith('cancelled_ram'):
            outcome='resource_cancellation'
        elif result.get('worker_error'):
            outcome='worker_error_requires_adjudication'
        elif caps:
            outcome='generation_cap_observed'
        elif result['state_correct']:
            outcome='state_verified_success'
        else:
            outcome='incorrect_state_requires_transcript_adjudication'
        audit=dict(task_id=result['task_id'],track=result['track'],evidence_errors=errors,
                   complete=not errors,chains=chains,attempt_chains=attempt_chains,execution_attempts=len(app_attempts),
                   tool_requests=len(tool_requests),model_requests=len(requests),committed_effects=len(committed),
                   warmup_requests=sum(e['kind']=='warmup_request' for e in model),
                   context_truncation='unknown',generation_caps=caps,
                   maximum_prompt_eval_tokens=max((r.get('prompt_eval_count',0) for r in responses),default=0),
                   minimum_sampled_available_ram_bytes=min((e['free_ram_bytes'] for e in resource),default=None))
        (run/'evidence-audit.json').write_text(json.dumps(audit,indent=2))
        row=dict(task_id=result['task_id'],fixture_id=result.get('fixture_id','single-create'),model=result['model'],
                 runner=result['runner'],track=result['track'],state_correct=result['state_correct'],outcome=outcome,
                 model_requests=len(requests),tool_requests=len(tool_requests),execution_attempts=len(app_attempts),
                 committed_effects=len(committed),duplicate_effects=result['duplicate_effects'],
                 evidence_complete=not errors,task_duration_s=result.get('task_duration_s'),
                 total_duration_s=result['duration_s'],generation_caps=caps,
                 application_load_harm='not_measured',natural_recovery='not observed',output=run.name)
        rows.append(row)
    if rows:
        with (ROOT/'results/pilot-results.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=dict(utc=datetime.now(timezone.utc).isoformat(),results=rows,
                limitations='Controlled development only; old single-create cohort must not be pooled with multi-step cohort')
    (ROOT/'results/pilot-evidence-summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
