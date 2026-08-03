"""忠实度校验器（S3）：引文定位、长度红线、数字出处规则。

设计原则：确定性优先，不信任任何单一模型结论。
- 引文定位：归一化后精确匹配，失败时做去标点模糊匹配；
- 数字规则：summary/title 中出现的每个数字，必须在引文或 source_note 中有出处；
- 任何一条红线失败，该 claim 不得标记为 verified。
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


NUMBER_RE = re.compile(
    r"\d[\d,\.]*(?:万|亿|千|百|%|％|倍|年|天|月|周|元|美元|港币|人民币|k|m|b|million|billion)?",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", " ", text).casefold().strip()


def strip_punct(text: str) -> str:
    """去标点，只保留字母、数字与 CJK 字符（用于模糊匹配）。"""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", normalize(text))


def find_quote_span(quote: str, source_text: str) -> dict[str, Any]:
    """返回 {found, start, end, method}；method 为 exact / fuzzy / missing。"""
    if not quote:
        return {"found": False, "start": None, "end": None, "method": "missing"}
    q = normalize(quote)
    s = normalize(source_text)
    pos = s.find(q)
    if pos >= 0:
        return {"found": True, "start": pos, "end": pos + len(q), "method": "exact"}
    q2 = strip_punct(quote)
    s2 = strip_punct(source_text)
    if len(q2) >= 8:
        pos = s2.find(q2)
        if pos >= 0:
            return {"found": True, "start": pos, "end": pos + len(q2), "method": "fuzzy"}
    return {"found": False, "start": None, "end": None, "method": "missing"}


def quote_length_ok(quote: str, max_chars: int, max_words: int) -> tuple[bool, str]:
    chars = len(quote)
    words = len(re.findall(r"[A-Za-z]+", quote))
    if chars > max_chars:
        return False, f"引文 {chars} 字 > {max_chars} 字上限"
    if words > max_words:
        return False, f"引文 {words} 词 > {max_words} 词上限"
    return True, ""


def extract_numbers(text: str) -> list[str]:
    return [m.group(0).casefold() for m in NUMBER_RE.finditer(text or "")]


def verify_claim(claim: dict[str, Any], source_text: str, cfg) -> dict[str, Any]:
    """对单条 claim 执行忠实度校验，返回补充校验字段后的 claim 副本。"""
    result = dict(claim)
    issues: list[str] = []
    quote = claim.get("source_quote", "") or ""
    result["checker"] = "rushi-verifier"

    if not quote:
        result["status"] = "no-quote"
        result["issues"] = ["缺少 source_quote，无法定位原文"]
        return result

    ok_len, msg = quote_length_ok(quote, cfg.quote_max_chars, cfg.quote_max_words)
    if not ok_len:
        result["status"] = "length-failed"
        result["issues"] = [msg]
        return result

    span = find_quote_span(quote, source_text)
    result["source_span"] = (
        f"{span['start']}-{span['end']}({span['method']})" if span["found"] else ""
    )
    if not span["found"]:
        result["status"] = "unverified"
        result["issues"] = ["引文未在源文本中找到"]
        return result

    numbers = set(extract_numbers(claim.get("summary", "")) + extract_numbers(claim.get("title", "")))
    quote_numbers = set(extract_numbers(quote))
    missing = sorted(n for n in numbers if n not in quote_numbers)
    if missing and not claim.get("source_note"):
        issues.append(f"数字无出处: {', '.join(missing)}（须出现在引文中或提供 source_note）")
        result["status"] = "numeric-review"
    elif missing and claim.get("source_note"):
        result["status"] = "verified-with-notes"
    else:
        result["status"] = "verified"
    result["issues"] = issues
    return result


def verify_claims(
    claims: list[dict[str, Any]], source_text: str, cfg
) -> dict[str, Any]:
    results = [verify_claim(c, source_text, cfg) for c in claims]
    stats: dict[str, int] = {}
    for r in results:
        stats[r["status"]] = stats.get(r["status"], 0) + 1
    blocked = stats.get("length-failed", 0) + stats.get("no-quote", 0)
    unverified = stats.get("unverified", 0)
    verified = stats.get("verified", 0) + stats.get("verified-with-notes", 0)
    total = len(results)
    fidelity_rate = verified / total if total else 0.0
    return {
        "results": results,
        "stats": stats,
        "total": total,
        "blocked": blocked,
        "unverified": unverified,
        "verified": verified,
        "fidelity_rate": round(fidelity_rate, 4),
        "pass": blocked == 0 and unverified == 0 and total > 0,
    }


def extract_r_quotes(skill_md_text: str) -> list[str]:
    """从 SKILL.md 的 R 段提取块引用（去掉归属行）。"""
    quotes: list[str] = []
    in_r = False
    for line in (skill_md_text or "").splitlines():
        if re.match(r"^##\s+R\b", line):
            in_r = True
            continue
        if in_r and re.match(r"^##\s+", line):
            break
        if in_r and line.strip().startswith(">"):
            text = re.sub(r"^>\s*", "", line).strip()
            if text and not re.match(r"^—|^[-–—]", text):
                quotes.append(text)
    return quotes


def verify_skill_quotes(skill_md_text: str, source_text: str, cfg) -> list[dict[str, Any]]:
    out = []
    for quote in extract_r_quotes(skill_md_text):
        ok, msg = quote_length_ok(quote, cfg.quote_max_chars, cfg.quote_max_words)
        if not ok:
            out.append({"quote": quote[:40], "status": "length-failed", "issue": msg})
            continue
        span = find_quote_span(quote, source_text)
        out.append(
            {
                "quote": quote[:60],
                "status": "verified" if span["found"] else "unverified",
                "method": span["method"],
                "issue": "" if span["found"] else "引文未在源文本中找到",
            }
        )
    return out


def render_provenance(results: list[dict[str, Any]], stats: dict[str, int]) -> str:
    lines = [
        "# PROVENANCE.md — 证据链",
        "",
        "> 由 rushi-verifier 确定性生成。每条 claim 的引文必须能在源文本中定位，",
        "> 数字必须带出处。任何未通过项不得进入发布包。",
        "",
        "## 统计",
        "",
        "| 状态 | 数量 |",
        "|---|---|",
    ]
    for status in sorted(stats):
        lines.append(f"| {status} | {stats[status]} |")
    lines += ["", "## 明细", "", "| claim_id | skill | 状态 | 定位 | 问题 |", "|---|---|---|---|---|"]
    for r in results:
        lines.append(
            f"| {r.get('claim_id', '?')} | {r.get('skill_slug', '?')} | {r.get('status', '?')} "
            f"| {r.get('source_span', '') or '-'} | {'; '.join(r.get('issues', [])) or '-'} |"
        )
    return "\n".join(lines) + "\n"


def write_provenance(book_dir: Path, report: dict[str, Any]) -> Path:
    out = book_dir / "PROVENANCE.md"
    out.write_text(
        render_provenance(report["results"], report["stats"]), encoding="utf-8"
    )
    return out

