# v1.1 海外案例扩充报告（第一批 7 例）

> 项目：智解国音 · 国际传播研究数据建设
> 批次：第一批案例扩充
> 日期：2026-10-30
> 数据版本：`v1.1`（reviewed / active）
> 当前 active_version：`v1.1`（reviewed）
> 范围：只做研究数据；不改数据库、migration、API、前端页面

---

## 1. 交付摘要

| 项目 | v1.0 | v1.1 |
|---|---:|---:|
| 正式案例 | 3 | 10 |
| 新增案例 | — | 7 |
| 来源 | 7 | 23 |
| 指标记录 | 30 | 100 |
| 新增指标记录 | — | 70 |
| 已知评分 | 26 | 73 |
| 未知评分 | 4 | 27 |
| 数据警告 | 0 | 0 |
| 版本状态 | reviewed / 历史 | reviewed / active |

新增案例：

- CASE004 Jeremy Moyer（加拿大，二胡/秦琴）
- CASE005 Clare Cooper（澳大利亚，古筝）
- CASE006 Jarrelle Barton（美国，古筝）
- CASE007 Colin Huehns（英国，二胡）
- CASE008 伦敦幽兰琴社（英国，古琴教育）
- CASE009 巴德中西乐团（美国，中西混合编制）
- CASE010 Djang San（法国，中阮/琵琶）

---

## 2. 这 7 例的真实性边界

案例口径与双样本明细见：[case-scope-review-v1.1.md](<case-scope-review-v1.1.md>)。

这 7 例不是“7 个完美外国个人演出案例”。必须按以下口径使用：

| 案例 | 可确认 | 不能宣称 |
|---|---|---|
| CASE004 Moyer | 加拿大音乐人；台湾学二胡；2004移居上海；民间采风；个人专辑 | 不能宣称其海外受众规模或演出效果 |
| CASE005 Cooper | 澳大利亚出生；古筝/竖琴；柏林；16国演出；实验/即兴 | 不能当传统曲目复原案例 |
| CASE006 Barton | 美国；13岁自学；随北京老师；Anderson Center 驻留；双城演出 | 评论原文、上座率、曲目单未知 |
| CASE007 Huehns | 英国；西安音乐学院三年；二胡十级；英国高校/BBC；RAM 任教 | 主要依据个人官网，独立报道不足 |
| CASE008 幽兰琴社 | 英国琴社；22年；150+雅集；21年夏校；20多国600+学员 | 2025雅集不是“外国人专场”；演奏者含多国 |
| CASE009 巴德中西乐团 | 美国高校乐团；2025-05-03 中西混合编制；世界首演 | 中国乐器演奏者国籍未逐人核实 |
| CASE010 Djang San | 法国；2000来华；中阮/琵琶；电子化；乐队 | 活动主要在中国，不是海外受众案例 |

因此：

- 正式案例数达到 10，但其中 2 例是**机构/教育传播**，1 例是**外国人在中国的跨文化创作**；
- 如果研究口径必须是“外国人在海外演出”，CASE008/009/010 需要降级或替换；
- 这些边界写在 `research_notes` 中，没有隐藏。

---

## 3. 案例字段与来源

每个新增案例均包含：

- 唯一 `case_id`：CASE004—CASE010；
- 身份、国家/地区、乐器、作品、活动、渠道、受众；
- 学习动机、改编方式、时代主题、宗教文化说明；
- 受众反馈（无则“未采集（未知）”）；
- 成功证据（至少 1 项可核验结果）；
- 研究限制；
- 2—3 条来源，含 URL、发布者、类型、可靠性、访问日期。

完整来源索引：

[source-index-v1.1.md](<source-index-v1.1.md>)

### 3.1 来源数量

| 案例 | 来源数 |
|---|---:|
| CASE004 | 3 |
| CASE005 | 2 |
| CASE006 | 3 |
| CASE007 | 2 |
| CASE008 | 2 |
| CASE009 | 2 |
| CASE010 | 2 |

新增 16 条来源，总来源 23 条。

---

## 4. 10 项指标编码

### 4.1 编码原则

- 0—3 分，未知为 `null`；
- 已知评分必须有 `source_ids` 和 evidence；
- 未知评分必须有 `missing_reason`；
- 不把“没有证据”写成 0 分；
- 7 个新案例每例 10 条记录，共 70 条；
- 编码者为“研究助手（初编）”，待项目负责人复核。

### 4.2 每例覆盖

| 案例 | 有评分 | 缺失 | 均分 | low_coverage |
|---|---:|---:|---:|---|
| CASE004 | 6 | 4 | 2.17 | false |
| CASE005 | 6 | 4 | 2.00 | false |
| CASE006 | 8 | 2 | 2.00 | false |
| CASE007 | 7 | 3 | 2.71 | false |
| CASE008 | 7 | 3 | 2.71 | false |
| CASE009 | 7 | 3 | 2.71 | false |
| CASE010 | 6 | 4 | 2.33 | false |

新增 70 条中：

```text
score null = 23
score 3 = 22
score 2 = 21
score 1 = 4
```

缺失集中在：

