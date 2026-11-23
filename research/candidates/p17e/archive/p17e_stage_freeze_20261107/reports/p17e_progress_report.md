# P17-E 第一批进度报告

> 范围：CASE008 五首曲目 + 40 个案例首要来源复核  
> 状态：第一批完成；P17-E 整体未完成  
> active_version：v1.6

## 1. 本批完成

```text
CASE008 曲目核查：5/5
40 案例首要来源请求：40/40
可访问（HTTP 200）：20
HTTP 202：1
请求失败：19
内容已逐页确认：1（CASE008）
302 首外部检索：未开始
```

## 2. CASE008 五首曲目

来源：C008-S001，欧洲时报英国版，2025-07-18。  
活动：2025-07-12，伦敦大学亚非学院，幽兰琴社22周年雅集。

| song_id | 曲目 | 状态 | 依据 |
|---:|---|---|---|
| 158 | 梅花三弄 | performance_confirmed | 原文明确《梅花三弄》 |
| 26 | 流水 | performance_confirmed | 原文明确《流水》 |
| 23 | 平沙落雁 | program_listed | 原文未点名 |
| 28 | 酒狂 | program_listed | 原文未点名 |
| 29 | 阳关三叠 | program_listed | 原文未点名 |

没有 `outcome_evidenced`。  
媒体演出后报道不等于受众接受或持续传播。

## 3. 40 案例来源复核

```text
verified_event_content：1（CASE008）
needs_more_evidence：20
source_unavailable：19
conflicting_evidence：0
```

- 20 个首要来源 HTTP 200，但除 CASE008 外内容未逐页核验；
- 19 个请求失败：SSL 12、502 5、403 2、其他 1；
- 1 个 HTTP 202，未核验；
- 不能把“URL 可访问”写成“案例已核实”。

## 4. 数据安全

- v1.6 未修改；
- active_version 仍为 v1.6；
- 候选目录独立；
- SQL Server / Neo4j 未写入。

## 5. 下一步

1. 对 20 个可访问来源逐页核验内容；
2. 对 19 个失败来源换官方域名/存档重试；
3. 补齐 3 首 CASE008 曲目演出证据；
4. 启动 302 首外部检索；
5. 再进行严格个人候选检索。

## 6. 输出

```text
research/candidates/p17e/
```

详见 `manifest.json`、`02_case_reverification/`、`04_case008_performance/`、`05_manual_review/`。
