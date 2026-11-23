# P17-E 冻结归档报告

> 归档日期：2026-11-07  
> 阶段结论：**CONDITIONAL_PASS**  
> 归档状态：**FROZEN**

## 1. 归档位置

```text
research/candidates/p17e/archive/p17e_stage_freeze_20261107/
```

内容：

- P17-E 候选目录快照；
- 报告与 CSV；
- 检索日志与人工复核记录；
- `FREEZE_RECORD.md`；
- `SHA256SUMS.csv`；
- `manifest.json`。

## 2. 归档统计

```text
文件：88
字节：348,665
SHA256：88/88
只读：true
```

## 3. 冻结状态

```text
active_version = v1.6
batch_01 = 25/25 已完成状态分类
performance_confirmed = 3
ambiguous_match = 6
rejected_match = 1
no_relevant_result = 15
not_searched = 0
outcome_evidenced = 0
candidate_links = 0
batch_01_sealed = false
batch_02_started = false
P18_started = false
```

## 4. 关键结论

- 3 条演出确认：song_id 3、13、24；
- 均为单来源；
- 当前原始页面重访失败；
- 6 条歧义未解决；
- 1 条错误匹配已拒绝；
- 15 条无相关结果；
- 正式数据未修改。

## 5. 正式数据保护

```text
manifest sha256 = ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a
v1.6 五个数据文件未修改
40 案例、302 曲目、400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 6. 使用限制

归档是只读快照，不进入正式 API，不自动合并到 v1.6。  
后续补充证据必须新建批次，不修改本归档。

## 7. 输出

- `research/candidates/p17e/archive/p17e_stage_freeze_20261107/`
- `research/candidates/p17e/reports/p17e_stage_audit_report.md`
- `research/candidates/p17e/reports/p17e_stage_decision.md`
- 本报告
