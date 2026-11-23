# P15 最终报告：严格个人与扩展跨文化样本分层比较

> 基线：v1.6  
> 严格组 2 例，扩展组 36 例，pending 2 例不纳入两组正式比较。  
> 本报告只做描述性比较，不做显著性推断或因果解释。

## 1. 最终结论

```text
CONDITIONAL_PASS
```

分析已完成、可复算，正式数据未变化；  
但严格组只有 2 例、扩展组缺失率高、activity_status 缺失，无法支持稳定群体结论。

## 2. 两组基本结构

| 项目 | strict | extended |
|---|---:|---:|
| 案例 | 2 | 36 |
| 有效评分 | 14 | 63 |
| null | 6 | 297 |
| 有效率 | 70.0% | 17.5% |
| 平均有效/案 | 7.0 | 1.75 |
| 来源关系 | 5 | 52 |
| 单来源案例 | 0 | 24 |
| 同机构重复风险 | 1 | 5 |
| 国家 | 2 | 12 |
| 地区 | 2 | 6 |

## 3. 主要描述性发现

### 主体

- 严格组：2 个身份 verified 的海外个人演奏者，均古筝；
- 扩展组：16 个机构教育、8 个机构乐团、7 个跨文化团队、5 个个人案例；
- 扩展组内部异质，不能当作单一群体。

### 指标

严格组每项最多 2 个有效评分，不计算均值。  
扩展组有效 n 为 1–10，均值只能描述当前样本：

```text
故事 1.80（n=10）
跨文化 2.30（n=10）
教育 2.40（n=5）
桥梁 2.13（n=8）
渠道 1.88（n=8）
时代 2.20（n=10）
持续 2.43（n=7）
```

情感、音色、受众参与的有效 n 不足以比较。

### 个案对照

- CASE005 与 CASE006：两个严格个人古筝案例，6/4 与 8/2；
- CASE004：扩展个人，二胡/秦琴，6/4；
- CASE032/CASE035：同古筝、同个人类型，但 10 项全 null。

同乐器不等于可比较；同类型也不等于同一主体结构。

## 4. 五个研究问题的回答边界

### 传播主体

可观察：严格组是 verified 个人；扩展组主体混合。  
不能推断：个人主体传播效果更好。

### 传播形式

严格组有音乐会/媒体/教育/线上视频；扩展组有机构课程、乐团、合作演出。  
`activity_status` 缺失，不能判断活动完成状态。

### 文化适配

CASE005、CASE006、CASE004 有跨文化评分和来源；CASE032/035 无评分。  
不能把评分当作受众接受度。

### 受众参与

严格组只有 CASE006 有 1 条受众参与评分；CASE005 null。  
扩展组只有 2 条有效受众参与评分。  
大多数案例只有活动记录，没有参与证据。

### 传播持续性

严格组两例持续性均为 3；CASE004 也为 3；CASE032/035 null。  
n=2 不能支持“个人持续性更强”的群体结论。

## 5. 为什么是 CONDITIONAL_PASS

- 严格个人仅 2 例；
- 两组样本量 2 vs 36；
- 缺失率 30% vs 82.5%；
- CASE007 仍待核实，排除；
- 306 条 null；
- activity_status 缺失；
- 62 条来源关系不等于 62 个独立来源；
- 只做描述性分析。

## 6. 图表

- [两组构成](<research/analysis/p15/charts/group_composition.svg>)
- [地区分布](<research/analysis/p15/charts/group_region_distribution.svg>)
- [乐器覆盖](<research/analysis/p15/charts/group_instrument_coverage.svg>)
- [指标有效 n](<research/analysis/p15/charts/group_indicator_valid_n.svg>)
- [评分分布对照](<research/analysis/p15/charts/group_indicator_score_distribution.svg>)
- [来源数量对照](<research/analysis/p15/charts/group_evidence_source_count.svg>)

## 7. 输出

- `research/analysis/p15/sample_profile_comparison.csv`
- `research/analysis/p15/indicator_stratified_statistics.csv`
- `research/analysis/p15/indicator_score_distribution.csv`
- `research/analysis/p15/case_comparison_matrix.csv`
- `research/analysis/p15/evidence_comparison.csv`
- `research/analysis/p15/comparison_case_selection.csv`

## 8. 正式状态

```text
active_version = v1.6
v1.6 数据未修改
v1.5 历史数据未修改
CASE007 pending_review 未变
CASE039/CASE040 审批评分未变
SQL Server / Neo4j 未写入
```

P15 到此停止，不自动进入 P16。
