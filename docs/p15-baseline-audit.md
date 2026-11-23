# P15.1 数据基线复核

> 基线：v1.6，只读分析。  
> active_version 仍为 v1.6。

## 1. 总量

```text
案例：40
来源关系：62
指标记录：400
有效评分：94
null：306
零分：0
```

## 2. 样本结构

```text
strict_individual：2
extended_cross_cultural：36
pending_review：2
```

## 3. 逐案校验

- 40 个案例均有 10 项指标记录；
- 无重复 case_id；
- 无重复 (case_id, indicator_id)；
- 无未映射指标；
- 来源 ID 均可关联；
- CASE007 仍为 `pending_review`，`strict_sample_eligible=false`；
- CASE039、CASE040 仍为扩展跨文化，15 有效 / 5 null。

## 4. 哈希

分析前后重新计算：

- v1.6 五个数据文件 SHA256 未变化；
- 主 manifest 未变化；
- active_version 仍为 v1.6；
- v1.5 历史文件未修改。

## 5. 结论

```text
PASS
```

数据基线满足 P15 分层比较要求。
