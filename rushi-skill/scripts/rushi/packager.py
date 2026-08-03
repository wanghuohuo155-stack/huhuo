"""打包（S8）与发布闸门（S9）：pack.json、产物完整性、证据嵌入。"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import schema


REQUIRED_BUILD_ARTIFACTS = (
    "PROVENANCE.md",
    "TEST_REPORT.md",
    "GLOSSARY.md",
    "INDEX.md",
)


def validate_build_dir(build_dir: Path) -> list[str]:
    """发布闸门核心：构建目录完整性检查。"""
    issues: list[str] = []
    for artifact in REQUIRED_BUILD_ARTIFACTS:
        if not (build_dir / artifact).exists():
            issues.append(f"缺少发布必需产物: {artifact}")
    test_report = build_dir / "TEST_REPORT.md"
    if test_report.exists() and "整体判定: PASS" not in test_report.read_text(encoding="utf-8"):
        issues.append("TEST_REPORT 判定不是 PASS（评测未通过，禁止打包）")
    provenance = build_dir / "PROVENANCE.md"
    if provenance.exists():
        m = re.search(
            r"^\| unverified \|\s*(\d+)\s*\|",
            provenance.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if m and int(m.group(1)) > 0:
            issues.append(f"PROVENANCE 存在 {m.group(1)} 条 unverified（禁止打包）")
    skills_root = build_dir / "skills"
    if not skills_root.exists():
        issues.append("缺少 skills/ 目录")
        return issues
    skill_dirs = [d for d in skills_root.iterdir() if d.is_dir()]
    if not skill_dirs:
        issues.append("skills/ 下没有任何 skill")
    for d in skill_dirs:
        for needed in ("SKILL.md", "tests/trigger.json"):
            if not (d / needed).exists():
                issues.append(f"{d.name}: 缺少 {needed}")
    return issues


def load_source_meta(build_dir: Path) -> dict[str, Any]:
    manifest = build_dir / "source.manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return {
            "title": data.get("title", ""),
            "author": data.get("author", ""),
            "year": data.get("year", ""),
            "kind": data.get("kind", ""),
            "sha256": data.get("sha256", ""),
        }
    return {}


def build_pack(
    build_dir: Path,
    out_root: Path,
    name: str,
    version: str,
    confidence: str = "unverified",
    freshness_days: int = 365,
) -> Path:
    """把构建目录变成可发布的 pack 目录。"""
    issues = validate_build_dir(build_dir)
    if issues:
        raise ValueError("构建目录未通过发布闸门:\n- " + "\n- ".join(issues))
    source = load_source_meta(build_dir)
    pack_dir = out_root / name
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    (pack_dir / "skills").mkdir(parents=True)

    for d in (build_dir / "skills").iterdir():
        if d.is_dir():
            shutil.copytree(d, pack_dir / "skills" / d.name)

    for artifact in REQUIRED_BUILD_ARTIFACTS:
        shutil.copy2(build_dir / artifact, pack_dir / artifact)

    # 关键设计：GLOSSARY 随包嵌入每个 skill 目录，防止原子化安装后术语断链
    for d in (pack_dir / "skills").iterdir():
        if d.is_dir():
            shutil.copy2(pack_dir / "GLOSSARY.md", d / "GLOSSARY.md")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    pack_json = {
        "schema_version": "1.0",
        "name": name,
        "version": version,
        "source": source,
        "confidence": confidence,
        "freshness": {
            "packaged_at": now,
            "expires_at": now,
            "policy": "recheck-by-expiry",
        },
        "skills": sorted(d.name for d in (pack_dir / "skills").iterdir() if d.is_dir()),
        "artifacts": list(REQUIRED_BUILD_ARTIFACTS),
        "engine": "rushi",
    }
    expiry = datetime.fromisoformat(now)
    pack_json["freshness"]["expires_at"] = (expiry + timedelta(days=freshness_days)).isoformat(
        timespec="seconds"
    )
    (pack_dir / "pack.json").write_text(
        json.dumps(pack_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return pack_dir


def validate_pack(pack_dir: Path, spec_dir: Path) -> list[str]:
    """pack 目录 schema + 产物校验。"""
    issues = []
    pack_json = pack_dir / "pack.json"
    if not pack_json.exists():
        return ["缺少 pack.json"]
    spec = spec_dir / "pack.schema.json"
    if spec.exists():
        issues += schema.validate_file(pack_json, spec)
    for name, path in (
        ("PROVENANCE.md", pack_dir / "PROVENANCE.md"),
        ("TEST_REPORT.md", pack_dir / "TEST_REPORT.md"),
        ("GLOSSARY.md", pack_dir / "GLOSSARY.md"),
        ("INDEX.md", pack_dir / "INDEX.md"),
    ):
        if not path.exists():
            issues.append(f"缺少 {name}")
    for d in (pack_dir / "skills").iterdir() if (pack_dir / "skills").exists() else []:
        if d.is_dir() and not (d / "SKILL.md").exists():
            issues.append(f"{d.name}: 缺少 SKILL.md")
        if d.is_dir() and not (d / "GLOSSARY.md").exists():
            issues.append(f"{d.name}: 缺少随包 GLOSSARY.md（共享术语上下文）")
    return issues
