# P17-E batch_01 封存记录

> 状态：**SEAL WITHHELD / CONDITIONAL_PASS**  
> 日期：2026-11-05  
> 批次：batch_01（25 首）  
> active_version：v1.6

## 1. 封存结论

```text
不封存
```

原因：

- 25 首中只有 21 首实际检索；
- ID 9–12 仍为 `not_searched`；
- 6 首 ambiguous 未人工确认；
- 3 条演出证据当前页面重访失败；
- 旧汇总存在 `25/25` 与逐曲记录冲突。

## 2. 批次统计

```text
曲目：25
实际检索：21
未检索：4
覆盖率：84%
performance_confirmed：3
ambiguous_match：6
no_relevant_result_after_search：12
outcome_evidenced：0
新增正式关联：0
```

## 3. 三条证据

| music_id | 曲目 | 来源 | 等级 |
|---:|---|---|---|
| 3 | 一生所爱 | 泰国格乐大学 | A |
| 13 | 赛马 | 大富频道 | B |
| 24 | 广陵散 | The Los Angeles Post | B |

当前重访：

```text
一生所爱：HTTP 502
赛马：SSL 中断
广陵散：SSL 中断
```

历史正文已核验；当前无法重访不否定原证据，但也未完成二次确认。

## 4. 未完成

```text
music_id 9 牵丝戏
music_id 10 神经病之歌
music_id 11 花田错
music_id 12 葬花吟
```

## 5. 哈希

```text
manifest:
ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a

batch_01_search_results_audited.csv:
2602cc1d039a06cc0fee3bde1c10fe178c2d6e20efcc597e2db9d0a5291dd105

batch_01_source_evidence_audited.csv:
df7b22983de17c7bb8f6403540576dc750ca710c9c78c04e70d26c6e1450a9f4

p17e_batch01_evidence_quality_review.csv:
b1577401ac9fdd1e4823b5311cbb6c9349eeefe36046bbd2f40790883a80e85d

p17e_batch01_manual_review_final.csv:
2c4a78760a2850df56bf31d035121dded470fd52f4d7c4220ae6b7605b4a5563
```

## 6. 解锁条件

1. 补检索 ID 9–12；
2. 人工处理 6 条 ambiguous；
3. 对 3 条演出证据做替代页面/存档复核；
4. 重新跑一致性统计；
5. 重新生成封存记录。

## 7. 数据安全

```text
active_version = v1.6
v1.6 文件哈希未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```
