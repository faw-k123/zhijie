# 国际传播专项：六国实测工作台说明

> 版本：v1.7 候选测试层  
> 状态：功能可用；真实六国反馈尚未导入；正式排名关闭  
> 正式数据：`active_version=v1.7`，本功能不写入正式版本

## 1. 量表与八项音乐的对应

| 八项 | 直接测量来源 | 处理 |
|---|---|---|
| 情绪共鸣 | `emotional_resonance` | 直接使用，1—5 |
| 音色辨识 | `timbre_identity` | 直接使用，1—5 |
| 旋律可进入性 | `melody_accessibility` | 直接使用，1—5 |
| 文化故事性 | `cultural_story` | **新增字段**，1—5 |
| 跨文化改编空间 | `adaptation_space` | **新增字段**，1—5 |
| 视觉表现力 | `visual_expressiveness` | **新增字段**，1—5 |
| 时代主题相关性 | `era_theme_relevance` | **新增字段**，1—5 |
| 既有传播证据 | 经审核的证据分 | **不由受众量表替代** |

原有的 `cultural_understanding`、`save_share_intent`、`learning_intent` 保留为辅助测量，不作为八项中的替代项。

### 不做的换算

- 不把“文化理解”直接当作“文化故事性”；
- 不把收藏/分享意愿当作“既有传播证据”；
- 不把播放量、点赞量或视频标题换算成接受度；
- 没有直接测量时保持 null，并阻止正式评分。

## 2. 建议门槛（尚未审批）

```yaml
min_per_variant: 20          # 每个国家×曲目×版本
min_per_cell: 40             # 每单元原版+适配版
variant_balance_tolerance: 0.25
min_country_total: 120
min_country_cells: 12
min_completion_rate: 70
max_missing_ratio: 0.20
winsorize_low: 0.01
winsorize_high: 0.99
cross_country_min_countries: 3
cross_country_min_cells: 12
```

这些是**建议值**，配置状态为 `proposed`。在负责人审批前：

- 不开放正式排名；
- 可以生成描述性统计；
- 可以生成待审批评分草稿。

## 3. 计算公式（统一 0—100）

问卷 1—5 先转 0—100：

```text
survey_100 = (mean_1_5 - 1) / 4 × 100
```

八项等权（各 0.125）；证据分本身为 0—100：

```text
score_100 = Σ(survey_100_i × 0.125) + evidence_0_100 × 0.125
```

最终必须满足 `0 ≤ score_100 ≤ 100`；越界直接报错，不截断。

前提：

1. 原版/适配版各达到最低样本量；
2. 版本差异不超过 25%；
3. 七项受众测量均达到最低有效样本；
4. 既有证据分存在且经审核；
5. 八项完整，None 不参与计算。

缺失、样本不足或证据缺失时，`formal_score = null`，不补 0。

## 4. 跨国汇总

先在国家内按曲目×版本聚合，再对国家等权：

```text
cross_country_score = mean(各达标国家的单元分)
```

不是把所有个体反馈混在一起按样本量加权，避免样本量大的国家支配结果。

## 5. 数据分层

```text
research/candidates/v1.7-six-country-pilot/
├── batches/<batch_id>/
│   ├── raw_deidentified.json
│   ├── clean.json
│   ├── rejected.json
│   ├── errors.csv
│   └── metadata.json
└── scores/<score_id>.json
```

- 原始层：去标识化后的原始行；
- 清洗层：通过校验且同意的行；
- 拒绝层：缺失、重复、未同意、越界等；
- 不覆盖，只新增批次；
- 文件摘要为 SHA256 canonical JSON；
- 批次审批后才可进入评分草稿。

## 6. 状态

```text
not_started             未开始
descriptive_only        仅描述
insufficient_sample     样本不足
variant_imbalance       版本不平衡
incomplete_measurement  测量不完整
awaiting_evidence       缺证据分
eligible_for_review     可评审
pending_approval        评分待审批
approved_candidate      候选分已审批，未发布
published               当前正式版本
superseded              已被新版本替代
revoked                 候选已撤销
revoked_published       正式版本已撤销
```

## 6.1 身份与权限

- 导入、证据录入：`operator`；
- 门槛审批、批次审批、证据审批、评分审批、发布、撤销：`approver`；
- `admin` 可执行全部；
- 令牌由服务端签发：`python manage.py issue_pilot_token <username> <role>`；
- 不接受请求体中的 `approver`/`operator` 姓名；
- 无令牌 401，角色不符 403。

## 6.2 证据分

证据分独立录入，0—100，必须包含来源和规则版本；提交后待审批。审批后只有一个 active 证据分，旧版本 superseded。未审批时正式评分为 null。

## 6.3 发布版本

- 待审批评分 → 已审批候选分 → 正式发布；
- 发布时旧 active 版本变为 superseded；
- 排名只读取 active/published 版本；
- 撤销当前版本后排名立即关闭，不恢复旧版本。

## 7. 接口

```text
GET  /api/research/pilot/config/
POST /api/research/pilot/config/submit/        operator/approver
POST /api/research/pilot/config/approve/       approver
GET  /api/research/pilot/overview/
POST /api/research/pilot/import/               operator
GET  /api/research/pilot/batches/
POST /api/research/pilot/batches/<id>/approve/ approver
POST /api/research/pilot/aggregate/
GET  /api/research/pilot/evidence/
POST /api/research/pilot/evidence/              operator
POST /api/research/pilot/evidence/<id>/approve/ approver
POST /api/research/pilot/evidence/<id>/revoke/  approver
GET  /api/research/pilot/scores/
POST /api/research/pilot/scores/               operator
GET  /api/research/pilot/scores/<id>/
POST /api/research/pilot/scores/<id>/approve/  approver
POST /api/research/pilot/scores/<id>/revoke/   approver
POST /api/research/pilot/scores/<id>/publish/  approver
POST /api/research/pilot/published/<version>/revoke/ approver
GET  /api/research/pilot/rankings/
```

## 8. 前端

```text
/research/pilot
```

六国实测工作台：

- 120 单元进度；
- 国家/曲目/版本筛选；
- 原版/适配版样本数；
- 样本不足、测量不完整、待证据、待审批状态；
- 开放回答与文化风险；
- 批次导入、批次审批、待审批评分、撤销；
- CSV 和 Markdown 报告导出。

## 9. 当前真实状态

```text
120 单元：0 条已导入真实量表反馈
20 条既有受众反馈：质性证据，不是 1—5 量表响应，未用于填充 120 单元
20 首候选音乐：八项评分为 null
已审批证据分：0
候选评分：0
正式发布版本：0
正式排名：关闭
```

这表示系统已具备测试、清洗、聚合和审批能力，不代表六国真实测试已经完成。
