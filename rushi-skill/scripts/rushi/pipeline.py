"""流水线状态机（S0–S10）：状态追踪、断点续跑、阶段分发。

LLM 阶段（S1/S2/S4/S5）默认启用强制 JSON 输出：
- 引擎内置每阶段的 JSON 规格（JSON_SPECS），prompt 追加规格指令；
- provider 以 response_format=json_object 调用；
- 解析结果写入结构化产物（BOOK_OVERVIEW.md / candidates/*.json / s4/ / skills/）。
关闭方式：rushi.json json_mode=false 或环境变量 RUSHI_JSON_MODE=0。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import builder, content, evaluator, evolve, linker, packager, verifier


STAGES: list[dict[str, str]] = [
    {"id": "S0", "name": "内容摄入", "kind": "deterministic"},
    {"id": "S1", "name": "整书理解（Adler）", "kind": "llm"},
    {"id": "S2", "name": "并行提取（5 路）", "kind": "llm"},
    {"id": "S3", "name": "忠实度校验", "kind": "deterministic"},
    {"id": "S4", "name": "外部三角验证", "kind": "llm"},
    {"id": "S5", "name": "RIA++ 构造", "kind": "llm"},
    {"id": "S6", "name": "关系链接", "kind": "deterministic"},
    {"id": "S7", "name": "评测", "kind": "deterministic"},
    {"id": "S8", "name": "打包", "kind": "deterministic"},
    {"id": "S9", "name": "发布闸门", "kind": "deterministic"},
    {"id": "S10", "name": "进化", "kind": "deterministic"},
]


JSON_SPECS: dict[str, dict[str, str | None]] = {
    "S1": {
        "key": "book_overview_md",
        "instruction": (
            "【强制 JSON 输出】只输出一个 JSON 对象（禁止 ```json 包裹、禁止前言）："
            '{"book_overview_md":"<完整 BOOK_OVERVIEW.md Markdown>"}。'
            "book_overview_md 必须包含小节标题 ## 1. 结构、## 2. 解释、## 3. 批判、## 4. 应用潜力；"
            "结构节含一行'一句话主旨:'；批判节 ≥3 条（局限/盲点/假设/反对意见）；术语 ≥5 条；"
            "应用潜力节同时列出'可 skill 化'与'不适合 skill 化'。"
        ),
    },
    "S2": {
        "key": "candidates",
        "instruction": (
            "【强制 JSON 输出】只输出一个 JSON 对象（禁止 ```json 包裹、禁止前言）："
            '{"candidates":[{"id":"f01","title":"...","type":"framework","source_chapter":"...",'
            '"source_quote":"...","summary":"...","tags":["..."]}]}。'
            "type 必须是本提取器职责对应的类型之一（framework/principle/case/counter-example/term）；"
            "source_quote 必须逐字来自源文本；没有候选时输出 {\"candidates\":[]}。"
            "若候选过多，只输出最有代表性的 ≤20 条；source_quote 只取最关键的一句（≤80 字），禁止长段拼接。"
        ),
    },
    "S4": {
        "key": None,
        "instruction": (
            "【强制 JSON 输出】只输出一个 JSON 对象（禁止 ```json 包裹、禁止前言）："
            '{"id":"...","external_evidence":[],"contradicting_evidence":[],'
            '"falsification_test":"...","confidence":"...","notes":"..."}\n'
            "规则：confidence 只能是 author-claim | empirically-supported | unverified 三者之一；"
            "使用你的世界知识找外部佐证，找不到就写 unverified，禁止编造来源；"
            'falsification_test 必须是一个可被观察推翻的具体陈述，禁止写"无法验证"类拒答。'
        ),
    },
    "S5": {
        "key": "skill_md",
        "instruction": (
            "【强制 JSON 输出】只输出一个 JSON 对象（禁止 ```json 包裹、禁止前言）："
            '{"skill_md":"<完整 SKILL.md，含 frontmatter 与全部六段，换行用 \\n 转义>"}\n'
            "规则：只依据【待构造单元】字段构造 SKILL.md；R 段引文必须逐字使用 source_quote 字段；"
            "源文本未提供，禁止复述或总结任何其他内容。"
            "frontmatter 必须包含 name/description/version/source/confidence/related/freshness 七个字段，"
            "description 必须包含'不适用'字样（何时不用）。"
            "正文必须严格使用以下六个标题（一字不差）："
            "## R — 原文（Reading）、## I — 方法论骨架（Interpretation）、"
            "## A1 — 书中的应用（Past Application）、## A2 — 触发场景（Future Trigger）★、"
            "## E — 可执行步骤（Execution）、## B — 边界（Boundary）★。"
            "R 段引文行必须以 '> ' 开头（Markdown 块引用）并标注出处；"
            "A2 段必须包含小节标题「### 语言信号」并列出 2-3 条；"
            "E 段每个编号步骤后必须写「完成标准: ...」；"
            "B 段必须包含「### 不要在以下情况使用」小节。"
        ),
    },
}


EXTRACTOR_FILES: dict[str, str] = {
    "extract-framework.md": "frameworks",
    "extract-principle.md": "principles",
    "extract-case.md": "cases",
    "extract-counter-example.md": "counter-examples",
    "extract-glossary.md": "glossary",
}


def parse_json_output(text: str, key: str | None) -> Any:
    """剥离代码块后解析 JSON；key=None 返回对象本身，否则返回 key 对应的值。"""
    m = re.match(r"^```[a-zA-Z]*\s*\n(.*?)\n```\s*$", text or "", re.DOTALL)
    if m:
        text = m.group(1)
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if key is None:
        return data if isinstance(data, dict) else None
    if isinstance(data, dict) and key in data:
        return data[key]
    return None


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class PipelineState:
    book_dir: Path
    stages: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def load(cls, book_dir: Path) -> "PipelineState":
        path = book_dir / ".rushi" / "state.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(book_dir=book_dir, stages=data.get("stages", {}))
        state = cls(book_dir=book_dir)
        for stage in STAGES:
            state.stages[stage["id"]] = {"status": "pending", "note": ""}
        return state

    def save(self) -> None:
        (self.book_dir / ".rushi").mkdir(parents=True, exist_ok=True)
        path = self.book_dir / ".rushi" / "state.json"
        path.write_text(
            json.dumps({"stages": self.stages}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.book_dir / "PIPELINE_STATE.md").write_text(
            self.render_md(), encoding="utf-8"
        )

    def mark(self, stage_id: str, status: str, note: str = "") -> None:
        self.stages[stage_id] = {"status": status, "note": note, "updated_at": utcnow()}
        self.save()

    def render_md(self) -> str:
        lines = ["# PIPELINE_STATE.md — 流水线状态", ""]
        for stage in STAGES:
            st = self.stages.get(stage["id"], {})
            status = st.get("status", "pending")
            note = st.get("note", "")
            icon = {"done": "✅", "failed": "❌", "needs-provider": "⏸", "skipped": "➖"}.get(
                status, "⬜"
            )
            lines.append(f"- {icon} {stage['id']} {stage['name']} — {status} {note}")
        return "\n".join(lines) + "\n"


@dataclass
class StageContext:
    cfg: Any
    build_dir: Path
    provider: Any = None


def run_stage(state: PipelineState, stage_id: str, ctx: StageContext, **kwargs: Any) -> str:
    """执行单个阶段；返回状态。"""
    if stage_id == "S0":
        result = _stage_ingest(ctx, **kwargs)
        status = "done" if result else "failed"
        state.mark("S0", status, result or "摄入失败")
        return status
    if stage_id == "S1":
        return _stage_adler(state, ctx)
    if stage_id == "S2":
        return _stage_extract(state, ctx)
    if stage_id == "S3":
        return _stage_verify(state, ctx)
    if stage_id == "S4":
        return _stage_external(state, ctx)
    if stage_id == "S5":
        return _stage_construct(state, ctx)
    if stage_id == "S6":
        return _stage_link(state, ctx)
    if stage_id == "S7":
        return _stage_test(state, ctx)
    if stage_id == "S8":
        return _stage_package(state, ctx, **kwargs)
    if stage_id == "S9":
        return _stage_gate(state, ctx)
    if stage_id == "S10":
        return _stage_evolve(state, ctx)
    raise ValueError(f"未知阶段 {stage_id}")


def _stage_ingest(ctx: StageContext, source: Path, title: str, author: str, year: str, kind: str) -> str:
    manifest = content.build_manifest(
        source, title, author, year, kind, chunk_size=ctx.cfg.chunk_size
    )
    text = content.read_source(source)
    content.write_manifest(ctx.build_dir, manifest, text)
    (ctx.build_dir / "candidates").mkdir(exist_ok=True)
    (ctx.build_dir / "skills").mkdir(exist_ok=True)
    return f"已摄入 {manifest.chunks.__len__()} 块，sha256={manifest.sha256[:12]}"


def _load_prompt(prompt_name: str, build_dir: Path, include_source: bool = True) -> str:
    path = Path(__file__).parent / "prompts" / prompt_name
    if not path.exists():
        raise FileNotFoundError(f"缺少提示词模板: {path}")
    text = path.read_text(encoding="utf-8")
    source_path = build_dir / "source.txt"
    if include_source and source_path.exists():
        source = source_path.read_text(encoding="utf-8")
        if len(source) > 200_000:
            source = source[:200_000] + "\n[已截断]"
        text += f"\n\n## 输入\n\n源文本:\n{source}\n"
    return text


def _write_prompt(build_dir: Path, name: str, text: str) -> Path:
    prompt_dir = build_dir / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    path = prompt_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def _call_provider(
    ctx: StageContext, prompt: str, prompt_name: str, stage_id: str
) -> tuple[str | None, str]:
    """返回 (输出, 错误)。provider 缺失时返回 ("", "needs-provider")。"""
    _write_prompt(ctx.build_dir, prompt_name, prompt)
    if ctx.provider is None:
        return None, "needs-provider"
    try:
        output = ctx.provider.complete(
            prompt, json_mode=ctx.cfg.json_mode and stage_id in JSON_SPECS
        )
    except Exception as exc:  # noqa: BLE001 外部调用失败统一转状态
        return None, f"{type(exc).__name__}: {exc}"
    return output, ""


def _call_provider_json(
    ctx: StageContext, prompt: str, prompt_name: str, stage_id: str, key: str | None
) -> tuple[Any, str | None, str]:
    """调用 provider；JSON 模式解析失败自动重试一次。
    返回 (值, 原始输出, 错误)。legacy（json_mode=False）模式下值=原始输出。"""
    text, err = _call_provider(ctx, prompt, prompt_name, stage_id)
    if err:
        return None, text, err
    if not ctx.cfg.json_mode:
        return text, text, ""
    value = parse_json_output(text, key)
    if value is not None:
        return value, text, ""
    retry_name = prompt_name.removesuffix(".md") + ".retry.md"
    text2, err2 = _call_provider(ctx, prompt, retry_name, stage_id)
    if err2:
        return None, text, f"{err2}（重试后仍失败）"
    value = parse_json_output(text2, key)
    if value is not None:
        return value, text2, ""
    return None, text2, "输出不是合法 JSON（重试后仍失败）"


def _stage_status(ok: int, total: int, errors: list[str], note: str) -> str:
    if ok == total:
        return "done"
    if errors and all("needs-provider" in e for e in errors):
        return "needs-provider"
    return "failed"


def _stage_adler(state: PipelineState, ctx: StageContext) -> str:
    prompt = _load_prompt("adler.md", ctx.build_dir)
    if ctx.cfg.json_mode:
        prompt += "\n\n" + str(JSON_SPECS["S1"]["instruction"])
    text, raw, err = _call_provider_json(ctx, prompt, "S1-adler.md", "S1", "book_overview_md")
    if err:
        if raw is not None:
            review_dir = ctx.build_dir / "s1-review"
            review_dir.mkdir(exist_ok=True)
            (review_dir / "raw.md").write_text(raw, encoding="utf-8")
        status = "needs-provider" if err == "needs-provider" else "failed"
        state.mark("S1", status, err)
        return status
    (ctx.build_dir / "BOOK_OVERVIEW.md").write_text(text, encoding="utf-8")
    state.mark("S1", "done", "BOOK_OVERVIEW.md 已生成")
    return "done"


def _stage_extract(state: PipelineState, ctx: StageContext) -> str:
    overview = ctx.build_dir / "BOOK_OVERVIEW.md"
    overview_text = ""
    if overview.exists():
        overview_text = "\n" + overview.read_text(encoding="utf-8")[:8000]
    errors: list[str] = []
    counts: list[str] = []
    for ex, fname in EXTRACTOR_FILES.items():
        prompt = _load_prompt(ex, ctx.build_dir) + overview_text
        if ctx.cfg.json_mode:
            prompt += "\n\n" + str(JSON_SPECS["S2"]["instruction"])
        value, raw, err = _call_provider_json(ctx, prompt, f"S2-{ex}", "S2", "candidates")
        if err:
            if raw is not None and ctx.cfg.json_mode:
                (ctx.build_dir / "candidates" / f"{fname}.raw.md").write_text(raw, encoding="utf-8")
            errors.append(f"{ex}: {err}")
            continue
        if ctx.cfg.json_mode:
            out = ctx.build_dir / "candidates" / f"{fname}.json"
            out.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
            counts.append(f"{fname}={len(value)}")
        else:
            out = ctx.build_dir / "candidates" / f"{fname}.md"
            out.write_text(value, encoding="utf-8")
            counts.append(f"{fname}=raw")
    status = _stage_status(len(counts), len(EXTRACTOR_FILES), errors, "")
    note = "；".join(counts + errors[:3])
    state.mark("S2", status, note or "无候选")
    return status


def _load_claims(build_dir: Path) -> list[dict[str, Any]] | None:
    path = build_dir / "claims.jsonl"
    if not path.exists():
        return None
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _stage_external(state: PipelineState, ctx: StageContext) -> str:
    claims = _load_claims(ctx.build_dir)
    if claims is None:
        state.mark("S4", "failed", "缺少 claims.jsonl")
        return "failed"
    ok = 0
    errors: list[str] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id", "?"))
        prompt = _load_prompt("verify-external.md", ctx.build_dir, include_source=False)
        prompt += f"\n## 待验证候选\n\n{json.dumps(claim, ensure_ascii=False)}"
        if ctx.cfg.json_mode:
            prompt += "\n\n" + str(JSON_SPECS["S4"]["instruction"])
        data, raw, err = _call_provider_json(ctx, prompt, f"S4-{claim_id}.md", "S4", None)
        if err:
            if raw is not None:
                review_dir = ctx.build_dir / "s4-review"
                review_dir.mkdir(exist_ok=True)
                (review_dir / f"{claim_id}.raw.md").write_text(raw, encoding="utf-8")
            errors.append(f"{claim_id}: {err}")
            continue
        if ctx.cfg.json_mode:
            out = ctx.build_dir / "s4" / f"{claim_id}.json"
            out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            out = ctx.build_dir / "s4" / f"{claim_id}.md"
            out.parent.mkdir(exist_ok=True)
            out.write_text(data, encoding="utf-8")
        ok += 1
    status = _stage_status(ok, len(claims), errors, "")
    state.mark("S4", status, f"已验证 {ok}/{len(claims)}" + ("；" + "；".join(errors[:3]) if errors else ""))
    return status


def _stage_construct(state: PipelineState, ctx: StageContext) -> str:
    claims = _load_claims(ctx.build_dir)
    if claims is None:
        state.mark("S5", "failed", "缺少 claims.jsonl")
        return "failed"
    ok = 0
    errors: list[str] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id", "?"))
        prompt = _load_prompt("construct-ria.md", ctx.build_dir, include_source=False)
        prompt += f"\n## 待构造单元\n\n{json.dumps(claim, ensure_ascii=False)}\n"
        if ctx.cfg.json_mode:
            prompt += "\n\n" + str(JSON_SPECS["S5"]["instruction"])
        else:
            prompt += (
                "只依据【待构造单元】字段构造 SKILL.md，R 段引文必须逐字使用 source_quote 字段，"
                "禁止复述或总结任何其他内容；请直接输出完整 SKILL.md，禁止代码块包裹。"
            )
        skill_md, raw, err = _call_provider_json(ctx, prompt, f"S5-{claim_id}.md", "S5", "skill_md")
        if err:
            if raw is not None:
                review_dir = ctx.build_dir / "s5-review"
                review_dir.mkdir(exist_ok=True)
                (review_dir / f"{claim_id}.raw.md").write_text(raw, encoding="utf-8")
            errors.append(f"{claim_id}: {err}")
            continue
        issues, _ = builder.validate_skill(skill_md, ctx.cfg)
        slug = str(claim.get("skill_slug", "skill")) or "skill"
        if not issues:
            skill_dir = ctx.build_dir / "skills" / slug
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
            ok += 1
        else:
            review_dir = ctx.build_dir / "s5-review"
            review_dir.mkdir(exist_ok=True)
            (review_dir / f"{claim_id}.md").write_text(
                skill_md + "\n\n<!-- 校验失败原因 -->\n" + "\n".join(f"- {i}" for i in issues[:10]),
                encoding="utf-8",
            )
            errors.append(f"{claim_id}: {'; '.join(issues[:3])}")
    status = _stage_status(ok, len(claims), errors, "")
    state.mark("S5", status, f"构造通过 {ok}/{len(claims)}" + ("；" + "；".join(errors[:3]) if errors else ""))
    return status


def _stage_verify(state: PipelineState, ctx: StageContext) -> str:
    claims_path = ctx.build_dir / "claims.jsonl"
    source_path = ctx.build_dir / "source.txt"
    if not claims_path.exists() or not source_path.exists():
        state.mark("S3", "failed", "缺少 claims.jsonl 或 source.txt")
        return "failed"
    claims = [json.loads(line) for line in claims_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = verifier.verify_claims(claims, source_path.read_text(encoding="utf-8"), ctx.cfg)
    verifier.write_provenance(ctx.build_dir, report)
    status = "done" if report["pass"] else "failed"
    state.mark("S3", status, f"fidelity={report['fidelity_rate']:.1%} verified={report['verified']}")
    return status


def _stage_link(state: PipelineState, ctx: StageContext) -> str:
    issues = linker.resolve_related(ctx.build_dir)
    meta = {
        "title": "未命名",
        "author": "",
        "theme": "",
        "created": utcnow(),
    }
    linker.write_index(ctx.build_dir, meta, [])
    linker.ensure_glossary(ctx.build_dir)
    status = "done" if not issues else "failed"
    state.mark("S6", status, "；".join(issues) or "INDEX.md 已生成")
    return status


def _stage_test(state: PipelineState, ctx: StageContext) -> str:
    report = evaluator.run_trigger_tests(ctx.build_dir, mode=ctx.cfg.provider)
    evaluator.write_test_report(ctx.build_dir, report)
    status = "done" if report["pass"] else "failed"
    state.mark("S7", status, f"rate={report['overall_rate']:.1%} bait_fail={report['bait_failures']}")
    return status


def _stage_package(state: PipelineState, ctx: StageContext, **kwargs: Any) -> str:
    try:
        out = packager.build_pack(
            ctx.build_dir,
            kwargs.get("out_root", ctx.build_dir / ".." / ".." / "packs").resolve(),
            kwargs.get("name", ctx.build_dir.name),
            kwargs.get("version", "0.1.0"),
        )
        state.mark("S8", "done", f"打包完成: {out}")
        return "done"
    except ValueError as exc:
        state.mark("S8", "failed", str(exc))
        return "failed"


def _stage_gate(state: PipelineState, ctx: StageContext) -> str:
    issues = packager.validate_build_dir(ctx.build_dir)
    status = "done" if not issues else "failed"
    state.mark("S9", status, "；".join(issues) or "发布闸门通过")
    return status


def _stage_evolve(state: PipelineState, ctx: StageContext) -> str:
    telemetry_path = ctx.build_dir / "telemetry.jsonl"
    if not telemetry_path.exists():
        state.mark("S10", "skipped", "无遥测数据")
        return "skipped"
    rows = evolve.load_telemetry_jsonl(telemetry_path)
    paths = evolve.generate_proposals(ctx.build_dir, rows, ctx.build_dir / "proposals", ctx.cfg)
    state.mark("S10", "done", f"生成 {len(paths)} 条提案")
    return "done"
