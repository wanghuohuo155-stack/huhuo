"""安装适配器：Claude Code / Cursor / Codex 的目标目录解析与复制。"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HOSTS = {
    "claude": {
        "user": lambda: Path.home() / ".claude" / "skills",
        "project": lambda p: Path(p) / ".claude" / "skills",
    },
    "cursor": {
        "project": lambda p: Path(p) / ".cursor" / "skills",
    },
    "codex": {
        "user": lambda: Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills",
    },
}


@dataclass
class InstallReport:
    host: str
    scope: str
    target: Path
    installed: list[Path]
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "scope": self.scope,
            "target": str(self.target),
            "installed": [str(p) for p in self.installed],
            "dry_run": self.dry_run,
        }


def resolve_target(host: str, scope: str, project: Path | None = None) -> Path:
    if host not in HOSTS:
        raise ValueError(f"未知宿主 {host!r}，可选: {', '.join(HOSTS)}")
    if scope not in HOSTS[host]:
        raise ValueError(f"宿主 {host} 不支持 scope {scope!r}，可选: {', '.join(HOSTS[host])}")
    if scope == "project":
        if project is None:
            raise ValueError("project scope 需要 --project 参数")
        return HOSTS[host]["project"](project)
    return HOSTS[host]["user"]()


def install_pack(
    pack_dir: Path,
    host: str,
    scope: str,
    project: Path | None = None,
    target: Path | None = None,
    dry_run: bool = False,
) -> InstallReport:
    skills_root = pack_dir / "skills"
    if not skills_root.exists():
        raise ValueError(f"{pack_dir} 不是有效 pack（缺少 skills/）")
    if target is None:
        target = resolve_target(host, scope, project)
    target = target.resolve()
    # 安全护栏：禁止把 pack 安装到它自己的父目录链（避免自我复制）
    pack_resolved = pack_dir.resolve()
    if target == pack_resolved or pack_resolved.is_relative_to(target):
        raise ValueError(f"拒绝安装到 pack 自身目录链: {target}")
    installed: list[Path] = []
    for d in sorted(skills_root.iterdir()):
        if not d.is_dir() or not (d / "SKILL.md").exists():
            continue
        dest = target / d.name
        if dry_run:
            installed.append(dest)
            continue
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(d, dest)
        installed.append(dest)
    return InstallReport(host=host, scope=scope, target=target, installed=installed, dry_run=dry_run)


def verify_install(report: InstallReport) -> list[str]:
    issues = []
    for path in report.installed:
        if not (path / "SKILL.md").exists():
            issues.append(f"{path}: 安装后缺少 SKILL.md")
    return issues

