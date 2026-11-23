# v1.2 第一阶段 36 条候选状态统计报告

- 版本：`v1.2-candidates-rev.1`（2026-11-01）
- 数据源：`docs/case-expansion-v1.2-screening.csv`（修订后，46 列 × 36 行）
- 机器可复算结果：`docs/case-expansion-v1.2-revision-summary.json`
- 复算脚本：`build_revision.py`（读取修订 CSV，按 `evidence_scope` 多值拆分计数）
- 口径：所有计数均为"行内出现次数"，`evidence_scope` 一行可含多个标签，故其合计大于 36

## 1. 总量校验

| 校验项 | 期望 | 实际 | 结果 |
|---|---:|---:|:--:|
| 候选总数 | 36 | 36 | ✅ |
| 去重后新增（`dedupe=new`） | 33 | 33 | ✅ |
| 与 v1.1 重复（`dedupe=CASE00x`） | 3 | 3 | ✅ |
| `candidate_id` 唯一 | 36 | 36 | ✅ |
| `source_id` 唯一 | 36 | 36 | ✅ |
| 新增的正式案例 | 0 | 0 | ✅ |

## 2. 候选管理状态（`status`，本版未改）

| 状态 | 数量 | 候选 |
|---|---:|---|
| `eligible_for_extended_review` | 21 | CAND001–CAND020、CAND022 |
| `pending_evidence` | 11 | CAND023, 024, 025, 026, 027, 028, 029, 030, 032, 033, 036 |
| `duplicate` | 3 | CAND021, CAND034, CAND035 |
| `excluded` | 1 | CAND031 |
| **合计** | **36** | — |

复算：`status` 列按值分组计数，四类相加 = 36。

## 3. 综合审核状态（`overall_status`，本版未改）

| overall_status | 数量 | 候选 |
|---|---:|---|
| `extended_lead` | 11 | 001, 002, 004, 010, 011, 012, 013, 014, 016, 018, 020 |
| `pending_evidence` | 21 | 003, 005, 006, 007, 008, 009, 015, 017, 019, 022, 023, 024, 025, 026, 027, 028, 029, 030, 032, 033, 036 |
| `duplicate` | 3 | 021, 034, 035 |
| `excluded` | 1 | 031 |
| **合计** | **36** | — |

> 注意：`status` 与 `overall_status` 是两个维度。例如 CAND003 是 `status=eligible_for_extended_review` 但 `overall_status=pending_evidence`（进了复核队列，证据链仍未闭合）。

## 4. 严格样本资格（`strict_sample_status`，新增）

| 取值 | 数量 | 候选 |
|---|---:|---|
| `eligible` | **0** | — |
| `pending` | 6 | CAND024, 026, 027, 028, 032, 033 |
| `not_eligible` | 30 | 其余 |
| **合计** | **36** | — |

- 本批**没有一条**同时满足"外国个人 + 中国乐器 + 海外演出 + 可核来源"四项，故直接批准 `strict_individual` = **0**。
- 6 条 `pending` 是"可能要补证成严格个人"的候选，不是已批准。
- CAND025 身份已核（美国学生），但活动在厦门（`location_status=verified_china`），海外条件不成立，故 `not_eligible`。

## 5. 扩展样本资格（`extended_sample_status`，新增）

| 取值 | 数量 | 候选 |
|---|---:|---|
| `eligible` | 21 | 与 `status=eligible_for_extended_review` 完全一致 |
| `eligible_cross_cultural_only` | 1 | CAND031 |
| `pending_more_evidence` | 11 | CAND023–030, 032, 033, 036 |
| `duplicate_reference` | 3 | CAND021, 034, 035 |
| **合计** | **36** | — |

交叉核对：

| `status` | `extended_sample_status` | 行数 |
|---|---|---:|
| `eligible_for_extended_review` | `eligible` | 21 |
| `pending_evidence` | `pending_more_evidence` | 11 |
| `duplicate` | `duplicate_reference` | 3 |
| `excluded` | `eligible_cross_cultural_only` | 1 |

> CAND031 是唯一 `status=excluded` 但仍有扩展资格的行：`strict=not_eligible`、`extended=eligible_cross_cultural_only`。这是本次修订要解决的"整体 excluded 却要保留合作线索"的矛盾。

## 6. 身份拆分后的两个维度

### 6.1 `organization_status`

| 取值 | 数量 |
|---|---:|
| `verified` | 12 |
| `partial` | 13 |
| `unverified` | 2 |
| `not_applicable` | 9 |

`verified` 的 12 条：001, 002, 006, 007, 009, 012, 013, 016, 020, 021, 034, 035（来源为该机构自述页或官方登记页，且 `evidence_scope` 含 `organization_existence`）。

### 6.2 `performer_identity_status`

