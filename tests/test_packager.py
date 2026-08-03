import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi import evaluator, linker, packager, verifier
from fixtures import make_build_dir


class PackagerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.build = make_build_dir(Path(self.tmp.name))
        # 生成发布必需产物
        source = (self.build / "source.txt").read_text(encoding="utf-8")
        claims = []
        for line in (self.build / "claims.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                import json

                claims.append(json.loads(line))
        from rushi.config import Config

        cfg = Config(project_dir=Path(self.tmp.name))
        report = verifier.verify_claims(claims, source, cfg)
        verifier.write_provenance(self.build, report)
        evaluator.write_test_report(self.build, evaluator.run_trigger_tests(self.build, mode="mock"))
        linker.ensure_glossary(self.build)
        linker.write_index(self.build, {"title": "t", "author": "a", "theme": "m", "created": "2026"}, [])

    def tearDown(self):
        self.tmp.cleanup()

    def test_validate_build_dir_ok(self):
        self.assertEqual(packager.validate_build_dir(self.build), [])

    def test_validate_build_dir_missing_report(self):
        (self.build / "TEST_REPORT.md").unlink()
        issues = packager.validate_build_dir(self.build)
        self.assertTrue(any("TEST_REPORT" in i for i in issues))

    def test_build_pack_and_validate(self):
        pack = packager.build_pack(self.build, Path(self.tmp.name) / "packs", "demo-pack", "0.1.0")
        self.assertTrue((pack / "pack.json").exists())
        self.assertTrue((pack / "skills" / "slow-gardener" / "GLOSSARY.md").exists())
        spec_dir = Path(__file__).resolve().parents[1] / "rushi-skill" / "references" / "specs"
        issues = packager.validate_pack(pack, spec_dir)
        self.assertEqual(issues, [])

    def test_build_pack_refuses_incomplete(self):
        (self.build / "PROVENANCE.md").unlink()
        with self.assertRaises(ValueError):
            packager.build_pack(self.build, Path(self.tmp.name) / "packs", "demo", "0.1.0")


if __name__ == "__main__":
    unittest.main()

