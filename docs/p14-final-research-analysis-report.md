# P14 最终研究分析报告

> 基线：v1.6（40 案例、62 来源关系、400 指标记录、94 有效评分、306 null）  
> 分析类型：描述性统计，不做因果推断。

## 1. 最终结论

```text
CONDITIONAL_PASS
```

P14 要求的统计已完成、可复算，正式数据未变化；  
但部分维度受样本量和字段限制，不能支持稳定比较或因果结论。

## 2. 主要描述性发现

### 案例结构

```text
国家：12
北美：20/40 = 50%
美国：16/40 = 40%
东南亚：0
其他/区域外：6
```

- 北美集中度高；
- 东南亚仍为空白；
- 中东、拉美各 2 例，不能代表区域。

### 乐器

```text
古筝：13 例
二胡：10 例
琵琶：6 例
古琴：3 例
笛：2 例
箫/扬琴/唢呐/中阮：各 1 例
未具体列明/合奏：22 例
```

- 11 个多乐器案例；
- 29 个单乐器/单一类别案例；
- 22 例无法具体到单一乐器。

### 案例类型

```text
overseas_institution_education：16
foreign_individual_cross_cultural：9
overseas_institution_ensemble：8
cross_cultural_ensemble：7
```

### 样本结构

```text
strict_individual：2（14 有效 / 6 null）
extended_cross_cultural：36（63 有效 / 297 null）
pending_review：2（17 有效 / 3 null）
```

### 指标

```text
有效评分：94/400 = 23.5%
null：306
0 分：0
```

有效率较高的指标：

```text
故事可解释性 14/40
跨文化改编 14/40
时代主题关联 14/40
```

有效率最低：

```text
情感共通性 3/40
音色辨识度 3/40
受众参与度 4/40
```

这些是覆盖差异，不是效果排名。

## 3. 证据质量

```text
来源数 1：24 案例
来源数 2：11 案例
来源数 3：4 案例
来源数 4：1 案例
全部 B 级
同机构重复风险：6 案例
```

62 条来源关系不等于 62 个独立来源；  
24 个案例只有单一来源；  
CASE039/CASE040 各有两条来源但同属 Xinhua，不构成独立双来源。

## 4. 关联分析

- 只做了分组描述；
- 未计算相关系数；
- 国家/乐器多数组 n 很小；
- 案例类型差异只能描述，不能解释为因果；
- 样本类型混合，不能直接比较。

## 5. 必须保留的限制

1. 严格个人样本只有 2 例；
2. 扩展跨文化样本不能替代严格个人样本；
3. 306 条 null 不是 0 分；
4. `activity_status` 缺失，公告/节目单/完成/结果无法自动区分；
5. 62 条来源关系不等于 62 个独立来源；
6. 活动举办或节目单不能证明传播效果；
7. 评论来源国家不能推断目标国受众偏好；
8. 当前分析是描述性统计，不是因果研究。

## 6. 图表

- [国家分布](<research/analysis/p14/charts/country_distribution.svg>)
- [地区分布](<research/analysis/p14/charts/region_distribution.svg>)
- [乐器分布](<research/analysis/p14/charts/instrument_distribution.svg>)
- [指标有效率](<research/analysis/p14/charts/indicator_valid_rate.svg>)
- [指标评分分布](<research/analysis/p14/charts/indicator_score_distribution.svg>)
- [样本构成](<research/analysis/p14/charts/sample_composition.svg>)
- [证据等级](<research/analysis/p14/charts/evidence_grade_distribution.svg>)

## 7. 输出

文档：

- `docs/p14-data-integrity-audit.md`
- `docs/p14-case-distribution-analysis.md`
- `docs/p14-indicator-statistics-report.md`
- `docs/p14-sample-stratification-report.md`
- `docs/p14-evidence-quality-report.md`
- `docs/p14-association-analysis.md`

数据：

- `research/analysis/p14/case_distribution.csv`
- `research/analysis/p14/country_distribution.csv`
- `research/analysis/p14/region_distribution.csv`
- `research/analysis/p14/instrument_distribution.csv`
- `research/analysis/p14/indicator_statistics.csv`
- `research/analysis/p14/indicator_score_distribution.csv`
- `research/analysis/p14/sample_stratification.csv`
- `research/analysis/p14/evidence_quality.csv`
- `research/analysis/p14/association_statistics.csv`

## 8. 正式状态

```text
active_version = v1.6
v1.6 数据未修改
v1.5 历史数据未修改
SQL Server / Neo4j 未写入
```

P14 到此停止，不自动进入 P15。
