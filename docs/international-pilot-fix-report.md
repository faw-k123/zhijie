# 六国实测工作台修复报告

> 日期：2026-11-08  
> 状态：修复完成；真实测试数据仍为 0；正式排名关闭

## 1. 修复清单

| 问题 | 修复 |
|---|---|
| 1—5 问卷与 0—100 证据分混算 | 问卷先转 0—100，八项等权，最终强制 0—100 |
| 证据分来自 `music_scores` 且可为空 | 独立 `evidence/` 候选层：来源、规则版本、录入人、审批人、撤销历史 |
| 客户端自填 approver/operator | 服务端 Bearer 令牌；角色 operator/approver/admin |
| 请求体伪造姓名 | 视图只读取令牌身份，忽略 body 姓名 |
| 跨批次重复计数 | 导入冲突隔离 + 审批阻断 + 聚合防御性去重 |
| 只有候选评分 | 增加 `approved_candidate` 与 `published` 分离 |
| 多个历史评分重复排名 | 只读 active/published 版本；旧版本 `superseded` |
| 撤销后自动恢复旧版本 | 撤销当前版本后 active 指针删除，不恢复 |
| 配置字段未全部生效 | `min_per_cell`、`max_missing_ratio`、`cross_country_min_cells` 等参与判断 |
| 配置只能一键批准 | `config_versions/`：提交、校验、审批、SHA-256、不可变 |
| 前端默认 owner/operator | 删除；改为服务端令牌输入，无默认身份 |
| 候选分显示为正式分 | 无 active 发布版本时显示“候选分（未发布）” |
| 导航重复 | 删除重复的六国实测工作台链接 |

## 2. 统一量纲

```text
survey_100 = (survey_mean_1_5 - 1) / 4 × 100
score_100 = Σ(survey_100_i × 0.125) + evidence_0_100 × 0.125
0 ≤ score_100 ≤ 100
```

问卷均值每项先 winsorize 1%/99%；证据分独立 0—100。  
证据分未审批、为空或越界时，`formal_score = null`。

## 3. 身份与权限

令牌签发：

```bash
python manage.py issue_pilot_token <username> operator
python manage.py issue_pilot_token <username> approver
python manage.py issue_pilot_token <username> admin
```

权限：

```text
operator：导入、录入证据、生成评分草稿
approver：门槛审批、批次审批、证据审批、评分审批、发布、撤销
admin：全部
```

未登录 401；角色不符 403。  
读接口（overview / aggregate / rankings / scores）保持研究页面只读公开。

## 4. 证据分与发布流程

```text
证据分提交（operator）→ 待审批 → approver 审批
评分草稿（operator）→ 待审批 → approver 审批为 approved_candidate
→ approver 发布 published → 旧 active 变 superseded
→ 撤销 published → 排名立即关闭，不恢复旧版本
```

记录：

- 证据分：来源、规则版本、录入人、审批人、时间、历史；
- 评分：输入批次、门槛版本/摘要、公式、审批人/时间；
- 发布版本：发布人/时间、完整历史、active 指针。

## 5. 重复反馈

导入时：

- 检查同批次重复；
- 检查所有候选/已审批批次 `response_id`；
- 冲突写入 `conflicts.csv`（新批次、反馈编号、原批次）；
- 冲突记录进入拒绝层；
- 有冲突的批次不可审批；
- 聚合再做一次防御性去重并返回 `defensive_duplicate_rows_excluded`。

## 6. 门槛版本

建议值仍为：

```text
min_per_variant=20
min_per_cell=40
variant_balance_tolerance=0.25
min_country_total=120
min_country_cells=12
min_completion_rate=70
max_missing_ratio=0.20
winsorize=1%/99%
cross_country_min_countries=3
cross_country_min_cells=12
```

这些仍是**建议值**，尚未获得负责人确认。  
审批后生成不可变配置版本和 SHA-256；修改必须新建版本。

## 7. 测试

```text
backend：43 passed
pilot 专项：12 passed
frontend type-check：passed
frontend build：passed
```

覆盖：身份、伪造姓名、证据量纲、越界、未审批、重复、跨批次、聚合去重、发布、superseded、撤销、配置字段、前端构建。

## 8. 当前真实状态

```text
真实量表反馈：0
证据分：0
候选评分：0
正式发布版本：0
正式排名：关闭
```

这不是测试完成，而是正式测试基础设施已可用。
