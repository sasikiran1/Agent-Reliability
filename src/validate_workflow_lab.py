"""Constructed measurement/readiness/cleanup checks. No live model."""
import json
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

from local_lab import JobStore, Trace, workflow_audit, audit, serve
from validate_local_lab import post

ROOT=Path(__file__).resolve().parents[1]


def assert_closed(url):
    parsed=urlparse(url)
    try:
        with socket.create_connection((parsed.hostname,parsed.port),timeout=.2):
            raise AssertionError('Server listener survived cleanup')
    except (ConnectionRefusedError,TimeoutError,OSError) as exc:
        if isinstance(exc,AssertionError):
            raise


def main():
    out=ROOT/'results'/('workflow-validation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir()
    fixture=json.loads((ROOT/'data/workflow-pilot-tasks.json').read_text())[0]
    store=JobStore(out/'application.sqlite');trace=Trace(out/'trace.jsonl');checks=[]
    blank=audit(store.path,'g','unused')['final_state_sha256']
    store.seed('g',fixture)
    baseline=workflow_audit(store.path,'g',fixture)
    def call(url,tool,args,**extra):
        return post(url,dict(goal_id='g',tool=tool,arguments=args,attempt_id=str(uuid.uuid4()),
                            parent_attempt=None,retry_source='direct_control',**extra))
    with serve(store,trace) as url:
        with urlopen(url+'/ready',timeout=2) as r:
            assert json.load(r)['ready']
        checks.append('readiness')
        try:
            call(url,'update_job',dict(job_id='missing',priority='high'))
            raise AssertionError('Expected explicit 409 error')
        except HTTPError as exc:
            assert exc.code==409 and 'not found' in exc.read().decode()
        checks.append('explicit_error_no_commit')
        assert not workflow_audit(store.path,'g',fixture)['effects']
        records=call(url,'list_jobs',{})['jobs']
        target=next(j['job_id'] for j in records if j['title']==fixture['target'])
        call(url,'update_job',dict(job_id=target,priority='high'))
        call(url,'create_followup',dict(parent_job_id=target,title=fixture['followup']))
        call(url,'list_jobs',{})
        result=workflow_audit(store.path,'g',fixture)
        assert result['correct'] and result['journal_consistent'] and len(result['effects'])==2
        (out/'direct-oracle.json').write_text(json.dumps(result,indent=2))
        checks.append('direct_multistep_persistent_correctness')
    assert_closed(url);checks.append('cleanup_after_success')
    try:
        with serve(store,trace) as url:
            raise RuntimeError('constructed caller failure')
    except RuntimeError:
        pass
    assert_closed(url);checks.append('cleanup_after_exception')
    from urllib.request import Request
    with serve(store,trace) as url:
        body=dict(goal_id='g',tool='list_jobs',arguments={},attempt_id=str(uuid.uuid4()),
                  intervention='delay_before_execution_100ms',retry_source='constructed_timeout_validation')
        try:
            urlopen(Request(url+'/tools',json.dumps(body).encode(),{'Content-Type':'application/json'}),timeout=.01)
            raise AssertionError('Expected actual client timeout')
        except (TimeoutError,socket.timeout):
            pass
    assert_closed(url);checks.append('cleanup_after_actual_client_timeout')
    stable=workflow_audit(store.path,'g',fixture)['final_state_sha256']
    try:
        with store.connect('forced_rollback') as db:
            db.execute('UPDATE jobs SET title=? WHERE job_id=?',('wrong',target))
            raise RuntimeError('constructed transaction failure')
    except RuntimeError:
        pass
    assert workflow_audit(store.path,'g',fixture)['final_state_sha256']==stable
    checks.append('data_and_trigger_journal_rollback_together')
    with store.connect('sensitivity') as db:
        db.execute('UPDATE jobs SET title=? WHERE job_id=?',('wrong',target))
    assert not workflow_audit(store.path,'g',fixture)['correct']
    assert workflow_audit(store.path,'g',fixture)['journal_consistent']
    checks.append('independent_oracle_rejects_wrong_state_even_with_consistent_journal')
    with store.connect() as db:
        db.execute("DELETE FROM effects WHERE attempt_id='sensitivity'")  # deliberate audit corruption
    assert not workflow_audit(store.path,'g',fixture)['journal_consistent']
    checks.append('journal_divergence_detected')
    store.reset()
    assert audit(store.path,'g','unused')['final_state_sha256']==blank
    checks.append('reset_restores_exact_blank_state')
    report=dict(live_model=False,track='constructed_measurement_validation',passed=True,checks=checks,
                original_seed=baseline,interventions=['caller_exception','100ms_reply_delay_and_10ms_client_timeout',
                'transaction_rollback','deliberate_wrong_state_and_journal_corruption'],output=str(out))
    (out/'summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(output=str(out),passed=True,checks=checks),indent=2))


if __name__=='__main__':
    main()
