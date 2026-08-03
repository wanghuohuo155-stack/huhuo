"""第一次 A/B 效果基线：10 个决策任务，带包 vs 不带包，LLM 盲评 rubric 打分。

用法（需要 OPENAI_API_KEY）：
    python examples/run_ab_baseline.py

输出：examples/ab_baseline/REPORT.md（逐任务分数、均值、增量）。
局限声明：生成与评判使用同一模型家族，结果视为代理指标，需人工复核样本。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rushi-skill" / "scripts"))

from rushi.config import Config
from rushi.providers import ProviderError, get_provider


OUT = ROOT / "examples" / "ab_baseline"
SKILL_MD = (ROOT / "examples" / "demo-pack" / "skills" / "slow-gardener" / "SKILL.md").read_text(
    encoding="utf-8"
)
SYSTEM = "你是一位资深决策顾问。只输出分析正文，不要输出无关说明。"

TASKS = [
    ("T01", "你收到一个新公司 offer，薪资 +30% 但业务方向你不熟悉，公司成立 2 年。", "我该不该接受这个 offer？"),
    ("T02", "朋友拉你投资他的餐饮创业项目，需要你出 50 万占 20%。", "我该不该投？"),
    ("T03", "你考虑从一线城市搬到二线城市，房价低但职业机会少。", "要不要搬家？"),
    ("T04", "有一个外包项目报价 20 万，工期 3 个月，客户口碑一般。", "要不要接这个外包？"),
    ("T05", "你工作稳定但想辞职创业做跨境电商，已准备了 6 个月生活费。", "要不要辞职创业？"),
    ("T06", "你计划买房，首付刚好够，月供占收入 45%，当前行业有裁员传闻。", "现在该不该买房？"),
    ("T07", "AI 教育赛道很热，你想从传统行业转过去，但没有任何相关经验。", "要不要进入这个新赛道？"),
    ("T08", "前同事邀请你合伙开工作室，他出资源你出技术，股权对半。", "要不要合伙？"),
    ("T09", "你拿到研究生录取，同时有一份不错的工作 offer，两条路都能走。", "读研还是工作？"),
    ("T10", "一个平台想和你签 3 年独家长期合约，收入稳定但限制你的其他合作。", "要不要签这份独家合约？"),
]

RUBRIC = """评分维度（1-5 整数）：
r1 最坏情况分析：是否识别并分析了关键失败风险
r2 判停条件：是否给出明确的可执行判停/行动标准
r3 结论质量：结论是否明确、具体、可执行
r4 内容相关性：是否紧扣任务、没有空话或教条"""


def gen(provider, task_id: str, scenario: str, question: str, with_pack: bool) -> str:
    if with_pack:
        prompt = (
            f"请先阅读以下方法，然后严格按这个方法分析决策。\n\n"
            f"【方法】\n{SKILL_MD}\n\n【任务】\n{scenario}\n{question}"
        )
    else:
        prompt = f"{scenario}\n{question}"
    return provider.complete(prompt, system=SYSTEM)


def judge(provider, task_id: str, scenario: str, output: str, arm: str) -> dict[str, object]:
    prompt = (
        f"你是盲评专家。对下面这份决策分析打分。\n{RUBRIC}\n\n"
        f"【任务】\n{scenario}\n\n【分析】\n{output}\n\n"
        "仅输出 JSON：{\"r1\":1,\"r2\":1,\"r3\":1,\"r4\":1,\"comment\":\"一句话\"}"
    )
    text = provider.complete(prompt, system="你是严格的评分专家，只输出 JSON。")
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"判官未输出 JSON: {text[:120]}")
    data = json.loads(m.group(0))
    scores = [int(data[k]) for k in ("r1", "r2", "r3", "r4")]
    if any(not (1 <= s <= 5) for s in scores):
        raise ValueError(f"分数越界: {data}")
    return {"arm": arm, "scores": scores, "mean": round(sum(scores) / 4, 2), "comment": data.get("comment", "")}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results_dir = OUT / "outputs"
    results_dir.mkdir(exist_ok=True)
    cfg = Config.load(ROOT)
    provider = get_provider(cfg)
    rows: list[dict[str, object]] = []
    failures: list[str] = []

    for task_id, scenario, question in TASKS:
        row: dict[str, object] = {"task": task_id, "scenario": scenario}
        for arm, with_pack in (("baseline", False), ("pack", True)):
            try:
                output = gen(provider, task_id, scenario, question, with_pack)
            except ProviderError as exc:
                failures.append(f"{task_id}/{arm}: 生成失败 {exc}")
                continue
            (results_dir / f"{task_id}-{arm}.md").write_text(output, encoding="utf-8")
            try:
                row[arm] = judge(provider, task_id, scenario, output, arm)
            except (ProviderError, ValueError, KeyError) as exc:
                failures.append(f"{task_id}/{arm}: 评分失败 {exc}")
                row[arm] = {"arm": arm, "scores": None, "mean": None, "comment": f"评分失败: {exc}"}
        if "baseline" in row and "pack" in row and row["baseline"].get("mean") and row["pack"].get("mean"):
            row["delta"] = round(row["pack"]["mean"] - row["baseline"]["mean"], 2)
        rows.append(row)

    complete = [r for r in rows if r.get("baseline", {}).get("mean") is not None and r.get("pack", {}).get("mean") is not None]
    baseline_mean = round(sum(r["baseline"]["mean"] for r in complete) / len(complete), 2) if complete else None
    pack_mean = round(sum(r["pack"]["mean"] for r in complete) / len(complete), 2) if complete else None
    delta_mean = round(pack_mean - baseline_mean, 2) if baseline_mean is not None else None
    wins = sum(1 for r in complete if r["delta"] > 0)
    losses = sum(1 for r in complete if r["delta"] < 0)

    report = {
        "model": provider.model if hasattr(provider, "model") else cfg.model,
        "tasks_total": len(rows),
        "tasks_complete": len(complete),
        "baseline_mean": baseline_mean,
        "pack_mean": pack_mean,
        "delta_mean": delta_mean,
        "wins": wins,
        "losses": losses,
        "failures": failures,
        "verdict": (
            "有效（≥+0.5）" if delta_mean is not None and delta_mean >= 0.5
            else "弱有效（0~+0.5）" if delta_mean is not None and delta_mean >= 0
            else "负效果" if delta_mean is not None
            else "不可判定"
        ),
        "rows": rows,
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(
        {k: v for k, v in report.items() if k not in ("rows", "failures")}, ensure_ascii=False, indent=2
    ))
    return 0


def write_markdown(report: dict[str, object]) -> None:
    lines = [
        "# A/B 效果基线报告（决策领域，10 任务）",
        "",
        f"- 模型: {report['model']}",
        f"- 完整配对任务: {report['tasks_complete']}/{report['tasks_total']}",
        f"- 基线均值: {report['baseline_mean']}",
        f"- 带包均值: {report['pack_mean']}",
        f"- 增量: {report['delta_mean']}",
        f"- 胜/负: {report['wins']}/{report['losses']}",
        f"- 结论: {report['verdict']}",
        "",
        "> 局限：生成与评判为同一模型家族，结果仅为代理指标，需人工复核样本。",
        "",
        "| 任务 | 基线 | 带包 | 增量 | 判官备注 |",
        "|---|---|---|---|---|",
    ]
    for r in report["rows"]:
        base = r.get("baseline", {}).get("mean")
        pack = r.get("pack", {}).get("mean")
        comment = (r.get("pack", {}).get("comment") or "")[:40]
        lines.append(f"| {r['task']} | {base if base is not None else '-'} | {pack if pack is not None else '-'} | {r.get('delta', '-')} | {comment} |")
    if report["failures"]:
        lines += ["", "## 失败记录", ""]
        lines += [f"- {f}" for f in report["failures"]]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
