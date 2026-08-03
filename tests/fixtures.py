"""测试夹具：构造一个最小可用 build 目录（含源文本、claims、一个 skill）。"""

from __future__ import annotations

import json
from pathlib import Path


SOURCE_TEXT = """# 慢园丁手记

第一节：决定之前

面对任何重要决定，先问自己：什么情况下我会彻底失败？把失败的方式写下来，
然后逐一划掉那些可以通过准备避免的失败。剩下的那条，才是真正需要恐惧的。

园丁种下种子之前不会问"它什么时候开花"，而是问"什么会杀死它"。干旱、虫害、
错季播种。他知道这些，才能决定是否值得种。

每天只做一个决定。做太多决定的人，最后连浇水的时间都没有。我见过太多园丁
在春天同时改造整座花园，然后在夏天精疲力竭，让一切荒芜。

第二节：失败教会我的事

有一年我为了赶在雨季前完成移植，跳过检查土壤墒情。结果根球全部烂在土里。
那不是天气的错，是急躁的错。赶时间不是策略，是没策略。

重要的决定要放在早晨做。早晨的头脑像清晨的土壤，松软而清醒。傍晚做的决定
往往带着一天的疲惫和情绪，就像在暴雨里修剪树枝。

第三节：术语

墒情：土壤含水量的状态，决定根系能否呼吸。园丁说"墒情好"，和普通人说的
"土挺湿"不是一回事——前者是判断，后者是感觉。

慢决定：一种决策节奏，指在信息完整之前不行动，但一旦行动就不反复。它不是
拖延，拖延是害怕行动，慢决定是等待条件。
"""


CLAIMS = [
    {
        "claim_id": "f01",
        "skill_slug": "slow-gardener",
        "kind": "framework",
        "title": "先问最坏情况",
        "source_chapter": "第一节",
        "source_quote": "面对任何重要决定，先问自己：什么情况下我会彻底失败？",
        "summary": "决策前先列出失败方式，划掉可通过准备避免的，剩下的才是真风险。",
        "tags": ["decision", "risk"],
    },
    {
        "claim_id": "p01",
        "skill_slug": "slow-gardener",
        "kind": "principle",
        "title": "每天只做一个决定",
        "source_chapter": "第一节",
        "source_quote": "每天只做一个决定。",
        "summary": "限制决策数量，避免决策疲劳耗尽执行资源。",
        "tags": ["decision", "focus"],
    },
    {
        "claim_id": "c01",
        "skill_slug": "slow-gardener",
        "kind": "case",
        "title": "雨季移植的失败",
        "source_chapter": "第二节",
        "source_quote": "赶时间不是策略，是没策略。",
        "summary": "跳过墒情检查导致根球烂掉，说明赶时间替代了决策流程。",
        "tags": ["case", "failure"],
    },
    {
        "claim_id": "x01",
        "skill_slug": "slow-gardener",
        "kind": "counter-example",
        "title": "傍晚做决定",
        "source_chapter": "第二节",
        "source_quote": "傍晚做的决定往往带着一天的疲惫和情绪。",
        "summary": "疲劳与情绪是决策质量的头号杀手。",
        "tags": ["bias", "warning"],
    },
    {
        "claim_id": "g01",
        "skill_slug": "slow-gardener",
        "kind": "term",
        "title": "慢决定",
        "source_chapter": "第三节",
        "source_quote": "它不是拖延，拖延是害怕行动，慢决定是等待条件。",
        "summary": "在信息完整前不行动，行动后不反复。",
        "tags": ["term"],
    },
]


