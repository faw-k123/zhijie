# v1.1 案例口径复核与双样本体系

> 日期：2026-10-30
> 状态：v1.1 reviewed / active（2026-10-30 激活）
> 范围：只整理案例口径与样本筛选；不新增案例、不改评分和来源、不改统计门禁

---

## 1. 三层结构

```text
主研究库：海外中国传统音乐跨文化传播案例（v1.1 共 10 例）
├─ 严格海外个人演奏样本 strict_individual
├─ 扩展跨文化传播样本 extended_cross_cultural
└─ 待核实 pending_review
```

主研究库保留广义案例；两个分析样本互斥；严格样本不能靠 `performer_type` 自动认定。

---

## 1.1 “外国个人”的操作性定义

本项目采用以下定义，避免把姓名、外貌、族裔或文化背景当作身份证据：

> 外国个人，是指能够通过公开资料核实其国籍，或符合项目预先规定的非中国籍身份标准的个人演奏者。

必须区分四个变量，不能互相替代：

- 国籍：公开资料支持的法律国籍/国民身份；
- 常驻地：长期生活或工作的国家/城市；
- 学习经历：在何地、向谁学习；
- 演出所在地：实际发生演奏/传播活动的地点。

判断严格样本时，以“身份 + 演奏 + 海外活动 + 来源”四项证据为准，不能用“常驻中国”或“曾在中国演出”反推国籍，也不能用“姓名/族裔”推断外国人身份。

## 1.2 负责人批准状态

CASE005/006/007 已完成负责人逐例审批：

```text
CASE005 = approved
CASE006 = approved
CASE007 = needs_more_evidence
```

其余案例为 `not_required`。因此 P5 严格样本会显示：

```text
候选 3 · 已批准 2 · 待审批 0 · 需补证 1 · 不批准 0
```

CASE007 已完成本轮审批，但研究状态是 `needs_more_evidence`，不得误标为 `approved`。

## 2. 7 例复核表

| 案例 | case_type | analysis_sample | 身份核验 | 演奏地点 | 海外活动 | strict_eligible | 理由 |
|---|---|---|---|---|---|---|---|
| CASE004 Moyer | foreign_individual_cross_cultural | extended_cross_cultural | verified | mixed | 是 | false | 加拿大个人，但活动含台湾学习与上海长期活动，不能确认纯海外演奏 |
| CASE005 Cooper | foreign_individual_cross_cultural | **strict_individual** | verified | overseas | 是 | **true** | 澳大利亚个人；柏林基地；16国演出；官方简介可核验 |
| CASE006 Barton | foreign_individual_cross_cultural | **strict_individual** | verified | overseas | 是 | **true** | 美国个人；Anderson Center 驻留与美国公开演出；多来源 |
| CASE007 Huehns | foreign_individual_cross_cultural | **strict_individual** | verified | overseas | 是 | **true** | 英国个人；西安学习、英国高校/BBC 演出与教学 |
| CASE008 幽兰琴社 | overseas_institution_education | extended_cross_cultural | partially_verified | overseas | 是 | false | 机构/教育传播；2025雅集不是外国人专场 |
| CASE009 巴德中西乐团 | cross_cultural_ensemble | extended_cross_cultural | partially_verified | overseas | 是 | false | 中西混合团体；中国乐器演奏者国籍未逐人核实 |
| CASE010 Djang San | foreign_individual_cross_cultural | extended_cross_cultural | verified | mainland_china | 否 | false | 法国个人，但已核实活动主要在中国境内 |

“严格样本候选”不等于正式批准；CASE005/006 已完成审批，CASE007 仍为 `needs_more_evidence`，不能写成“已批准”。

命名说明：数据字段 `analysis_sample=strict_individual` 表示“严格样本候选类别”；API 查询参数 `strict_candidate` 取全部候选，`strict_individual` 只取 `owner_approval_status=approved` 的正式案例。当前正式严格样本为 CASE005、CASE006 两例。

---

## 3. 原有 3 例的处理

| 案例 | analysis_sample | 理由 |
|---|---|---|
| CASE001 Eliott Tordo | `pending_review` | 法国身份与二胡活动有来源；海外现场地点未逐场核验，不能自动进入 strict |
| CASE002 Bard Chinese Ensemble | `extended_cross_cultural` | 美国高校乐团，机构传播；成员国籍未逐人核实 |
| CASE003 2026二胡群英会 | `extended_cross_cultural` | 日本五人组合，团体传播，不是单个外国个人 |

