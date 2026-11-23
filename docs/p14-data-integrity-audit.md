# P14.1 v1.6 数据完整性审计

> 审计对象：active_version=v1.6  
> 审计方式：只读；不修改 v1.6、v1.5、active_version。

## 1. 总体数量

| 项目 | 结果 |
|---|---:|
| 案例 | 40 |
| 来源关系 | 62 |
| 指标记录 | 400 |
| 有效评分 | 94 |
| null | 306 |
| 新增零分 | 0 |
| warnings | 0 |

## 2. 结构检查

- 每个案例 10 项指标：通过；
- 40 × 10 = 400：通过；
- 无重复 `case_id`；
- 无重复 `(case_id, indicator_id)`；
- 无未映射指标；
- 62 个来源关系均可关联；
- CASE039、CASE040 各 10 条；
- CASE007 仍为 `pending_review`、`strict_sample_eligible=false`。

## 3. 样本结构

```text
strict_individual：2
extended_cross_cultural：36
pending_review：2
```

## 4. 新案例

```text
CASE039：9 有效 + 1 null
CASE040：6 有效 + 4 null
新增有效 15
新增 null 5
```

## 5. 哈希

分析前后重新计算：

- v1.6 五个数据文件 SHA256 未变化；
- 主 manifest SHA256 未变化；
- active_version 仍为 v1.6；
- v1.5 历史文件未修改。

## 6. 已确认的限制

- `activity_status` 仍缺失，40/40 为 `NOT_RECORDED`；
- 306 条 null 保持未知，不填 0；
- 严格个人样本只有 2 例。

## 7. 结论

```text
PASS
```

数据完整性满足 P14 描述性统计要求。
