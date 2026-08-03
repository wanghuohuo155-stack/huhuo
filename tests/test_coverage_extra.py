"""补足覆盖率的边角测试：schema/linker/verifier/pipeline/CLI 未测分支。"""

import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi import builder, linker, schema, verifier
from rushi.cli import main
from rushi.config import Config
from rushi.pipeline import PipelineState, StageContext, run_stage
from fixtures import SKILL_MD, SOURCE_TEXT, TRIGGER_TESTS, make_build_dir


class FakeProvider:
    name = "fake"

    def __init__(self, payload: str, marker: str):
        self.payload = payload
        self.marker = marker

    def complete(self, prompt: str, system: str = "", json_mode: bool | None = None) -> str:
        return self.payload if self.marker in prompt else "{}"


class SchemaExtraTest(unittest.TestCase):
    def test_oneof(self):
        errors = schema.validate(
            1, {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        )
        self.assertEqual(errors, [])
        errors = schema.validate(True, {"oneOf": [{"type": "string"}, {"type": "integer"}]})
        self.assertEqual(len(errors), 1)

    def test_const_and_min_items(self):
        self.assertEqual(schema.validate("x", {"const": "x"}), [])
        self.assertTrue(schema.validate([], {"type": "array", "minItems": 1}))

    def test_additional_properties_false(self):
        errors = schema.validate(
            {"a": 1, "b": 2},
            {"type": "object", "properties": {"a": {}}, "additionalProperties": False},
        )
        self.assertTrue(any("未声明字段" in e for e in errors))

    def test_pattern_and_length(self):
        self.assertEqual(schema.validate("ABC", {"type": "string", "pattern": "^[A-Z]+$"}), [])
        self.assertTrue(schema.validate("ab", {"type": "string", "minLength": 3}))


class LinkerExtraTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.build = make_build_dir(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_ensure_glossary_missing_raises(self):
        (self.build / "candidates" / "glossary.md").unlink()
        (self.build / "GLOSSARY.md").unlink(missing_ok=True)
        with self.assertRaises(ValueError):
            linker.ensure_glossary(self.build)

    def test_discover_relations_threshold(self):
        skills = [
            linker.SkillMeta("a", self.build, "a", "desc", ["x", "y"], []),
            linker.SkillMeta("b", self.build, "b", "desc", ["x", "y"], []),
            linker.SkillMeta("c", self.build, "c", "desc", ["z"], []),
        ]
        rels = linker.discover_relations(skills, tag_threshold=0.3)
        self.assertEqual(len(rels), 1)
        self.assertEqual((rels[0]["slug_a"], rels[0]["slug_b"]), ("a", "b"))

    def test_render_index_confirmed_relations(self):
        skills = [
            linker.SkillMeta("a", self.build, "a", "描述", ["x"], []),
            linker.SkillMeta("b", self.build, "b", "描述", ["x"], []),
        ]
        rels = [{"slug_a": "a", "slug_b": "b", "relation": "depends-on", "status": "confirmed"}]
        md = linker.render_index(skills, rels, "T", "A", "M", "2026")
        self.assertIn("a --> b", md)
        self.assertIn("1. `a`", md)

    def test_collect_skills_string_related(self):
        md = (self.build / "skills" / "slow-gardener" / "SKILL.md")
        text = md.read_text(encoding="utf-8").replace("related: []", "related: [other]")
        md.write_text(text, encoding="utf-8")
        skills = linker.collect_skills(self.build)
        self.assertEqual(skills[0].related, [{"slug": "other", "relation": ""}])


class VerifierExtraTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = Config(project_dir=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_render_provenance_and_write(self):
        report = verifier.verify_claims(
            [
                {
                    "claim_id": "f01",
                    "skill_slug": "s",
                    "kind": "framework",
                    "title": "t",
                    "source_chapter": "c",
                    "source_quote": "面对任何重要决定，先问自己：什么情况下我会彻底失败？",
                    "summary": "s",
                }
            ],
            SOURCE_TEXT,
            self.cfg,
        )
        text = verifier.render_provenance(report["results"], report["stats"])
        self.assertIn("f01", text)
        out = verifier.write_provenance(self.root, report)
        self.assertTrue(out.exists())

    def test_verify_skill_quotes(self):
        missing = "# x\n\n## R — 原文（Reading）\n\n> 不存在的引文内容\n"
        results = verifier.verify_skill_quotes(missing, SOURCE_TEXT, self.cfg)
        self.assertEqual(results[0]["status"], "unverified")
        long = "# x\n\n## R — 原文（Reading）\n\n> " + "长" * 200 + "\n"
        results = verifier.verify_skill_quotes(long, SOURCE_TEXT, self.cfg)
        self.assertEqual(results[0]["status"], "length-failed")

    def test_extract_r_quotes_skips_attribution(self):
        md = "## R — 原文（Reading）\n\n> 引文内容\n> — 作者, 章节\n\n## I — x\n"
        quotes = verifier.extract_r_quotes(md)
        self.assertEqual(quotes, ["引文内容"])


class PipelineExtraTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.build = make_build_dir(self.root / "build")
        self.cfg_json = Config(project_dir=self.root, json_mode=True)
        self.cfg_legacy = Config(project_dir=self.root, json_mode=False)

    def tearDown(self):
        self.tmp.cleanup()

    def _state(self):
        return PipelineState.load(self.build)

    def test_s2_s4_s5_needs_provider(self):
        ctx = StageContext(self.cfg_json, self.build, None)
        self.assertEqual(run_stage(self._state(), "S2", ctx), "needs-provider")
        self.assertEqual(run_stage(self._state(), "S4", ctx), "needs-provider")
        self.assertEqual(run_stage(self._state(), "S5", ctx), "needs-provider")
        self.assertEqual(len(list((self.build / "prompts").glob("S2-*.md"))), 5)
        self.assertEqual(len(list((self.build / "prompts").glob("S4-*.md"))), 5)
        self.assertEqual(len(list((self.build / "prompts").glob("S5-*.md"))), 5)

    def test_s1_persistent_invalid_json_keeps_raw(self):
        provider = FakeProvider("not-json", "整书理解")
        status = run_stage(self._state(), "S1", StageContext(self.cfg_json, self.build, provider))
        self.assertEqual(status, "failed")
        raw = self.build / "s1-review" / "raw.md"
        self.assertTrue(raw.exists())
        self.assertEqual(raw.read_text(encoding="utf-8"), "not-json")

    def test_s5_validation_failure_keeps_review(self):
        bad_md = json.dumps({"skill_md": "# 标题\n\n## BX\n"}, ensure_ascii=False)
        provider = FakeProvider(bad_md, "待构造单元")
        status = run_stage(self._state(), "S5", StageContext(self.cfg_json, self.build, provider))
        self.assertEqual(status, "failed")
        reviews = list((self.build / "s5-review").glob("*.md"))
        self.assertEqual(len(reviews), 5)
        self.assertIn("校验失败原因", reviews[0].read_text(encoding="utf-8"))

    def test_legacy_raw_paths(self):
        provider = FakeProvider("# raw 输出\n\n内容", "输入")
        self.assertEqual(
            run_stage(self._state(), "S2", StageContext(self.cfg_legacy, self.build, provider)),
            "done",
        )
        self.assertTrue((self.build / "candidates" / "frameworks.md").exists())
        self.assertEqual(
            run_stage(self._state(), "S4", StageContext(self.cfg_legacy, self.build, provider)),
            "done",
        )
        self.assertTrue((self.build / "s4" / "f01.md").exists())
        skill_provider = FakeProvider(SKILL_MD, "待构造单元")
        self.assertEqual(
            run_stage(self._state(), "S5", StageContext(self.cfg_legacy, self.build, skill_provider)),
            "done",
        )
        self.assertTrue((self.build / "skills" / "slow-gardener" / "SKILL.md").exists())

    def test_package_gate_fail_and_evolve_skip(self):
        (self.build / "TEST_REPORT.md").unlink(missing_ok=True)
        self.assertEqual(
            run_stage(self._state(), "S8", StageContext(self.cfg_json, self.build), name="p", version="0.1.0"),
            "failed",
        )
        self.assertEqual(run_stage(self._state(), "S9", StageContext(self.cfg_json, self.build)), "failed")
        self.assertEqual(run_stage(self._state(), "S10", StageContext(self.cfg_json, self.build)), "skipped")


class CliExtraTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "proj"
        self.project.mkdir()
        self.build = make_build_dir(self.root / "build")

    def tearDown(self):
        self.tmp.cleanup()

    def test_stage_s1_mock_returns_needs_provider(self):
        rc = main(
            ["stage", "--build", str(self.build), "S1", "--project", str(self.project), "--mode", "mock"]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(len(list((self.build / "prompts").glob("S1-*.md"))), 1)

    def test_verify_skill_md(self):
        md = self.root / "skill.md"
        md.write_text(SKILL_MD, encoding="utf-8")
        self.assertEqual(
            main(["verify", "--build", str(self.build), "--project", str(self.project), "--skill-md", str(md)]),
            0,
        )
        bad = self.root / "bad.md"
        bad.write_text(SKILL_MD.replace("面对任何重要决定，先问自己：什么情况下我会彻底失败？", "不存在的引文"), encoding="utf-8")
        self.assertEqual(
            main(["verify", "--build", str(self.build), "--project", str(self.project), "--skill-md", str(bad)]),
            1,
        )

    def test_gate_missing_pack(self):
        self.assertEqual(main(["gate", "--pack", str(self.root / "nope")]), 1)

    def test_report(self):
        self.assertEqual(main(["report", "--build", str(self.build)]), 0)

    def test_evolve_cli(self):
        telemetry = self.root / "telemetry.jsonl"
        telemetry.write_text(
            '{"skill_slug":"s","event":"invocations"}\n{"skill_slug":"s","event":"mis_trigger"}\n',
            encoding="utf-8",
        )
        out = self.root / "proposals"
        rc = main(
            [
                "evolve",
                "--project", str(self.project),
                "--pack", str(self.root),
                "--telemetry", str(telemetry),
                "--out", str(out),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(len(list(out.glob("*.md"))), 1)

    def test_doctor_broken_config(self):
        (self.project / "rushi.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(main(["doctor", "--project", str(self.project)]), 1)

    def test_install_real_copy(self):
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
        target = self.root / "target"
        rc = main(
            [
                "install",
                "--pack", str(self.project / "packs" / "demo-pack"),
                "--host", "codex",
                "--scope", "user",
                "--target", str(target),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue((target / "slow-gardener" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
