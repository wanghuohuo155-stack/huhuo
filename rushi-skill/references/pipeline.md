# 入世流水线（S0–S10）

## 目录

1. 总览
2. 各阶段规格
3. 确定性 gate 汇总
4. 断点续跑

## 1. 总览

入世把仓颉的 7 阶段流水线升级为 10 阶段。所有 LLM 阶段（S1/S2/S4）产出必须带
可定位的原文引用；所有确定性阶段（S3/S5/S6/S7/S8/S9/S10）由引擎自动执行，
不通过即打回。

## 2. 各阶段规格

| 阶段 | 名称 | 类型 | 输入 | 输出 | gate |
|---|---|---|---|---|---|
| S0 | 内容摄入 | deterministic | 源文件 | source.txt + source.manifest.json | 源哈希入库、分块完整 |
| S1 | 整书理解（Adler） | llm | source.txt + adler.md | BOOK_OVERVIEW.md | 批判 ≥3、术语 ≥5 |
| S2 | 并行提取（5 路） | llm | BOOK_OVERVIEW + 5 个 extractor | candidates/*.md | 每条候选带 source_quote |
| S3 | 忠实度校验 | deterministic | claims.jsonl + source.txt | PROVENANCE.md | 引文定位 100%、数字带出处 |
| S4 | 外部三角验证 | llm | verified 候选 | 外部证据 + confidence | 未佐证不得标 empirically-supported |
| S5 | RIA++ 构造 | manual | 验证通过单元 | skills/<slug>/SKILL.md | 六段完整、description 有反触发 |
| S6 | 关系链接 | deterministic | skills/* | INDEX.md + GLOSSARY.md | 无孤儿引用 |
| S7 | 评测 | deterministic | tests/trigger.json | TEST_REPORT.md | 诱饵容错 0、通过率 ≥80% |
| S8 | 打包 | deterministic | build 目录 | packs/<name>/pack.json | 产物完整性 |
| S9 | 发布闸门 | deterministic | pack 目录 | 证据徽章 | schema + artifact 全过 |
| S10 | 进化 | deterministic | telemetry.jsonl | proposals/*.md | 人类审批 + 回归测试 |

## 3. 确定性 gate 汇总

- **S3**：`rushi verify` — 引文必须在源文本中定位（精确/去标点模糊），
  summary/title 中的每个数字必须出现在引文或 source_note 中。
- **S5**：`rushi check` — 六段（R/I/A1/A2/E/B）齐全；description ≤300 字且含
  反触发信号；E 段有完成标准；B 段有反场景。
- **S6**：`rushi link` — related 引用必须能解析到真实 skill 目录。
- **S7**：`rushi test` — should_not_trigger 容错为 0；总通过率 ≥80%；
  至少 5 条用例且含诱饵。
- **S9**：`rushi gate` — pack.json 通过 schema 校验；PROVENANCE/TEST_REPORT/
  GLOSSARY/INDEX 齐全；每个 skill 有 SKILL.md 与随包 GLOSSARY。

## 4. 断点续跑

每个 build 目录有 `.rushi/state.json` 与 `PIPELINE_STATE.md`。`rushi report --build <dir>`
查看状态；`rushi stage --build <dir> S<N>` 从任意阶段恢复执行。LLM 阶段在未配置
provider 时标记 `needs-provider` 并写入 prompts/ 目录，供人工或真实 provider 执行。

