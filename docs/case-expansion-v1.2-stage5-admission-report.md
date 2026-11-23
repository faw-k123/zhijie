# v1.2 正式准入报告

> 结论：v1.2 已创建并激活；新增 26 个扩展案例；严格个人新增 0。

## 1. 准入结果

| 状态 | 数量 | 说明 |
|---|---:|---|
| `approved_strict` | 0 | CAND024 仍缺演出完成证据 |
| `approved_extended` | 26 | 已写入 v1.2 |
| `pending_evidence` | 7 | 不进入 v1.2 |
| `excluded` | 3 | 与既有案例重复 |

## 2. 正式编号

- 保留 CASE001–CASE010；
- CASE011–CASE036 对应 26 个扩展候选；
- 映射保存在 `research/data/v1.2/cases.json` 的 `candidate_id` 字段；
- 没有重复编号；
- 没有给 7 个 pending 或 3 个 excluded 分配 CASE 编号。

## 3. 主体类型

```text
overseas_institution_education   16
foreign_individual_cross_cultural 9
overseas_institution_ensemble     8
cross_cultural_ensemble           3
```

## 4. 严格个人

CAND024 仍是严格复核候选：

- 加拿大身份有 CMC 标题支持；
- 古筝二人演出有 Western Front program；
- 实际演出状态仍为 `program_listed`；
- 没有演出后记录；
- 因此不进入 v1.2 严格个人样本。

严格个人正式数仍为 2（CASE005、CASE006）。

## 5. 扩展案例边界

- 26 个扩展案例全部 `review_status=B`、`display_allowed=true`；
- 但 `strict_sample_eligible=false`；
- 指标全部 null；
- 不参与排名；
- 不生成传播效果结论；
- 不写成严格个人演奏案例。

## 6. 版本状态

```text
active_version = v1.2
v1.2 status = reviewed
v1.1 保留 reviewed
v1.0 保留 reviewed
```

v1.1 原始文件未覆盖。
