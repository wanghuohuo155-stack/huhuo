import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi import linker
from fixtures import SKILL_MD, make_build_dir


class LinkerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.build = make_build_dir(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_collect_skills(self):
        skills = linker.collect_skills(self.build)
        self.assertEqual([s.slug for s in skills], ["slow-gardener"])
        self.assertIn("decision", skills[0].tags)

    def test_resolve_related_ok(self):
        issues = linker.resolve_related(self.build)
        self.assertEqual(issues, [])

    def test_resolve_related_orphan(self):
        md = (self.build / "skills" / "slow-gardener" / "SKILL.md")
        text = md.read_text(encoding="utf-8").replace("related: []", "related: [{slug: ghost, relation: depends-on}]")
        md.write_text(text, encoding="utf-8")
        issues = linker.resolve_related(self.build)
        self.assertTrue(any("ghost" in i for i in issues))

    def test_discover_relations(self):
        skills = linker.collect_skills(self.build)
        relations = linker.discover_relations(skills, tag_threshold=0.0)
        self.assertIsInstance(relations, list)

    def test_render_index(self):
        skills = linker.collect_skills(self.build)
        md = linker.render_index(skills, [], "测试", "rushi", "主旨", "2026")
        self.assertIn("slow-gardener", md)
        self.assertIn("mermaid", md)

    def test_ensure_glossary_promotes_candidates(self):
        out = linker.ensure_glossary(self.build)
        self.assertTrue(out.exists())
        self.assertIn("墒情", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

