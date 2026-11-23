# v1.2 第一阶段候选数据一致性修订 · 修订前后差异报告

- 版本：`v1.2-candidates-rev.1`（2026-11-01）
- 修订对象：`docs/case-expansion-v1.2-screening.csv`、`docs/case-expansion-v1.2-evidence-chain.csv`（两文件修订后仍字节一致）
- 修订前原件：`docs/_backup-v1.2-pre-revision-20261101/`
- 逐单元格记录：`docs/case-expansion-v1.2-revision-changes.csv`（386 条，含原值/新值/原因/来源依据）
- 未改动：`research/data/**`、`manifest.json`、`active_version`（仍为 `v1.1`）、v1.0/v1.1 正式数据、`cases.json`、任何评分

## 1. 修订范围与不变项

| 项 | 修订前 | 修订后 | 说明 |
|---|---|---|---|
| 候选行数 | 36 | 36 | 不增不减 |
| 列数 | 35 | 46 | 新增 11 列 |
| 去重后新增候选 | 33 | 33 | `dedupe=new` 计数不变 |
| `candidate_id` / `source_id` | 36 / 36 | 36 / 36 | 全部唯一，无重命名 |
| 候选管理状态 `status` | 21/11/3/1 | 21/11/3/1 | **未改**（eligible/pending/duplicate/excluded） |
| `overall_status` | 11/21/3/1 | 11/21/3/1 | **未改** |
| A/B/C/D 分组 | 6/14/8/8 | 6/14/8/8 | **未改** |
| 正式案例 | 0 | 0 | 本阶段不创建 |

## 2. 变更总量

- 变更单元格：**386**
- 按字段：

| 字段 | 变更数 | 性质 |
|---|---:|---|
| 9 个新列（`strict_sample_status`、`extended_sample_status`、`organization_status`、`performer_identity_status`、`source_published_at`、`event_date`、`event_date_precision`、`source_reliability`、`fact_support_level`、`fact_verification_status`、`evidence_scope_detail`） | 每列 36，共 324（其中 `source_published_at`、`event_date` 仅在实际有值时计入，见下） | 新增列赋值 |
| `date_status` | 14 | 按"演出日期"新口径重算 |
| `event_date` | 11 | 新增值（含从 `published_at` 迁入） |
| `evidence_scope` | 10 | 证据范围纠正 |
| `source_published_at` | 10 | 来源发布日期迁入 |
| `date_source` | 6 | 补齐/清空来源指针 |
| `instrument_status` | 5 | 无来源支持的 partial 降级 |
| `performance_source` | 4 | 补齐来源指针 |
| `performance_status` | 2 | 纠正 |
| 其余新列 | 见 CSV | — |

## 3. 六条指定候选的修订（任务书 §二）

### 3.1 CAND031 Wu Fei & Abigail Washburn —— 拆分严格/扩展资格

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `status` | `excluded` | `excluded`（不变） | 保持"不进入本轮扩展复核队列"的池状态，21 条口径不变 |
| `strict_sample_status` | 无此列 | `not_eligible` | Abigail 演奏班卓琴、非中国乐器；Wu Fei 为中国演奏者。不构成"外国个人演奏中国乐器"的严格案例 |
| `extended_sample_status` | 无此列 | `eligible_cross_cultural_only` | 保留跨文化合作扩展研究资格 |
| `performer_identity_status` | （旧 `identity_status=partial`） | `partial` | 仅 Wu Fei 的古筝身份可核，Abigail 不属于中国乐器演奏者 |
| `evidence_scope_detail` | 无 | 明确写"电台节目页确认 2026-10-08 访谈与演奏；Abigail 演奏班卓琴（非中国乐器），不构成严格案例" | 防止误读 |

> 结论：CAND031 **不进入 strict_individual**，但不再被简单标成"整体排除"，其跨文化合作价值由 `extended_sample_status=eligible_cross_cultural_only` 承载。

### 3.2 CAND033 Mona Li —— 保留 `program_listed`，不得写成已确认演出

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `performance_status` | `program_listed` | `program_listed`（不变） | 节目单只证明"列入曲目/演奏者"，不证明现场完成 |
| `evidence_scope` | `event_program` | `event_program`（不变） | 来源为乐团节目单 PDF |
| `date_status` | `verified` | `unverified` | 原值把"2022 演出季"当成演出日期；节目单未见具体场次日期 |
| `source_published_at` | `2022`（在旧 `published_at`） | `2022`（迁入新列） | 该年份是 PDF/演出季年份，属来源日期 |
| `verification_note` 补充 | "节目单明确 Mona Li 演奏古筝" | 改为"节目单列明其担任古筝演奏（演出前材料，不等于现场完成）" | 去掉"已演奏"暗示 |

