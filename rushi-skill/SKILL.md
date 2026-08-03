---
name: rushi-skill
description: |
  入世（rushi）——自验证、可进化、面向真实效果的 Agent Skill 生产系统。
  当用户要求把书/长视频/播客/课程/文档蒸馏成可调用、可验证、可进化的 skill 包时使用；
  当用户要求"评估/升级/打包/安装/测试某个 skill 或 skill 包"时使用；
  当用户提到 evidence/provenance/trigger 测试/效果评测/进化闭环 时使用。
  触发词：拆书成 skill、蒸馏、入世、rushi、把 X 做成 skill、make a skill pack from、
  distill, verify skill, skill provenance, trigger tests, skill evolution。
  不适用于：简单摘要、书评、角色扮演作者（用 nuwa-skill）、纯问答、普通技能安装。
---

# 入世（rushi）— 自验证、可进化、面向真实效果的 Agent Skill 生产系统

## 使命

把高价值内容（书、长视频转写、播客、课程、内部文档）蒸馏成一组**可调用、可验证、
可测试、可进化**的原子 skill，并让 skill 接受真实世界使用反馈的检验。

区别于仓颉（cangjie-skill）：

- 仓颉问"知识如何变成 skill"；入世问"skill 如何自证可信、可测效果、持续进化"。
- 入世强制证据链（引文定位 + 数字出处）、发布闸门、效果评测与进化闭环。

## 快速开始

引擎入口（本 skill 自带脚本）：

```bash
python scripts/rushi-cli.py doctor
```

端到端示例（以 `examples/demo-pack` 演示）：

```bash
python scripts/rushi-cli.py verify --build ../../examples/demo-pack
python scripts/rushi-cli.py check  --build ../../examples/demo-pack
python scripts/rushi-cli.py link   --build ../../examples/demo-pack --title "演示源" --author "rushi"
python scripts/rushi-cli.py test   --build ../../examples/demo-pack --mode mock
python scripts/rushi-cli.py package --build ../../examples/demo-pack --project ../../.. --name demo-pack
python scripts/rushi-cli.py gate   --pack ../../../packs/demo-pack
python scripts/rushi-cli.py install --pack ../../../packs/demo-pack --host codex --scope user --dry-run
```

> 相对路径以 `rushi-skill/` 为工作目录。真实项目使用 `--project` 指定项目根。

## 工作流（按用户意图分派）

### 1. 用户要"从内容蒸馏 skill 包"

按 10 阶段流水线执行（详见 `references/pipeline.md`）：

1. `init` — 初始化项目（`rushi.json`）。
2. `ingest` — 摄入源文本（S0）。必须有真实文本，禁止凭记忆蒸馏。
3. `stage S1` / `stage S2` — 整书理解与并行提取（LLM 阶段；无 provider 时
   生成 prompts/ 待执行）。
4. 整理候选为 `claims.jsonl` 后 `verify`（S3 忠实度校验，确定性 gate）。
5. `stage S4` 外部三角验证（LLM）。
6. 按 `assets/templates/SKILL.md.template` 构造每个 skill（S5），然后 `check`。
7. `link`（S6）生成 INDEX/GLOSSARY。
8. 写 `tests/trigger.json` 后 `test`（S7）。
9. `package`（S8）→ `gate`（S9）→ 询问用户安装目标后 `install`（S10 由遥测驱动）。

### 2. 用户要"评估/校验已有 skill 或包"

- 引文与证据：`verify --build <dir> --skill-md <path>` 或对 `claims.jsonl` 全量校验。
- 六段完整性：`check --build <dir>`。
- 触发评测：`test --build <dir> --mode mock|provider`。
- 发布闸门：`gate --pack <dir>`。

### 3. 用户要"基于反馈进化 skill"

1. 收集遥测（`telemetry.jsonl` 或 SQLite）。
2. `evolve --pack <dir> --telemetry <file>` 生成提案。
3. 人类审批后修改 SKILL.md/tests，重跑 `check` + `test` + `gate`，semver 发版。

### 4. 用户要"把入世包装到宿主"

```bash
python scripts/rushi-cli.py install --pack <pack-dir> --host claude|codex|cursor \
  --scope user|project [--target <dir>] [--dry-run]
```

## 质量红线（违反则打回）

1. **每条 claim 的引文必须在源文本中可定位**（`verify` 不通过禁止打包）。
2. **数字必须带出处**：summary/title 中的数字须出现在引文或 source_note 中。
3. **description 必须含反触发信号**（何时不用），≤300 字。
4. **六段缺一不可**：R / I / A1 / A2 / E / B。
5. **诱饵容错为 0**：should_not_trigger 任何一条失败即 FAIL。
6. **发布包必须带 4 份证据**：PROVENANCE.md / TEST_REPORT.md / GLOSSARY.md / INDEX.md，
   且 GLOSSARY 随包嵌入每个 skill 目录（防止原子化断链）。
7. **未通过外部佐证的不得标记 empirically-supported**。
8. **进化提案必须经人类审批 + 回归测试后才能发版**。

## 规范与文档索引（按需读取）

- 流水线规格与 gate：`references/pipeline.md`
- Schema 速查：`references/schemas.md`
- 评测体系：`references/evaluation.md`
- 遥测与进化：`references/telemetry.md`
- 模板：`assets/templates/`（SKILL.md / pack.json / trigger.json / outcome.json / 证据文档）
- LLM 阶段提示词：`scripts/rushi/prompts/`

## 与生态的关系

- 蒸馏对象是"方法论"，不是人设（人设用 nuwa-skill）。
- 产出包可接入任何遵循"skills/<slug>/SKILL.md"约定的宿主。
- 本 skill 自身是入世系统的第一个参考实现，使用本 skill 蒸馏的内容会反哺引擎。

## 调用惯例

- 永远先跑 `doctor` 确认环境。
- 阶段之间主动汇报：每完成一个 gate 输出一行结果摘要。
- 不做表面修补：S7 失败必须回炉 S5（A2/E/B），而非改测试凑通过率。
- 用户没给文本时停下来问，绝不凭记忆蒸馏。
