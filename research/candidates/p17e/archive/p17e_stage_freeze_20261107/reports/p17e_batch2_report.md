# P17-E 第二批报告

## 1. 批次范围

- 已核验 CASE008：保持；
- 20 个 HTTP 200 中，除 CASE008 外的 19 个逐页检查；
- 19 个失败来源各重试 1 次；
- 1 个 HTTP 202 单独处理；
- 302 首外部检索：未开始。

## 2. 来源访问状态

```text
accessible：27
inaccessible：12
challenge_or_pending：1
```

## 3. 内容核验状态

19 个待核验来源：

```text
content_partially_verified：8
content_unreadable：7
content_not_relevant：4
content_verified：0（CASE008 之外没有新的全文确认）
content_not_reviewed：0
```

## 4. 40 案例最终状态

```text
verified_event_content：1（CASE008）
partially_verified：8
needs_more_evidence：19
source_unavailable：12
conflicting_evidence：0
```

## 5. CASE008

```text
梅花三弄：performance_confirmed
流水：performance_confirmed
平沙落雁：program_listed
酒狂：program_listed
阳关三叠：program_listed
outcome_evidenced：0
```

未重复核验两首已确认曲目，三首未升级。

## 6. 输出

- `02_case_reverification/case_reverification_batch2.csv`
- `02_case_reverification/source_recheck_batch2.csv`
- `02_case_reverification/source_content_verification.csv`
- `02_case_reverification/source_manual_review_queue.csv`

## 7. 前端修正

已完成案例库“案例库收录 40/40”、CASE007 待核实/不纳入严格样本、详情均值“仅供描述”等文字和标签修正。

详见 `docs/p17e-frontend-correction.md`。

## 8. 验收结论

```text
CONDITIONAL_PASS
```

已完成 19 个 200 来源内容检查、19 个失败来源重试、202 处理、前端展示修正；
但仍有 12 个来源不可访问、19 个案例内容未完全核验、302 首外部检索未开始。

不启动 P18，不修改正式数据。
