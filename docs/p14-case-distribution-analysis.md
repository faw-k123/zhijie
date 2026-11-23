# P14.2 案例结构分析

> `n=40`；每个案例只计一次国家。  
> “其他”指澳大利亚、新西兰等六区域外案例，不强行归入亚洲/欧洲。

## 1. 国家分布

| 国家 | 案例数 | 占 40 |
|---|---:|---:|
| 美国 | 16 | 40.0% |
| 澳大利亚 | 5 | 12.5% |
| 加拿大 | 4 | 10.0% |
| 英国 | 4 | 10.0% |
| 德国 | 2 | 5.0% |
| 日本 | 2 | 5.0% |
| 法国 | 2 | 5.0% |
| 墨西哥 | 1 | 2.5% |
| 新西兰 | 1 | 2.5% |
| 科威特 | 1 | 2.5% |
| 阿根廷 | 1 | 2.5% |
| 阿联酋 | 1 | 2.5% |

```text
国家/地区：12
美国集中度：16/40 = 40%
北美合计：20/40 = 50%
```

## 2. 目标地区分布

| 地区 | 案例数 | 占 40 |
|---|---:|---:|
| 北美 | 20 | 50.0% |
| 欧洲 | 8 | 20.0% |
| 其他/区域外 | 6 | 15.0% |
| 东亚 | 2 | 5.0% |
| 中东及部分伊斯兰文化地区 | 2 | 5.0% |
| 拉丁美洲 | 2 | 5.0% |
| 东南亚 | 0 | 0.0% |

关键结论：

- 北美占一半；
- 东南亚仍为 0；
- 中东、拉美各 2 例，仍不足以代表区域；
- 澳大利亚/新西兰归为“其他”，没有强行并入亚洲。

## 3. 乐器分布

多乐器案例分别计入各乐器，因此合计可超过 40。

| 乐器 | 涉及案例数 | 占 40 |
|---|---:|---:|
| 古筝 | 13 | 32.5% |
| 二胡 | 10 | 25.0% |
| 琵琶 | 6 | 15.0% |
| 古琴 | 3 | 7.5% |
| 笛 | 2 | 5.0% |
| 箫 | 1 | 2.5% |
| 扬琴 | 1 | 2.5% |
| 唢呐 | 1 | 2.5% |
| 中阮 | 1 | 2.5% |
| 未具体列明/合奏 | 22 | 55.0% |

结构：

```text
单乐器/单一类别案例：29
多乐器案例：11
未具体列明/合奏：22（占 55%）
```

“未具体列明”不能算作某一具体乐器，也不能从合奏描述推断个人主奏。

## 4. 案例类型

| case_type | 数量 |
|---|---:|
| overseas_institution_education | 16 |
| foreign_individual_cross_cultural | 9 |
| overseas_institution_ensemble | 8 |
| cross_cultural_ensemble | 7 |

样本分类：

```text
strict_individual：2
extended_cross_cultural：36
pending_review：2
```

## 5. 图表

- [国家分布](<research/analysis/p14/charts/country_distribution.svg>)
- [目标地区分布](<research/analysis/p14/charts/region_distribution.svg>)
- [乐器分布](<research/analysis/p14/charts/instrument_distribution.svg>)
- [样本构成](<research/analysis/p14/charts/sample_composition.svg>)

## 6. 输出

- `research/analysis/p14/case_distribution.csv`
- `research/analysis/p14/country_distribution.csv`
- `research/analysis/p14/region_distribution.csv`
- `research/analysis/p14/instrument_distribution.csv`
