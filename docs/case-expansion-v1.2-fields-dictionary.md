# v1.2 第一阶段候选表 · 字段数据字典

- 版本：`v1.2-candidates-rev.1`（2026-11-01）
- 适用文件：`case-expansion-v1.2-screening.csv`、`case-expansion-v1.2-evidence-chain.csv`（两文件字节一致）
- 数据对象：第二批海外案例候选 **36 条 × 46 列**（35 个原有列 + 11 个新增列）
- 不适用范围：`research/data/v1.0`、`research/data/v1.1` 的正式数据使用 `data-contract-v1.md` 的另一套字典，本字典不适用于正式案例数据
- 配套文件：`case-expansion-v1.2-revision-changes.csv`（逐单元格变更）、`case-expansion-v1.2-revision-summary.json`（可复算统计）

## 0. 通用约定

| 约定 | 说明 |
|---|---|
| 空值 | 空字符串表示"未核定/不适用/来源未给出"，不使用 `null`、`N/A`、`unknown` 字符串填单元格；日期精度未知时用 `event_date_precision=unknown` 表达 |
| 多值 | 只有 `evidence_scope` 允许 `A|B` 多值（顺序为"主要用途在前"），其余列均为单值 |
| 枚举 | 所有状态列只允许本字典列出的取值；新增取值必须先改本字典再改数据 |
| 大小写 | 枚举值全部小写 + 下划线 |
| 语言 | 说明性字段（`supports`、`verification_note`、`evidence_scope_detail` 等）用中文；枚举用英文 |
| 证据原则 | 任何 `*_status=verified` 必须能指向 `*_source` 中具体来源直接支持的内容；来源权威（高校/政府/主流媒体）**不构成**其未直接支持事实的核实依据 |

## 1. 标识与来源（10 列）

| 字段 | 类型/取值 | 含义 | 规则 |
|---|---|---|---|
| `candidate_id` | `CAND001`–`CAND036` | 候选编号 | 唯一；本版未新增/未删除候选 |
| `candidate` | 文本 | 候选名称（机构/乐团/个人） | 与来源标题一致 |
| `source_id` | `CANDxxx-S001` | 本行所依据的来源编号 | 唯一；一候选一行时固定为 `-S001` |
| `source_title` | 文本 | 来源标题原文 | 不改写 |
| `publisher` | 文本 | 来源发布机构 | — |
| `url` | URL | 来源链接 | 保序，不做短链 |
| `source_type` | `高校官网`/`乐团官网`/`机构官网`/`主流媒体`/`公共媒体`/`政府文化机构`/`学术论文`/`艺术中心档案`/`活动页`/`视频平台`/`公共图书馆`/`大学剧院`/`城市旅游官网`/`唱片机构`/`电台`/`高校学生组织`/`高校活动 PDF`/`乐团 PDF`/`学术/机构 PDF`/`地方媒体` | 来源载体类型 | 只描述载体，不直接等价于可靠性 |
| `source_published_at` | `YYYY-MM-DD` / `YYYY-MM` / `YYYY` / 空 | **来源自身**的发布或更新日期 | 来源未标注即留空；**不得**把演出日期写进本列 |
| `published_at`（deprecated） | 同上 | 旧列，混装了来源发布日期与演出日期 | 自本版起冻结，保留原值供追溯；新数据一律写 `source_published_at` |

## 2. 候选属性（6 列）

| 字段 | 类型/取值 | 含义 |
|---|---|---|
| `category` | `严格海外个人演奏候选`/`海外教育与机构传播`/`海外本土乐团演奏`/`跨文化个人创作` | 候选的研究类别 |
| `country` | 国家/地区名 | 候选所属或活动所在国家 |
| `instrument` | 文本（常含"待核"） | 涉及的中国乐器；不确定时标注"待核" |
| `activity` | 文本 | 活动/组织描述 |
| `activity_type` | `education`/`ensemble_performance`/`community_activity`/`research_only`/`individual_performance`/`cross_cultural_collaboration` | 活动类型 |
| `research_group` | `A`/`B`/`C`/`D` | 研究管理分组：A 严格个人候选；B 机构/教育；C 具体演出/乐团；D 重复、暂缓、跨文化合作 |

## 3. 候选管理状态与资格（3 列）

| 字段 | 类型/取值 | 含义 | 规则 |
|---|---|---|---|
| `status` | `eligible_for_extended_review`/`pending_evidence`/`duplicate`/`excluded` | **首轮筛选池状态**（进入扩展复核队列 / 待补证 / 重复 / 排除） | 本版不变，仍为 21/11/3/1 |
| `overall_status` | `extended_lead`/`pending_evidence`/`duplicate`/`excluded` | 六项证据链的综合审核结论 | 与 `status` 分开，不合并 |
| `strict_sample_status` **新增** | `pending`/`not_eligible`/`eligible` | **严格样本资格**：是否可作为"海外个人 + 中国乐器 + 海外演出 + 可核来源"的严格个人案例 | 本批 `eligible`=0；`pending`=6（CAND024/026/027/028/032/033）；其余 `not_eligible` |
| `extended_sample_status` **新增** | `eligible`/`eligible_cross_cultural_only`/`pending_more_evidence`/`duplicate_reference` | **扩展样本资格**：可进入扩展研究（机构/乐团/教育/研究）的范围 | 与 `status` 解耦：`status=excluded` 的 CAND031 仍可 `eligible_cross_cultural_only` |

> 关键区分：`strict_sample_status` 判"能不能当严格个人案例"，`extended_sample_status` 判"能不能进扩展研究"。机构/乐团案例只在扩展侧取值，不得因 `overall_status=extended_lead` 就视为严格个人。

## 4. 身份（3 列，其中 1 列废弃）

| 字段 | 类型/取值 | 含义 | 规则 |
|---|---|---|---|
| `organization_status` **新增** | `verified`/`partial`/`unverified`/`not_applicable` | 候选作为**机构/团体**的存在性与身份状态 | `verified` 需来源为该机构自述页或官方登记页，且 `evidence_scope` 含 `organization_existence`；个人候选填 `not_applicable` |
| `performer_identity_status` **新增** | `verified`/`partial`/`unverified`/`not_applicable` | 候选作为**具名演奏者个人**的身份状态（国籍/身份口径是否可核） | 机构/团体候选若无具名身份主张填 `not_applicable`，**不得**因机构核实而填 `verified` |
| `identity_status`（deprecated） | 旧值：`organization_verified`/`verified`/`partial`/`unverified` | 旧列，混用机构与个人身份 | 自本版起冻结，不再新增；新判断写上面两列 |

判定口径：

- 机构候选：`organization_verified` **不是**个人身份已核实的依据；CAND001/002 等 12 条机构案只有机构层证据。
- 个人候选：`verified` 仅当来源直接给出可核身份（姓名 + 身份描述 + 行为），本批仅 CAND025（美国学生，视频明确）。

## 5. 六项证据状态（12 列）

| 字段 | 取值 | 含义 |
|---|---|---|
| `identity_status`/`identity_source` | verified/partial/unverified + `CANDxxx-S0xx` | 身份证据 |
| `instrument_status`/`instrument_source` | 同上 | 中国乐器证据 |
| `performance_status`/`performance_source` | `scheduled`/`program_listed`/`performed_confirmed`/`partial`/`unverified` + 来源 | 实际演奏证据 |
| `location_status`/`location_source` | `verified`/`verified_china`/`partial`/`unverified` + 来源 | 海外地点证据；`verified_china` 表示"地点已核实但在中国境内"，**不算海外** |
| `date_status`/`date_source` | `verified`/`partial`/`unverified` + 来源 | **演出/活动日期**证据；具体到日=`verified`，仅年/月或有时间线索无可用日期=`partial`，无=`unverified` |
| `outcome_status`/`outcome_source` | `verified`/`partial`/`unverified` + 来源 | 传播结果证据；本批 36 条全部 `unverified` 或 `partial` |

`performance_status` 细则：

| 取值 | 含义 | 不表示 |
|---|---|---|
| `scheduled` | 有演出安排/票务/活动公告 | 不表示演出已完成 |
| `program_listed` | 已列入节目单（含演奏者/曲目） | 不自动等于现场完成 |
| `performed_confirmed` | 有演出后报道、录像等事后材料 | — |
| `partial` | 有部分演奏事实 | — |
| `unverified` | 无法确认 | — |

一致性规则：任何非 `unverified` 的 `*_status` 必须有对应的 `*_source`；没有来源支持的事实一律降为 `unverified`。

## 6. 日期（3 列新增 + 1 列废弃）

| 字段 | 类型/取值 | 含义 |
|---|---|---|
| `source_published_at` **新增** | `YYYY-MM-DD`/`YYYY-MM`/`YYYY`/空 | 来源发布日期 |
| `event_date` **新增** | `YYYY-MM-DD`/`YYYY-MM`/`YYYY`/空 | 演出或活动发生（或公告举办）的日期 |
| `event_date_precision` **新增** | `day`/`month`/`year`/`unknown` | `event_date` 的精度；无日期时固定 `unknown` |
| `published_at`（deprecated） | — | 旧列混装两类日期，已冻结 |

规则：

1. 来源发布日期与演出日期**必须分开**；旧列 `published_at` 中被误写成演出日期的（CAND010、CAND035、CAND030），本版已迁到 `event_date`，`source_published_at` 留空。
2. 无法核实的日期留空，并在 `evidence_scope_detail` 或 `verification_note` 写明"来源未给出具体日期"。
3. 日期精度必须与取值一致：`2026` 配 `year`，`2022-07` 配 `month`，`2025-05-17` 配 `day`。

## 7. 证据范围（2 列）

