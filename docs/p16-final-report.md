# P16 最终报告：302首传统音乐海外传播潜力与案例证据审计

> 基线：v1.6  
> 只读审计；未修改数据库、案例、映射和正式版本。

## 1. 执行范围与版本

```text
active_version：v1.6
歌曲：302
案例：40
来源关系：62
指标记录：400
有效评分：94
null：306
```

v1.6 文件与 manifest 哈希未变化。

## 2. 数据完整性

```text
歌曲：302
分类：4（器乐/戏曲/民歌/说唱）
评论：192,882
sentiment 有效：134,093
sentiment 缺失：58,789（30.48%）
情感时间序列：81,388
```

基础字段缺失：

```text
audio_url：3
cover_url：83
genre：0
```

评论：

```text
重复 comment.id 分组：14,628
孤立 song_id：0
likes=2147483647：2
```

未按 comment.id 去重；缺失情感未填 0。

## 3. 歌曲—案例关联

```text
明确关联 A：5
弱关联 B：0
待核实 C：0
无关联 D：297
明确关联比例：5/302 = 1.66%
关联案例：1（CASE008）
关联来源：1（C008-S001）
重复关联：0
```

5 首：

```text
23 平沙落雁
158 梅花三弄
26 流水
28 酒狂
29 阳关三叠
```

全部为 `program_listed`，`performance_confirmed=NO`。  
A 只表示具体曲目节目单关联，不表示实际演出或传播效果。

## 4. 八因素可计算性

```text
完整可计算：0
部分可计算：5
暂不可计算：297
```

因素覆盖：

```text
available：0
partial：20（4因素×5首CASE008）
unavailable：2,396
```

原因：

- 无音色/旋律/视觉特征；
- 评论情感不作为情感普适性因素分；
- story/cross/era 只有 CASE008 案例级评分；
- 既有案例反馈只有节目单，无受众反馈。

未重新分配权重。

## 5. 评论与情感辅助分析

评论国家前几：

```text
中国 104,463（54.16%）
未知 18,601（9.64%）
美国 11,300（5.86%）
日本 9,532（4.94%）
韩国 7,922（4.11%）
```

限制：

- 评论来源国家不是目标受众；
- 情感缺失 30.48%；
- 评论量不证明传播成功；
- 不同歌曲评论量不能直接排名。

## 6. 歌曲—区域证据

```text
区域矩阵：1,812
有曲目级证据：5（欧洲/CASE008）
unknown：1,807
其他五区域：0
```

5 条仅标记：

```text
conditional_program_only
```

不能把节目单当作欧洲受众接受。

## 7. 302首分析准备度

| 类别 | 数量 |
|---|---:|
| 第一类：完整可算 | 0 |
| 第二类：部分指标 | 0 |
| 第三类：有明确案例关联但数据不完整 | 5 |
| 第四类：暂不具备可靠评价条件 | 297 |

第三类 5 首即 CASE008 五首曲目。  
第二类为 0，因为评论情感未被当作已验证的潜力因素。

## 8. 核心发现

1. 音乐库 302 首完整可读，但歌曲级案例连接只有 5/302。
2. 5 条都是 CASE008 节目单关联，不能升级为演出完成。
3. 没有一首具备八因素完整数据，不能生成综合潜力分。
4. 音色、旋律、视觉三类数据完全缺失。
5. 评论数据量大，但缺 user_id、情感缺失 30.48%，不能做传播效果推断。
6. 区域矩阵只有欧洲 5 条曲目级证据，其余 1,807 条 unknown。
7. 当前不能做逐曲排名，也不能据此形成区域推荐。

## 9. 数据局限与风险

- 5/302 关联覆盖极低；
- 5 条全部 program_listed；
- 评论 id 重复 14,628 组；
- 情感缺失 30.48%；
- 3 首缺音频、83 首缺封面；
- 无音色/旋律/视觉特征；
- 无受众反馈；
- 无 activity_status；
- 62 条案例来源关系不等于 62 个独立来源；
- 区域证据仅欧洲 5 条。

## 10. 后续补充建议

按优先级：

1. 为 CASE008 五首曲目补充演出后记录/节目单定位；
2. 建立歌曲级音色、旋律、视觉特征；
3. 为更多歌曲建立可追溯歌曲—案例映射；
4. 统一 comment 去重规则，但不按 id 直接删除；
5. 补情感缺失，保留缺失标记；
6. 建立受众反馈/上座/互动数据；
7. 补 activity_status；
8. 再讨论逐曲传播潜力模型。

## 11. 阶段验收结论

```text
CONDITIONAL_PASS
```

原因：

- 数据完整性和关联审计完成；
- 关键限制明确；
- 5 条明确关联可追溯；
- 但没有完整八因素数据，不能做逐曲综合分或排名。

## 12. 验收清单

- [x] active_version 仍为 v1.6
- [x] v1.6 文件及 manifest 哈希未变化
- [x] 302 首歌曲及业务表未修改
- [x] 未新增或修改案例
- [x] 未自动创建歌曲—案例关联
- [x] 未把 null 转换为 0
- [x] 未重新分配权重
- [x] 明确关联可追溯
- [x] A/B/C/D 严格区分
- [x] 区域建议有 match_reason
- [x] 评论/情感未被当作传播成功
- [x] 报告、CSV、图表已生成
- [x] 最终结论明确

## 13. 输出

### 报告

- `docs/p16_data_integrity_report.md`
- `docs/p16_mapping_coverage_report.md`
- `docs/p16_potential_model_audit.md`
- `docs/p16_comment_data_limitations.md`
- `docs/p16_region_recommendation_audit.md`
- `docs/p16_readiness_summary.md`

### 数据

- `research/analysis/p16/p16_song_data_audit.csv`
- `research/analysis/p16/p16_relation_integrity.csv`
- `research/analysis/p16/p16_song_case_mapping_audit.csv`
- `research/analysis/p16/p16_potential_factor_coverage.csv`
- `research/analysis/p16/p16_potential_computability.csv`
- `research/analysis/p16/p16_song_comment_statistics.csv`
- `research/analysis/p16/p16_song_emotion_statistics.csv`
- `research/analysis/p16/p16_song_region_evidence.csv`
- `research/analysis/p16/p16_song_readiness_classification.csv`

### 图表

`research/analysis/p16/charts/` 5 张 SVG。
