# P9 数据质量评估

> 只读统计；不导出用户名、密码、邮箱、评论正文或测试答案。  
> 统计时间：2026-11-01。

## 1. 总览

| 数据源 | 总记录 | 有效记录 | 重复 | 关联成功率 | 备注 |
|---|---:|---:|---:|---:|---|
| traditional_song | 302 | 302 | 0 | — | 主键唯一 |
| comment | 192,882 | 192,882 | 0 | song_id 100% | 无 user_id |
| emotion_time_series | 81,388 | 81,388 | 0 | song_id 302/302 歌曲 | 音乐级 |
| behave.Users | 17 | 17 | 0 | — | 17 个唯一 user_id |
| behave.PlayRecords | 12 | 12 | 0 | user 100%；song 100% | 3 用户/8 歌曲/9 用户-歌曲对 |
| song_like | 9 | 9 | 0 | user 8/9；song 3/9 | 6 条歌曲无法匹配 |
| favorite_song | 5 | 5 | 0 | user 5/5；song 1/5 | 4 条歌曲无法匹配 |
| favorite_folder | 8 | 8 | 0 | user 6/8 | 2 条用户无法匹配 |
| guofeng_persona_test | 7 | 7 | 0 | user 6/7 | 标签测试结果 |
| cultural_circle_test | 10 | 10 | 0 | user 10/10 | 小样本 |
| profile | 1 | 1 | 0 | 无稳定 user_id | 不能作主表 |
| auth_user | 0 | 0 | 0 | — | 空表 |
| user_behave.* | 0 | 0 | 0 | — | 空表 |
| tag_rating / tag_ratings | 0 | 0 | 0 | — | 表不存在 |
| Neo4j | — | — | — | — | 7687 未监听 |

## 2. 缺失值

| 字段 | 缺失数 | 缺失率 |
|---|---:|---:|
| comment.country | 18,601 | 9.64% |
| comment.song_id | 0 | 0% |
| behave.Users.country | 2 | 11.76% |
| PlayRecords.user_id | 0 | 0% |
| PlayRecords.song_id | 0 | 0% |
| song_like.user_id | 0 | 0% |
| song_like.song_id | 0 | 0% |
| favorite_song.song_id | 0 | 0% |
| guofeng.tag_scores | 0 | 0% |
| profile.tags | 0 | 0% |

## 3. 关联失败

### 3.1 评论

- 192,882 条全部有 `song_id`；
- 192,882 条全部匹配 302 首音乐；
- 但**没有 user_id**，不能进入用户—音乐联合数据集。

### 3.2 点赞

- 9 条中 8 条能匹配用户；
- 只有 3 条能匹配 `traditional_song.id`；
- 6 条歌曲 ID 可能是外部 ID，未确认映射，不能强行合并。

### 3.3 收藏

- 5 条中 5 条能通过收藏夹匹配用户；
- 只有 1 条能匹配 `traditional_song.id`；
- 4 条歌曲无法匹配。

### 3.4 视频

- `behave.ViewRecords` 为空；
- 没有视频内容表；
- 没有视频 ID ↔ 音乐 ID 的真实映射。

## 4. 时间字段

| 数据源 | 范围 |
|---|---|
| comment.comment_time | 2017-09-09 至 2026-09-15 |
| PlayRecords.play_time | 2026-09-20 至 2026-10-25 |
| emotion_time_series.date | 2017-09-09 至 2026-09-15 |

时间字段可用于趋势，但用户行为时间范围很短，不能做长期行为分析。

## 5. 用户—音乐联合数据集

当前能确认的真实用户—音乐关系：

```text
播放：9 个唯一用户-歌曲对（12 条记录，3 用户，8 歌曲）
点赞：3 个匹配用户-歌曲对
收藏：1 个匹配用户-歌曲对
```

合并后仍远低于聚类、偏好矩阵或协同过滤的最低样本要求。

## 6. 结论

### 可用

- 302 首音乐特征；
- 302 首音乐的情感时序；
- 192,882 条评论的音乐级/国家/时间聚合；
- 少量用户测试标签。

### 不可用

- 用户级音乐偏好矩阵；
- 用户聚类；
- 协同过滤/推荐模型；
- 视频—音乐映射；
- 全量 `tag_rating` 分析；
- 用户—案例直接关联。

### 处理原则

- 不删除无关联记录；
- 不把外部歌曲 ID 强行映射到 302 首库；
- 不把匿名评论当用户行为；
- 不把测试标签当全量 tag_rating；
- 不输出用户敏感信息。
