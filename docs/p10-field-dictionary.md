# P10 字段字典

> 音乐级分析数据集；主键 `music_id`。  
> 缺失值保持 null，不填 0；0 只表示真实计数为 0。

## 1. 音乐基础特征

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| music_id | int | `traditional_song.id` | 302 首唯一 |
| title | string | `title` | 原曲名 |
| genre | string | `genre` | 原始风格/标签 |
| category_id | int | `category_id` | 原分类 |
| audio_url | string/null | `audio_url` | 部分为空 |
| cover_url | string/null | `cover_url` | 部分为空 |
| has_audio | bool | 派生 | `audio_url` 是否非空 |
| instrument_hint | null | 派生 | 当前无可靠字段，全部 null，不按 genre 猜 |
| source | string | 常量 | `traditional_song` |

## 2. 评论统计

| 字段 | 类型 | 说明 |
|---|---|---|
| comment_count | int | 原始评论行数；含重复 id |
| unique_comment_id_count | int | 本歌曲内唯一 comment.id |
| comment_duplicate_id_rows | int | `comment_count - unique_comment_id_count` |
| first_comment_time / last_comment_time | datetime | 评论时间范围 |
| sentiment_missing_count | int | `sentiment_score` 为空的数量 |
| sentiment_mean / min / max | float/null | 仅对非空 sentiment_score 计算 |
| positive_count / negative_count / neutral_count | int | 按 polarity 中文值计数 |
| polarity_null_count / polarity_blank_count | int | 空值/空字符串 |
| country_count | int | 本歌曲不同评论来源国家数 |
| country_missing_count | int | country 为空的数量 |
| likes_sentinel_count | int | `likes=2147483647` 的异常值数量 |
| likes_sum_excluding_sentinel | int | 剔除 sentinel 后的点赞合计 |
| likes_mean_excluding_sentinel | float/null | 剔除 sentinel 后的均值 |

## 3. 情感时序特征

| 字段 | 类型 | 说明 |
|---|---|---|
| emotion_rows | int | 该曲的时序行数 |
| emotion_first_date / last_date | date | 时间范围 |
| emotion_days | int | 不同日期数 |
| emotion_span_days | int | 首尾日期跨度 |
| emotion_coverage_ratio | float/null | `emotion_days / emotion_span_days` |
| emotion_mean | float | `emotion_index` 均值 |
| emotion_volatility | float/null | `emotion_index` 总体标准差 |
| emotion_min / max | float | 观测范围 |
| emotion_trend_slope_per_day | float/null | OLS 斜率：emotion_index ~ 距首日天数 |
| positive_rate_mean | float | 原始 positive_rate 均值 |
| negative_rate_mean | float | 原始 negative_rate 均值 |
| total_count_sum | int | 原始 total_count 合计 |

## 4. 案例关联

| 字段 | 类型 | 说明 |
|---|---|---|
| case_count | int | 已验证映射数量（0/1） |
| case_ids | string | 关联案例 |
| mapping_status | string | `verified` 或 `no_verified_mapping` |
| performance_status | string | `program_listed` 或 `not_applicable` |
| source_ids | string | 映射来源 |

## 5. 综合特征

| 字段 | 说明 |
|---|---|
| feature_completeness | 6 个组件中非空比例：title、genre、audio_url、comment_count、sentiment_mean、emotion_mean |
| sentiment_mean | 音乐级评论情感均值，不是传播成功 |
| emotion_mean | 音乐级情感时序均值，不是受众偏好 |
| case_count | 只含 5 条已验证映射，不代表全部案例 |

## 6. null 语义

- `sentiment_mean=null`：没有可用的 sentiment_score；
- `emotion_* = null`：没有可用情感时序；
- `case_count=0`：没有已验证映射，不是缺失；
- `instrument_hint=null`：没有可靠依据；
- `country_count` 只描述评论来源，不是目标国受众偏好。
