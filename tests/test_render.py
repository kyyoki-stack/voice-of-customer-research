"""Synthetic renderer contract tests; no collection or browser verification."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('renderer', Path(__file__).resolve().parents[1] / 'voice-of-customer-research/scripts/render.py')
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        (self.project / 'data').mkdir()
        (self.project / 'docs').mkdir()
        self.write_csv('feedback.csv', renderer.REQUIRED, [dict(sample_id='F1', platform='Synthetic', quote='Synthetic off-topic feedback', source_url='https://example.com/review', relevance='不相关', sentiment='中性')])
        self.write_csv('needs.csv', renderer.NEED_FIELDS, [])
        for filename in ('01-数据分析报告.md', '02-MRD.md', '03-洞察总结.md'):
            (self.project / 'docs' / filename).write_text('# Synthetic only\nNo actual collection.', encoding='utf-8')

    def write_csv(self, filename, fields, rows):
        with (self.project / 'data' / filename).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=sorted(fields))
            writer.writeheader()
            writer.writerows(rows)

    def render_audit(self, sample_ids, url='https://example.com/review'):
        self.write_csv('source_audit.csv', {'source_id', 'url', 'status', 'decision', 'sample_ids'}, [dict(source_id='S1', url=url, status='Synthetic', decision='Synthetic', sample_ids=sample_ids)])
        return renderer.render(self.project, 'Synthetic ecommerce', self.project / 'research.html')

    def test_missing_sample_is_rejected_before_output(self):
        with self.assertRaisesRegex(ValueError, 'S1:'):
            self.render_audit('F1, MISSING')
        self.assertFalse((self.project / 'research.html').exists())

    def test_excluded_feedback_remains_valid_audit_evidence(self):
        result = self.render_audit(' F1 , ')
        self.assertEqual(result['related'], 0)
        page = (self.project / 'research.html').read_text(encoding='utf-8')
        payload = page.split('<script id="audit-data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(json.loads(payload)[0]['sample_ids'], 'F1')

    def test_failed_source_without_samples_is_allowed(self):
        self.write_csv('feedback.csv', renderer.REQUIRED, [])
        result = self.render_audit('', url='')
        self.assertEqual(result['collected'], 0)

    def test_nonvehicle_report_has_general_evidence_boundary(self):
        self.render_audit('F1')
        page = (self.project / 'research.html').read_text(encoding='utf-8')
        self.assertNotIn('不代表全部车主', page)
        self.assertIn('不代表全部用户', page)
        self.assertIn('本次数据报告', page)


if __name__ == '__main__':
    unittest.main()
