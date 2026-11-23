# P17.2 40个既有案例证据复核

## 1. 复核方式

本阶段完成的是**桌面复核**：

- 核对 40 个 case_id 与来源 ID；
- 核对来源元数据；
- 未逐页重新打开全部外部网页；
- 未发现新增活动证据；
- 未将来源元数据自动升级为活动完成。

## 2. 结果

```text
案例复核：40/40
来源 ID 可关联：40/40
新增活动证据：0
实际活动确认：0
传播结果证据：0
来源冲突：0
待补外部复核：40
```

## 3. 活动状态

```text
unknown：40
announced：0
program_listed：0（新增证据）
performance_confirmed：0（新增证据）
outcome_verified：0
```

现有 CASE008 的 5 条是历史 program_listed，不在本表重复计为“新增活动”。

## 4. 关键边界

- 来源 ID 存在不等于来源内容仍有效；
- 来源存在不等于活动发生；
- 活动发生不等于传播结果；
- 同一机构长期存在不等于具体活动发生。

## 5. 输出

- `research/candidates/p17/case_reviews.json`
- `research/candidates/p17/case_activity_evidence.csv`
- `research/analysis/p17/case_review_summary.csv`