| 取值 | 数量 | 候选 |
|---|---:|---|
| `verified` | 1 | CAND025 |
| `partial` | 5 | CAND024, 026, 027, 028, 031 |
| `unverified` | 6 | CAND018, 021, 030, 032, 033, 036 |
| `not_applicable` | 24 | 机构/团体/研究/匿名类 |
| **合计** | **36** | — |

> 与旧版最大区别：旧 `identity_status` 里 12 条 `organization_verified` 现在**不再**出现在个人身份列；个人身份 `verified` 只剩 1 条。

## 7. 活动类型（`activity_type`，未改）

| 取值 | 数量 |
|---|---:|
| `education` | 13 |
| `ensemble_performance` | 11 |
| `individual_performance` | 7 |
| `research_only` | 2 |
| `cross_cultural_collaboration` | 2 |
| `community_activity` | 1 |
| **合计** | 36 |

## 8. 演奏证据（`performance_status`）

| 取值 | 修订后 | 修订前 |
|---|---:|---:|
| `partial` | 11 | 12 |
| `unverified` | 11 | 9 |
| `scheduled` | 7 | 8 |
| `performed_confirmed` | 5 | 5 |
| `program_listed` | 2 | 2 |
| **合计** | **36** | **36** |

变化来源：CAND019（`partial`→`unverified`，领事探访报道无演出）、CAND034（`scheduled`→`unverified`，机构介绍页无场次）。

## 9. 证据范围（`evidence_scope`，多值按次计）

| 标签 | 修订后 | 修订前 |
|---|---:|---:|
| `organization_existence` | 20 | 17 |
| `event_announcement` | 9 | 8 |
| `performance_record` | 7 | 9 |
| `event_program` | 2 | 1 |
| `performer_identity` | 2 | 1 |
| `research_record` | 1 | 1 |
| `community_activity_record`（新增） | 1 | 0 |
| `long_term_impact` | **0** | 1 |
| `audience_feedback` | 0 | 0 |
| **出现次数合计** | **42** | 38 |

- 撤用 `long_term_impact`：CAND021 的单篇 22 周年雅集报道不足以支撑"长期传播影响"。
- 新增 `community_activity_record`：仅 CAND019（领事看望艺术团属社区活动记录）。
- `audience_feedback` 仍为 0：本批没有任何来源提供观众评论或反馈。

## 10. 日期证据

| `date_status` | 数量 | 含义 |
|---|---:|---|
| `verified` | 5 | CAND010, 014, 030, 031, 035（具体到日） |
| `partial` | 7 | 003, 008, 013, 017, 024, 026, 036（仅年/月，或只有时间线索） |
| `unverified` | 24 | 无可用演出日期 |

| `event_date_precision` | 数量 |
|---|---:|
| `day` | 5 |
| `month` | 1（CAND017） |
| `year` | 5（003, 008, 024, 026, 036） |
| `unknown` | 25 |

`source_published_at` 有值 10 条（003, 006, 008, 017, 019, 021, 026, 027, 033, 036），其余来源未标注发布日。

## 11. 来源可靠性与事实支持

| `source_reliability` | 数量 | `fact_support_level` | 数量 | `fact_verification_status` | 数量 |
|---|---:|---|---:|---|---:|
| `high` | 18 | `direct` | 25 | `verified` | 25 |
| `medium` | 17 | `partial` | 11 | `partial` | 11 |
| `low` | 1 | `indirect` | 0 | `unverified` | 0 |

> 三者分离的意义：18 条 high 来源里，仍有 11 条事实只能算 `partial`（例如高校官网只证明机构存在，不证明个人演奏）。

## 12. 研究分组（`research_group`，未改）

| 组 | 数量 | 候选 |
|---|---:|---|
| A 严格个人候选 | 6 | 024, 026, 027, 028, 032, 033 |
| B 机构/教育 | 14 | 001–008, 011–013, 016, 019, 020 |
| C 具体演出/乐团 | 8 | 009, 010, 014, 015, 017, 018, 022, 036 |
| D 重复/暂缓/跨文化 | 8 | 021, 023, 025, 029, 030, 031, 034, 035 |

## 13. 结论

1. 候选总数仍为 36，去重后新增仍为 33，管理状态 21/11/3/1 与 `overall_status` 11/21/3/1 均可复算。
2. 新增的严格/扩展双资格把"能否当严格个人"与"能否进扩展研究"彻底分开：严格 `eligible` = 0，扩展 `eligible` = 21，跨文化专用 1。
3. 身份、日期、可靠性三个维度拆开后，原有的"机构=已核实身份""来源日期=演出日期""高可靠来源=事实已核实"三类混淆不再出现。
4. 本阶段新增正式案例 0；所有候选的传播结果仍未核实；v1.2 正式案例数据尚未创建。
