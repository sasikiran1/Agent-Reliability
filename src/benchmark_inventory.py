"""Inventory pinned benchmark tasks without executing or modifying them (stdlib only)."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'feasibility'
SEED = '20261028'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(key):
    return hashlib.sha256(f'{SEED}:{key}'.encode()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'vendor/webarena-verified/assets/dataset/webarena-verified.json'
    tasks = json.loads(source.read_text(encoding='utf-8'))
    assert len({t['task_id'] for t in tasks}) == len(tasks), 'Duplicate task IDs'
    rows = []
    for task in tasks:
        kinds = sorted({e.get('expected', {}).get('task_type', 'unspecified') for e in task['eval']})
        statuses = sorted({e.get('expected', {}).get('status', 'unspecified') for e in task['eval']})
        rows.append(dict(task_id=task['task_id'], template_id=task['intent_template_id'],
                         sites='+'.join(sorted(task['sites'])), task_types='+'.join(kinds),
                         expected_statuses='+'.join(statuses), intent=task['intent'],
                         evaluator_types='+'.join(sorted({e['evaluator'] for e in task['eval']}))))
    # Split by template across the ENTIRE dataset, not independently by task/site.
    # This avoids same-template leakage between pilot and the candidate holdout.
    templates = sorted({r['template_id'] for r in rows}, key=rank)
    pilot_templates = set(templates[:max(1, len(templates) // 5)])
    for row in rows:
        row['split'] = 'development' if row['template_id'] in pilot_templates else 'holdout_candidate'
        row['annotation_status'] = 'needs_independent_state_oracle_review'
    with (OUT / 'task-inventory.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    # Candidate development tasks: one per template and task-type stratum, max 8.
    # Selection precedes model outcomes; it does not imply these tasks are supported.
    eligible = sorted((r for r in rows if r['sites'] == 'shopping_admin' and r['split'] == 'development'),
                      key=lambda r: rank(r['task_id']))
    chosen, seen = [], set()
    for row in eligible:
        key = (row['template_id'], row['task_types'])
        if key not in seen:
            chosen.append(row)
            seen.add(key)
        if len(chosen) == 8:
            break
    summary = dict(seed=SEED, dataset_sha256=digest(source), total_tasks=len(rows),
                   total_templates=len(templates), development_templates=len(pilot_templates),
                   sites=dict(Counter(r['sites'] for r in rows)),
                   task_types=dict(Counter(r['task_types'] for r in rows)),
                   candidate_pilot_tasks=chosen, selection_uses_model_outcomes=False,
                   main_sample_size='pending feasibility, oracle audit, effect-size/precision calculation')
    (OUT / 'task-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    sources = []
    for name, repository in [('webarena-verified', 'ServiceNow/webarena-verified'),
                             ('WorkArena', 'ServiceNow/WorkArena'), ('AgentLab', 'ServiceNow/AgentLab')]:
        checkout = ROOT / 'vendor' / name
        ref = checkout / '.git/refs/heads/main'
        sources.append(dict(name=name, url=f'https://github.com/{repository}', commit=ref.read_text().strip(),
                            readme_sha256=digest(checkout / 'README.md'), source_pin_only=True))
    (OUT / 'source-manifest.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'candidate_pilot_tasks'}, indent=2))
    print('Candidate pilot IDs:', [r['task_id'] for r in chosen])


if __name__ == '__main__':
    main()
