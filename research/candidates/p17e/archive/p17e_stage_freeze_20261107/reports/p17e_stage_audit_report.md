# P17-E 阶段性结项审计报告

> 日期：2026-11-07  
> 结论：**P17E_STAGE_AUDIT = CONDITIONAL_PASS**  
> batch_01_sealed = false  
> batch_02_started = false  
> P18_started = false

## 1. 阶段范围

本审计覆盖 P17-E 第一批至第八批已有候选记录：

- batch_01 曲目 25 首；
- 40 个正式案例的首要来源复核；
- 6 条 ambiguous 补证；
- 3 条 performance_confirmed；
- 来源质量、人工复核、数据保护。

本审计不开展新检索。

## 2. 真实执行量

### 曲目层

```text
batch_01 曲目：25
实际检索：25
未检索：0
原始网页打开：4
正文核验：4
有效演出证据：3
performance_confirmed：3
ambiguous_match：6
rejected_match：1
no_relevant_result：15
outcome_evidenced：0
candidate_links：0
```

打开并核验正文的 4 个页面：

```text
song_id 3  一生所爱
song_id 13 赛马
song_id 24 广陵散
song_id 8  江南（核验后拒绝匹配）
```

### 案例层

```text
40 个案例首要来源检查：40
HTTP 200：20
HTTP 202：1
请求失败：19
重试恢复：7
仍不可访问：12
内容逐页确认：1（CASE008）
needs_more_evidence：19
source_unavailable：12
```

案例层结果不能与曲目层混算。

## 3. batch_01 最终状态

| 状态 | 数量 |
|---|---:|
| performance_confirmed | 3 |
| ambiguous_match | 6 |
| rejected_match | 1 |
| no_relevant_result_after_search | 15 |
| not_searched | 0 |
| 合计 | 25 |

### 3 条演出确认

```text
3  一生所爱  A  泰国格乐大学
13 赛马      B  大富频道
24 广陵散    B  The Los Angeles Post
```

三条均为单来源；无独立第二来源；`outcome_evidenced=0`。

### 6 条 ambiguous

```text
1  三寸天堂
5  倩女幽魂
12 葬花吟
17 万蝶振翅
19 关山月
22 卧龙吟
```

均保持歧义，未强行升级。

### 1 条 rejected

```text
8 江南
```

加拿大报道为无锡民族乐团曲目，不含歌曲《江南》。

### 15 条无相关结果

保持 `no_relevant_result_after_search`，不解释为从未海外传播。

## 4. 三条演出确认审计

### 一生所爱

- 来源：泰国格乐大学官方页面；
- 活动：2022 元宵晚会；
- 演奏者：安贝；
- 曲目：二胡独奏《一生所爱》；
- 等级：A；
- 历史正文：已核验；
- 当前重访：HTTP 502；
- 独立第二来源：无；
- 结论：保留 `performance_confirmed`，单来源限制。

### 赛马

- 来源：大富频道；
- 活动：2026-11-01 东京上野旧东京音乐学校奏乐堂；
- 演奏者：张滨；
- 曲目：《赛马》；
- 等级：B；
- 当前重访：SSL 中断；
- 独立第二来源：无；
- 结论：保留 `performance_confirmed`，媒体单来源限制。

### 广陵散

- 来源：The Los Angeles Post；
- 活动：2026-10-30 USC 课堂；
- 演奏者：马玢；
- 曲目：完整《广陵散》四十五段；
- 等级：B；
- 当前重访：SSL 中断；
- 独立第二来源：无；
- 结论：保留 `performance_confirmed`，课堂场景限制。

## 5. 六条 ambiguous 补证

八批检索后仍无法解决：

| song_id | 曲目 | 失败原因 | 还需要 |
|---:|---|---|---|
| 1 | 三寸天堂 | 胡琴学院页面抓取失败 | 原始活动页/海外演出证据 |
| 5 | 倩女幽魂 | 无原始 URL/正文 | 视频原始发布者/活动页 |
| 12 | 葬花吟 | 小红书 404 | 牛津活动主办方/节目单 |
| 17 | 万蝶振翅 | B站/古筝网验证码 | 原始视频/活动组织者 |
| 19 | 关山月 | 小红书 404/微信验证 | 北美琴社原始活动页 |
| 22 | 卧龙吟 | B站验证码 | 幽兰琴社原始记录 |

404、验证码、抓取失败都不等于活动不存在，也不等于实际演出。

## 6. 来源质量与独立性

10 条曲目相关来源记录：

```text
来源域名：7（含一个无 URL 记录）
原始页面打开：4
正文核验：4
A：1
B：2
C：6
D：1（拒绝匹配的目标证据）
独立第二来源验证：0
同稿转载/同源：1 组（CASE008 旧关联，非本批新增）
```

40 个案例来源中：

```text
HTTP 200：20
202：1
失败：19
失败类型：SSL 12、502 5、403 2
```

不能把 URL 数量当独立来源数量。

## 7. 未解决事项

- 6 条 ambiguous 未解决；
- 3 条演出确认均为单来源；
- 3 个 confirmed 原始页面当前不可重访；
- `outcome_evidenced=0`；
- 40 案例中 19 个仍需人工内容核验；
- 12 个案例来源仍不可访问；
- batch_01 未封存。

## 8. 数据保护

```text
active_version = v1.6
manifest sha256 = ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a
v1.6 五个文件哈希未变化
40 案例、302 曲目、400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 9. 阶段结论

```text
CONDITIONAL_PASS
```

阶段审计完成，证据和统计可追溯；  
但不足以封存 batch_01，也不足以进入 batch_02 或 P18。

## 10. 输出

- `p17e_all_batches_execution_audit.csv`
- `p17e_source_quality_audit.csv`
- `p17e_confirmed_performance_review.csv`
- `p17e_ambiguous_cases_review.csv`
- `p17e_data_protection_audit.md`
- `p17e_stage_decision.md`
