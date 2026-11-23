# P9 多源数据融合设计

> 本文件是设计，不是建模结果。  
> 不新增表、不写 Neo4j、不修改业务库。

## 1. 逻辑数据集

### A. 用户特征

```text
user_id
country
persona_tags（7条测试，6可关联）
cultural_circle（10条）
profile_tags（1条，无稳定 user_id）
```

状态：**样本不足**。17 个用户，不能做用户聚类或稳定分群。

### B. 音乐特征

```text
music_id
title
genre
category_id
instrument_hint
emotion_index（音乐级时序）
comment_count / sentiment（音乐级聚合）
```

状态：302 首，可做描述性音乐特征分析。

### C. 用户—音乐行为

```text
user_id
music_id
behavior_type（play/like/favorite）
behavior_value
event_time
```

状态：**严重不足**。

```text
播放：12 条 / 3 用户 / 8 歌曲 / 9 个用户-歌曲对
点赞：9 条，仅 3 条匹配歌曲
收藏：5 条，仅 1 条匹配歌曲
```

### D. 海外传播案例

```text
case_id
country / region
case_type
performance_status
indicator scores（v1.3 candidate: 87 有效）
source_id
```

状态：36 案例，可做案例级描述；不能做复杂模型。

### E. 音乐—案例映射

```text
case_id
music_id
mapping_status
performance_status
source_id
```

状态：CASE008 的 5 条 verified mapping；performance 仍是 program_listed。

## 2. 关联图

```text
用户 user_id
   │ 少量播放/点赞/收藏
   ▼
音乐 music_id ── 302 首 ── 评论/情感（音乐级）
   │
   │ 仅 5 条已核验映射
   ▼
海外案例 case_id ── 36 案例 ── 指标（87 有效）
   │
   ▼
国家/地区、渠道
```

关键限制：

- 评论没有 user_id，不能把评论当用户行为；
- 用户与案例之间没有直接键；
- 音乐与案例只有 5 条映射；
- 没有视频—音乐映射。

## 3. 方法评估

| 方法 | 所需数据 | 当前样本 | 结论 |
|---|---|---|---|
| 用户偏好分析 | 用户-音乐行为 | 9 播放对/3 点赞/1 收藏 | **insufficient** |
| 用户聚类 | 用户特征 + 行为 | 17 用户，3 有播放 | **insufficient** |
| 音乐属性关联 | 302 音乐 + 属性 | 302 首 | 可做描述性 |
| 标签关联规则 | tag_rating | 表不存在 | **insufficient** |
| 用户—音乐偏好矩阵 | 足够行为 | 稀疏且极小 | **insufficient** |
| 海外案例描述 | 36 案例/87 有效 | 36 案例 | 可做描述性 |
| 音乐—案例关联 | 映射 | 5 条 | **insufficient** |

## 4. 可用分析

### 可以做

1. 302 首音乐的类型/乐器/评论量/情感时序描述；
2. 评论的国家分布与时间趋势；
3. 36 个案例的国家、类型、证据等级、指标覆盖描述；
4. CASE008 的 5 条曲目映射核验；
5. 数据缺口报告。

### 不能做

1. 用户聚类；
2. 协同过滤；
3. 用户偏好预测；
4. 因果分析；
5. “某国受众喜欢某音乐”的推断；
6. 用 5 条映射代表整个案例库的音乐关联。

## 5. 数据分层建议

```text
研究事实层：v1.2 / v1.3 JSON（版本化，not modified）
分析派生层：research/analysis/*.csv
业务只读层：traditional_song / comment / emotion_time_series
用户隐私层：behave.Users 等，只做聚合，不导出
图谱层：Neo4j 暂不接入
```

## 6. 下一阶段的前置条件

进入真正的用户行为挖掘前，至少需要：

1. 统一 `user_id`；
2. 补 `tag_rating` 或明确替代字段；
3. 扩大播放/点赞/收藏记录；
4. 建立视频—音乐映射；
5. 确认评论是否可关联用户（当前不能）；
6. 明确隐私与授权边界。

## 7. 结论

P9 当前只能完成：

- 音乐级描述；
- 案例级描述；
- 关联键验证；
- 数据质量评估；
- 融合方案设计。

不能声称已经完成用户偏好挖掘或智能推荐。
