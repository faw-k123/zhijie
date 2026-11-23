# P16.5 歌曲—区域证据关联审计

## 1. 矩阵基线

```text
6 个目标区域 × 302 首 = 1,812 条
有案例支持：5
unknown：1,807
```

## 2. 区域分布

| 区域 | 曲目级证据 | unknown |
|---|---:|---:|
| 北美 | 0 | 302 |
| 欧洲 | 5 | 297 |
| 东亚 | 0 | 302 |
| 东南亚 | 0 | 302 |
| 中东及部分伊斯兰文化地区 | 0 | 302 |
| 拉丁美洲 | 0 | 302 |

5 条全部为：

```text
CASE008（英国/欧洲）
music_id 23、158、26、28、29
performance_status = program_listed
```

## 3. 证据等级

本阶段只使用：

```text
explicit_song_case_program：5
no_evidence：1,807
```

没有：

- 用同乐器推断区域适配；
- 用同音乐类别推断区域偏好；
- 用“某国存在中国音乐机构”推断所有曲目适合该国；
- 把澳大利亚/新西兰强行归入六区域；
- 把节目单当作实际演出。

## 4. 区域建议含义

欧洲的 5 条只能标记：

```text
conditional_program_only
```

即“有节目单曲目级关联”，不是“已验证欧洲受众接受”。

其他五个区域没有曲目级证据，不能生成推荐。

## 5. 输出

- `p16_song_region_evidence.csv`（1,812 行）
- [区域证据覆盖图](<research/analysis/p16/charts/region_evidence_coverage.svg>)