- 情感共通性：0/7 有评分（没有受众原话）
- 音色辨识度：1/7 有评分（仅 Barton 自述）
- 受众参与度：1/7 有评分（仅 Barton 视频观看规模）
- 教育支持：3/7 有评分（Huehns、幽兰、巴德）

完整逐条编码表：

[case-coding-v1.1.csv](<case-coding-v1.1.csv>)

字段：

```text
case_id, performer, indicator_id, indicator_label,
score, evidence, source_ids, missing_reason, coder, coded_at
```

---

## 5. 版本与校验

### 5.1 文件

```text
research/data/v1.1/
├── cases.json              10 案例
├── success_factors.json    100 条指标记录
├── music_scores.json       pending / 0 items
└── regional_strategies.json pending / rows=[]
```

### 5.2 manifest

- `v1.0`：reviewed / active；
- `v1.1`：reviewed / active；
- v1.1 四个文件已写入 SHA256 与 bytes；
- 不覆盖 v1.0；
- 当前 API 仍读取 v1.0，页面不会自动变成 10 例。

### 5.3 激活校验结果

2026-10-30 负责人确认激活 v1.1：

```text
python manage.py validate_research_data
OK active_version=v1.1 status=reviewed cases=10 scores=100 warnings=0
```

```text
python manage.py test propagation.tests
Ran 25 tests
OK
```

v1.0 保留为历史版本。

### 5.4 测试代码调整

原测试硬编码 `n=3`、`insufficient`、`v1.0`，v1.1 激活后会误报失败。只修改了测试断言：

- 样本数、状态、进度改为从 status 动态读取；
- 成功因素门禁按样本数分支；
- 破坏性测试改为操作当前 active_version，不再写死 v1.0。

**未修改业务 API、数据加载逻辑、前端页面、数据库、migration。**

---

## 6. 激活前必须处理的问题

### 6.1 指标级门禁已实现

针对 v1.1 暴露的问题，已增加指标级统计门禁：

| 单个指标 n | 状态 | 是否排序 |
|---:|---|---|
| 0 | 暂无数据 | 否 |
| 1—4 | 证据不足 | 否 |
| 5—19 | 探索性 | 否；显示 n、缺失量、均值 |
| ≥20 | 描述性 | 是 |

实测 v1.1：

```text
availability = exploratory
rankings = []
gate_counts = { insufficient: 3, exploratory: 7, descriptive: 0 }
emotional_resonance: n=1, status=insufficient, rank=null
```

因此 n=1 的指标不会再排第一。v1.1 目前仍保持 draft，原因是案例口径仍需项目负责人复核，而不是排行榜门禁未实现。

### 6.2 页面数字仍是 3/40

当前 active v1.0，所以：

- 全球传播效果仍显示 3/40；
- 案例库仍显示 3 例；
- 成功因素仍 unavailable；
- 音乐潜力仍 pending。

v1.1 通过复核并切换后，页面才会显示 10/40、10 例、指标级探索性展示（仍不会生成 n<20 的排行榜）。

### 6.3 机构/教育案例的口径

CASE008、CASE009 不是“全部由外国演奏者演出”。如果项目最终坚持“外国人演奏”口径：

- 需要把这两例移到“机构/教育传播”子库，或降级为 C；
- 不能用它们填充“外国个人演奏者”数量。

---

## 7. 去重与质量

- CASE004—CASE010 与 CASE001—CASE003 无重复 `case_id`；
- 与 CASE002 同机构的“巴德中国民乐室内乐”已排除，避免重复；
- 伦敦幽兰琴社是琴社/教育机构，不是个人；
- 所有来源 URL 为 http/https，来源 ID 唯一；
- B 级 10 例，A 级 0；没有把 B 级包装成 A 级；
- 23 条 null 全部有 `missing_reason`；
- 没有虚构演奏者、演出、来源、评分或传播效果。

---

## 8. 交付物

- [案例口径复核与双样本](<case-scope-review-v1.1.md>)
- [候选清单与审核表](<case-candidates-v1.1.md>)
- [来源索引](<source-index-v1.1.md>)
- [10 项指标逐条编码 CSV](<case-coding-v1.1.csv>)
- `research/data/v1.1/cases.json`
- `research/data/v1.1/success_factors.json`
- `research/data/v1.1/music_scores.json`
- `research/data/v1.1/regional_strategies.json`
- `research/data/manifest.json`（v1.1 draft）

---

## 9. 结论

第一批 7 例已完成数据建设：

- 正式案例 3 → 10（v1.1 draft）；
- 来源 7 → 23；
- 指标记录 30 → 100；
- 结构校验 0 警告；
- 指标级门禁已实现并验证；
- 25 个测试在 v1.0 和 v1.1 下均通过；
- 未改数据库、migration、页面；API 只新增了 `success-factors` 的指标级门禁字段。

但 v1.1 **尚未激活**。案例口径复核与负责人审批已完成：

- CASE005、CASE006：approved；
- CASE007：needs_more_evidence；
- 正式严格样本 2 例；
- 扩展样本 6 例；
- 待核实 1 例。

v1.1 已于 2026-10-30 由负责人确认激活，v1.0 保留为历史版本。激活检查见：[v1.1-final-activation-check.md](<v1.1-final-activation-check.md>)。