SKILL_MD = """---
name: slow-gardener
description: |
  用户在重要决策前纠结、列好处却理不出头绪，或想避免冲动决定时使用。
  语言信号："我该不该"、"拿不定主意"、"要不要再想想"、"是不是也该"、"大家都在做" /
  "should I", "can't decide", "everyone else is doing it"。
  不适用于：纯信息查询、日常琐事选择、已有充分专业判断的领域。
  反触发信号：天气、菜谱、外卖、出行等日常信息查询不触发；"今晚吃什么""明天天气"等琐事不触发。
version: 0.1.0
source:
  title: 慢园丁手记
  author: 入世示例
  year: 2026
  span_id: 第一节
confidence: author-claim
related: []
freshness:
  checked_at: 2026-08-02T00:00:00+00:00
  expires_at: 2027-08-02T00:00:00+00:00
  policy: recheck-by-expiry
tags: [decision, risk, focus]
---

# 慢决定（先问最坏情况）

## R — 原文（Reading）

> 面对任何重要决定，先问自己：什么情况下我会彻底失败？
>
> — 慢园丁手记, 第一节

---

## I — 方法论骨架（Interpretation）

慢决定是一个决策框架，核心是两条：

1. 先问最坏情况，而不是先算最好收益；
2. 限制每天的重大决策数量，保护执行资源。

它把"决策"从一次头脑活动变成一个小流程：列失败方式 → 划掉可避免的 →
只恐惧剩下的那一条。

---

## A1 — 书中的应用（Past Application）

### 案例 1: 雨季移植

- **问题**: 赶在雨季前完成移植
- **方法论的使用**: 跳过墒情检查，用"赶时间"替代决策流程
- **结论**: 根球全部烂在土里
- **结果**: 损失一季收成

---

## A2 — 触发场景（Future Trigger）★

### 用户会在什么情境下需要？

1. 面临重要决定且列了一堆好处
2. 感觉到"再不做就来不及"的催促
3. 一天内要做多个重大决定

### 语言信号

- "我该不该接这个项目？" / "should I take this deal?"
- "拿不定主意" / "can't decide"
- "大家都在冲，我是不是也该冲" / "FOMO"

### 与相邻 skill 的区分

- 与 `margin-of-safety` 的区别：安全边际问价格，慢决定问决策节奏。

---

## E — 可执行步骤（Execution）

1. **列出失败方式**
   - 完成标准: 写出至少 3 种"什么情况下我会彻底失败"

2. **划掉可通过准备避免的失败**
   - 完成标准: 每划掉一条都对应一个具体准备动作；且必须至少保留 1 条不可控风险
   - 判停条件: 若所有风险都被划掉 → 把"准备动作本身可能失败/执行不到位"列为剩余真风险，
     禁止得出"无风险"结论；若剩余真风险只有这一条 → 跳到步骤 3，不得跳到步骤 4

3. **审视剩下的真风险**
   - 完成标准: 能说出它发生的概率和代价

4. **给出决策**
   - 完成标准: 明确"做/不做/等条件"，并注明等待什么条件

---

## B — 边界（Boundary）★

### 不要在以下情况使用

- 纯信息查询
- 时间窗口极短且无需深度分析的琐事

### 作者警告的失败模式

- 把"赶时间"当策略
- 傍晚/疲劳时做决定
- 把"可以通过准备避免"误解为"可以全部避免"——准备动作本身可能失败，
  必须保留至少 1 条不可控风险作为真风险

### 作者盲点 / 时代局限

- 慢节奏框架可能不适用高压快反馈环境（如交易大厅）

---

## 相关 skills

- 暂无（示例包）

---

## 审计信息

- 验证: V1/V2/V3 + 外部验证见 PROVENANCE.md
- 测试: 见 TEST_REPORT.md
- 版本: 0.1.0
"""


TRIGGER_TESTS = {
    "skill": "slow-gardener",
    "version": "0.1.0",
    "minimum_pass_rate": 0.8,
    "test_cases": [
        {
            "id": "should-trigger-01",
            "type": "should_trigger",
            "prompt": "我该不该接这个新项目？列了一堆好处但还是没底",
            "expected_behavior": "应激活 slow-gardener，先列出最坏情况",
            "notes": "决策纠结",
        },
        {
            "id": "should-trigger-02",
            "type": "should_trigger",
            "prompt": "拿不定主意要不要辞职创业",
            "expected_behavior": "应激活 slow-gardener",
            "notes": "拿不定主意",
        },
        {
            "id": "should-trigger-03",
            "type": "should_trigger",
            "prompt": "大家都在冲这个赛道，我是不是也该冲",
            "expected_behavior": "应激活 slow-gardener，检查 FOMO",
            "notes": "FOMO",
        },
        {
            "id": "should-not-trigger-01",
            "type": "should_not_trigger",
            "prompt": "帮我查一下这个 API 的参数",
            "expected_behavior": "不应激活本 skill，这是纯信息查询",
            "notes": "诱饵：信息查询",
        },
        {
            "id": "should-not-trigger-02",
            "type": "should_not_trigger",
            "prompt": "这家公司的护城河强不强",
            "expected_behavior": "不应激活本 skill，应激活 economic-moat 类竞争分析 skill",
            "notes": "跨 skill 混淆诱饵",
        },
        {
            "id": "should-not-trigger-03",
            "type": "should_not_trigger",
            "prompt": "今天天气怎么样",
            "expected_behavior": "不应激活本 skill，这是日常信息查询",
            "notes": "诱饵：遥测误触发场景",
        },
        {
            "id": "should-not-trigger-04",
            "type": "should_not_trigger",
            "prompt": "晚饭吃什么好",
            "expected_behavior": "不应激活本 skill，这是日常琐事",
            "notes": "诱饵：遥测误触发场景",
        },
        {
            "id": "edge-01",
            "type": "edge_case",
            "prompt": "今天晚饭吃什么好",
            "expected_behavior": "不应调用（日常琐事，虽字面是决策）",
            "notes": "边界：区分严肃决策和日常选择",
        },
    ],
}


def make_build_dir(root: Path) -> Path:
    build = root / "demo"
    (build / "candidates").mkdir(parents=True)
    (build / "skills" / "slow-gardener" / "tests").mkdir(parents=True)
    (build / "source.txt").write_text(SOURCE_TEXT, encoding="utf-8")
    (build / "claims.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in CLAIMS) + "\n",
        encoding="utf-8",
    )
    (build / "skills" / "slow-gardener" / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (build / "skills" / "slow-gardener" / "tests" / "trigger.json").write_text(
        json.dumps(TRIGGER_TESTS, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (build / "candidates" / "glossary.md").write_text(
        "# 术语\n\n| 术语 | 用法 |\n|---|---|\n| 墒情 | 土壤含水量状态 |\n",
        encoding="utf-8",
    )
    return build
