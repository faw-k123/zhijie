# P12.3 正式准入审核报告

> 结果：approved 2；needs_more_evidence 3；rejected 0；hold 0。  
> 没有分配正式 CASE 编号，没有写入 v1.2。

## 1. 审核结果

| candidate_id | case_type | admission_decision | 核心理由 |
|---|---|---|---|
| P12-C001 | overseas_institution_education | needs_more_evidence | 只有 program_listed，无演出完成记录 |
| P12-C002 | cross_cultural_ensemble | approved | 演出后报道、乐器、曲目、地点清楚 |
| P12-C003 | cross_cultural_ensemble | approved | 演出后报道、二胡与跨文化合作、曲目清楚 |
| P12-C004 | overseas_institution_ensemble | needs_more_evidence | 有演出，但无具体乐器/曲目 |
| P12-C005 | overseas_institution_ensemble | needs_more_evidence | PR 稿为主，缺独立来源和具体曲目/乐器 |

## 2. approved 的含义

`approved` 只表示：

- 可以进入新版候选案例；
- 不是自动分配 CASE；
- 不是十项指标全部可评分；
- 不是严格外国个人。

P12-C002/P12-C003 都归入扩展跨文化样本，不进入 `strict_individual`。

## 3. 指标可评分性

### P12-C002

```text
可考虑：故事可解释性、跨文化适配、渠道适配、时代主题
不可评分：情感共鸣、音色辨识度、受众参与、教育支持、个人桥梁、持续性
```

### P12-C003

```text
可考虑：故事可解释性、跨文化适配、渠道适配、时代主题
不可评分：情感共鸣、音色辨识度、受众参与、教育支持、个人桥梁、持续性
```

### 其余

- C001：教育/故事/渠道线索，但演出完成未确认；
- C004：只有渠道线索；
- C005：只有渠道线索，PR 稿不足。

## 4. 为什么没有 rejected

5 条都有真实活动或官方页面，没有发现虚假主体；问题主要是证据不足，不是造假。

## 5. 为什么没有 hold

没有发现身份/活动性质/来源冲突到必须冻结的程度；因此用 `needs_more_evidence`。

## 6. 版本管理

- 不修改 v1.2；
- 不激活 v1.3；
- 不分配 CASE037 等编号；
- approved 候选留在候选层，等待下一版数据构建；
- 新来源 ID 已保留：P12-S001–S005。

## 7. 输出

- `research/analysis/p12-admission-decisions.csv`
- `research/analysis/p12-indicator-evidence-matrix.csv`
