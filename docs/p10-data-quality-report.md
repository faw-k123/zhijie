# P10 数据质量报告

> 只读分析；未修改 `traditional_song`、`comment`、`emotion_time_series`。  
> 统计时间：2026-11-01。

## 1. 原始数据量与实际读取量

| 数据源 | 原始行数 | 实际读取 | 唯一音乐 |
|---|---:|---:|---:|
| traditional_song | 302 | 302 | 302 |
| comment | 192,882 | 192,882 | 302 |
| emotion_time_series | 81,388 | 81,388 | 302 |
| v1.3 音乐—案例映射 | 5 | 5 | 5 |

## 2. 主键与重复

### 音乐

```text
traditional_song：302 行，302 个唯一 id
重复：0
```

### 评论

```text
comment 行数：192,882
全局唯一 comment.id：158,087
重复 id 行数：34,795
重复 id 组：14,628
单 id 最大行数：5
```

**重要：`comment.id` 不是全局唯一主键。**  
不能把 `comment.id` 当唯一评论键，也不能用 `COUNT(DISTINCT id)` 直接代表全部评论。

歌曲级统计使用原始评论行；同时提供：

- `comment_count`：原始行数；
- `unique_comment_id_count`：该歌曲内唯一 id；
- `comment_duplicate_id_rows`：本歌曲内重复 id 行数，合计 15,715。

### 情感时序

```text
81,388 行
81,388 个唯一 id
81,388 个唯一 (song_id,date)
重复：0
```

## 3. 关联成功率

| 关联 | 成功率 |
|---|---:|
| comment.song_id → traditional_song.id | 192,882 / 192,882 = 100% |
| emotion.song_id → traditional_song.id | 302 / 302 歌曲 = 100% |
| v1.3 mapping → traditional_song.id | 5 / 5 = 100% |
| comment → user | 0%，comment 无 user_id |

## 4. 缺失值

### 评论

```text
sentiment_score 缺失：58,789 / 192,882 = 30.48%
polarity 为 NULL：48,485
polarity 为空字符串：1
country 缺失：18,601 / 192,882 = 9.64%
```

有 18 首歌曲全部 sentiment_score 为空，`sentiment_mean=null`。

### 情感时序

```text
emotion_index 缺失：0
date 缺失：0
total_count=0：0
```

## 5. 异常值

### likes

```text
likes=2147483647：2 条
```

这是 `int` 最大值，按异常/哨兵值处理，不纳入点赞均值。  
`likes_sum_excluding_sentinel` 与 `likes_mean_excluding_sentinel` 已剔除。

### 时间

```text
comment.comment_time：2017-09-09 至 2026-09-15
未来时间：0
2017 年前：0
emotion.date：2017-09-09 至 2026-09-15
未来时间：0
```

## 6. 情感值口径

`comment.sentiment_score`：

```text
观测范围：-0.8 至 1.0
缺失：30.48%
```

`emotion_time_series.emotion_index`：

```text
观测范围：-1.0 至 1.0
均值：0.1331
```

当前数据库没有给出 `emotion_index` 的计算公式。  
因此只使用：

- 均值；
- 波动（总体标准差）；
- 时间趋势斜率；
- 覆盖率。

不解释为“传播成功”或“受众态度”。

## 7. 国家字段

```text
comment.country：13 个取值
中国 104,463
美国 11,300
日本 9,532
韩国 7,922
英国 6,232
...
缺失 18,601
```

这只表示评论来源国家分布，不是目标国家受众偏好，也不能和国家传播效果直接等同。

## 8. 综合特征完整度

```text
feature_completeness 最小值：0.8333
最大值：1.0
均值：0.9884
```

6 个组件：title、genre、audio_url、comment_count、sentiment_mean、emotion_mean。

## 9. 映射

```text
已验证映射：5 条
音乐：23、158、26、28、29
案例：CASE008
mapping_status=verified
performance_status=program_listed
```

映射只证明曲目对应，不证明演出完成。

## 10. 结论

P10 可以支持：

- 302 首音乐的基础特征；
- 音乐级评论量/情感/国家/时间聚合；
- 音乐级情感时序；
- 5 条已核验音乐—案例关联；
- 描述性特征分析。

P10 不能支持：

- 用户偏好/聚类；
- 因果推断；
- 目标国家受众偏好；
- 用评论情感替代传播成功；
- 把 5 条映射代表全部案例。
