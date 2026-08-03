"""进化闭环（S10）：遥测聚合 → 提案生成（人类审批门前置）。"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def aggregate_telemetry(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"invocations": 0, "mis_trigger": 0, "positive": 0, "negative": 0}
    )
    for r in rows:
        slug = r.get("skill_slug", "?")
        event = r.get("event", "")
        if event in out[slug]:
            out[slug][event] += 1
    return dict(out)


def generate_proposals(
    pack_dir: Path,
    telemetry_rows: list[dict[str, Any]],
    out_dir: Path,
    cfg,
) -> list[Path]:
    stats = aggregate_telemetry(telemetry_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for slug in sorted(stats):
        s = stats[slug]
        proposals: list[str] = []
        if s["invocations"] > 0:
            mis_rate = s["mis_trigger"] / s["invocations"]
            if mis_rate > cfg.mis_trigger_proposal_rate:
                proposals.append(
                    f"- 误触发率 {mis_rate:.0%} 超过阈值 {cfg.mis_trigger_proposal_rate:.0%}\n"
                    f"  建议: 收紧 description（补充反触发信号），并新增对应诱饵测试用例。\n"
                    f"  回归要求: 旧 trigger.json 全过 + 新增误触发 prompt 用例。"
                )
        if s["negative"] >= cfg.negative_feedback_proposal_min:
            proposals.append(
                f"- 负面反馈 {s['negative']} 条 ≥ {cfg.negative_feedback_proposal_min}\n"
                f"  建议: 复审 B（Boundary）段与 E 段判停条件，补充失败模式。\n"
                f"  回归要求: 全量评测通过后发版。"
            )
        if s["positive"] >= cfg.positive_feedback_promote_min:
            proposals.append(
                f"- 正面反馈 {s['positive']} 条 ≥ {cfg.positive_feedback_promote_min}\n"
                f"  建议: 将 confidence 提升一档（需 pack.json 同步版本号）。"
            )
        if proposals:
            path = out_dir / f"{now}-{slug}.md"
            path.write_text(
                f"# 进化提案: {slug}\n\n"
                f"生成时间: {now}\n\n"
                f"遥测统计: 调用 {s['invocations']}，误触发 {s['mis_trigger']}，"
                f"正面 {s['positive']}，负面 {s['negative']}\n\n"
                + "\n".join(proposals)
                + "\n\n## 审批\n\n- [ ] 人类审查\n- [ ] 回归测试\n- [ ] 版本号更新\n",
                encoding="utf-8",
            )
            written.append(path)
    return written


def load_telemetry_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows

