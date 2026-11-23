# P17-E 第八批：batch_01 六条歧义证据专项补证计划

> 状态：计划 / 未启动  
> 当前结论：CONDITIONAL_PASS  
> batch_01_sealed=false  
> batch_02_started=false  
> P18_started=false

## 1. 当前冻结状态

```text
active_version = v1.6
batch_01：25/25 已完成状态分类
performance_confirmed：3
ambiguous_match：6
rejected_match：1
no_relevant_result：15
not_searched：0
outcome_evidenced：0
```

三条演出确认：

```text
3  一生所爱
13 赛马
24 广陵散
```

均保留原来源、等级、历史核验记录；当前原始页面重访失败，不反向否定历史正文。

## 2. 本批范围

只处理 6 条 ambiguous：

| song_id | 曲目 | 当前问题 |
|---:|---|---|
| 1 | 三寸天堂 | 台湾胡琴学院页面，未确认海外活动 |
| 5 | 倩女幽魂 | 只有微信视频线索，无原始活动页 |
| 12 | 葬花吟 | 小红书页面 404 |
| 17 | 万蝶振翅 | B站验证码，无法核对视频正文 |
| 19 | 关山月 | 小红书 404 |
| 22 | 卧龙吟 | B站验证码 |

不处理 3 条 performance_confirmed 的评级变更；可单独补独立来源，但不得自行升级/降级。

## 3. 每条优先找什么

### 1 三寸天堂

- 胡琴学院原始页面；
- 活动时间、地点、主办方；
- 是否为台湾/海外公开演出；
- 演奏者与曲目版本。

### 5 倩女幽魂

- 微信视频原始账号、发布时间；
- 活动主办方/场地；
- 是否能确认海外活动，而非国内翻奏。

### 12 葬花吟

- 牛津活动的主办方/学院/音乐人类学项目页；
- 演出者、日期、曲目版本；
- 小红书 404 不能证明活动不存在。

### 17 万蝶振翅

- 西班牙/英国街头活动的主办方或演奏者原始发布；
- 视频正文/账号；
- 是否存在官方活动记录。

### 19 关山月

- 北美琴社/伯克利活动原始页；
- 演出日期、演奏者、节目单；
- 社交帖不能单独作为演出确认。

### 22 卧龙吟

- 伦敦幽兰琴社活动原始记录；
- 雅集日期、演奏者、曲目；
- B站验证码不能替代正文。

## 4. 结论规则

- 找到官方原始记录，且能确认目标曲目 + 海外活动 + 实际演出：可建议 `performance_confirmed`；
- 只有节目单：`program_listed`；
- 只有社交视频/标题/404：保持 `ambiguous_match`；
- 能确认是错误曲目/版本：`rejected_match`；
- 仍未检索：`not_searched`；
- 不能因 404 直接判不存在。

## 5. 输出

```text
research/candidates/p17e/03_song_external_search/
├── batch_01_ambiguous_supplement_batch8.csv
├── batch_01_ambiguous_evidence_batch8.csv
├── batch_01_ambiguous_coverage_batch8.csv
└── batch_01_ambiguous_manual_review_batch8.csv
```

报告：

```text
research/candidates/p17e/reports/p17e_batch8_ambiguous_supplement_report.md
```

## 6. 数据安全

- 不修改 active_version；
- 不修改 v1.6 JSON/manifest；
- 不修改 40 案例、302 曲目、400 指标；
- 不写 SQL Server/Neo4j；
- 不建立正式关联；
- 不启动 batch_02/P18。

## 7. 停止条件

完成 6 条补证后停止，等待人工验收。  
不自动将任何候选结论写入正式数据。
