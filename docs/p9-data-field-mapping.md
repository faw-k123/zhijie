# P9 字段映射设计

## 1. 统一实体

| 实体 | 统一键 | 真实来源 | 状态 |
|---|---|---|---|
| 用户 | `user_id` | `behave.Users.user_id` | 17 条；其他表部分可关联 |
| 音乐 | `music_id` | `traditional_song.id` | 302 条 |
| 案例 | `case_id` | v1.2 / v1.3 cases | 36 条 |
| 来源 | `source_id` | cases.sources | 56 条案例来源关系 |
| 行为 | `behavior_id` | `PlayRecords.record_id` / `song_like.id` / `favorite_song.id` | 分散 |
| 时间 | `event_time` | `play_time` / `comment_time` / `created_at` | 格式不统一 |

## 2. A. 用户特征

| 逻辑字段 | 来源字段 | 类型 | 关联 | 备注 |
|---|---|---|---|---|
| user_id | `behave.Users.user_id` | varchar | 主键 | 17 个用户 |
| country | `behave.Users.country` | nvarchar | — | 2/17 缺失 |
| register_date | `behave.Users.register_date` | datetime | — | 17 条 |
| persona | `guofeng_persona_test.matched_personas` | nvarchar | user_id | 7 条，6 可关联 |
| persona_tags | `guofeng_persona_test.tag_scores` | nvarchar | user_id | 测试结果，不是 tag_rating |
| cultural_circle | `cultural_circle_test.matched_circles` | nvarchar | user_id | 10 条 |
| profile_tags | `profile.tags` | nvarchar | 无稳定 user_id | 仅 1 行，不可作主表 |

**不能做**：把 `profile.username` 当稳定用户键；把 `tag_scores` 当全量用户标签。

## 3. B. 音乐特征

| 逻辑字段 | 来源字段 | 类型 | 备注 |
|---|---|---|---|
| music_id | `traditional_song.id` | int | 302 |
| title | `title` | nvarchar | 可标准化 |
| genre | `genre` | nvarchar | 乐器/风格提示 |
| category_id | `category_id` | int | 分类 |
| audio_url | `audio_url` | nvarchar | 部分为空 |
| cover_url | `cover_url` | nvarchar | 部分为空 |
| emotion_index | `emotion_time_series.emotion_index` | float | 音乐级时序 |
| comment_count | `comment` 聚合 | int | 音乐级 |

## 4. C. 用户—音乐行为

| 逻辑字段 | 来源 | 关联键 | 有效量 |
|---|---|---|---:|
| user_id | `behave.PlayRecords.user_id` | `behave.Users.user_id` | 12/12 |
| music_id | `behave.PlayRecords.song_id` | `traditional_song.id`（字符串转 int） | 12/12 |
| behavior_type | 表名 | 播放/点赞/收藏 | 3 类 |
| behavior_value | `play_duration` / `reaction_type` | — | 播放有值，点赞有类型 |
| event_time | `play_time` / `created_at` | — | 可解析 |

### 关键限制

- 播放：12 条、3 用户、8 歌曲；
- 点赞：9 条，仅 3 条匹配歌曲；
- 收藏：5 条，仅 1 条匹配歌曲；
- 不能把 `song_like.song_id` 中无法匹配的 6 条强行映射。

## 5. D. 海外传播案例

| 逻辑字段 | 来源 |
|---|---|
| case_id | `v1.2/cases.json` / `v1.3/cases.json` |
| country/region | `cases.country/region` |
| case_type | `cases.case_type` |
| indicator scores | `success_factors.scores` |
| source_id | `cases.sources[].source_id` |

v1.3 候选：36 案例，87 条有效评分。

## 6. E. 音乐—案例映射

| 字段 | 来源 | 例 |
|---|---|---|
| case_id | mapping | CASE008 |
| music_id | mapping | 23/158/26/28/29 |
| mapping_status | P8 审查 | verified |
| performance_status | P8 审查 | program_listed |
| source_id | mapping | C008-S001 |

`mapping_status` 与 `performance_status` 必须分开；曲目对得上不等于演出完成。

## 7. 关联键判定

| 关联 | 可用键 | 成功率 | 结论 |
|---|---|---|---:|
| comment → music | `song_id` | 192882/192882 = 100% | 可做音乐级聚合 |
| play → user | `user_id` | 12/12 = 100% | 可关联，但只有 3 用户 |
| play → music | `song_id` 转 int | 12/12 = 100% | 可关联，8 歌曲 |
| like → user | `user_id` | 8/9 = 88.9% | 不完整 |
| like → music | `song_id` 转 int | 3/9 = 33.3% | 大部分不可关联 |
| favorite → music | `song_id` 转 int | 1/5 = 20% | 不足 |
| favorite → user | folder → user | 5/5 = 100% | 可关联 |
| persona → user | `user_id` | 6/7 = 85.7% | 小样本 |
| cultural → user | `user_id` | 10/10 = 100% | 小样本 |
| tag_rating → user | 无表 | 0% | 不存在 |

## 8. 敏感字段处理

不导出：

- 用户名、密码、邮箱；
- 评论正文；
- 测试答案/结果详情；
- 用户国家以外的可识别信息。

分析层只保留 `user_id` 的哈希或内部 ID，不输出明文身份。
