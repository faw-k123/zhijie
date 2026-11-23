# P9 数据源盘点

> 只读盘点 SQL Server 与本地数据源；未修改任何表、未导出用户敏感信息。  
> 盘点时间：2026-11-01。

## 1. 结论

P9 目前可以形成“音乐级”研究数据，但还不能形成可靠的“用户级”偏好数据。

关键原因：

1. `tag_rating / tag_ratings` 在数据库中不存在；
2. `auth_user` 为空；
3. 用户只存在于 `behave.Users`，共 17 人；
4. 播放记录仅 12 条、3 个用户、8 首歌曲；
5. 评论 192,882 条，覆盖 302 首音乐，但没有 `user_id`；
6. `song_like` 9 条中只有 3 条能匹配 `traditional_song.id`；
7. `favorite_song` 5 条中只有 1 条能匹配；
8. Neo4j 本机 7687 未监听，未读取、未修改。

## 2. 真实存在的数据源

| 数据源 | 表 | 行数 | 主要关联键 | 研究可用性 |
|---|---|---:|---|---|
| 音乐库 | `dbo.traditional_song` | 302 | `id` | 可做音乐级分析 |
| 用户 | `behave.Users` | 17 | `user_id` | 仅聚合，含敏感信息 |
| 播放 | `behave.PlayRecords` | 12 | `user_id`、`song_id` | 可关联，但样本极小 |
| 浏览 | `behave.ViewRecords` | 0 | `user_id`、`target_id` | 空表 |
| 人格测试 | `behave.PersonalityTests` | 10 | `user_id` | 小样本 |
| 国风人格 | `dbo.guofeng_persona_test` | 7 | `user_id` | 6/7 可关联用户 |
| 文化圈测试 | `dbo.cultural_circle_test` | 10 | `user_id` | 10/10 可关联用户 |
| 用户资料 | `dbo.profile` | 1 | 无稳定 user_id | 不能作为用户主表 |
| 评论 | `dbo.comment` | 192,882 | `song_id` | 音乐级情感/国家聚合 |
| 情感时序 | `dbo.emotion_time_series` | 81,388 | `song_id` | 302 首全覆盖 |
| 点赞 | `dbo.song_like` | 9 | `user_id`、`song_id` | 仅 3/9 匹配歌曲 |
| 收藏歌曲 | `dbo.favorite_song` | 5 | `folder_id`、`song_id` | 仅 1/5 匹配歌曲 |
| 收藏夹 | `dbo.favorite_folder` | 8 | `user_id` | 6/8 可关联用户 |
| Django 用户 | `dbo.auth_user` | 0 | `id` | 空表 |
| 新用户行为库 | `user_behave.*` | 0 | — | 空表 |
| tag_rating | 不存在 | 0 | — | 无法盘点 |
| Neo4j | 未连接 | — | — | 未读取 |

## 3. 关键缺口

### 3.1 tag_rating 不存在

数据库中既没有 `tag_rating`，也没有 `tag_ratings`。

现有近似数据：

- `profile.tags`：1 行；
- `guofeng_persona_test.tag_scores`：7 行；
- `guofeng_persona_test.matched_personas`：7 行。

这些都不是通用的“用户—标签—评分”表，不能替代 `tag_rating`。

### 3.2 评论有音乐键，没有用户键

`comment.song_id` 100% 匹配 `traditional_song.id`，可做：

- 每首歌的评论量；
- 情感极性；
- 国家/来源聚合；
- 时间趋势。

但不能做：

- 用户偏好矩阵；
- 用户聚类；
- 用户—音乐关联。

### 3.3 视频—音乐映射不存在

`behave.ViewRecords` 为空；`favorite_song.mv_url` 只是 URL 字段，不是视频表。没有可核验的视频 ID ↔ 音乐 ID 映射。

### 3.4 用户主键不统一

- `auth_user.id` 是 int，但表为空；
- `behave.Users.user_id` 是 varchar；
- `profile` 没有 user_id；
- `song_like.user_id`、`favorite_folder.user_id` 是 nvarchar；
- 没有统一的用户身份表。

## 4. 敏感信息

以下字段只做存在性/缺失率盘点，不导出值：

- `behave.Users.password`；
- `behave.Users.username`；
- `auth_user.password/email`；
- `profile.username/description`；
- `comment.content`；
- 测试 `answers/result_detail`。

P9 分析只使用 ID、计数、时间、标签/指标等聚合字段。

## 5. 研究可用性分级

```text
可用：traditional_song、emotion_time_series、comment 的音乐级聚合
有限可用：behave.PlayRecords、song_like、favorite_song、guofeng、cultural
不可用：tag_rating、auth_user、user_behave、Neo4j（当前）
```

## 6. 输出

- `research/analysis/p9-data-source-inventory.csv`
