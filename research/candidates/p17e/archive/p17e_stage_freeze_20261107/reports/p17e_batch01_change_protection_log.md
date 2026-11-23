# P17-E 变更与正式数据保护记录

## 1. 本轮修改

```text
batch_01_search_results_all_final.csv
batch_01_search_coverage_all_final.csv
song_search_log.csv
song_search_coverage.csv
batch_01_ambiguous_review_batch7B.csv
batch_01_ambiguous_evidence_batch7B.csv
```

新增：

```text
p17e_batch7B_adoption_report.md
p17e_batch01_consistency_audit.md
```

## 2. 修改内容

- song_id 8 从 `ambiguous_match` 更新为 `rejected_match`；
- 其余 6 条保持 `ambiguous_match`；
- batch_01 总状态更新为 3/6/1/15/0；
- 全局覆盖更新为 25/302；
- 三条演出确认未修改；
- 无新增候选关联。

## 3. 哈希

```text
manifest：
ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a

batch_01_search_results_all_final.csv：
163e4f1d254d1b55ee4c216892d266549a3cda4d2c9e3300f4d0e5e7a48b95f3

batch_01_search_coverage_all_final.csv：
52b5b46eedae65c5552b5d15794911e0bcf4dea0cdb6a8610783909bd4a11a09

song_search_log.csv：
daccfdc9904f6fd0a96526b8d7d2b86a18b7cba0711ae68a19ad08a6fc895bc0

song_search_coverage.csv：
effc47b26e64308c20ec850afee08ac247a9c4fff34697764869ecd90b5b57c2
```

## 4. 未修改的正式数据

```text
active_version = v1.6
v1.6 五个数据文件哈希未变化
manifest 未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server 未写入
Neo4j 未写入
```

## 5. 状态

```text
batch_01_sealed = false
batch_02_started = false
P18_started = false
```
