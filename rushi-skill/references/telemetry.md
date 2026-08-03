# 遥测与进化闭环（S10）

## 目录

1. 遥测事件
2. 聚合规则
3. 提案类型
4. 审批流程

## 1. 遥测事件

```json
{"skill_slug": "margin-of-safety", "event": "mis_trigger", "ts": "2026-08-02T00:00:00Z", "detail": "用户问市场趋势被误触发"}
```

事件枚举：

- `invocations` — 被调用
- `mis_trigger` — 不应调用却调用
- `positive` — 用户正面反馈
- `negative` — 用户负面反馈/误用报告

## 2. 聚合规则

按 skill 聚合：调用数、误触发数、正/负面数。误触发率 =
mis_trigger / invocations（仅在有调用记录时计算）。

## 3. 提案类型

| 触发条件 | 提案 | 回归要求 |
|---|---|---|
| 误触发率 > 15% | 收紧 description + 新增诱饵用例 | 旧 trigger.json 全过 + 新用例 |
| 负面反馈 ≥ 3 | 复审 B/E 段，补充失败模式 | 全量评测通过 |
| 正面反馈 ≥ 10 | confidence 提升一档 | 版本号更新 |
| 90 天零调用 | 复审相关性 / 建议过期或重构 | 人工决策 |

## 4. 审批流程

1. `rushi evolve` 生成 `proposals/<ts>-<slug>.md`
2. 人类审查：同意 / 修改 / 驳回
3. 通过的提案修改 SKILL.md + tests，跑 `rushi check/test/gate`
4. 发版：semver + CHANGELOG + 可回滚
