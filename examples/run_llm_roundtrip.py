"""真实 provider 往返评测：在 demo 内容上量化 S1/S2/S4/S5 的真实通过率。

用法（需要 OPENAI_API_KEY 环境变量）：
    python examples/run_llm_roundtrip.py

输出：examples/llm_eval/REPORT.md（含各阶段指标），退出码 0=可计算，1=全部调用失败。
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
from rushi import builder, verifier
from rushi.pipeline import JSON_SPECS, parse_json_output


OUT = ROOT / "examples" / "llm_eval"
DEMO = ROOT / "examples" / "demo-pack"
PROMPTS = ROOT / "rushi-skill" / "scripts" / "rushi" / "prompts"
SYSTEM = "你是一个严谨的方法论蒸馏执行器。所有输出必须来自给定文本，禁止编造。"

SOURCE = (DEMO / "source.txt").read_text(encoding="utf-8")
CLAIMS = [
    json.loads(line)
    for line in (DEMO / "claims.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
EXTRACTORS = [
    "extract-framework.md",
    "extract-principle.md",
    "extract-case.md",
    "extract-counter-example.md",
    "extract-glossary.md",
]


def call(
    provider, prompt: str, name: str, json_mode: bool = False
) -> tuple[str | None, str | None]:
    """返回 (输出文本, 错误)；输出同时落盘。"""
    try:
        text = provider.complete(prompt, system=SYSTEM, json_mode=json_mode)
    except ProviderError as exc:
        return None, f"ProviderError: {exc}"
    except Exception as exc:  # 外部调用失败路径
        return None, f"{type(exc).__name__}: {exc}"
    (OUT / name).write_text(text, encoding="utf-8")
    return text, None


def strip_fence(text: str) -> str:
    """剥离 ```yaml/markdown/json 代码块（若存在）。"""
    m = re.search(r"^```[a-zA-Z]*\s*\n(.*?)\n```\s*$", text, re.DOTALL)
    return m.group(1) if m else text


def parse_candidates(text: str) -> list[dict[str, str]]:
    text = strip_fence(text)
    data = parse_json_output(text, "candidates")
    if isinstance(data, list):
        return [
            {
                "id": str(c.get("id", "")),
                "title": str(c.get("title", "")),
                "type": str(c.get("type", "")),
                "source_chapter": str(c.get("source_chapter", "")),
                "source_quote": str(c.get("source_quote", "")),
                "summary": str(c.get("summary", "")),
                "tags": c.get("tags", []),
            }
            for c in data
            if isinstance(c, dict)
        ]
    items = re.split(r"(?m)^\s*-\s*id:\s*", text)
    out: list[dict[str, str]] = []
    for chunk in items[1:]:
        c: dict[str, str] = {}
        m = re.search(r"^([A-Za-z0-9_-]+)", chunk, re.M)
        if m:
            c["id"] = m.group(1)
        for key in ("title", "type", "summary", "tags"):
            m = re.search(rf"(?m)^\s*{key}:\s*(.+)$", chunk)
            if m:
                c[key] = m.group(1).strip().strip("'\"")
        q = re.search(
            r"(?ms)source_quote:\s*(?:[|>]\s*)?\s*[\"']?(.*?)[\"']?\s*"
            r"(?=\n\s{2}[a-z_]+:|\n\s*-\s*id:|\Z)",
            chunk,
        )
        if q:
            quote = q.group(1).strip()
            quote = re.sub(r"^[\"']|[\"']$", "", quote)
            c["source_quote"] = quote
        if c.get("id") or c.get("title"):
            out.append(c)
    if not out:
        # 兼容模型只输出 "candidates:\n  - source_quote: ..." 的格式
        m = re.search(r"(?m)^candidates:\s*$", text)
        if m:
            for q in re.finditer(
                r"(?m)^\s*-\s+source_quote:\s*[\"']?(.*?)[\"']?\s*$", text[m.end() :]
            ):
                out.append({"source_quote": q.group(1).strip()})
    return out


def eval_s1(text: str) -> dict[str, bool]:
    return {
        "一句话主旨": bool(re.search(r"主旨|核心|一句话|主题", text)),
        "结构/骨架(≥3 个二级标题)": len(re.findall(r"(?m)^##\s+", text)) >= 3,
        "批判(局限/盲点/不足/反对)": len(re.findall(r"局限|盲点|不足|批判|反对", text)) >= 3,
        "术语(≥5 条)": len(re.findall(r"术语|定义|概念", text)) >= 5,
        "应用潜力": bool(re.search(r"应用|skill|复用|可调用", text, re.IGNORECASE)),
    }


def eval_s4(text: str) -> dict[str, bool]:
    text = strip_fence(text)
    conf = ""
    has_fals = False
    has_evidence = False
    try:
        data = json.loads(text)
        conf = str(data.get("confidence", ""))
        has_fals = bool(data.get("falsification_test"))
        has_evidence = bool(data.get("external_evidence"))
    except (json.JSONDecodeError, TypeError):
        m = re.search(r"confidence:\s*(\S+)", text)
        conf = m.group(1) if m else ""
        has_fals = bool(re.search(r"falsification_test|可证伪", text))
        has_evidence = bool(re.search(r"external_evidence|佐证|外部", text))
    return {
        "格式合规": conf in {"author-claim", "empirically-supported", "unverified"} and has_fals,
        "含外部证据字段": has_evidence,
        "误标empirically-supported": conf == "empirically-supported" and not has_evidence,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = Config.load(ROOT)
    provider = get_provider(cfg)
    report: dict[str, object] = {"model": provider.model if hasattr(provider, "model") else cfg.model}
    stage_results: dict[str, object] = {}
    total_calls = 0
    ok_calls = 0

    # ---- S1 整书理解 ----
    total_calls += 1
    s1_prompt = f"{PROMPTS / 'adler.md'}\n\n## 输入\n\n{SOURCE}"
    if cfg.json_mode:
        s1_prompt += "\n\n" + str(JSON_SPECS["S1"]["instruction"])
    s1_text, s1_err = call(provider, s1_prompt, "S1-book-overview.md", json_mode=cfg.json_mode)
    if s1_text is None:
        stage_results["S1"] = {"ok": False, "error": s1_err}
    else:
        ok_calls += 1
        if cfg.json_mode:
            s1_text = parse_json_output(s1_text, "book_overview_md") or s1_text
        checks = eval_s1(s1_text)
        stage_results["S1"] = {
            "ok": True,
            "checks": checks,
            "pass_rate": sum(checks.values()) / len(checks),
        }

    # ---- S2 并行提取 ----
    candidates_all: list[dict[str, str]] = []
    extractor_errors: list[str] = []
    for ex in EXTRACTORS:
        total_calls += 1
        prompt = (
            f"{PROMPTS / ex}\n\n## 输入\n\n源文本:\n{SOURCE}\n\n"
        )
        if cfg.json_mode:
            prompt += "\n\n" + str(JSON_SPECS["S2"]["instruction"])
        else:
            prompt += "请严格按上述 YAML 格式输出候选（每条 source_quote 必须是源文本中的逐字句子）。"
        text, err = call(provider, prompt, f"S2-{ex}.md", json_mode=cfg.json_mode)
        if text is None:
            extractor_errors.append(f"{ex}: {err}")
            continue
        ok_calls += 1
        candidates_all.extend(parse_candidates(text))

    cfg_v = Config(project_dir=ROOT)
    verified_n = 0
    quote_n = 0
    for c in candidates_all:
        if c.get("source_quote"):
            quote_n += 1
            claim = {
                "claim_id": c.get("id", "x00"),
                "skill_slug": "llm-extracted",
                "kind": c.get("type", "framework"),
                "title": c.get("title", ""),
                "source_chapter": "llm",
                "source_quote": c["source_quote"],
                "summary": c.get("summary", ""),
            }
            r = verifier.verify_claim(claim, SOURCE, cfg_v)
            if r["status"] == "verified":
                verified_n += 1
    fixture_recall = sum(
        1
        for f in CLAIMS
        if any(
            verifier.normalize(f["source_quote"]) == verifier.normalize(c.get("source_quote", ""))
            or verifier.normalize(f["source_quote"]) in verifier.normalize(c.get("source_quote", ""))
            or verifier.normalize(c.get("source_quote", "")) in verifier.normalize(f["source_quote"])
            for c in candidates_all
        )
    )
    stage_results["S2"] = {
        "ok": len(extractor_errors) < len(EXTRACTORS),
        "extractor_errors": extractor_errors,
        "candidates_total": len(candidates_all),
        "structured_count": sum(1 for c in candidates_all if c.get("id") and c.get("title") and c.get("summary")),
        "candidates_with_quote": quote_n,
        "candidates_verified": verified_n,
        "quote_verified_rate": round(verified_n / quote_n, 3) if quote_n else 0.0,
        "structure_rate": round(
            sum(1 for c in candidates_all if c.get("id") and c.get("title") and c.get("summary"))
            / len(candidates_all),
            3,
        )
        if candidates_all
        else 0.0,
        "fixture_recall": round(fixture_recall / len(CLAIMS), 3),
        "fixture_recall_n": fixture_recall,
    }

    # ---- S4 外部三角验证 ----
    s4_ok = 0
    s4_mislabel = 0
    for claim in CLAIMS:
        total_calls += 1
        prompt = (
            f"{PROMPTS / 'verify-external.md'}\n\n## 待验证候选\n\n"
            f"{json.dumps(claim, ensure_ascii=False)}"
        )
        if cfg.json_mode:
            prompt += "\n\n" + str(JSON_SPECS["S4"]["instruction"])
        text, err = call(provider, prompt, f"S4-{claim['claim_id']}.md", json_mode=cfg.json_mode)
        if text is None:
            continue
        ok_calls += 1
        checks = eval_s4(text)
        if checks["格式合规"]:
            s4_ok += 1
        if checks["误标empirically-supported"]:
            s4_mislabel += 1
    stage_results["S4"] = {
        "ok": s4_ok > 0,
        "format_pass": s4_ok,
        "total": len(CLAIMS),
        "format_pass_rate": round(s4_ok / len(CLAIMS), 3),
        "mislabel_count": s4_mislabel,
    }

    # ---- S5 RIA++ 构造 ----
    s5_pass = 0
    s5_quote_pass = 0
    s5_failures: list[str] = []
    for claim in CLAIMS:
        total_calls += 1
        prompt = (
            f"{PROMPTS / 'construct-ria.md'}\n\n## 待构造单元\n\n"
            f"{json.dumps(claim, ensure_ascii=False)}\n\n"
        )
        if cfg.json_mode:
            prompt += "\n\n" + str(JSON_SPECS["S5"]["instruction"])
        else:
            prompt += (
                "只依据【待构造单元】字段构造 SKILL.md，R 段引文必须逐字使用 source_quote 字段，"
                "禁止复述或总结任何其他内容；请直接输出完整 SKILL.md，禁止代码块包裹。"
            )
        text, err = call(provider, prompt, f"S5-{claim['claim_id']}.md", json_mode=cfg.json_mode)
        if text is None:
            s5_failures.append(f"{claim['claim_id']}: {err}")
            continue
        ok_calls += 1
        skill_md = text
        if cfg.json_mode:
            try:
                skill_md = json.loads(strip_fence(text))["skill_md"]
            except (json.JSONDecodeError, KeyError, TypeError):
                skill_md = text
        issues, _ = builder.validate_skill(strip_fence(skill_md), cfg_v)
        if not issues:
            s5_pass += 1
        else:
            s5_failures.append(f"{claim['claim_id']}: {'; '.join(issues[:3])}")
        quotes = verifier.verify_skill_quotes(strip_fence(skill_md), SOURCE, cfg_v)
        if quotes and all(q["status"] == "verified" for q in quotes):
            s5_quote_pass += 1
    stage_results["S5"] = {
        "ok": s5_pass > 0,
        "construct_pass": s5_pass,
        "construct_pass_rate": round(s5_pass / len(CLAIMS), 3),
        "quote_verified_pass": s5_quote_pass,
        "failures": s5_failures[:10],
    }

    report["stages"] = stage_results
    report["calls"] = {"total": total_calls, "ok": ok_calls, "failed": total_calls - ok_calls}
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok_calls > 0 else 1


def write_markdown(report: dict[str, object]) -> None:
    s1 = report["stages"]["S1"]
    s2 = report["stages"]["S2"]
    s4 = report["stages"]["S4"]
    s5 = report["stages"]["S5"]
    lines = [
        "# LLM 往返评测报告（真实 provider）",
        "",
        f"- 模型: {report['model']}",
        f"- 调用: {report['calls']['ok']}/{report['calls']['total']} 成功",
        "",
        "## S1 整书理解",
        "",
    ]
    if s1.get("ok"):
        for k, v in s1["checks"].items():
            lines.append(f"- {'✅' if v else '❌'} {k}")
        lines.append(f"\n通过率: {s1['pass_rate']:.0%}\n")
    else:
        lines.append(f"- ❌ {s1.get('error')}\n")
    lines += [
        "## S2 并行提取",
        "",
        f"- 候选总数: {s2['candidates_total']}",
        f"- 结构化候选(含 id/title/summary): {s2['structured_count']}（结构合规率 {s2['structure_rate']:.0%}）",
        f"- 带引文: {s2['candidates_with_quote']}",
        f"- 引文可定位(verified): {s2['candidates_verified']}",
        f"- 引文定位率: {s2['quote_verified_rate']:.0%}",
        f"- fixture 召回: {s2['fixture_recall_n']}/5 = {s2['fixture_recall']:.0%}",
        "",
        "## S4 外部三角验证",
        "",
        f"- 格式合规: {s4['format_pass']}/{s4['total']} = {s4['format_pass_rate']:.0%}",
        f"- 误标 empirically-supported: {s4['mislabel_count']}",
        "",
        "## S5 RIA++ 构造",
        "",
        f"- 六段校验通过: {s5['construct_pass']}/5 = {s5['construct_pass_rate']:.0%}",
        f"- R 引文可定位: {s5['quote_verified_pass']}/5",
        "",
    ]
    if s5["failures"]:
        lines.append("失败样例：")
        lines += [f"- {f}" for f in s5["failures"]]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