| 字段 | 类型/取值 | 含义 |
|---|---|---|
| `evidence_scope` | 多值，`A|B` | 本来源直接支持的事实范围 |
| `evidence_scope_detail` **新增** | 文本 | 逐范围说明"支持什么 / 不支持什么" |

字典（9 个合法标签，缺一不可）：

| 标签 | 定义 | 典型证据 | 不能证明 |
|---|---|---|---|
| `organization_existence` | 机构/团体存在并开展相关活动 | 官网介绍、机构登记、官方活动页 | 个人国籍、单场演出完成 |
| `event_announcement` | 活动已公告（时间/地点/参与方） | 活动页、票务页、新闻稿 | 演出已完成、上座率 |
| `event_program` | 节目单（含曲目/演奏者） | 音乐会节目单 PDF | 演出已完成 |
| `performance_record` | 演出记录（演出后材料） | 演出后报道、录像、档案条目 | 受众认可、传播效果 |
| `performer_identity` | 演奏者身份线索 | 人物访谈、艺术家页 | 国籍（除非来源明示） |
| `audience_feedback` | 受众反馈 | 评论、留言、报道中的观众反应 | 本批 0 条使用 |
| `long_term_impact` | 长期传播影响 | 多年数据、持续报道、影响评估 | 单场活动不能支撑（CAND021 已撤） |
| `research_record` | 学术/研究记录 | 论文、研究档案 | 个体演奏事实 |
| `community_activity_record` **本版新增** | 社区活动记录（探访、社区演出、文化活动） | 使领馆/社区报道 | 专业演出与传播效果 |

新增 `community_activity_record` 的同步更新：本字典第 7 节、`case-expansion-v1.2-evidence-chain.md` §0.3 分布表、`case-expansion-v1.2-status-report.md` 均已加入该标签；仅 CAND019 使用。

## 8. 可靠性与事实支持（3 列新增 + 1 列废弃）

| 字段 | 取值 | 含义 | 规则 |
|---|---|---|---|
| `source_reliability` **新增** | `high`/`medium`/`low` | **来源本身**的可靠性 | 官网/官方机构=high；地方媒体、聚合页、未逐页核的 PDF=medium；活动聚合站=low |
| `fact_support_level` **新增** | `direct`/`partial`/`indirect`/`none` | 该来源对 `supports` 所载事实的支持程度 | direct=来源正文直接陈述；partial=只支持一部分或需推断；none=不支持（出现即须改事实） |
| `fact_verification_status` **新增** | `verified`/`partial`/`unverified` | 该事实的核实状态 | 只能按来源直接支持的内容给值；**来源权威 ≠ 事实已核实** |
| `reliability`（deprecated） | `高`/`中`/`低` | 旧列 | 与 `source_reliability` 一一映射，保留供追溯 |

三者的关系（必须分开判断）：

```
source_reliability = high        （来源是高校官网）
fact_support_level = partial     （但只支持"机构存在"，不支持"个人演奏"）
fact_verification_status = partial（因此该事实只是部分核实）
```

## 9. 说明性字段（5 列）

| 字段 | 含义 | 规则 |
|---|---|---|
| `supports` | 该来源直接支持的事实（一句话） | 写"来源说了什么"，不写推断 |
| `evidence_gap` | 仍缺什么证据 | 与 `next_action` 对应 |
| `next_action` | 下一步动作 | 不得写成"可直接纳入" |
| `verification_note` | 核验备注 | 记录口径判断与已知限制 |
| `dedupe` | `new` 或 `CASE00x` | 与 v1.1 正式案例的去重结果 |

## 10. 本版字段变更清单

| 变更 | 字段 | 说明 |
|---|---|---|
| 新增 | `strict_sample_status`、`extended_sample_status` | 拆分严格/扩展样本资格 |
| 新增 | `organization_status`、`performer_identity_status` | 拆分机构状态与个人身份 |
| 新增 | `source_published_at`、`event_date`、`event_date_precision` | 拆分来源日期与演出日期 |
| 新增 | `source_reliability`、`fact_support_level`、`fact_verification_status` | 拆分来源可靠性与事实支持程度 |
| 新增 | `evidence_scope_detail` | 逐范围说明支持事实 |
| 扩展 | `evidence_scope` 字典 | 增加 `community_activity_record` |
| 冻结 | `published_at`、`identity_status`、`reliability` | 保留原值，不再写入新判断 |

## 11. 复算方式

```bash
python build_revision.py     # 读取原始 CSV（备份目录）→ 生成修订 CSV + 变更日志 + summary.json
```

`case-expansion-v1.2-revision-summary.json` 中的每个分布都可由修订 CSV 直接重算（按 `evidence_scope` 的多值拆分计数）。校验项包括：行数 36、去重新增 33、`candidate_id`/`source_id` 唯一、非 `unverified` 状态必须有来源、枚举合法、`organization_status=verified` 必须伴随 `organization_existence` 范围。
