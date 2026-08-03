"""pipeline LLM 阶段（S1/S2/S4/S5）的 JSON 模式产物测试。"""

import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi.config import Config
from rushi.pipeline import PipelineState, StageContext, parse_json_output, run_stage
from fixtures import SKILL_MD, make_build_dir


class FakeProvider:
    name = "fake"

    def __init__(self, responses: list[tuple[str, str]]):
        self.responses = responses

    def complete(self, prompt: str, system: str = "", json_mode: bool | None = None) -> str:
        for marker, payload in self.responses:
            if marker in prompt:
                return payload
        return "{}"


class FlakyProvider(FakeProvider):
    """指定 marker 第一次返回非法 JSON，第二次起返回正常负载。"""

    def __init__(self, responses: list[tuple[str, str]], flaky_markers: set[str]):
        super().__init__(responses)
        self.flaky_markers = flaky_markers
        self.marker_calls: dict[str, int] = {}

    def complete(self, prompt: str, system: str = "", json_mode: bool | None = None) -> str:
        for marker, payload in self.responses:
            if marker in prompt:
                n = self.marker_calls.get(marker, 0) + 1
                self.marker_calls[marker] = n
                if marker in self.flaky_markers and n == 1:
                    return "not-json"
                return payload
        return "{}"


def make_provider() -> FakeProvider:
    return FakeProvider(
        [
            (
                "整书理解",
                '{"book_overview_md":"# B\\n## 1. 结构\\n- 一句话主旨: x\\n'
                '## 2. 解释\\n- 术语 1: ...\\n## 3. 批判\\n- 局限 1: ...\\n- 盲点 1: ...\\n- 假设 1: ...\\n'
                '## 4. 应用潜力\\n- 可 skill 化: y\\n- 不适合 skill 化: z\\n"}',
            ),
            (
                "框架提取器",
                '{"candidates":[{"id":"f01","title":"先问最坏情况","type":"framework",'
                '"source_chapter":"第一节",'
                '"source_quote":"面对任何重要决定，先问自己：什么情况下我会彻底失败？",'
                '"summary":"先列失败方式","tags":["decision"]}]}',
            ),
            ("原则提取器", '{"candidates":[]}'),
            ("案例提取器", '{"candidates":[]}'),
            ("反例提取器", '{"candidates":[]}'),
            ("术语提取器", '{"candidates":[]}'),
            (
                "待验证候选",
                '{"id":"f01","external_evidence":[],"contradicting_evidence":[],'
                '"falsification_test":"x","confidence":"unverified","notes":"n"}',
            ),
            ("待构造单元", json.dumps({"skill_md": SKILL_MD}, ensure_ascii=False)),
        ]
    )


class PipelineJsonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.build = make_build_dir(self.root / "build")
        self.cfg = Config(project_dir=self.root, json_mode=True)
        self.provider = make_provider()

    def tearDown(self):
        self.tmp.cleanup()

    def _ctx(self):
        return StageContext(self.cfg, self.build, self.provider)

    def test_s1_json_writes_book_overview(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S1", self._ctx())
        self.assertEqual(status, "done")
        text = (self.build / "BOOK_OVERVIEW.md").read_text(encoding="utf-8")
        self.assertIn("一句话主旨", text)

    def test_s2_json_writes_candidates(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S2", self._ctx())
        self.assertEqual(status, "done")
        files = sorted((self.build / "candidates").glob("*.json"))
        self.assertEqual(len(files), 5)
        data = json.loads((self.build / "candidates" / "frameworks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["source_quote"], "面对任何重要决定，先问自己：什么情况下我会彻底失败？")

    def test_s4_json_writes_results(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S4", self._ctx())
        self.assertEqual(status, "done")
        files = sorted((self.build / "s4").glob("*.json"))
        self.assertEqual(len(files), 5)
        data = json.loads((self.build / "s4" / "f01.json").read_text(encoding="utf-8"))
        self.assertEqual(data["confidence"], "unverified")

    def test_s5_json_writes_skill(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S5", self._ctx())
        self.assertEqual(status, "done")
        out = self.build / "skills" / "slow-gardener" / "SKILL.md"
        self.assertTrue(out.exists())
        self.assertEqual(out.read_text(encoding="utf-8"), SKILL_MD)

    def test_s1_legacy_raw_when_json_disabled(self):
        cfg = Config(project_dir=self.root, json_mode=False)
        provider = FakeProvider([("整书理解", "# 原始输出\n\n一句话主旨: x")])
        state = PipelineState.load(self.build)
        status = run_stage(state, "S1", StageContext(cfg, self.build, provider))
        self.assertEqual(status, "done")
        self.assertEqual(
            (self.build / "BOOK_OVERVIEW.md").read_text(encoding="utf-8"),
            "# 原始输出\n\n一句话主旨: x",
        )

    def test_parse_json_output(self):
        self.assertEqual(parse_json_output('```json\n{"a":1}\n```', "a"), 1)
        self.assertIsNone(parse_json_output("not json", "a"))
        self.assertIsNone(parse_json_output('{"b":2}', "a"))

    def test_s1_needs_provider_writes_prompt(self):
        state = PipelineState.load(self.build)
        status = run_stage(state, "S1", StageContext(self.cfg, self.build, None))
        self.assertEqual(status, "needs-provider")
        self.assertEqual(len(list((self.build / "prompts").glob("S1-*.md"))), 1)

    def test_s1_retries_on_invalid_json(self):
        provider = FlakyProvider(
            [("整书理解", '{"book_overview_md":"# B\\n- 一句话主旨: x\\n"}')],
            {"整书理解"},
        )
        state = PipelineState.load(self.build)
        status = run_stage(state, "S1", StageContext(self.cfg, self.build, provider))
        self.assertEqual(status, "done")
        self.assertEqual(provider.marker_calls["整书理解"], 2)
        self.assertTrue((self.build / "BOOK_OVERVIEW.md").exists())

    def test_s5_retries_on_invalid_json(self):
        provider = FlakyProvider(
            [("待构造单元", json.dumps({"skill_md": SKILL_MD}, ensure_ascii=False))],
            {"待构造单元"},
        )
        state = PipelineState.load(self.build)
        status = run_stage(state, "S5", StageContext(self.cfg, self.build, provider))
        self.assertEqual(status, "done")
        # 5 个 claim 各 1 次正常调用 + 首次失败后 1 次重试
        self.assertEqual(provider.marker_calls["待构造单元"], 6)
        self.assertEqual(len(list((self.build / "prompts").glob("S5-*.retry.md"))), 1)
        self.assertTrue((self.build / "skills" / "slow-gardener" / "SKILL.md").exists())

    def test_s5_persistent_failure_keeps_raw_review(self):
        provider = FakeProvider([("待构造单元", "not-json")])
        state = PipelineState.load(self.build)
        status = run_stage(state, "S5", StageContext(self.cfg, self.build, provider))
        self.assertEqual(status, "failed")
        raws = list((self.build / "s5-review").glob("*.raw.md"))
        self.assertEqual(len(raws), 5)
        self.assertEqual(raws[0].read_text(encoding="utf-8"), "not-json")


if __name__ == "__main__":
    unittest.main()
