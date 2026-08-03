"""入世 CLI：一条命令端到端。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .builder import check_skill_dir
from .config import Config, default_config
from .content import book_dir
from .evaluator import run_trigger_tests, write_test_report
from .evolve import generate_proposals, load_telemetry_jsonl
from .installer import install_pack, verify_install
from .linker import ensure_glossary, resolve_related, write_index
from .packager import build_pack, validate_build_dir, validate_pack
from .pipeline import PipelineState, StageContext, run_stage
from .providers import get_provider
from .store import Store
from .verifier import verify_claims, verify_skill_quotes, write_provenance


def _err(message: str) -> None:
    print(f"[rushi] 错误: {message}", file=sys.stderr)


def _build_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--build", type=Path, required=True, help="构建目录（books/<slug> 或 pack）")


def _load_cfg(project: Path | None = None) -> Config:
    if project is None:
        project = Path.cwd()
    return Config.load(project)


def _require_build_dir(build: Path) -> int | None:
    if not build.is_dir():
        _err(f"构建目录不存在: {build}")
        return 1
    if not (build / "skills").is_dir():
        _err(f"构建目录缺少 skills/: {build}")
        return 1
    return None


def cmd_init(args: argparse.Namespace) -> int:
    cfg = default_config(args.project)
    cfg.save()
    for sub in ("books", "packs", "proposals"):
        (args.project / sub).mkdir(exist_ok=True)
    print(f"[rushi] 项目已初始化: {args.project.resolve()}（rushi.json）")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args.project)
    build = book_dir(args.project, args.slug)
    state = PipelineState.load(build)
    status = run_stage(
        state,
        "S0",
        StageContext(cfg, build),
        source=args.source,
        title=args.title,
        author=args.author,
        year=args.year,
        kind=args.kind,
    )
    if status != "done":
        _err("摄入失败")
        return 1
    print(f"[rushi] S0 完成: {build}")
    return 0


def cmd_stage(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args.project)
    build = args.build.resolve()
    rc = _require_build_dir(build)
    if rc is not None:
        return rc
    state = PipelineState.load(build)
    provider = None
    if args.mode == "provider":
        try:
            provider = get_provider(cfg)
        except Exception as exc:  # noqa: BLE001
            _err(str(exc))
            return 1
    kwargs = {}
    if args.stage == "S8":
        kwargs.update(name=args.name, version=args.version, out_root=(args.project / "packs"))
    status = run_stage(state, args.stage, StageContext(cfg, build, provider), **kwargs)
    print(f"[rushi] {args.stage} -> {status}")
    return 0 if status == "done" else 2


def cmd_verify(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args.project)
    build = args.build.resolve()
    rc = _require_build_dir(build)
    if rc is not None:
        return rc
    source_text = (build / "source.txt").read_text(encoding="utf-8")
    if args.skill_md:
        report = {"results": verify_skill_quotes(args.skill_md.read_text(encoding="utf-8"), source_text, cfg)}
        ok = all(r["status"] == "verified" for r in report["results"])
        for r in report["results"]:
            print(f"  [{r['status']}] {r['quote']} — {r.get('issue', '')}")
        return 0 if ok and report["results"] else 1
    if not (build / "source.txt").exists():
        _err("构建目录缺少 source.txt")
        return 1
    claims_path = build / "claims.jsonl"
    if not claims_path.exists():
        _err("缺少 claims.jsonl")
        return 1
    claims = [
        json.loads(line)
        for line in claims_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = verify_claims(claims, source_text, cfg)
    write_provenance(build, report)
    print(
        f"[rushi] S3 忠实度: fidelity={report['fidelity_rate']:.1%} "
        f"verified={report['verified']} unverified={report['unverified']} "
        f"blocked={report['blocked']}"
    )
    for r in report["results"]:
        mark = "✅" if r["status"] in ("verified", "verified-with-notes") else "❌"
        print(f"  {mark} {r['claim_id']} [{r['status']}] {r.get('source_span', '') or ''} {'; '.join(r.get('issues', []))}")
    return 0 if report["pass"] else 1


def cmd_check(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args.project)
    rc = _require_build_dir(args.build)
    if rc is not None:
        return rc
    issues: list[str] = []
    for d in (args.build / "skills").iterdir() if (args.build / "skills").exists() else []:
        if d.is_dir():
            issues += check_skill_dir(d, cfg)
    for i in issues:
        print(f"  ❌ {i}")
    print(f"[rushi] S5 构造校验: {'通过' if not issues else f'{len(issues)} 个问题'}")
    return 0 if not issues else 1


def cmd_link(args: argparse.Namespace) -> int:
    rc = _require_build_dir(args.build)
    if rc is not None:
        return rc
    issues = resolve_related(args.build)
    write_index(
        args.build,
        {"title": args.title, "author": args.author, "theme": args.theme, "created": ""},
        [],
    )
    ensure_glossary(args.build)
    for i in issues:
        print(f"  ❌ {i}")
    print(f"[rushi] S6 链接: INDEX.md 已生成；关系问题 {len(issues)}")
    return 0 if not issues else 1


def cmd_test(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args.project)
    rc = _require_build_dir(args.build)
    if rc is not None:
        return rc
    report = run_trigger_tests(args.build, mode=args.mode)
    write_test_report(args.build, report)
    print(
        f"[rushi] S7 评测: rate={report['overall_rate']:.1%} "
        f"bait_fail={report['bait_failures']} -> {'PASS' if report['pass'] else 'FAIL'}"
    )
    return 0 if report["pass"] else 1


def cmd_package(args: argparse.Namespace) -> int:
    try:
        pack = build_pack(
            args.build,
            args.project / "packs",
            args.name,
            args.version,
            confidence=args.confidence,
        )
    except ValueError as exc:
        _err(str(exc))
        return 1
    print(f"[rushi] S8 打包: {pack}")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    issues = validate_pack(
        args.pack, Path(__file__).resolve().parents[2] / "references" / "specs"
    )
    for i in issues:
        print(f"  ❌ {i}")
    print(f"[rushi] S9 发布闸门: {'通过' if not issues else f'{len(issues)} 个问题'}")
    return 0 if not issues else 1


def cmd_install(args: argparse.Namespace) -> int:
    try:
        report = install_pack(
            args.pack,
            args.host,
            args.scope,
            project=args.project,
            target=args.target,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        _err(str(exc))
        return 1
    mode = "（dry-run）" if report.dry_run else ""
    issues = [] if report.dry_run else verify_install(report)
    print(f"[rushi] 安装 {mode}: host={report.host} scope={report.scope} target={report.target}")
    for p in report.installed:
        print(f"  → {p}")
    for i in issues:
        print(f"  ❌ {i}")
    return 0 if not issues else 1


def cmd_evolve(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args.project)
    telemetry_path = args.telemetry
    if telemetry_path is None:
        db = args.project / ".rushi" / "telemetry.db"
        if db.exists():
            store = Store(db)
            rows = store.telemetry()
            store.close()
        else:
            _err("未指定 --telemetry，且项目无遥测库")
            return 1
    else:
        rows = load_telemetry_jsonl(telemetry_path)
    out = args.out or (args.project / "proposals")
    paths = generate_proposals(args.pack, rows, out, cfg)
    for p in paths:
        print(f"  → {p}")
    print(f"[rushi] S10 进化: 生成 {len(paths)} 条提案（待人类审批）")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    build = args.build.resolve()
    rc = _require_build_dir(build)
    if rc is not None:
        return rc
    state = PipelineState.load(build)
    print(state.render_md())
    for artifact in ("PROVENANCE.md", "TEST_REPORT.md", "GLOSSARY.md", "INDEX.md", "DIGEST.md"):
        print(f"  {'✅' if (build / artifact).exists() else '⬜'} {artifact}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    ok = True
    checks = [
        ("Python", sys.version.split()[0]),
        ("引擎版本", __version__),
        ("CLI 自举", "python rushi-cli.py"),
    ]
    for name, value in checks:
        print(f"  ✅ {name}: {value}")
    cfg_path = args.project / "rushi.json"
    if cfg_path.exists():
        try:
            cfg = _load_cfg(args.project)
            print(f"  ✅ 配置可读: {cfg_path}（provider={cfg.provider}, model={cfg.model or '默认'}）")
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"  ❌ 配置不可读: {cfg_path} — {exc}")
            ok = False
    else:
        print(f"  ⬜ 无 rushi.json（{args.project}），将使用默认配置")
    specs = Path(__file__).resolve().parents[2] / "references" / "specs"
    for spec in ("skill.schema.json", "pack.schema.json", "claim.schema.json", "test.schema.json"):
        exists = (specs / spec).exists()
        print(f"  {'✅' if exists else '❌'} spec/{spec}")
        ok = ok and exists
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rushi",
        description="入世：自验证、可进化、面向真实效果的 Agent Skill 生产系统",
    )
    parser.add_argument("--version", action="version", version=f"rushi {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="初始化项目（rushi.json + 目录）")
    p.add_argument("--project", type=Path, default=Path.cwd())
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("ingest", help="S0 摄入源文本")
    p.add_argument("--project", type=Path, default=Path.cwd())
    p.add_argument("--slug", required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--author", default="")
    p.add_argument("--year", default="")
    p.add_argument("--kind", default="doc", choices=["book", "video", "podcast", "course", "interview", "doc"])
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("stage", help="执行指定阶段 S0–S10")
    p.add_argument("--project", type=Path, default=Path.cwd())
    _build_arg(p)
    p.add_argument("stage", choices=[f"S{i}" for i in range(11)])
    p.add_argument("--mode", choices=["mock", "provider"], default="mock")
    p.add_argument("--name", default="")
    p.add_argument("--version", default="0.1.0")
    p.set_defaults(func=cmd_stage)

    p = sub.add_parser("verify", help="S3 忠实度校验（claims.jsonl 或 SKILL.md 引文）")
    p.add_argument("--project", type=Path, default=Path.cwd())
    _build_arg(p)
    p.add_argument("--skill-md", type=Path, default=None)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("check", help="S5 RIA++ 六段校验")
    p.add_argument("--project", type=Path, default=Path.cwd())
    _build_arg(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("link", help="S6 关系链接 + INDEX")
    p.add_argument("--project", type=Path, default=Path.cwd())
    _build_arg(p)
    p.add_argument("--title", default="未命名")
    p.add_argument("--author", default="")
    p.add_argument("--theme", default="")
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("test", help="S7 触发评测")
    p.add_argument("--project", type=Path, default=Path.cwd())
    _build_arg(p)
    p.add_argument("--mode", choices=["mock", "provider"], default="mock")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("package", help="S8 打包")
    p.add_argument("--project", type=Path, default=Path.cwd())
    _build_arg(p)
    p.add_argument("--name", required=True)
    p.add_argument("--version", default="0.1.0")
    p.add_argument("--confidence", default="unverified", choices=["author-claim", "empirically-supported", "unverified"])
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("gate", help="S9 发布闸门")
    p.add_argument("--pack", type=Path, required=True)
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("install", help="安装到宿主 skills 目录")
    p.add_argument("--pack", type=Path, required=True)
    p.add_argument("--host", choices=["claude", "cursor", "codex"], required=True)
    p.add_argument("--scope", required=True, help="user 或 project")
    p.add_argument("--project", type=Path, default=None)
    p.add_argument("--target", type=Path, default=None)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("evolve", help="S10 遥测 -> 进化提案")
    p.add_argument("--project", type=Path, default=Path.cwd())
    p.add_argument("--pack", type=Path, required=True)
    p.add_argument("--telemetry", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None)
    p.set_defaults(func=cmd_evolve)

    p = sub.add_parser("report", help="流水线状态报告")
    _build_arg(p)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("doctor", help="环境自检")
    p.add_argument("--project", type=Path, default=Path.cwd())
    p.set_defaults(func=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        _err(str(exc))
        return 1
