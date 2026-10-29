"""Validate the analysis-critical split invariants, not benchmark outcomes."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InventoryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'data/feasibility/task-inventory.csv').open(encoding='utf-8') as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.summary = json.loads((ROOT / 'data/feasibility/task-summary.json').read_text())

    def test_complete_source_coverage(self):
        source = ROOT / 'vendor/webarena-verified/assets/dataset/webarena-verified.json'
        tasks = json.loads(source.read_text())
        self.assertEqual({int(r['task_id']) for r in self.rows}, {t['task_id'] for t in tasks})
        self.assertEqual(len(self.rows), len(tasks))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), self.summary['dataset_sha256'])

    def test_templates_do_not_cross_split(self):
        development = {r['template_id'] for r in self.rows if r['split'] == 'development'}
        holdout = {r['template_id'] for r in self.rows if r['split'] == 'holdout_candidate'}
        self.assertFalse(development & holdout)
        self.assertEqual(len(development | holdout), self.summary['total_templates'])

    def test_pilot_excludes_holdout_and_other_sites(self):
        by_id = {int(r['task_id']): r for r in self.rows}
        for candidate in self.summary['candidate_pilot_tasks']:
            row = by_id[candidate['task_id']]
            self.assertEqual(row['split'], 'development')
            self.assertEqual(row['sites'], 'shopping_admin')
        self.assertFalse(self.summary['selection_uses_model_outcomes'])


if __name__ == '__main__':
    unittest.main()
