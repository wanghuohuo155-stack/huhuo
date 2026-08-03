"""Zettelkasten 链接（S6）：关系解析、自动发现、INDEX.md 生成。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .builder import parse_frontmatter


RELATION_TYPES = ("depends-on", "contrasts-with", "composes-with")


@dataclass
class SkillMeta:
    slug: str
    dir: Path
    title: str
    description: str
    tags: list[str]
    related: list[dict[str, str]]


def collect_skills(build_dir: Path) -> list[SkillMeta]:
    out: list[SkillMeta] = []
    skills_root = build_dir / "skills"
    if not skills_root.exists():
        return out
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        md = skill_dir / "SKILL.md"
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
        related_raw = fm.get("related", fm.get("related_skills", []))
        related: list[dict[str, str]] = []
        if isinstance(related_raw, list):
            for item in related_raw:
                if isinstance(item, str):
                    related.append({"slug": item, "relation": ""})
                elif isinstance(item, dict):
                    related.append(
                        {
                            "slug": str(item.get("slug", "")),
                            "relation": str(item.get("relation", "")),
                        }
                    )
        out.append(
            SkillMeta(
                slug=skill_dir.name,
                dir=skill_dir,
                title=str(fm.get("name", skill_dir.name)),
                description=str(fm.get("description", "")),
                tags=tags,
                related=related,
            )
        )
    return out


def resolve_related(build_dir: Path) -> list[str]:
    """检查所有 related 引用是否可解析（无孤儿引用）。"""
    skills = collect_skills(build_dir)
    slugs = {s.slug for s in skills}
    issues: list[str] = []
    for s in skills:
        for r in s.related:
            target = r.get("slug", "")
            if not target:
                issues.append(f"{s.slug}: related 条目缺少 slug")
            elif target not in slugs:
                issues.append(f"{s.slug}: 引用不存在的 skill '{target}'")
            elif r.get("relation") and r["relation"] not in RELATION_TYPES:
                issues.append(f"{s.slug}: 未知关系类型 '{r['relation']}'")
    return issues


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def discover_relations(skills: list[SkillMeta], tag_threshold: float = 0.34) -> list[dict[str, Any]]:
    """启发式关系发现：标签重叠度高 → 候选 composes-with（人工确认）。"""
    candidates: list[dict[str, Any]] = []
    for i, a in enumerate(skills):
        for b in skills[i + 1 :]:
            score = _jaccard(set(a.tags), set(b.tags))
            if score >= tag_threshold:
                candidates.append(
                    {
                        "slug_a": a.slug,
                        "slug_b": b.slug,
                        "relation": "composes-with",
                        "score": round(score, 3),
                        "basis": f"标签重叠 {score:.2f}: {sorted(set(a.tags) & set(b.tags))}",
                        "status": "candidate",
                    }
                )
    candidates.sort(key=lambda c: (-c["score"], c["slug_a"], c["slug_b"]))
    return candidates


def render_index(
    skills: list[SkillMeta],
    relations: list[dict[str, Any]],
    title: str,
    author: str,
    theme: str,
    created: str,
) -> str:
    lines = [
        f"# {title} — Skill Index",
        "",
        f"> 由 rushi-linker 生成 | 作者: {author} | 主旨: {theme} | 生成时间: {created}",
        "",
        f"共产出 **{len(skills)}** 个 skills。",
        "",
        "## Skill 列表",
        "",
    ]
    for s in skills:
        lines.append(f"- [`{s.slug}`](./skills/{s.slug}/SKILL.md) — {s.description.splitlines()[0][:60]}")
    lines += ["", "## 引用图（mermaid）", "", "```mermaid", "graph LR"]
    for r in relations:
        if r.get("status") == "confirmed":
            arrow = {
                "depends-on": "-->",
                "contrasts-with": "-.->",
                "composes-with": "===>",
            }.get(r["relation"], "---")
            lines.append(f"    {r['slug_a']} {arrow} {r['slug_b']}")
    lines += ["```", "", "图例: `-->` depends-on | `-.->` contrasts-with | `===>` composes-with", ""]
    lines += ["## 关系候选（待人工确认）", ""]
    if relations:
        for r in relations:
            lines.append(f"- {r['slug_a']} --{r['relation']}--> {r['slug_b']}（{r.get('basis', '')}）")
    else:
        lines.append("- 无")
    lines += [
        "",
        "## 推荐学习顺序",
        "",
    ]
    dependents = {
        r["slug_a"]: r["slug_b"]
        for r in relations
        if r.get("status") == "confirmed" and r["relation"] == "depends-on"
    }
    order = [s.slug for s in skills if s.slug not in dependents.values()]
    order += [v for v in dependents.values() if v not in order]
    for idx, slug in enumerate(order, 1):
        lines.append(f"{idx}. `{slug}`")
    lines.append("")
    return "\n".join(lines)


def write_index(build_dir: Path, meta: dict[str, Any], confirmed: list[dict[str, Any]]) -> Path:
    skills = collect_skills(build_dir)
    text = render_index(
        skills,
        confirmed,
        meta.get("title", "未命名"),
        meta.get("author", ""),
        meta.get("theme", ""),
        meta.get("created", ""),
    )
    out = build_dir / "INDEX.md"
    out.write_text(text, encoding="utf-8")
    return out


def ensure_glossary(build_dir: Path) -> Path:
    """把 candidates/glossary.md 或 glossary.json 提升为 GLOSSARY.md（若缺失）。"""
    out = build_dir / "GLOSSARY.md"
    if out.exists():
        return out
    src = build_dir / "candidates" / "glossary.md"
    if src.exists():
        out.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return out
    src_json = build_dir / "candidates" / "glossary.json"
    if src_json.exists():
        import json

        entries = json.loads(src_json.read_text(encoding="utf-8"))
        lines = ["# GLOSSARY.md — 共享术语词典", "", "| 术语 | 作者的用法 | 与常识的差异 | 出处 |", "|---|---|---|---|"]
        for e in entries if isinstance(entries, list) else []:
            lines.append(
                f"| {e.get('term', '')} | {e.get('definition', '')} | "
                f"{e.get('difference', '')} | {e.get('source_chapter', '')} |"
            )
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out
    else:
        raise ValueError("缺少 candidates/glossary.md，无法生成 GLOSSARY.md（发布必需产物）")
