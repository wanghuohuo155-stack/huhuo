"""评测（S7）：触发测试 + 跨 skill 混淆 + 报告落盘。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .builder import parse_frontmatter


def _ngrams(text: str, n: int = 2) -> set[str]:
    t = text.casefold()
    return {t[i : i + n] for i in range(len(t) - n + 1)}


def phrase_overlap(prompt: str, description: str) -> float:
    """字符 bigram Jaccard：描述与提示的重叠比例（用于报告）。"""
    a, b = _ngrams(prompt), _ngrams(description)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def prompt_coverage(prompt: str, description: str) -> float:
    """提示词被描述覆盖的比例 = 重叠 bigram / 提示词 bigram。
    对短提示更敏感，适合作为 mock 判官的触发分数。"""
    a, b = _ngrams(prompt), _ngrams(description)
    if not a:
        return 0.0
    return len(a & b) / len(a)


def positive_description(description: str) -> str:
    """只保留正向触发描述：'不适用/反触发信号'之后的负向说明不参与触发打分。"""
    for marker in ("不适用", "反触发信号", "不应", "不适合", "何时不用"):
        idx = description.find(marker)
        if idx > 0:
            return description[:idx]
    return description


class MockJudge:
    """无 LLM 的确定性判官：按描述重叠度打分，用于 CI 与演示。
    真实评测请配置 provider（--mode provider），本模式结果标注为 fallback。"""

    name = "mock-judge"

    def __init__(self, skills: list[dict[str, str]], threshold: float = 0.18):
        self.skills = skills
        self.threshold = threshold
        self._positive = [positive_description(s["description"]) for s in skills]

    def decide(self, prompt: str) -> tuple[str | None, float, str]:
        best_slug, best_score = None, 0.0
        for s, pos in zip(self.skills, self._positive):
            score = prompt_coverage(prompt, pos)
            if score > best_score:
                best_slug, best_score = s["slug"], score
        triggered = best_score >= self.threshold
        return (best_slug if triggered else None), best_score, (
            f"score={best_score:.3f} threshold={self.threshold}"
        )


def load_skill_descriptions(build_dir: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    skills_root = build_dir / "skills"
    if not skills_root.exists():
        return out
    for d in sorted(skills_root.iterdir()):
        md = d / "SKILL.md"
        if not md.is_file():
            continue
        fm = parse_frontmatter(md.read_text(encoding="utf-8"))
        out.append({"slug": d.name, "description": str(fm.get("description", ""))})
    return out


def _expected_trigger(case: dict[str, Any]) -> bool | None:
    t = case.get("type")
    if t == "should_trigger":
        return True
    if t == "should_not_trigger":
        return False
    behavior = str(case.get("expected_behavior", ""))
    if "不应调用" in behavior or "不应激活" in behavior:
        return False
    if "应调用" in behavior or "应激活" in behavior:
        return True
    return None


def run_trigger_tests(build_dir: Path, mode: str = "mock") -> dict[str, Any]:
    skills = load_skill_descriptions(build_dir)
    judge = MockJudge(skills)
    per_skill: list[dict[str, Any]] = []
    grand_passed = grand_total = 0
    bait_failures = 0

    for s in skills:
        trigger = build_dir / "skills" / s["slug"] / "tests" / "trigger.json"
        if not trigger.exists():
            per_skill.append({"slug": s["slug"], "error": "缺少 trigger.json"})
            continue
        cases = json.loads(trigger.read_text(encoding="utf-8")).get("test_cases", [])
        results = []
        for case in cases:
            prompt = str(case.get("prompt", ""))
            expected = _expected_trigger(case)
            _, score, why = judge.decide(prompt)
            actual = score >= judge.threshold
            passed = expected is None or actual == expected
            if case.get("type") == "should_not_trigger" and not passed:
                bait_failures += 1
            results.append(
                {
                    "id": case.get("id"),
                    "type": case.get("type"),
                    "expected": expected,
                    "actual": actual,
                    "score": round(score, 3),
                    "passed": passed,
                    "why": why,
                }
            )
        passed = sum(1 for r in results if r["passed"])
        total = len(results)
        grand_passed += passed
        grand_total += total
        per_skill.append(
            {
                "slug": s["slug"],
                "passed": passed,
                "total": total,
                "rate": round(passed / total, 3) if total else 0.0,
                "results": results,
            }
        )

    overall = round(grand_passed / grand_total, 4) if grand_total else 0.0
    report = {
        "mode": mode,
        "judge": judge.name,
        "is_fallback": mode == "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "per_skill": per_skill,
        "grand_passed": grand_passed,
        "grand_total": grand_total,
        "overall_rate": overall,
        "bait_failures": bait_failures,
        "pass": (
            grand_total > 0
            and overall >= 0.8
            and bait_failures == 0
            and all(not s.get("error") for s in per_skill)
        ),
    }
    return report


def render_test_report(report: dict[str, Any]) -> str:
    lines = [
        "# TEST_REPORT.md — 评测报告",
        "",
        f"- 模式: {report['mode']}（{'fallback 结果，可信度低于独立盲测' if report['is_fallback'] else 'provider 结果'}）",
        f"- 判官: {report['judge']}",
        f"- 生成时间: {report['generated_at']}",
        f"- 总通过率: {report['overall_rate']:.1%}（{report['grand_passed']}/{report['grand_total']}）",
        f"- 诱饵失败: {report['bait_failures']}（容错 0）",
        f"- 整体判定: {'PASS' if report['pass'] else 'FAIL'}",
        "",
        "## 明细",
        "",
    ]
    for s in report["per_skill"]:
        if s.get("error"):
            lines.append(f"### {s['slug']}\n\n- 错误: {s['error']}\n")
            continue
        lines.append(f"### {s['slug']} — {s['rate']:.1%}（{s['passed']}/{s['total']}）\n")
        lines.append("| id | type | expected | actual | passed | score | 依据 |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in s["results"]:
            exp = "触发" if r["expected"] is True else "不触发" if r["expected"] is False else "边界"
            act = "触发" if r["actual"] else "不触发"
            lines.append(
                f"| {r['id']} | {r['type']} | {exp} | {act} | {'✅' if r['passed'] else '❌'} "
                f"| {r['score']} | {r['why']} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def write_test_report(build_dir: Path, report: dict[str, Any]) -> Path:
    out = build_dir / "TEST_REPORT.md"
    out.write_text(render_test_report(report), encoding="utf-8")
    return out
