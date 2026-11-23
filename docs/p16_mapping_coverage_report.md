# P16.2 歌曲—案例关联审计

## 1. 关联总量

```text
302 首歌曲
明确关联（A）：5 首
弱关联（B）：0
待核实（C）：0
无关联（D）：297
明确关联比例：5/302 = 1.66%
关联案例：1（CASE008）
关联证据来源：1（C008-S001）
重复关联：0
```

## 2. 五条明确关联

| song_id | 曲目 | case_id | 证据类型 | 演出状态 |
|---:|---|---|---|---|
| 23 | 平沙落雁 | CASE008 | program_listed | 未确认 |
| 158 | 梅花三弄 | CASE008 | program_listed | 未确认 |
| 26 | 流水 | CASE008 | program_listed | 未确认 |
| 28 | 酒狂 | CASE008 | program_listed | 未确认 |
| 29 | 阳关三叠 | CASE008 | program_listed | 未确认 |

来源：

```text
C008-S001
https://www.oushinet.com/static/content/ouzhong/ouzhongnews/2025-07-18/app_1395807074034145417.html
```

## 3. A 类的严格含义

A = 来源能明确证明 CASE008 的节目单包含该具体曲目。  
A **不表示**：

- 实际演出完成；
- 现场反馈；
- 受众接受；
- 传播效果。

`performance_confirmed=NO` 对所有五条成立。

## 4. 为什么没有 B/C

- B 需要“同乐器/同类别但非具体曲目”的可追溯关联；本阶段没有把类别相似自动升级为关联。
- C 需要关联线索但来源不足；五条已有明确节目单来源，不列为 C。
- 没有用曲名相似、乐器相同或文化主题相似自动新增 B/C。

## 5. 无关联

```text
297 首歌曲没有可核查的歌曲—案例关联
```

不能从歌曲分类、乐器、地区或评论来源推断它们“适合”某案例或某区域。

## 6. 输出

- `p16_song_case_mapping_audit.csv`
- [关联覆盖图](<research/analysis/p16/charts/song_case_mapping_coverage.svg>)