### 3.3 CAND035 Bard East/West Ensemble —— 演出记录改为活动公告

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `evidence_scope` | `performance_record` | `event_announcement|organization_existence` | 来源是官网 `events/...` 活动页（演出前公告），不是演出后记录 |
| `event_date` | `2025-05-03`（在旧 `published_at`） | `2025-05-03` | 该日期是演出日期，迁入 `event_date` |
| `source_published_at` | — | 空 | 活动页未标注独立发布日 |
| `performance_status` | `scheduled` | `scheduled`（不变） | 公告 ≠ 完成 |

### 3.4 CAND034 Bard Chinese Ensemble —— 机构存在性 vs 活动公告

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `evidence_scope` | `performance_record` | `organization_existence` | 来源是乐团介绍页（`barduschinemusic.org/bard-chinese-ensemble`），无任何场次信息 |
| `performance_status` | `scheduled` | `unverified` | 原值 `scheduled` 却无 `performance_source`，属自相矛盾；该页不支持任何场次 |
| `organization_status` | （旧 `identity_status=unverified`） | `verified` | 该团介绍页由所属研究所自建站发布 |

### 3.5 CAND028 Nicholas Ng —— 核实 `performance_record` 是否成立

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `evidence_scope` | `performer_identity|performance_record` | `performer_identity` | ABC 访谈页只介绍"二胡演奏者/研究者"，页面没有任何具体演出场次 |
| `performance_status` | `partial` | `partial`（不变） | 保留"有部分事实"，但不升级为记录 |
| `date_status` | `partial` | `unverified` | 无演出日期 |

### 3.6 CAND023 Chinese Music Society of North America —— 组织存在性 vs 研究记录

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `evidence_scope` | `organization_existence` | `organization_existence`（保留） | 来源为学术机构档案 PDF，介绍该研究会，可支持"组织存在"（partial：PDF 未逐页核） |
| `research_record` | 未使用 | 不采用 | 该 PDF 是机构史料，不是研究产出、也不是研究记录 |
| `fact_support_level`/`fact_verification_status` | — | `partial`/`partial` | 与"未逐页核"一致 |

### 3.7 CAND024 Randy Raine-Reusch —— `individual_performance` 是否有足够材料

| 字段 | 原值 | 新值 | 原因 |
|---|---|---|---|
| `activity_type` | `individual_performance` | `individual_performance`（保留，候选类型） | 档案确有其 1999 年与 Orchid Ensemble 的演出条目 |
| `evidence_scope` | `event_announcement` | `performance_record` | 档案条目是事后记录，不是活动公告 |
| `event_date` | — | `1999`（`year`） | 档案给出年份，未给出月日 |
| `date_status` | `verified` | `partial` | 仅到年 |
| `instrument_status` | `unverified` | `unverified`（不变） | 档案未载明具体中国乐器 → 不能称"个人演奏中国乐器" |

> 结论：CAND024 可支持"具名个人 + 海外演出条目"，但**尚不足以**支持"演奏中国乐器"这一严格条件，故 `strict_sample_status=pending`。

## 4. 规则性改动（影响全部 36 条）

| 规则 | 改动 | 影响 |
|---|---|---|
| 身份拆分 | 旧 `identity_status` 中 `organization_verified` 不再当作"个人身份已核" | 12 条机构案改为 `organization_status=verified` + `performer_identity_status=not_applicable`；24 条个人/匿名案 `performer_identity_status` 独立判定 |
| 日期拆分 | `published_at` 拆为 `source_published_at` + `event_date` + `event_date_precision` | 11 条有演出日期；10 条来源日期迁入；`date_status` 重算 14 条 |
| 证据范围 | 统一 9 标签字典，一个来源可多范围 | 10 条改 `evidence_scope`；撤 `long_term_impact`（CAND021）；新增 `community_activity_record`（CAND019） |
| 可靠性拆分 | `reliability` 拆为 `source_reliability` + `fact_support_level` + `fact_verification_status` | 36 条全部重新标注；`direct/partial` 25/11 |
| 状态-来源一致性 | 非 `unverified` 必须有 `*_source` | 修复 22 处"有状态无来源"；其中 5 处 `instrument_status` 降级、2 处 `performance_status` 纠正 |

## 5. 逐候选变更汇总（36 条）

