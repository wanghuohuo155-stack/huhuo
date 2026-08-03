# TEST_REPORT.md — 评测报告

- 模式: mock（fallback 结果，可信度低于独立盲测）
- 判官: mock-judge
- 生成时间: 2026-08-03T03:19:37+00:00
- 总通过率: 100.0%（8/8）
- 诱饵失败: 0（容错 0）
- 整体判定: PASS

## 明细

### slow-gardener — 100.0%（8/8）

| id | type | expected | actual | passed | score | 依据 |
|---|---|---|---|---|---|---|
| should-trigger-01 | should_trigger | 触发 | 触发 | ✅ | 0.19 | score=0.190 threshold=0.18 |
| should-trigger-02 | should_trigger | 触发 | 触发 | ✅ | 0.545 | score=0.545 threshold=0.18 |
| should-trigger-03 | should_trigger | 触发 | 触发 | ✅ | 0.438 | score=0.438 threshold=0.18 |
| should-not-trigger-01 | should_not_trigger | 不触发 | 不触发 | ✅ | 0.0 | score=0.000 threshold=0.18 |
| should-not-trigger-02 | should_not_trigger | 不触发 | 不触发 | ✅ | 0.0 | score=0.000 threshold=0.18 |
| should-not-trigger-03 | should_not_trigger | 不触发 | 不触发 | ✅ | 0.0 | score=0.000 threshold=0.18 |
| should-not-trigger-04 | should_not_trigger | 不触发 | 不触发 | ✅ | 0.0 | score=0.000 threshold=0.18 |
| edge-01 | edge_case | 不触发 | 不触发 | ✅ | 0.0 | score=0.000 threshold=0.18 |

