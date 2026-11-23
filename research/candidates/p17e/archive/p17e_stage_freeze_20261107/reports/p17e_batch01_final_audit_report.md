# P17-E batch_01 最终复核报告

> 复核日期：2026-11-05  
> 状态：**SEAL WITHHELD / CONDITIONAL_PASS**  
> active_version：v1.6

## 1. 结论先行

现有汇总声称 batch_01 为 25/25，但逐曲原始记录复核后：

```text
曲目：25
实际检索：21
未检索：4
覆盖率：21/25 = 84%
```

因此**不能标记 PASS（batch_01 FINAL SEALED）**，只能标记：

```text
CONDITIONAL_PASS
```

## 2. 数据不一致

发现的原始记录问题：

1. `batch_01_search_results_all.csv` 中 ID 9–12 仍为 `not_searched`；
2. `batch_01_source_evidence` 曾把《广陵散》写成 `music_id=16`，实际正式 ID 为 **24**；
3. 第五批报告将 17 首写成 17/17，但逐曲表实际只有 13 首有状态；
4. 覆盖表写成 25/25，与逐曲表冲突。

本次以逐曲记录为准，生成：

- `batch_01_search_results_audited.csv`
- `batch_01_source_evidence_audited.csv`

不覆盖旧文件。

## 3. 25 首最终状态

```text
performance_confirmed：3
ambiguous_match：6
no_relevant_result_after_search：12
not_searched：4
```

### 3 条演出确认

| music_id | 曲目 | 来源 | 等级 | 当前重访 |
|---:|---|---|---|---|
| 3 | 一生所爱 | 泰国格乐大学 | A | HTTP 502 |
| 13 | 赛马 | 大富频道 | B | SSL 中断 |
| 24 | 广陵散 | The Los Angeles Post | B | SSL 中断 |

三条均在之前实际打开并核验过正文；当前重访失败不反向否定原记录。  
三条都是单来源，`outcome_evidenced=0`。

### 6 条 ambiguous

```text
music_id 1：三寸天堂
music_id 5：倩女幽魂
music_id 8：江南
music_id 17：万蝶振翅
music_id 19：关山月
music_id 22：卧龙吟
```

这些只有视频/社交帖/区域报道线索，未完成主体或活动核验，保持 `ambiguous_match`。

### 4 条未检索

```text
music_id 9：牵丝戏
music_id 10：神经病之歌
music_id 11：花田错
music_id 12：葬花吟
```

保持 `not_searched`，不得写成无结果。

### 12 条无相关结果

```text
2、4、6、7、14、15、16、18、20、21、23、25
```

包括《二泉映月》《梁祝》《平沙落雁》《梅花三弄》等；  
没有找到本轮新增海外活动，不等于从未海外传播。  
《平沙落雁》《梅花三弄》已有 CASE008 关联，未重复计入新增证据。

## 4. 三条证据复核

### 一生所爱

- 页面：格乐大学2022元宵晚会节目展播；
- 事实：学生安贝二胡独奏《一生所爱》；
- 日期：只写“2022年元宵节”，未擅自补公历日；
- 等级 A：学校官方宣传页；
- 局限：单来源、现代曲目、无结果证据。

### 赛马

- 页面：张滨二胡音乐会2026东京公演举行；
- 事实：2026-11-01 东京上野旧东京音乐学校奏乐堂，张滨演奏《赛马》；
- 等级 B：媒体演出后报道；
- 局限：单一媒体、无受众结果。

### 广陵散

- 页面：《广陵散》全本奏响南加州大学；
- 事实：2026-10-30 USC 课堂，马玢完整演奏四十五段；
- 等级 B：媒体专题报道；
- 限制：课堂场景，不能等同于长期教学项目；不推断学生数量/反馈。

## 5. 来源独立性

```text
3 条证据均为单来源
A1 / B2
没有独立第二来源
没有 outcome 证据
```

## 6. 统计一致性

逐曲表重算：

```text
25 = 3 + 6 + 12 + 4
```

旧汇总 25/25 与逐曲表冲突，已记录为审计问题；本次不修改旧汇总，仅以 audited 文件为准。

## 7. 数据安全

```text
active_version = v1.6
manifest sha256 = ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a
v1.6 文件哈希未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 8. 封存意见

```text
SEAL WITHHELD
```

原因：

- 4 首未检索；
- 6 首 ambiguous 未人工确认；
- 3 条证据当前页面重访失败（历史正文已核验）；
- 旧汇总存在 ID/覆盖率冲突。

不启动 batch_02，不启动 P18。
