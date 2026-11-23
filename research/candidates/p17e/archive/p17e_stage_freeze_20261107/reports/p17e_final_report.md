# P17-E 第一批最终报告

> 状态：第一批完成；P17-E 整体未完成  
> 结论：**CONDITIONAL_PASS（batch 1）**  
> active_version：v1.6，未修改

## 1. 本批结果

```text
40 个案例首要来源检查：40
HTTP 200：20
HTTP 202：1
请求失败：19
内容逐页确认：1（CASE008）
CASE008 五首曲目：5/5 检查
performance_confirmed：2（梅花三弄、流水）
program_listed：3（平沙落雁、酒狂、阳关三叠）
outcome_evidenced：0
302 首外部检索：未开始
严格个人新候选：0
```

## 2. 失败原因

```text
SSL/TLS 中断：12
HTTP 502：5
HTTP 403：2
HTTP 202：1
```

详见 `p17e_source_failure_analysis.md`。

这些是访问/网关/反爬问题，不等于来源不存在，也不等于案例不真实。

## 3. CASE008

来源 C008-S001 原文确认：

- 2025-07-12 伦敦大学亚非学院活动；
- 演出后报道；
- 《梅花三弄》《流水》明确出现；
- 另外三首未在文中点名。

因此只把两首升级为 `performance_confirmed`；三首仍保持 `program_listed`。  
没有 `outcome_evidenced`。

## 4. 40 案例

```text
verified_event_content：1
needs_more_evidence：20
source_unavailable：19
conflicting_evidence：0
```

不能把 20 个“URL 可访问”写成“内容已核实”。

## 5. 数据安全

```text
v1.6 文件哈希：未变化
manifest 哈希：未变化
active_version：v1.6
40 案例：未修改
302 曲目：未修改
400 指标记录：未修改
SQL Server / Neo4j：未写入
```

## 6. 输出

```text
research/candidates/p17e/
├── manifest.json
├── README.md
├── 01_song_evidence/
├── 02_case_reverification/
├── 03_strict_performer_candidates/
├── 04_case008_performance/
├── 05_manual_review/
└── reports/
```

## 7. 未完成

- 20 个可访问来源的内容核验；
- 19 个失败来源的人工重试；
- 3 首 CASE008 曲目演出后证据；
- 302 首外部检索；
- 严格个人候选外部检索；
- 人工审核。

## 8. 下一批建议

1. 人工浏览器复核 40 个来源；
2. 用官方档案/存档替代 502/403；
3. 为 3 首缺失曲目逐首找演出后证据；
4. 启动 302 首外部检索，分批记录；
5. 再启动严格个人候选检索。

## 9. 结论

```text
CONDITIONAL_PASS（仅第一批）
```

P17-E 整体不能标记为完成，P18 未启动，正式数据未修改。
