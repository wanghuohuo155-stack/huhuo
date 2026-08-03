import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi.cli import main
from fixtures import make_build_dir


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "proj"
        self.project.mkdir()
        self.build = make_build_dir(self.root / "build")

    def tearDown(self):
        self.tmp.cleanup()

    def test_doctor(self):
        self.assertEqual(main(["doctor"]), 0)

    def test_init(self):
        rc = main(["init", "--project", str(self.project)])
        self.assertEqual(rc, 0)
        self.assertTrue((self.project / "rushi.json").exists())

    def test_ingest(self):
        src = self.root / "sample.txt"
        src.write_text("第一章\n\n内容一\n\n第二章\n\n内容二", encoding="utf-8")
        rc = main(
            [
                "ingest",
                "--project", str(self.project),
                "--slug", "demo",
                "--source", str(src),
                "--title", "示例",
                "--author", "rushi",
                "--year", "2026",
                "--kind", "doc",
            ]
        )
        self.assertEqual(rc, 0)
        build = self.project / "books" / "demo"
        self.assertTrue((build / "source.txt").exists())
        self.assertTrue((build / "source.manifest.json").exists())

    def test_verify_cli(self):
        rc = main(
            ["verify", "--build", str(self.build), "--project", str(self.project)]
        )
        self.assertEqual(rc, 0)
        self.assertTrue((self.build / "PROVENANCE.md").exists())

    def test_check_cli(self):
        rc = main(["check", "--build", str(self.build), "--project", str(self.project)])
        self.assertEqual(rc, 0)

    def test_link_cli(self):
        rc = main(
            [
                "link",
                "--build", str(self.build),
                "--project", str(self.project),
                "--title", "演示",
                "--author", "rushi",
                "--theme", "demo",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue((self.build / "INDEX.md").exists())

    def test_test_cli(self):
        rc = main(["test", "--build", str(self.build), "--project", str(self.project), "--mode", "mock"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.build / "TEST_REPORT.md").exists())

    def test_package_and_gate_cli(self):
        main(["verify", "--build", str(self.build), "--project", str(self.project)])
        main(["test", "--build", str(self.build), "--project", str(self.project), "--mode", "mock"])
        main(["link", "--build", str(self.build), "--project", str(self.project)])
        rc = main(
            [
                "package",
                "--build", str(self.build),
                "--project", str(self.project),
                "--name", "demo-pack",
                "--version", "0.1.0",
            ]
        )
        self.assertEqual(rc, 0)
        pack = self.project / "packs" / "demo-pack"
        self.assertTrue((pack / "pack.json").exists())
        rc = main(["gate", "--pack", str(pack)])
        self.assertEqual(rc, 0)

    def test_install_dry_run(self):
        main(["verify", "--build", str(self.build), "--project", str(self.project)])
        main(["test", "--build", str(self.build), "--project", str(self.project), "--mode", "mock"])
        main(["link", "--build", str(self.build), "--project", str(self.project)])
        main(
            [
                "package",
                "--build", str(self.build),
                "--project", str(self.project),
                "--name", "demo-pack",
            ]
        )
        pack = self.project / "packs" / "demo-pack"
        target = self.root / "skills-target"
        rc = main(
            [
                "install",
                "--pack", str(pack),
                "--host", "codex",
                "--scope", "user",
                "--target", str(target),
                "--dry-run",
            ]
        )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

