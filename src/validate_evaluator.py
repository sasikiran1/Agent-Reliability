"""Offline validation using upstream supplied traces, NOT new agent results."""
import copy
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from webarena_verified.api.webarena_verified import WebArenaVerified
from webarena_verified.types.config import WebArenaVerifiedConfig

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/setup/evaluator-validation'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    config = WebArenaVerifiedConfig(
        test_data_file=ROOT / 'vendor/webarena-verified/assets/dataset/webarena-verified.json',
        environments={'__SHOPPING_ADMIN__': {'urls': ['http://localhost:7780']}},
    )
    evaluator = WebArenaVerified(config=config)
    rows = []
    for task_id in (107, 108):
        fixture = ROOT / f'vendor/webarena-verified/examples/agent_logs/demo/{task_id}'
        expected = json.loads((fixture / 'eval_result.json').read_text(encoding='utf-8'))
        result = evaluator.evaluate_task(task_id=task_id, agent_response=fixture / 'agent_response.json',
                                         network_trace=fixture / 'network.har')
        actual = result.model_dump(mode='json')
        (OUT / f'{task_id}.json').write_text(json.dumps(actual, indent=2), encoding='utf-8')
        matched = actual['status'] == expected['status'] and actual['score'] == expected['score']
        rows.append(dict(check=f'provided_fixture_{task_id}', expected_status=expected['status'],
                         observed_status=actual['status'], matched=matched,
                         fixture_sha256=hashlib.sha256((fixture / 'agent_response.json').read_bytes()).hexdigest()))
    # A deliberate bad-answer control checks sensitivity; it is not a model failure.
    fixture = ROOT / 'vendor/webarena-verified/examples/agent_logs/demo/108'
    bad = copy.deepcopy(json.loads((fixture / 'agent_response.json').read_text(encoding='utf-8')))
    for item in bad['retrieved_data']:
        item['count'] = -999
    result = evaluator.evaluate_task(task_id=108, agent_response=bad, network_trace=fixture / 'network.har')
    actual = result.model_dump(mode='json')
    (OUT / '108-deliberate-wrong-count.json').write_text(json.dumps(actual, indent=2), encoding='utf-8')
    rows.append(dict(check='deliberately_corrupted_fixture_108', expected_status='failure',
                     observed_status=actual['status'], matched=actual['status'] == 'failure'))
    packages = {p.metadata['Name']: p.version for p in importlib.metadata.distributions()}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), track='controlled_setup', live_model=False,
                  new_agent_tasks_attempted=0, fixture_checks=rows, all_matched=all(r['matched'] for r in rows),
                  python=platform.python_version(), packages=packages,
                  limitations='Offline answer/trace checks only; application commit/effect oracles not validated')
    (OUT / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'packages'}, indent=2))
    if not report['all_matched']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
