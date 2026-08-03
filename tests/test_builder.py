import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi.config import Config
from rushi import builder
from fixtures import SKILL_MD, TRIGGER_TESTS

import json


class ConfigStub(Config):
    def __init__(self):
        super().__init__(project_dir=Path("."))


class FrontmatterTest(unittest.TestCase):
    def test_parse_block_and_list(self):
        fm = builder.parse_frontmatter(SKILL_MD)
        self.assertEqual(fm["name"], "slow-gardener")
        self.assertIn("不适用", fm["description"])
        self.assertEqual(fm["confidence"], "author-claim")
        self.assertIsInstance(fm["related"], list)

    def test_parse_frontmatter_tolerates_one_space_indent(self):
        text = "---\nname: demo\n description: |\n  不适用于：A。\nversion: 0.1.0\n---\n"
        fm = builder.parse_frontmatter(text)
        self.assertEqual(fm["name"], "demo")
        self.assertIn("不适用于", fm["description"])

    def test_anti_trigger_accepts_when_not_to_use(self):
        text = SKILL_MD.replace("不适用于：纯信息查询、日常琐事选择、已有充分专业判断的领域。", "何时不用：纯信息查询。")
        issues, _ = builder.validate_skill(text, Config(project_dir=Path(".")))
        self.assertFalse(any("反触发" in i for i in issues))


class ValidateSkillTest(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigStub()

    def test_valid(self):
        issues, meta = builder.validate_skill(SKILL_MD, self.cfg)
        self.assertEqual(issues, [])
        self.assertEqual(set(meta["sections"]), {"R", "I", "A1", "A2", "E", "B"})

    def test_missing_b_section(self):
        text = SKILL_MD.replace("## B — 边界（Boundary）★", "## BX")
        issues, _ = builder.validate_skill(text, self.cfg)
        self.assertTrue(any("缺少 B" in i for i in issues))

    def test_description_without_anti_trigger(self):
        text = (
            SKILL_MD.replace("不适用于：纯信息查询、日常琐事选择、已有充分专业判断的领域。", "适用场景包括：多种日常场景。")
            .replace("要不要再想想", "是否再想想")
            .replace("can't decide", "hesitating")
        )
        issues, _ = builder.validate_skill(text, self.cfg)
        self.assertTrue(any("反触发" in i for i in issues))

    def test_long_description(self):
        text = SKILL_MD.replace(
            "不适用于：纯信息查询、日常琐事选择、已有充分专业判断的领域。",
            "不适用于：纯信息查询。" + "补充" * 200,
        )
        issues, _ = builder.validate_skill(text, self.cfg)
        self.assertTrue(any("> 300" in i for i in issues))


class CheckSkillDirTest(unittest.TestCase):
    def test_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "slow-gardener"
            (d / "tests").mkdir(parents=True)
            (d / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
            (d / "tests" / "trigger.json").write_text(
                json.dumps(TRIGGER_TESTS), encoding="utf-8"
            )
            issues = builder.check_skill_dir(d, ConfigStub())
            self.assertEqual(issues, [])

    def test_missing_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "slow-gardener"
            d.mkdir()
            (d / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
            issues = builder.check_skill_dir(d, ConfigStub())
            self.assertTrue(any("trigger.json" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
