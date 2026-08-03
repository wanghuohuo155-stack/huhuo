import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401

from rushi.installer import InstallReport, install_pack, resolve_target, verify_install


def make_pack(root: Path) -> Path:
    pack = root / "pack"
    (pack / "skills" / "demo" / "tests").mkdir(parents=True)
    (pack / "skills" / "demo" / "SKILL.md").write_text("# demo", encoding="utf-8")
    (pack / "skills" / "demo" / "GLOSSARY.md").write_text("g", encoding="utf-8")
    (pack / "skills" / "demo" / "tests" / "trigger.json").write_text("{}", encoding="utf-8")
    return pack


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolve_target_unknown_host(self):
        with self.assertRaises(ValueError):
            resolve_target("unknown", "user")

    def test_resolve_target_bad_scope(self):
        with self.assertRaises(ValueError):
            resolve_target("codex", "project")

    def test_resolve_target_project_requires_project(self):
        with self.assertRaises(ValueError):
            resolve_target("claude", "project")

    def test_resolve_target_codex_user(self):
        with mock.patch.dict(
            "os.environ", {"CODEX_HOME": str(self.root / "ch")}, clear=False
        ):
            target = resolve_target("codex", "user")
        self.assertEqual(target, self.root / "ch" / "skills")

    def test_resolve_target_project(self):
        target = resolve_target("claude", "project", project=self.root / "proj")
        self.assertEqual(target, self.root / "proj" / ".claude" / "skills")

    def test_install_missing_skills(self):
        with self.assertRaises(ValueError):
            install_pack(self.root / "nope", "codex", "user", target=self.root / "t")

    def test_install_guard_self_target(self):
        pack = make_pack(self.root)
        with self.assertRaises(ValueError):
            install_pack(pack, "codex", "user", target=self.root)

    def test_install_real_copy(self):
        pack = make_pack(self.root)
        target = self.root / "skills-target"
        report = install_pack(pack, "codex", "user", target=target)
        self.assertEqual(len(report.installed), 1)
        self.assertTrue((target / "demo" / "SKILL.md").exists())
        self.assertTrue((target / "demo" / "GLOSSARY.md").exists())
        self.assertEqual(verify_install(report), [])

    def test_verify_install_detects_missing(self):
        report = InstallReport(
            host="codex", scope="user", target=self.root / "t", installed=[self.root / "t" / "ghost"], dry_run=False
        )
        issues = verify_install(report)
        self.assertEqual(len(issues), 1)
        self.assertIn("SKILL.md", issues[0])


if __name__ == "__main__":
    unittest.main()
