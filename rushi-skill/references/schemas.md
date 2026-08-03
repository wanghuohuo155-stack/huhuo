# 规范速查（Schema v1.0）

## 目录

1. 文件位置
2. SKILL.md frontmatter
3. pack.json
4. claims.jsonl
5. trigger.json / outcome.json
6. 校验方法

## 1. 文件位置

所有 JSON Schema 位于 `references/specs/`：

- `skill.schema.json` — SKILL.md frontmatter
- `pack.schema.json` — pack.json
- `claim.schema.json` — claims.jsonl 单行
- `test.schema.json` — tests/trigger.json

## 2. SKILL.md frontmatter

```yaml
name: slug                    # kebab-case，2-63 字符
description: |                # ≤300 字；必须含"何时用 + 何时不用 + trigger 词"
version: 0.1.0                # semver
source: {title, author, year, span_id}
confidence: author-claim      # author-claim | empirically-supported | unverified
related: [{slug, relation, direction, weight}]
freshness: {checked_at, expires_at, policy}
tags: [tag1, tag2]
```

正文六段：R（逐字引用 ≤150 字/≤100 词）→ I（自述 5-15 行）→ A1（案例，
数字可溯源）→ A2（触发场景，★）→ E（编号步骤 + 完成标准）→ B（边界，★）。

## 3. pack.json

`rushi package` 自动生成。要点：schema_version=1.0、name/version、
source.sha256（64 位）、confidence、freshness（过期策略）、skills 列表、
artifacts 必须含 4 份证据文档、engine=rushi。

## 4. claims.jsonl

每行一条 claim，必填：claim_id（如 `f01`）、skill_slug、kind、title、
source_chapter、source_quote。`source_span` 由 S3 回填，禁止手写。

## 5. trigger.json / outcome.json

- trigger.json：≥5 条用例，三类缺一不可（should_trigger / should_not_trigger /
  edge_case），诱饵中至少 1 条是跨 skill 混淆。
- outcome.json：效果基准任务 + rubric + 基线预期，用于 S7 效果评测（A/B）。

## 6. 校验方法

```bash
python rushi-skill/scripts/rushi-cli.py gate --pack <pack-dir>
```

内置微型 JSON Schema 校验器（stdlib，无第三方依赖）。

