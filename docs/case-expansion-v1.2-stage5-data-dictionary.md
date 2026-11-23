# v1.2 数据字典与版本说明

> 数据版本：v1.2  
> 状态：reviewed / active_version=v1.2  
> 案例：36（CASE001–CASE036）  
> 指标记录：360；有效 73；null 287  
> 正式来源记录：56（案例来源合计，非独立来源数）

## 1. 版本组成

| 组成 | 数量 | 说明 |
|---|---:|---|
| 既有案例 | 10 | CASE001–CASE010，从 v1.1 原样保留 |
| 新增扩展案例 | 26 | CASE011–CASE036，来自第四阶段 approved_extended |
| 严格新增 | 0 | CAND024 仍为严格复核，不进入 v1.2 严格样本 |
| 指标记录 | 360 | 36 × 10 |
| 有效指标值 | 73 | 全部来自既有 10 个案例 |
| null | 287 | 26 个扩展案例的 260 条 + 既有 27 条 |

## 2. 案例分类

`case_type` 使用既有契约枚举：

- `foreign_individual_cross_cultural`
- `overseas_institution_ensemble`
- `overseas_institution_education`
- `cross_cultural_ensemble`

扩展研究分类保留在 `extended_category`：

- `overseas_institution_education`
- `overseas_ensemble_performance`
- `cross_cultural_collaboration`
- `community_music_activity`

## 3. 字段

案例核心字段与 v1.1 一致；新增扩展字段：

| 字段 | 说明 |
|---|---|
| `candidate_id` | 候选编号，如 CAND026 |
| `extended_category` | 扩展研究分类 |
| `performer_identity_status` | 个人身份状态；团体为 not_applicable |
| `performance_location` | 活动国家/地点 |
| `overseas_activity` | 是否海外活动 |
| `strict_sample_eligible` | 是否严格样本；扩展案例为 false |
| `eligibility_reason` | 扩展准入理由 |
| `evidence_limitations` | 证据缺口 |

## 4. null 语义

- null = 证据不足，不是 0 分；
- 26 个扩展案例的 260 条指标全部 null；
- 原因：来源主要是机构/活动/教育入口，缺个人表演、受众反馈、音色/情感证据；
- 不允许用机构知名度、活动规模推断分数。

## 5. 数据文件

```text
research/data/v1.2/cases.json
research/data/v1.2/sources.json
research/data/v1.2/success_factors.json
research/data/v1.2/music_scores.json
research/data/v1.2/regional_strategies.json
research/data/manifest.json
research/analysis/v1.2-case-dataset.csv
research/analysis/v1.2-music-case-mapping.json
```

## 6. 样本门槛

```text
n=0          unavailable
n=1–4        insufficient
n=5–19       exploratory
n≥20         descriptive
```

v1.2 案例总数为 36，但新增案例的指标有效值 n=0；指标门槛按每个指标的实际 n 计算，不按案例总数。
