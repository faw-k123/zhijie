# v1.2 逐候选证据链核验表（第一阶段）

> 本表把 36 条候选拆成身份、乐器、实际演奏、海外地点、日期、传播结果六项；每项只记录来源能直接支持的内容。
> 不写入正式 cases.json，不修改 v1.1/v1.0，不切换 active_version。

> **数据一致性修订（v1.2-candidates-rev.1，2026-11-01）**：身份拆分为 `organization_status` / `performer_identity_status`，日期拆分为 `source_published_at` / `event_date` / `event_date_precision`，本表 §0.3 的分布已按修订后数据重算；CAND031 的"排除"改为"严格不适用 + 扩展跨文化资格"。字段口径见 `case-expansion-v1.2-fields-dictionary.md`。

## 1. 总览

- 候选：36 条；
- 来源条目：36 条；
- 本轮新增正式案例：0；
- 直接批准进入严格个人样本：0。

状态分布：

| 筛选状态 | 数量 |
|---|---:|
| `eligible_for_extended_review` | 21 |
| `duplicate` | 3 |
| `pending_evidence` | 11 |
| `excluded` | 1 |

证据链总体判断：

| overall_status | 数量 |
|---|---:|
| `extended_lead` | 11 |
| `pending_evidence` | 21 |
| `duplicate` | 3 |
| `excluded` | 1 |


## 0. 两个状态字段的定义

- `status`：候选池管理状态，决定下一步是扩展复核、待补证、排除还是去重；
- `overall_status`：六项证据链的综合审核状态，决定这条材料当前能支持什么研究用途。

两者不能合并。例如 CAND014 可以是 `status=eligible_for_extended_review`，同时 `overall_status=extended_lead`。

### 0.1 实际演奏状态

| 状态 | 含义 |
|---|---|
| `scheduled` | 已发布演出安排/票务页，但不能证明演出已实际完成 |
| `program_listed` | 已列入节目单，证明演出安排与曲目，不自动等于现场完成 |
| `performed_confirmed` | 有演出后报道、录像或其他事后材料确认 |
| `partial` | 有部分演奏事实，但信息不完整 |
| `unverified` | 无法确认 |

### 0.2 研究管理分组

| 组 | 数量 | 候选 |
|---|---:|---|
| A | 6 | CAND024, CAND026, CAND027, CAND028, CAND032, CAND033 |
| B | 14 | CAND001, CAND002, CAND003, CAND004, CAND005, CAND006, CAND007, CAND008, CAND011, CAND012, CAND013, CAND016, CAND019, CAND020 |
| C | 8 | CAND009, CAND010, CAND014, CAND015, CAND017, CAND018, CAND022, CAND036 |
| D | 8 | CAND021, CAND023, CAND025, CAND029, CAND030, CAND031, CAND034, CAND035 |

研究分组只用于管理，不替代 `status` / `overall_status`，也不构成正式纳入。

### 0.3 字段分布

| activity_type | 数量 |
|---|---:|
| `education` | 13 |
| `ensemble_performance` | 11 |
| `community_activity` | 1 |
| `research_only` | 2 |
| `individual_performance` | 7 |
| `cross_cultural_collaboration` | 2 |

| performance_status | 数量 |
|---|---:|
| `partial` | 11 |
| `unverified` | 11 |
| `scheduled` | 7 |
| `performed_confirmed` | 5 |
| `program_listed` | 2 |

| evidence_scope | 出现次数 |
|---|---:|
| `organization_existence` | 20 |
| `event_announcement` | 9 |
| `performance_record` | 7 |
| `event_program` | 2 |
| `performer_identity` | 2 |
| `research_record` | 1 |
| `community_activity_record` | 1 |

> 修订说明（v1.2-candidates-rev.1）：`long_term_impact` 由 1 降为 0（CAND021 单篇雅集报道不足以支撑长期影响）；新增 `community_activity_record` 1 条（CAND019）；`audience_feedback` 仍为 0。一个来源可支持多个标签，逐项支持事实写在 `evidence_scope_detail` 列。
>
> 严格/扩展双资格：`strict_sample_status` = `eligible` 0 / `pending` 6 / `not_eligible` 30；`extended_sample_status` = `eligible` 21 / `eligible_cross_cultural_only` 1 / `pending_more_evidence` 11 / `duplicate_reference` 3。