CASE001 不会因为此前是 B 级就自动进入严格样本。

---

## 4. 样本清单

### 4.1 严格样本候选

```text
CASE005 Clare Cooper
CASE006 Jarrelle Barton
CASE007 Colin Huehns
```

共 3 例候选；候选有效评分 21 条；负责人已批准 **2/3**（CASE005/006）。CASE007 为 `needs_more_evidence`，不进入正式严格样本。

正式 `strict_individual` 为 **2 例**、有效评分 **14 条**，因为只有 `approved` 才能计入。

### 4.2 扩展样本

```text
CASE002 巴德中国民乐室内乐
CASE003 2026二胡群英会
CASE004 Jeremy Moyer
CASE008 伦敦幽兰琴社
CASE009 巴德中西乐团
CASE010 Djang San
```

共 6 例；有效评分 42 条。

### 4.3 待核实

```text
CASE001 Eliott Tordo
```

共 1 例；有效评分 10 条。

### 4.4 全部

10 例；有效评分 73 条。

---

## 5. 样本筛选 API

以下接口支持 `analysis_sample`：

```text
GET /api/research/cases/?analysis_sample=...
GET /api/research/statistics/?analysis_sample=...
GET /api/research/success-factors/?analysis_sample=...
```

取值：

- `all`
- `strict_candidate`（候选，3 例）
- `strict_individual`（仅 approved，当前 2 例）
- `extended_cross_cultural`
- `pending_review`

响应统一带：

```json
{
  "analysis_scope": {
    "key": "strict_individual",
    "label": "严格海外个人演奏样本",
    "case_count": 3,
    "scored_case_count": 3,
    "valid_score_count": 21,
    "thresholds": { "exploratory": 5, "descriptive": 20 }
  }
}
```

统计口径：

- `n` / `valid_count`：独立案例数，不按来源数或证据片段数放大；
- `missing_count`：当前样本案例数 − 有效评分数；
- `coverage_rate`：有效评分数 / 当前样本案例数。

P5 页面已增加“分析样本”选择器；切换后重新加载案例、统计、成功因素和矩阵。

---

## 6. 测试

```text
Found 25 test(s)
Ran 25 tests
OK
```

覆盖：

1. 机构案例不进入 strict；
2. 团体案例不进入 strict；
3. 中国境内活动不进入 strict；
4. 关键证据不足 → pending_review；
5. 扩展样本保留不符合 strict 的案例；
6. 筛选不改变原始评分和来源；
7. 指标级门禁继续有效；
8. 无效 `analysis_sample` 返回 400。

v1.1 激活校验：

```text
OK active_version=v1.1 status=reviewed cases=10 scores=100 warnings=0
```

v1.1 现为 active / reviewed；v1.0 保留为历史版本。

---

## 6.1 区域矩阵与样本范围

`regional-matrix` 是独立的区域研究框架，不依赖案例样本；它不随 `analysis_sample` 切换。

API 返回：

```json
{
  "independent_of_case_sample": true,
  "scope_note": "区域矩阵是独立的研究框架，不随案例样本筛选变化；当前 rows=0。"
}
```

P5 区域传播适配页已明确显示这条说明。因此：

- 案例统计切到严格样本 3 例时，区域矩阵仍展示 6 个研究区域；
- 这不是“统计口径不一致”，而是两个独立研究对象；
- 若未来区域矩阵改为依赖案例样本，必须同步增加 `analysis_sample` 筛选，不能默认沿用全部案例。

## 7. 当前结论

- 双样本体系已建立；
- 严格样本 3 例，扩展样本 6 例，待核实 1 例；
- 不新增案例；
- 不修改原始证据、评分、来源；
- 已由负责人确认激活 v1.1；
- v1.1 已完成逐例审批，并于 2026-10-30 激活；v1.0 保留为历史版本。

严格样本候选有 3 例，正式批准的 `strict_individual` 为 2 例；正式样本仍少于 5 例，因此 P5 显示“证据不足”，不会生成排行榜。CASE007 保留候选并显示“需要补充证据”，不得当作正式样本。
