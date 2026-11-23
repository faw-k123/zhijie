# P17-E batch_01 数据状态对账报告

> 对账日期：2026-11-05  
> 结论：**CONDITIONAL_PASS**  
> 封存结论：**不封存**

## 1. 最终可信统计

```text
batch_01 曲目：25
实际检索：21
未检索：4
覆盖率：21/25 = 84%

performance_confirmed：3
program_listed：0
ambiguous_match：6
no_relevant_result_after_search：12
outcome_evidenced：0

打开原始网页：3
有效证据：3
候选关联：0
```

全局：

```text
302 首中实际检索：21
覆盖率：21/302 = 6.95%
未检索：281
```

## 2. 哪组数字正确

正确的一组是：

```text
21 / 25
```

之前第五批报告的：

```text
25 / 25
```

不成立。

## 3. 冲突原因

### 原因一：批次5文件只更新到 ID 17

`batch_01_search_results_batch5.csv` 实际只有 9 首有检索状态，8 首仍是 `not_searched`：

```text
18–25 仍在 not_searched
```

但 `batch_01_search_coverage_batch5.csv` 写成了：

```text
17 searched / 0 not_searched
```

### 原因二：合并文件仍是半成品

`batch_01_search_results_all.csv` 中：

```text
17 searched / 8 not_searched
```

但 `batch_01_search_coverage_all.csv` 写成了：

```text
25 searched / 0 not_searched
```

汇总数字与逐曲记录冲突。

### 原因三：ID 错位

`batch_01_source_evidence_all.csv` 曾把《广陵散》写成：

```text
music_id = 16
```

实际正式 ID 为：

```text
music_id = 24
```

ID 16 实际是《飞雪玉花》。

### 原因四：搜索状态与标题映射错位

第五批按曲名分组记录时，部分状态被写到了错误的 song_id 上，导致：

- ID 9–12 实际没有检索，却被覆盖表算入；
- ID 18–25 有检索，却没有进入 batch5 文件；
- 覆盖表按“计划 17 首”而不是“实际记录”统计。

## 4. 逐首结果

| 状态 | 数量 | song_id |
|---|---:|---|
| performance_confirmed | 3 | 3、13、24 |
| ambiguous_match | 6 | 1、5、8、17、19、22 |
| no_relevant_result_after_search | 12 | 2、4、6、7、14、15、16、18、20、21、23、25 |
| not_searched | 4 | 9、10、11、12 |

## 5. 三条演出确认

```text
music_id 3  一生所爱  A  泰国格乐大学
music_id 13 赛马      B  大富频道
music_id 24 广陵散    B  The Los Angeles Post
```

均能追溯到原始来源；当前重访失败不否定历史正文核验。

## 6. 是否完成 25/25

```text
否
```

4 首仍是 `not_searched`：

```text
9 牵丝戏
10 神经病之歌
11 花田错
12 葬花吟
```

## 7. 是否具备封存条件

```text
不具备
```

原因：

- 4 首未检索；
- 6 条 ambiguous 未人工确认；
- 旧文件存在覆盖表和逐曲表冲突；
- `广陵散` ID 已纠正，但旧证据表仍保留错误版本。

## 8. 数据安全

```text
active_version = v1.6
manifest sha256 = ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a
v1.6 文件哈希未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 9. 输出

- `p17e_batch01_song_level_reconciliation.csv`
- `p17e_batch01_statistics_recalculated.csv`
- 本报告

## 10. 结论

```text
CONDITIONAL_PASS
```

不是 BLOCKED：原始逐曲记录可读，问题范围已定位。  
但不能封存，需补检索 4 首并人工处理 6 条 ambiguous 后重新对账。  
不启动 batch_02，不启动 P18。
