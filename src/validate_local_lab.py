"""Controlled no-model HTTP controls and independent SQL-oracle validation."""
import csv
import http.client
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from local_lab import JobStore, Trace, audit, serve

ROOT = Path(__file__).resolve().parents[1]


def post(url, body):
    with urlopen(Request(url + '/tools', json.dumps(body).encode(), {'Content-Type': 'application/json'}), timeout=5) as r:
        return json.load(r)


def main():
    run = ROOT / 'results' / ('lab-validation-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir()
    trace, rows = Trace(run / 'trace.jsonl'), []
    for name, protected, lost_ack in [('nominal_direct', False, False), ('lost_ack_direct_retry', False, True),
                                      ('lost_ack_idempotent_retry', True, True)]:
        goal = name
        store = JobStore(run / f'{name}.sqlite')
        with serve(store, trace) as url:
            body = dict(goal_id=goal, tool='create_job', arguments=dict(title='Check dataset manifest', priority='normal'),
                        attempt_id=str(uuid.uuid4()), parent_attempt=None, retry_source='none',
                        idempotency_key=goal if protected else None, intervention='drop_reply_after_commit' if lost_ack else None)
            first = body['attempt_id']
            try:
                post(url, body)
                assert not lost_ack, 'Lost-reply control unexpectedly received reply'
            except (http.client.RemoteDisconnected, ConnectionError):
                assert lost_ack
            if lost_ack:
                body.update(attempt_id=str(uuid.uuid4()), parent_attempt=first, retry_source='researcher_direct_client', intervention=None)
                post(url, body)
        result = audit(store.path, goal, 'Check dataset manifest')
        expected_duplicates = 1 if lost_ack and not protected else 0
        assert result['duplicate_committed_effects'] == expected_duplicates
        assert result['correct'] == (expected_duplicates == 0)
        (run / f'{name}-oracle.json').write_text(json.dumps(result, indent=2))
        rows.append(dict(check=name, live_model=False, intervention='lost_commit_ack_then_one_explicit_retry' if lost_ack else 'none',
                         committed_effects=len(result['effects']), duplicate_effects=result['duplicate_committed_effects'], passed=True))

    store = JobStore(run / 'oracle-checks.sqlite')
    before = audit(store.path, 'g', 'Correct')['final_state_sha256']
    store.create('g', dict(title='Wrong', priority='normal'), 'a')
    assert not audit(store.path, 'g', 'Correct')['correct']
    store.reset()
    store.create('g', dict(title='Correct', priority='normal'), 'a', 'key')
    assert audit(store.path, 'g', 'Correct')['correct']
    # Wrong payload under same key must not commit another effect.
    try:
        store.create('g', dict(title='Changed', priority='normal'), 'b', 'key')
        raise AssertionError('Key collision was accepted')
    except ValueError:
        pass
    assert len(audit(store.path, 'g', 'Correct')['effects']) == 1
    store.create('g', dict(title='Correct', priority='normal'), 'b')
    assert not audit(store.path, 'g', 'Correct')['correct']
    assert audit(store.path, 'g', 'Correct')['duplicate_committed_effects'] == 1
    store.reset()
    store.create('g', dict(title='Correct', priority='normal'), 'a')
    with store.connect() as db:
        db.execute('DELETE FROM effects')  # deliberate partial-state corruption for oracle sensitivity
    assert not audit(store.path, 'g', 'Correct')['correct']
    store.reset()
    assert audit(store.path, 'g', 'Correct')['final_state_sha256'] == before
    rows.append(dict(check='wrong_value_duplicate_partial_state_key_conflict_and_reset', live_model=False,
                     intervention='deliberate_SQL_state_changes_on_disposable_data', committed_effects='', duplicate_effects='', passed=True))
    with (run / 'checks.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (run / 'summary.json').write_text(json.dumps(dict(track='controlled_harness_validation', live_model=False,
         checks=rows, all_passed=True, natural_tasks=0, recovery_measured=False,
         limitations='Researcher-created job application and explicit interventions; not a natural incident or published reproduction'), indent=2))
    print(json.dumps(dict(output=str(run), checks=rows), indent=2))


if __name__ == '__main__':
    main()
