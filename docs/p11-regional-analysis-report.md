# P11 区域传播适配分析报告

> 六个目标区域沿用项目原有设计：东亚、东南亚、欧洲、北美、中东及部分伊斯兰文化地区、拉丁美洲。  
> 当前正式版本 v1.2；v1.3 仍为 draft。

## 1. 区域案例覆盖

| 区域 | v1.2 案例数 | 证据状态 |
|---|---:|---|
| 北美 | 20 | 有机构/教育/乐团案例，缺受众效果 |
| 欧洲 | 8 | 有案例与 CASE008 曲目映射 |
| 东亚 | 2 | 日本案例，样本很小 |
| 东南亚 | 0 | 只有评论来源国家计数 |
| 中东及部分伊斯兰文化地区 | 0 | 无正式案例 |
| 拉丁美洲 | 0 | 无正式案例 |

另有 6 个澳大利亚/新西兰案例，不属于上述六区域，未强行归入。

## 2. 音乐—区域匹配

生成 302 首音乐 × 6 区域 = 1,812 条：

```text
case_supported_program：5 条
unknown：1,807 条
```

5 条全部是：

```text
CASE008（英国）→ music_id 23、158、26、28、29
```

这只是节目单曲目对应，`performance_status=program_listed`，不代表演出完成或区域受众接受。

其余 1,807 条没有区域证据，保持 unknown，没有做“曲风相似度”或“乐器相同”推断。

## 3. 区域 × 分类矩阵

生成 6 区域 × 35 个音乐分类 = 210 条：

```text
case_supported_program：1 条
unknown：209 条
```

唯一有案例关联的是欧洲分类 2（5 首 CASE008 曲目）；不代表该分类在欧洲普遍受欢迎。

## 4. 区域策略草案

| 区域 | 状态 | 结论 |
|---|---|---|
| 北美 | exploratory | 可提教育/乐团/社区场景，不能声称受众偏好 |
| 欧洲 | exploratory | 有 CASE008 曲目映射，仍无受众效果 |
| 东亚 | exploratory | 日本案例样本小，不能推广 |
| 东南亚 | insufficient | 只有评论来源，不生成推荐 |
| 中东及部分伊斯兰文化地区 | insufficient | 无案例，不生成推荐 |
| 拉丁美洲 | insufficient | 无案例，不生成推荐 |

## 5. 重要限制

- 评论来源国家 ≠ 目标国受众偏好；
- 评论数量/情感 ≠ 传播成功；
- 乐器/曲风相似 ≠ 区域适配已验证；
- 5 条映射 ≠ 全库关联；
- 六个区域的文化背景仍需按国别做来源核验；
- 区域策略是研究草案，不是效果承诺。

## 6. 输出

- `research/analysis/p11-region-profile.csv`
- `research/analysis/p11-region-evidence.csv`
- `research/analysis/p11-music-region-matching.csv`
- `research/analysis/p11-region-music-matrix.csv`
- `research/analysis/p11-regional-strategy-draft.json`
