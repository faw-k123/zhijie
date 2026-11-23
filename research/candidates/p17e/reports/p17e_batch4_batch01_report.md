# P17-E 第四批 batch_01 报告

> 范围：batch_01 前 25 首  
> 实际完成：8/25  
> 未检索：17/25  
> 结论：**CONDITIONAL_PASS**

## 1. 检索覆盖

```text
batch_01 曲目：25
已实际检索：8
未检索：17
检索覆盖率：8/25 = 32%
打开原始网页：1
新增证据：1
新增候选关联：0
```

## 2. 有效证据

### 《一生所爱（Cover 卢冠廷）》

来源：

```text
泰国格乐大学官网
http://krirkcn.com/home/single?id=74730868531278
```

页面事实：

```text
2022年元宵晚会
格乐大学学生安贝
二胡独奏《一生所爱》
```

判定：

```text
activity_status = performance_confirmed
evidence_grade = A
outcome_evidenced = NO
```

限制：

- 学校宣传页；
- 单来源；
- 公历日期未写；
- 无受众反馈/持续传播；
- 未关联任何正式案例。

## 3. 其余检索

```text
ambiguous_match：3
no_relevant_result_after_search：4
not_searched：17
```

- 三寸天堂：台湾胡琴学院页面，非海外活动；
- 倩女幽魂、江南：只有视频/加拿大江南音韵报道，未确认具体曲目；
- 二泉映月、琴师、战马奔腾、梁祝：未找到与目标曲目直接相关的海外活动。

## 4. 未检索 17 首

包括：

```text
牵丝戏、神经病之歌、花田错、葬花吟、赛马、
迴梦游仙、穿越时空的思念、飞雪玉花、万蝶振翅、
不染、关山月、初见、半山听雨、卧龙吟、
平沙落雁、广陵散、梅花三弄
```

这些都标记 `not_searched`，不是无结果。

> 平沙落雁、梅花三弄已有 CASE008 节目单关联；本轮没有重新执行其外部检索。

## 5. 数据安全

```text
active_version = v1.6
v1.6 文件哈希未变化
manifest 未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 6. 输出

- `batch_01_search_results.csv`（25行）
- `batch_01_source_evidence.csv`（1条）
- `batch_01_mapping_candidates.csv`（0条）
- `batch_01_search_coverage.csv`
- `batch_01_manual_review.csv`（4条）

## 7. 结论

```text
CONDITIONAL_PASS
```

只完成 8/25 的真实检索，不能声称 batch_01 或 302 首已完成。  
下一批应先补齐 batch_01 剩余 17 首，再讨论 batch_02；不启动 P18，不修改 v1.6。