## 2. 重点候选

| 候选 | 机构状态 | 个人身份 | 乐器 | 实际演奏 | 海外地点 | 日期 | 传播结果 | 下一步 |
|---|---|---|---|---|---|---|---|---|
| CAND024 Randy Raine-Reusch | not_applicable | partial | unverified | program_listed | verified | partial（1999，year） | unverified | 找 1999 演出节目单，确认具体中国乐器与曲目 |
| CAND025 Shane Spurgeon | not_applicable | verified | verified | performed_confirmed | verified_china | unverified | unverified | 找中国境外演出记录；否则只能作跨文化学习案例 |
| CAND026 Belle / Erin Lam | not_applicable | partial | verified | performed_confirmed | verified | partial（2025，year） | unverified | 按项目身份定义核验；补具体演出/曲目 |
| CAND027 Chris Stephens | not_applicable | partial | unverified | unverified | unverified | unverified | unverified | 暂缓；先确认中国乐器与实际演奏 |
| CAND028 Nicholas Ng | not_applicable | partial | verified | partial | verified | unverified | unverified | 核验身份口径与具体海外演出场次 |
| CAND031 Wu Fei & Abigail Washburn | not_applicable | partial | partial | performed_confirmed | verified | verified（2026-10-08） | unverified | 仅作跨文化合作线索；严格 `not_eligible`、扩展 `eligible_cross_cultural_only` |
| CAND032 Jia Ling | not_applicable | unverified | verified | partial | verified | unverified | unverified | 先确认项目身份标准；不得按姓名/族裔排除 |
| CAND033 Mona Li | not_applicable | unverified | verified | program_listed | verified | unverified | unverified | 优先核验身份/国籍；节目单只列名，不等于现场完成 |
| CAND036 东京古筝乐团（Tokyo Guzheng Orchestra） | partial | unverified | verified | partial | verified | partial（2018，year） | unverified | 核验具名演奏者身份与国籍；补演出后记录 |
| CAND014 Harmony Guzheng Ensemble | partial | not_applicable | verified | scheduled | verified | verified（2025-05-17） | unverified | 核验成员国籍、曲目单与受众反馈 |
| CAND021 London Youlan Qin Society | verified | unverified | partial | performed_confirmed | verified | unverified | partial | 与 CASE008 合并，不新建案例 |
| CAND035 Bard East/West Ensemble | verified | not_applicable | verified | scheduled | verified | verified（2025-05-03） | unverified | 与 CASE009 合并，不新建案例 |

## 3. 关键纠正

- 不再用“华人身份”直接排除 CAND032/033；改为 `pending_evidence`，先确认项目身份定义。
- CAND033 的德国节目单只**列明** Mona Li 担任古筝演奏（`performance_status=program_listed`）；节目单是演出前材料，不等于现场完成，更不能据此认定身份。
- CAND031 的"排除"只是不进严格个人池：`strict_sample_status=not_eligible`、`extended_sample_status=eligible_cross_cultural_only`；不得当作“外国个人演奏中国乐器”的严格案例。
- CAND025 的厦门活动证明美国学生演奏二胡，但地点在中国境内，不能算海外演出。
- CAND018/020/021 的机构/成员信息只能支持机构传播，不自动升级为外国个人。
- 所有候选的 `outcome_status` 均为未核实，不能把演出记录直接解释为受众认可。

## 4. 下一步

- 先锁定“外国个人”定义：按可核实国籍，还是按海外本土活动身份；
- 优先核 CAND024、026、028、033、036 的身份与演出链；
- 机构/教育候选单独建组，不混入严格个人；
- 补实际传播结果：演出后报道、主办方回顾、节目单、观众评论、课程参与记录；
- 不在本阶段创建 v1.2 正式数据。
