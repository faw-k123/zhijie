# P10 音乐级多源数据融合报告

## 1. 阶段结论

P10 已完成音乐级只读融合：

```text
302 首音乐
192,882 条评论
81,388 条情感时序
36 个案例（36 案例中仅 5 条已核验音乐映射）
```

融合后形成 302 行、以 `music_id` 为主键的综合特征数据集。

## 2. 数据来源与关联

| 数据 | 键 | 结果 |
|---|---|---|
| traditional_song | music_id | 302 唯一 |
| comment | song_id | 192,882 / 192,882 匹配 |
| emotion_time_series | song_id | 302 / 302 歌曲匹配 |
| v1.3 mapping | music_id | 5 / 5 匹配 |

关联方式：

```text
music_id = traditional_song.id
comment.song_id -> music_id
emotion_time_series.song_id -> music_id
v1.3 mapping.music_id -> music_id
```

没有用户级关联；评论没有 `user_id`。

## 3. 输出数据集

| 文件 | 行数 | 用途 |
|---|---:|---|
| `p10-music-basic-features.csv` | 302 | 音乐基础属性 |
| `p10-comment-statistics.csv` | 302 | 每首音乐的评论统计 |
| `p10-emotion-timeseries-features.csv` | 302 | 每首音乐的情感时序特征 |
| `p10-music-case-joined.csv` | 302 | 音乐—案例关联 |
| `p10-music-integrated-features.csv` | 302 | 综合特征 |

## 4. 主要特征

- 74 个 genre 值、35 个 category；
- 每首音乐都有评论；
- 18 首音乐所有评论 sentiment_score 都为空；
- 每首音乐都有情感时序；
- 5 首音乐有已验证案例映射，均为 CASE008；
- `feature_completeness` 均值 0.9884。

## 5. 关键质量发现

### 5.1 评论 id 不唯一

```text
评论行：192,882
全局唯一 id：158,087
重复 id 行：34,795
```

评论统计以原始行为准，同时提供 `unique_comment_id_count` 和 `duplicate_id_rows`。  
没有把重复 id 静默删除。

### 5.2 情感缺失

```text
sentiment_score 缺失：58,789 / 192,882 = 30.48%
18 首歌曲无 sentiment_mean
```

缺失保持 null，不填 0。

### 5.3 点赞异常值

```text
likes=2147483647：2 条
```

按哨兵值处理，剔除后计算 likes_sum/mean。

### 5.4 国家字段

评论来源国家 13 个，缺失 18,601。  
只能描述评论来源，不能解释为目标国家受众偏好。

### 5.5 情感时序口径

`emotion_index` 观测范围 -1 至 1，均值 0.1331；数据库未提供计算公式。  
本阶段只计算均值、波动、趋势斜率、覆盖率，不解释为传播成功。

## 6. 案例关联

只使用 P8 审查后的 5 条映射：

```text
CASE008 -> music_id 23, 158, 26, 28, 29
mapping_status=verified
performance_status=program_listed
```

没有通过曲名相似、乐器相同或国家相同生成新映射。  
没有把 `program_listed` 写成 `performed_confirmed`。

## 7. 可用与不可用

### 可用

- 音乐级基础特征；
- 评论量/情感/国家/时间描述；
- 情感时序特征；
- 5 条案例—音乐关联；
- 数据质量与缺失诊断。

### 不可用

- 用户偏好/聚类；
- 因果推断；
- 目标国家受众偏好；
- 评论情感=传播成功；
- 5 条映射代表全部案例；
- 预测模型。

## 8. 文件边界

- 未修改 `traditional_song`；
- 未修改 `comment`；
- 未修改 `emotion_time_series`；
- 未修改 v1.2 原始数据；
- 未激活 v1.3；
- 未新增数据库表/migration；
- 未修改 Neo4j。

## 9. 下一步

P10 完成后应暂停，先检查：

1. 评论 id 重复是否来自多个来源，是否需要源级去重；
2. sentiment_score 的生成口径；
3. emotion_index 的计算公式；
4. 评论国家字段的采集含义；
5. 是否扩大已验证音乐—案例映射；
6. 是否允许进入 P11 的区域/知识图谱分析。
