import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi import evaluator
from fixtures import make_build_dir


class MockJudgeTest(unittest.TestCase):
    def test_decision(self):
        judge = evaluator.MockJudge(
            [{"slug": "a", "description": "用户拿不定主意要不要做重大决定时使用"}],
            threshold=0.12,
        )
        slug, score, _ = judge.decide("我拿不定主意要不要辞职")
        self.assertEqual(slug, "a")
        self.assertGreaterEqual(score, 0.12)

    def test_no_trigger_on_unrelated(self):
        judge = evaluator.MockJudge(
            [{"slug": "a", "description": "用户拿不定主意要不要做重大决定时使用"}],
            threshold=0.12,
        )
        slug, _, _ = judge.decide("帮我查一下这个 API 的参数")
        self.assertIsNone(slug)


class TriggerTestsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.build = make_build_dir(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_report_pass(self):
        report = evaluator.run_trigger_tests(self.build, mode="mock")
        self.assertTrue(report["pass"], report)
        self.assertEqual(report["bait_failures"], 0)
        self.assertEqual(report["grand_total"], 8)

    def test_bait_failure_detected(self):
        trigger = (
            self.build / "skills" / "slow-gardener" / "tests" / "trigger.json"
        )
        import json

        data = json.loads(trigger.read_text(encoding="utf-8"))
        data["test_cases"][3]["prompt"] = "我拿不定主意要不要做重大决定"
        trigger.write_text(json.dumps(data), encoding="utf-8")
        report = evaluator.run_trigger_tests(self.build, mode="mock")
        self.assertFalse(report["pass"])
        self.assertEqual(report["bait_failures"], 1)

    def test_report_rendering(self):
        report = evaluator.run_trigger_tests(self.build, mode="mock")
        text = evaluator.render_test_report(report)
        self.assertIn("PASS", text)
        self.assertIn("slow-gardener", text)


if __name__ == "__main__":
    unittest.main()
