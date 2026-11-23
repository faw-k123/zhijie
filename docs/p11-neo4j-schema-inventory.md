# P11 Neo4j 现有图谱结构清单

## 1. 状态

Neo4j 服务不可用，Bolt 7687 未监听。

因此本文件只记录“未读取”，不假设任何节点标签、关系类型或属性。

## 2. 现有结构

```text
节点标签：unknown
关系类型：unknown
属性键：unknown
节点数量：unknown
关系数量：unknown
用户节点：unknown
音乐节点：unknown
用户类别：unknown
音乐类别：unknown
```

## 3. 不能做的事

- 不能声称已存在某个标签；
- 不能声称已有 `User`/`Music` 节点；
- 不能声称已有用户—音乐关系；
- 不能凭项目记忆编造图谱结构。

## 4. 服务恢复后的只读检查清单

```text
CALL db.labels()
CALL db.relationshipTypes()
CALL db.propertyKeys()
MATCH (n) RETURN labels(n), count(*)
MATCH ()-[r]->() RETURN type(r), count(*)
```

只读执行，结果写入待审清单。

## 5. 结论

当前只能做逻辑设计，不能做实际图谱映射。
