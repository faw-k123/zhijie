# P11 图谱关系设计

> 设计层，不执行写入。  
> 只有 P8 审查通过的 5 条音乐—案例映射可以作为正式关系候选。

## 1. 节点

| 逻辑标签 | 键 | 来源 | 状态 |
|---|---|---|---|
| Music | music_id | traditional_song / P10 | 302 |
| Case | case_id | v1.2 cases | 36 |
| Region | region_id | 六区域设计 | 6 |
| Source | source_id | cases.sources / P10 | 可追溯 |
| Scene | scene_id | 教育/音乐会/社区等 | 设计 |
| Evidence | evidence_id | P11 区域证据 | 设计 |

不建议在没有用户主键与授权的情况下创建 User 节点。

## 2. 关系

### 正式候选

```text
(Case)-[:CASE_PERFORMS_MUSIC {
  mapping_status: "verified",
  performance_status: "program_listed",
  source_ids: ["C008-S001"]
}]->(Music)
```

仅允许 5 条：

```text
CASE008 -> 23, 158, 26, 28, 29
```

`program_listed` 不能写成 `performed_confirmed`。

```text
(Case)-[:OCCURRED_IN_REGION]->(Region)
```

来源为案例 country/region；只证明活动发生地，不证明受众偏好。

```text
(Case)-[:SUPPORTED_BY]->(Source)
(Region)-[:HAS_EVIDENCE]->(Evidence)
```

### 探索性/未知

```text
(Music)-[:POTENTIAL_FOR_REGION {
  status: "exploratory" | "unknown",
  reason: ...
}]->(Region)
```

当前没有足够的区域受众证据，除 5 条 CASE008 的欧洲活动外，绝大多数应为 `unknown`，不应生成正式边。

```text
(Region)-[:HAS_SCENE]->(Scene)
```

需要区域证据支持，不能凭印象创建。

## 3. 正式/探索性边界

| 关系 | 状态 | 条件 |
|---|---|---|
| CASE_PERFORMS_MUSIC | verified | P8 mapping verified |
| CASE_OCCURRED_IN_REGION | verified | 案例来源有地点 |
| MUSIC_POTENTIAL_FOR_REGION | exploratory/unknown | 需区域证据；当前大多 unknown |
| REGION_HAS_CULTURAL_PROFILE | evidence-graded | 需来源 |
| USER_PREFERS_MUSIC | 不创建 | 无足够用户键/行为数据 |

## 4. 不写入

- 不写 Neo4j；
- 不修改现有节点/关系；
- 不创建 User 节点；
- 不把 5 条映射扩展成全库；
- 不把评论国家当区域偏好边。