| 候选 | 变更单元格 | 主要改动 |
|---|---:|---|
| CAND001 | 10 | `date_status` partial→unverified（无日期） |
| CAND002 | 10 | 同上 |
| CAND003 | 14 | 新增 `event_announcement`；`source_published_at=2026`、`event_date=2026`（year） |
| CAND004 | 10 | `date_status` partial→unverified |
| CAND005 | 10 | 新增 `event_announcement`（原只有组织存在） |
| CAND006 | 10 | `source_published_at=2024`；`date_status`→unverified |
| CAND007 | 9 | 仅规则性新列 |
| CAND008 | 14 | 新增 `event_program`；`event_date=2016`（year）；`date_status` partial |
| CAND009 | 9 | 仅规则性新列 |
| CAND010 | 12 | `event_date=2026-02-07`（从 `published_at` 迁入）；`instrument_status`→unverified |
| CAND011 | 10 | `instrument_status`→unverified（名册只列曲目） |
| CAND012 | 11 | `instrument_status`、`date_status`→unverified |
| CAND013 | 10 | `date_status=partial`（1989 年起有活动、无场次日期） |
| CAND014 | 10 | `event_date=2025-05-17` |
| CAND015 | 10 | `performance_source` 补齐；`date_status`→unverified（报道无年份） |
| CAND016 | 11 | `instrument_status`、`date_status`→unverified |
| CAND017 | 12 | `source_published_at=2022-07`、`event_date=2022-07`（month） |
| CAND018 | 10 | `date_status`→unverified |
| CAND019 | 12 | `evidence_scope`→`organization_existence|community_activity_record`；`performance_status`→unverified |
| CAND020 | 11 | `instrument_status`、`date_status`→unverified |
| CAND021 | 12 | 撤 `long_term_impact`；`date_status` verified→unverified（只有文章日期） |
| CAND022 | 10 | `performance_source` 补齐 |
| CAND023 | 9 | `organization_existence` 保留；`research_record` 不采用（见 3.6） |
| CAND024 | 12 | `event_announcement`→`performance_record`；`event_date=1999`；`date_status`→partial（见 3.7） |
| CAND025 | 9 | 仅规则性新列（地点=`verified_china`，不算海外） |
| CAND026 | 12 | `source_published_at=2025-11-28`、`event_date=2025`（year） |
| CAND027 | 11 | `evidence_scope` `organization_existence`→`performer_identity`（个人候选不该用组织存在） |
| CAND028 | 11 | 撤 `performance_record`；`date_status`→unverified（见 3.5） |
| CAND029 | 9 | 仅规则性新列（研究记录，无具名演奏者） |
| CAND030 | 13 | `event_date=2024-11-29`；`date_status`→verified；`source_reliability=low` |
| CAND031 | 10 | 严格/扩展资格拆分（见 3.1）；`event_date=2026-10-08` |
| CAND032 | 9 | 仅规则性新列（身份未核，不得按姓名推断） |
| CAND033 | 11 | `date_status` verified→unverified；`source_published_at=2022`（见 3.2） |
| CAND034 | 11 | `performance_record`→`organization_existence`；`scheduled`→`unverified`（见 3.4） |
| CAND035 | 11 | `performance_record`→`event_announcement|organization_existence`；`event_date=2025-05-03`（见 3.3） |
| CAND036 | 11 | `source_published_at=2018-06-19`、`event_date=2018`（year） |

## 6. 修订前后关键分布对比

| 维度 | 修订前 | 修订后 |
|---|---|---|
| `performance_status` | partial 12 / unverified 9 / scheduled 8 / performed_confirmed 5 / program_listed 2 | partial 11 / unverified 11 / scheduled 7 / performed_confirmed 5 / program_listed 2 |
| `evidence_scope`（多值按次计） | 组织存在 17 / 活动公告 8 / 演出记录 9 / 长期影响 1 / 演奏者身份 1 / 研究记录 1 / 节目单 1 | 组织存在 20 / 活动公告 9 / 演出记录 7 / 节目单 2 / 演奏者身份 2 / 研究记录 1 / 社区活动 1 |
| `date_status` | verified 5 / partial 12 / unverified 9（部分 partial 无任何日期） | verified 5 / partial 7 / unverified 24（每个值都有来源或明确无日期） |

## 7. 未改动声明

- 未新增/删除候选，未改动候选名称、类别、国家、来源 URL。
- 未改动 `status`、`overall_status`、`research_group`、`dedupe`。
- 未创建任何 v1.2 正式案例数据，未生成任何评分或传播效果指标。
- 未修改 `research/data/manifest.json`、`active_version`（仍 `v1.1`）、v1.0/v1.1 任何文件。
- 未编造来源：所有新增值均可回溯到 `case-expansion-v1.2-source-index.md` 中该候选的 `CANDxxx-S001` 条目；无来源支持的事实一律留空或降级为 `unverified`。
