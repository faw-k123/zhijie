# P17-E 第五批 batch_01 报告

> 范围：补完 batch_01 剩余 17 首  
> 结果：17/17 完成两组外部检索  
> 结论：**PASS（batch_01 检索完成）**  
> 全局仍为 25/302，未完成 302。

## 1. 本轮覆盖

```text
本轮17首：17 已检索，0 未检索
打开原始网页：2
新增有效证据：2
新增 performance_confirmed：2
新增 program_listed：0
新增 outcome_evidenced：0
ambiguous_match：3
no_relevant_result_after_search：12
```

## 2. 新增证据

### 《赛马》 music_id 13

来源：

```text
大富频道
https://www.daifutv.com/c/index.php?option=com_content&view=article&id=8650:2026&catid=77:japan-news&Itemid=234
```

事实：

```text
2026-11-01
东京上野 旧东京音乐学校奏乐堂
张滨二胡音乐会2026东京公演
张滨演奏《赛马》
```

判定：

```text
performance_confirmed
evidence_grade = B
outcome_evidenced = NO
```

### 《广陵散》 music_id 16

来源：

```text
The Los Angeles Post
https://lapost.us/?p=84999
```

事实：

```text
2026-10-30
南加州大学课堂
马玢完整演奏《广陵散》四十五段
```

判定：

```text
performance_confirmed
evidence_grade = B
outcome_evidenced = NO
```

## 3. 本轮 ambiguous

```text
万蝶振翅：B站西班牙/英国街头视频，来源C，未核验主体
关山月：小红书北美琴社伯克利活动帖，未打开正文
卧龙吟：B站伦敦幽兰琴社雅集视频，未打开正文
```

均进入人工复核，不升级为 performance_confirmed。

## 4. 本轮无结果

```text
不染、初见、半山听雨、平沙落雁、梅花三弄
以及其他未命名结果，共12首
```

其中《平沙落雁》《梅花三弄》已有 CASE008 节目单关联，本轮没有新增外部证据，不重复计算。

## 5. batch_01 合并

```text
曲目：25
已检索：25
覆盖率：100%
打开网页：3
证据：3
performance_confirmed：3（一生所爱、赛马、广陵散）
program_listed：0（本轮新增）
outcome_evidenced：0
ambiguous：6
no_relevant_result：16
候选关联：0
证据等级：A1 / B2 / C6 / D0
```

## 6. 数据安全

```text
active_version = v1.6
v1.6 哈希未变化
manifest 未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 7. 输出

- `batch_01_search_results_batch5.csv`
- `batch_01_source_evidence_batch5.csv`
- `batch_01_search_coverage_batch5.csv`
- `batch_01_manual_review_batch5.csv`
- `batch_01_search_results_all.csv`
- `batch_01_search_coverage_all.csv`

## 8. 结论

```text
PASS（batch_01 25/25 检索完成）
```

这不是 302 首完成；下一步应从 batch_02 开始，仍需人工复核 3 条 ambiguous 和 3 条 performance 证据。  
不启动 batch_02，不启动 P18，不修改 v1.6。
