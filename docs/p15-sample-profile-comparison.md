# P15.2 两组样本基本特征比较

## 1. 总体

| 指标 | strict_individual | extended_cross_cultural |
|---|---:|---:|
| 案例 | 2 | 36 |
| 有效评分 | 14 | 63 |
| null | 6 | 297 |
| 有效评分率 | 70.0% | 17.5% |
| 平均有效评分/案 | 7.0 | 1.75 |
| 国家 | 2 | 12 |
| 地区 | 2 | 6 |
| 来源关系 | 5 | 52 |
| 单来源案例 | 0 | 24 |
| 同机构重复风险 | 1 | 5 |

pending_review 的 2 例另有 17 有效 / 3 null，未纳入本表。

## 2. 传播主体

### strict_individual

```text
CASE005 Clare Cooper（澳大利亚）
CASE006 Jarrelle Barton（美国）
case_type：foreign_individual_cross_cultural
performer_identity_status：verified
owner_approval_status：approved
```

### extended_cross_cultural

```text
overseas_institution_education：16
overseas_institution_ensemble：8
cross_cultural_ensemble：7
foreign_individual_cross_cultural：5
```

扩展组内部高度异质：

- 有机构教育；
- 有机构乐团；
- 有跨文化合作团队；
- 也有未进入严格样本的个人案例（CASE004、CASE010、CASE032、CASE033、CASE035）。

不能把它当作单一“个人演奏组”。

## 3. 国家与地区

### 严格组

```text
国家：澳大利亚、美国
地区：其他/区域外、北美
```

### 扩展组

```text
国家：12
地区：6（含其他/区域外）
```

扩展组国家：

```text
美国15、加拿大4、澳大利亚4、英国3、日本2、德国2、法国1、
墨西哥1、新西兰1、科威特1、阿根廷1、阿联酋1
```

严格组样本量只有 2，不能比较“国家集中度”的总体差异。

## 4. 乐器

### 严格组

```text
古筝：2 例
```

### 扩展组

```text
未具体列明/合奏：22
古筝：11
二胡：8
琵琶：6
古琴：3
笛：2
箫/唢呐/中阮：各1
```

多标签统计：一个案例可包含多种乐器，不能相加当作 36。

## 5. 活动与传播形式

严格组：

- CASE005：线下音乐会、媒体；
- CASE006：线上视频、线下音乐会、教育。

扩展组包含机构教育、机构乐团、合作演出等。

`activity_status` 全部为 `NOT_RECORDED`，不能从字段判断活动是公告、节目单还是完成。

## 6. 图表

- [两组构成](<research/analysis/p15/charts/group_composition.svg>)
- [地区分布](<research/analysis/p15/charts/group_region_distribution.svg>)
- [乐器覆盖](<research/analysis/p15/charts/group_instrument_coverage.svg>)

## 7. 输出

- `research/analysis/p15/sample_profile_comparison.csv`
