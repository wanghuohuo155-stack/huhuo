"""RIA++ 构造校验（S5）：SKILL.md v2 六段完整性、frontmatter 触发描述红线。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .verifier import quote_length_ok


SECTION_RE = re.compile(r"^##\s+(R|I|A1|A2|E|B)\b", re.MULTILINE)


def parse_frontmatter(text: str) -> dict[str, Any]:
    """解析极简 YAML frontmatter（支持标量、| 块、内联数组）。"""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    data: dict[str, Any] = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        km = re.match(r"^ ?([a-zA-Z_][\w-]*):\s*(.*)$", line)
        if not km:
            i += 1
            continue
        key, value = km.group(1), km.group(2).strip()
        if not value:
            # 一层嵌套对象：后续以两个空格缩进的 "子键: 值" 行
            nested: dict[str, Any] = {}
            j = i + 1
            while j < len(lines) and lines[j].startswith("  ") and lines[j].strip():
                child = re.match(r"^  ([a-zA-Z_][\w-]*):\s*(.*)$", lines[j])
                if child:
                    nested[child.group(1)] = child.group(2).strip().strip("'\"")
                j += 1
            if nested:
                data[key] = nested
                i = j
                continue
        if value == "|":
            block: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i] == ""):
                if lines[i].strip():
                    block.append(lines[i].strip())
                i += 1
            data[key] = "\n".join(block)
            continue
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            data[key] = items
        else:
            data[key] = value.strip("'\"")
        i += 1
    return data


def section_bodies(text: str) -> dict[str, str]:
    """按一级小节标题切分正文，返回 {R: ..., I: ..., ...}。"""
    matches = list(re.finditer(r"^##\s+(R|I|A1|A2|E|B)\b.*$", text, re.MULTILINE))
    bodies: dict[str, str] = {}
    for idx, m in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        bodies[m.group(1)] = text[m.end() : end]
    return bodies


def validate_skill(text: str, cfg) -> tuple[list[str], dict[str, Any]]:
    """返回 (issues, meta)。issues 为空表示通过。"""
    issues: list[str] = []
    fm = parse_frontmatter(text)
    meta = {"frontmatter": fm, "sections": section_bodies(text)}

    name = fm.get("name", "")
    if not re.match(r"^[a-z0-9][a-z0-9-]{1,62}$", name):
        issues.append("frontmatter.name 缺失或不符合 kebab-case（2-63 字符）")
    desc = fm.get("description", "")
    if not desc:
        issues.append("frontmatter.description 缺失")
    else:
        if len(desc) > 300:
            issues.append(f"description 长度 {len(desc)} > 300 字上限")
        if not re.search(r"不适用|不应|不要|不适合|何时不用|don'?t|do not", desc, re.IGNORECASE):
            issues.append("description 必须包含反触发信号（何时不用）")
    if not (fm.get("source_book") or fm.get("source")):
        issues.append("缺少 source_book / source 溯源字段")

    bodies = meta["sections"]
    for section in ("R", "I", "A1", "A2", "E", "B"):
        if section not in bodies:
            issues.append(f"缺少 {section} 段")

    if "R" in bodies:
        if not re.search(r"^>", bodies["R"], re.MULTILINE):
            issues.append("R 段必须包含原文块引用（>）")
        for q in re.findall(r"^>\s*(.+)$", bodies["R"], re.MULTILINE):
            q = re.sub(r"^—|^[-–—]", "", q.strip())
            if q:
                ok, msg = quote_length_ok(q, cfg.quote_max_chars, cfg.quote_max_words)
                if not ok:
                    issues.append(f"R 段引文超限: {msg}")
                break
    if "A2" in bodies and not re.search(r"语言信号|触发", bodies["A2"]):
        issues.append("A2 段应包含'语言信号'或'触发场景'")
    if "E" in bodies:
        if not re.search(r"完成标准", bodies["E"]) and not re.search(r"^\s*1[.、]", bodies["E"], re.MULTILINE):
            issues.append("E 段必须包含编号步骤或'完成标准'")
    if "B" in bodies and not re.search(r"不要|不适用|Boundary|失败模式", bodies["B"]):
        issues.append("B 段必须包含反场景/失败模式")
    return issues, meta


def check_skill_dir(skill_dir: Path, cfg) -> list[str]:
    """校验一个 skill 目录：SKILL.md 六段 + 触发测试文件。"""
    issues: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.name}: 缺少 SKILL.md"]
    text = skill_md.read_text(encoding="utf-8")
    issues += [f"{skill_dir.name}: {i}" for i in validate_skill(text, cfg)[0]]
    trigger = skill_dir / "tests" / "trigger.json"
    if not trigger.exists():
        issues.append(f"{skill_dir.name}: 缺少 tests/trigger.json")
    else:
        try:
            data = json.loads(trigger.read_text(encoding="utf-8"))
            cases = data.get("test_cases", [])
            types = {c.get("type") for c in cases}
            if "should_trigger" not in types:
                issues.append(f"{skill_dir.name}: trigger.json 缺少 should_trigger 用例")
            if "should_not_trigger" not in types:
                issues.append(f"{skill_dir.name}: trigger.json 缺少诱饵用例")
            if len(cases) < 5:
                issues.append(f"{skill_dir.name}: trigger.json 用例数 {len(cases)} < 5")
        except json.JSONDecodeError as exc:
            issues.append(f"{skill_dir.name}: trigger.json 不是合法 JSON（{exc}）")
    return issues
