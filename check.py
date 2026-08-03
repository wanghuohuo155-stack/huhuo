"""最小可运行检查：python check.py。任何核心逻辑写错都会以非零退出码失败。"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "rushi-skill" / "scripts"))

from rushi.config import Config
from rushi import builder, packager, verifier


SOURCE = "面对任何重要决定，先问自己：什么情况下我会彻底失败？\n每天只做一个决定。\n"

SKILL_MD = """---
name: demo-skill
description: |
  用户在重要决策前纠结、列好处却理不出头绪时使用。
  语言信号："我该不该"、"拿不定主意" / "should I", "can't decide"。
  不适用于：纯信息查询、日常琐事选择。
version: 0.1.0
source:
  title: 演示源
  author: rushi
  year: 2026
  span_id: 第一节
confidence: author-claim
related: []
freshness:
  checked_at: 2026-08-02T00:00:00+00:00
  expires_at: 2027-08-02T00:00:00+00:00
  policy: recheck-by-expiry
tags: [decision]
---

# 演示 Skill

## R — 原文（Reading）

> 面对任何重要决定，先问自己：什么情况下我会彻底失败？

---

## I — 方法论骨架（Interpretation）

先列出失败方式，再划掉可避免的，剩下的才是真风险。

---

## A1 — 书中的应用（Past Application）

### 案例 1: 示例

- **问题**: 示例问题
- **方法论的使用**: 先问最坏情况
- **结论**: 明确风险
- **结果**: 决策清晰

---

## A2 — 触发场景（Future Trigger）★

### 语言信号

- "我该不该做 X" / "should I"

---

## E — 可执行步骤（Execution）

1. **列出失败方式**
   - 完成标准: 至少 3 条

---

## B — 边界（Boundary）★

### 不要在以下情况使用

- 纯信息查询
"""

TRIGGER_TESTS = {
    "skill": "demo-skill",
    "version": "0.1.0",
    "test_cases": [
        {"id": "t1", "type": "should_trigger", "prompt": "我该不该接这个项目", "expected_behavior": "应激活"},
        {"id": "t2", "type": "should_trigger", "prompt": "拿不定主意要不要辞职", "expected_behavior": "应激活"},
        {"id": "t3", "type": "should_trigger", "prompt": "要不要投资这个新领域", "expected_behavior": "应激活"},
        {"id": "n1", "type": "should_not_trigger", "prompt": "帮我查一下 API 参数", "expected_behavior": "不应激活"},
        {"id": "n2", "type": "should_not_trigger", "prompt": "这家公司的护城河强不强", "expected_behavior": "不应激活本 skill"},
        {"id": "e1", "type": "edge_case", "prompt": "今天晚饭吃什么好", "expected_behavior": "不应调用（日常琐事）"},
    ],
}


def main() -> int:
    cfg = Config(project_dir=Path(tempfile.mkdtemp()))

    # 1. 忠实度校验：真引用必须 verified，假引用必须 unverified
    good = verifier.verify_claim(
        {
            "claim_id": "f01",
            "skill_slug": "demo-skill",
            "kind": "framework",
            "title": "先问最坏情况",
            "source_chapter": "第一节",
            "source_quote": "面对任何重要决定，先问自己：什么情况下我会彻底失败？",
            "summary": "先列出失败方式",
        },
        SOURCE,
        cfg,
    )
    assert good["status"] == "verified", good
    bad = dict(good)
    bad["source_quote"] = "这句引文不在源文本里"
    bad = verifier.verify_claim(bad, SOURCE, cfg)
    assert bad["status"] == "unverified", bad

    # 2. RIA++ 六段校验：完整通过，缺 B 段必须失败
    assert builder.validate_skill(SKILL_MD, cfg)[0] == []
    broken = SKILL_MD.replace("## B — 边界（Boundary）★", "## BX")
    assert any("缺少 B" in i for i in builder.validate_skill(broken, cfg)[0])

    # 3. 发布闸门：缺 TEST_REPORT.md 失败，齐全通过
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "demo"
        (build / "skills" / "demo-skill" / "tests").mkdir(parents=True)
        (build / "skills" / "demo-skill" / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
        (build / "skills" / "demo-skill" / "tests" / "trigger.json").write_text(
            json.dumps(TRIGGER_TESTS), encoding="utf-8"
        )
        (build / "PROVENANCE.md").write_text("p", encoding="utf-8")
        (build / "GLOSSARY.md").write_text("g", encoding="utf-8")
        (build / "INDEX.md").write_text("i", encoding="utf-8")
        assert packager.validate_build_dir(build), "缺少 TEST_REPORT.md 时应失败"
        (build / "TEST_REPORT.md").write_text("# TEST_REPORT.md\n- 整体判定: PASS\n", encoding="utf-8")
        assert packager.validate_build_dir(build) == []

    print("check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
