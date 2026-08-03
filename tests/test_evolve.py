import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi.config import Config
from rushi import evolve


class ConfigStub(Config):
    def __init__(self):
        super().__init__(project_dir=Path("."))


class EvolveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = ConfigStub()

    def tearDown(self):
        self.tmp.cleanup()

    def test_mis_trigger_proposal(self):
        rows = [
            {"skill_slug": "a", "event": "invocations"},
            {"skill_slug": "a", "event": "mis_trigger"},
            {"skill_slug": "a", "event": "invocations"},
        ]
        paths = evolve.generate_proposals(Path(self.tmp.name), rows, Path(self.tmp.name) / "p", self.cfg)
        self.assertEqual(len(paths), 1)
        text = paths[0].read_text(encoding="utf-8")
        self.assertIn("误触发率 50%", text)
        self.assertIn("审批", text)

    def test_negative_feedback_proposal(self):
        rows = [{"skill_slug": "b", "event": "negative"}] * 3
        paths = evolve.generate_proposals(Path(self.tmp.name), rows, Path(self.tmp.name) / "p", self.cfg)
        self.assertEqual(len(paths), 1)
        self.assertIn("负面反馈", paths[0].read_text(encoding="utf-8"))

    def test_clean_telemetry_no_proposal(self):
        rows = [{"skill_slug": "c", "event": "invocations"}, {"skill_slug": "c", "event": "positive"}]
        paths = evolve.generate_proposals(Path(self.tmp.name), rows, Path(self.tmp.name) / "p", self.cfg)
        self.assertEqual(paths, [])

    def test_aggregate(self):
        rows = [
            {"skill_slug": "a", "event": "invocations"},
            {"skill_slug": "a", "event": "mis_trigger"},
        ]
        stats = evolve.aggregate_telemetry(rows)
        self.assertEqual(stats["a"]["invocations"], 1)
        self.assertEqual(stats["a"]["mis_trigger"], 1)


if __name__ == "__main__":
    unittest.main()

