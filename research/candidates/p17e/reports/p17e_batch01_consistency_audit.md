# P17-E batch_01 一致性审计

## 1. 总量

```text
曲目：25
最终状态：25
每首唯一状态：YES
```

## 2. 状态分布

| 状态 | 数量 |
|---|---:|
| performance_confirmed | 3 |
| ambiguous_match | 6 |
| rejected_match | 1 |
| no_relevant_result_after_search | 15 |
| not_searched | 0 |
| 合计 | 25 |

## 3. 重点核对

```text
song_id 8 江南：rejected_match
其余 6 条：ambiguous_match
song_id 3 一生所爱：performance_confirmed
song_id 13 赛马：performance_confirmed
song_id 24 广陵散：performance_confirmed
outcome_evidenced：0
candidate_links：0
```

## 4. 文件一致性

- `batch_01_search_results_all_final.csv`：25 行；
- `batch_01_search_coverage_all_final.csv`：3/6/1/15/0；
- `batch_01_ambiguous_review_batch7B.csv`：6 remain + 1 rejected；
- `song_search_coverage.csv`：25/302；
- 旧审计版文件保留未覆盖。

## 5. 正式数据保护

```text
active_version = v1.6
manifest sha256 = ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a
v1.6 哈希未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 6. 结论

```text
PASS（一致性审计）
```

但不能封存 batch_01：6 条 ambiguous、1 条 rejected、3 条演出确认仍为单来源。
