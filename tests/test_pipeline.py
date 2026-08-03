import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi.config import Config
from rushi.pipeline import PipelineState, StageContext, run_stage
from rushi import content
from fixtures import make_build_dir


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.build = make_build_dir(self.root / "build")
        self.cfg = Config(project_dir=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_state_roundtrip(self):
        state = PipelineState.load(self.build)
        state.mark("S3", "done", "ok")
        state2 = PipelineState.load(self.build)
        self.assertEqual(state2.stages["S3"]["status"], "done")
        md = (self.build / "PIPELINE_STATE.md").read_text(encoding="utf-8")
        self.assertIn("S3", md)
        self.assertIn("✅", md)

    def test_s3_stage(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S3", StageContext(self.cfg, self.build))
        self.assertEqual(status, "done")
        self.assertTrue((self.build / "PROVENANCE.md").exists())

    def test_s1_needs_provider(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S1", StageContext(self.cfg, self.build))
        self.assertEqual(status, "needs-provider")
        prompts = list((self.build / "prompts").glob("S1-*.md"))
        self.assertEqual(len(prompts), 1)

    def test_s7_stage(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S7", StageContext(self.cfg, self.build))
        self.assertEqual(status, "done")
        self.assertTrue((self.build / "TEST_REPORT.md").exists())

    def test_ingest_stage(self):
        src = self.root / "src.txt"
        src.write_text("第一节\n\n内容\n\n第二节\n\n更多内容", encoding="utf-8")
        state = PipelineState.load(self.build)
        status = run_stage(
            state,
            "S0",
            StageContext(self.cfg, self.build),
            source=src,
            title="t",
            author="a",
            year="2026",
            kind="doc",
        )
        self.assertEqual(status, "done")
        manifest = content.load_manifest(self.build)
        self.assertEqual(manifest.title, "t")


if __name__ == "__main__":
    unittest.main()
