# P16.3 八因素传播潜力可计算性审计

## 1. 模型

沿用既有权重，未修改、未重新归一化：

| 因素 | 权重 |
|---|---:|
| 情感普适性 | 20% |
| 音色辨识度 | 15% |
| 旋律易接受性 | 15% |
| 文化故事可解释性 | 10% |
| 跨文化适配性 | 10% |
| 视觉表演性 | 10% |
| 当代主题相关性 | 10% |
| 既有海外案例与反馈 | 10% |

## 2. 因素覆盖

| 因素 | available | partial | unavailable |
|---|---:|---:|---:|
| 情感普适性 | 0 | 0 | 302 |
| 音色辨识度 | 0 | 0 | 302 |
| 旋律易接受性 | 0 | 0 | 302 |
| 文化故事可解释性 | 0 | 5 | 297 |
| 跨文化适配性 | 0 | 5 | 297 |
| 视觉表演性 | 0 | 0 | 302 |
| 当代主题相关性 | 0 | 5 | 297 |
| 既有案例与反馈 | 0 | 5 | 297 |

- 20 条 partial 全部来自 CASE008 的 5 首映射曲目；
- 2,396 条 unavailable；
- available = 0。

## 3. 为什么没有完整综合分

`timbre_identity`、`melody_acceptability`、`visual_performance` 没有任何歌曲级特征数据；  
`emotional_universality` 不用评论情感替代；  
story/cross/era 只有 CASE008 的案例级评分；  
existing feedback 只有节目单关联、没有受众反馈。

因此：

```text
完整可计算：0
部分可计算：5（CASE008 五首）
暂不可计算：297
```

没有重新分配权重，也没有用其他因素补偿缺失。

## 4. 评论数据的定位

评论情感是 P16.4 的辅助描述，不作为“情感普适性”因素分：

- 评论没有 user_id；
- 情感缺失 30.48%；
- 评论来源国家不是目标受众；
- 情感分数不等于传播成功。

## 5. 输出

- `p16_potential_factor_coverage.csv`（302×8）
- `p16_potential_computability.csv`
- [八因素覆盖图](<research/analysis/p16/charts/potential_factor_coverage.svg>)
