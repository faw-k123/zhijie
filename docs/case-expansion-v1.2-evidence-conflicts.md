# v1.2 第一阶段候选数据 · 证据冲突检查报告

- 版本：`v1.2-candidates-rev.1`（2026-11-01）
- 检查对象：修订后 `case-expansion-v1.2-screening.csv` / `-evidence-chain.csv`（46 列 × 36 行）、`case-expansion-v1.2-candidates.md`、`case-expansion-v1.2-evidence-chain.md`、`case-expansion-v1.2-fields-dictionary.md`
- 结论摘要：**修复 22 处状态-来源冲突、10 处证据范围错配、14 处日期口径错配；未发现虚构来源；发现 1 类跨文件版本差异（第二阶段新增来源），需在合并阶段处理**

## 1. 完整性检查清单（任务书 §四）

| # | 检查项 | 方法 | 结果 |
|---:|---|---|:--:|
| 1 | 候选总数仍为 36 | `len(rows)` | ✅ 36 |
| 2 | 去重后新增仍为 33 | `dedupe=="new"` 计数 | ✅ 33 |
| 3 | 候选管理状态可复算 | `status` 分组，四值相加 | ✅ 21+11+3+1=36 |
| 4 | `overall_status` 可复算 | 分组计数 | ✅ 11+21+3+1=36 |
| 5 | A/B/C/D 分组可复算 | `research_group` 分组 | ✅ 6+14+8+8=36 |
| 6 | `activity_type`/`performance_status`/`evidence_scope` 可复算 | 分组计数（scope 按 `|` 拆分） | ✅ 13+11+7+2+2+1=36；11+11+7+5+2=36；scope 合计 42 |
| 7 | `source_id` 唯一 | 集合大小 | ✅ 36 个唯一 |
| 8 | 状态值符合数据字典 | 枚举白名单校验 | ✅ 全部命中字典 |
| 9 | 空值/非法枚举/矛盾状态 | 规则校验（见 §3） | ✅ 0 残留（修复后） |
| 10 | 报告、CSV、字典同一版数据 | 版本号 + 计数交叉核对 | ✅ 三处均标 `v1.2-candidates-rev.1`，计数一致 |

## 2. 已修复的证据冲突

### 2.1 状态有值但无来源（22 处）

规则：非 `unverified` 的 `*_status` 必须有 `*_source`。原表有 22 处违反。

| 处理方式 | 处数 | 候选-字段 |
|---|---:|---|
| 补齐来源指针（来源确实支持） | 6 | CAND003/008/013/017/026 的 `date_source`、CAND010/015/022/030 的 `performance_source` |
| 降级为 `unverified`（来源不支持） | 5 | CAND010/011/012/016/020 的 `instrument_status`（来源只列曲目或仅提乐团，未给乐器） |
| 纠正状态值 | 2 | CAND019 `performance_status` partial→unverified（领事探访报道不含演出）；CAND034 scheduled→unverified（乐团介绍页无任何场次） |
| 重算日期状态 | 14 | 见 §2.3 |

### 2.2 证据范围错配（10 处）

| 候选 | 原 `evidence_scope` | 新 `evidence_scope` | 冲突 | 依据 |
|---|---|---|---|---|
| CAND003 | `organization_existence` | `organization_existence|event_announcement` | 来源是 2026 年度音乐会活动页，具公告性质 | 活动页标题与内容 |
| CAND005 | `organization_existence` | `event_announcement|organization_existence` | 校园活动页首先是活动公告 | 页面性质 |
| CAND008 | `organization_existence` | `event_program|organization_existence` | 2016 音乐会节目单 PDF 属节目单 | PDF 类型 |
| CAND019 | `event_announcement` | `organization_existence|community_activity_record` | 领事"看望艺术团"报道不是活动公告 | 报道内容 |
| CAND021 | `performance_record|long_term_impact` | `performance_record|organization_existence` | 单篇 22 周年雅集报道不足以支撑"长期影响"，但可支撑琴社延续 | 论证强度 |
| CAND024 | `event_announcement` | `performance_record` | 档案条目是事后记录，不是公告 | Western Front 档案页性质 |
| CAND027 | `organization_existence` | `performer_identity` | 个人候选不应挂"组织存在" | 候选类型 |
| CAND028 | `performer_identity|performance_record` | `performer_identity` | ABC 访谈页无任何具体场次 | 页面内容 |
| CAND034 | `performance_record` | `organization_existence` | 乐团介绍页无场次信息 | 页面内容 |
| CAND035 | `performance_record` | `event_announcement|organization_existence` | 官网 events 页是演出前公告 | URL 路径 `/events/` |

### 2.3 日期口径错配（14 处）

| 类型 | 候选 | 原值 → 新值 | 原因 |
|---|---|---|---|
| 把"无日期"当 partial | CAND001, 002, 004, 012, 016, 018, 020 | `partial` → `unverified` | 来源根本没有演出日期 |
| 把"演出季/年份"当 verified | CAND033 | `verified` → `unverified` | 节目单只标 2022 演出季，无场次日期 |
| 把"文章日期"当演出日期 | CAND021 | `verified` → `unverified` | 2025-07-18 是报道日期，不是雅集日期 |
| 把"档案年份"当 verified | CAND024 | `verified` → `partial` | 只有 1999 年，无月日 |
| 实际有日期但标 unverified | CAND003, 008, 017, 030 | `unverified`/`partial` → `partial`/`verified` | 活动日期可从来源读出 |

### 2.4 身份口径错配

| 候选 | 冲突 | 处理 |
|---|---|---|
| CAND001/002/006/007/009/012/013/016/020/021/034/035 | 旧 `identity_status=organization_verified` 被读成"身份已核实" | 拆为 `organization_status=verified` + `performer_identity_status=not_applicable` |
| CAND034 | 旧 `identity_status=unverified`，但来源正是该乐团介绍页 | `organization_status=verified`（个人身份仍 `not_applicable`） |
| CAND031 | `status=excluded` 与"保留跨文化合作线索"矛盾 | `strict_sample_status=not_eligible` + `extended_sample_status=eligible_cross_cultural_only` |
| CAND025 | 身份 verified 但地点在中国 | 保留 `performer_identity_status=verified`；`location_status=verified_china`；`strict_sample_status=not_eligible` |

### 2.5 "不得为了消除字段冲突而虚构证据"

本报告的所有修复只有三种动作：**补齐来源指针**（来源确实写了）、**降级状态**（来源没写）、**改写证据范围标签**（标签与来源性质不符）。没有任何一处新增来源、新增 URL 或新增事实描述。

例：

- CAND033 没有因为 `date_status` 与 `program_listed` 冲突就补一个"2022-09-07"（那是第二阶段才核到的），而是把 `date_status` 降为 `unverified` 并注明"节目单未见具体场次日期"。
- CAND034 没有把 `scheduled` 保留成"有公告"，也没有补一个活动链接，而是降为 `unverified`。

## 3. 残留一致性校验（修订后）

| 校验规则 | 违反数 |
|---|---:|
| 非 `unverified` 状态必须有 `*_source` | 0 |
| `performer_identity_status=verified` 必须属个人活动（`individual_performance`） | 0 |
| `organization_status=verified` 必须伴随 `evidence_scope` 含 `organization_existence` | 0 |
| `event_date` 非空时 `event_date_precision` 不得为 `unknown` | 0 |
| 枚举值全部在字典内 | 0 |
| `candidate_id`/`source_id` 唯一 | 0 |
| 行数 36、去重新增 33 | 0 |

## 4. 跨文件版本差异（第二阶段新增来源）

检查中发现 `docs/` 下存在 **2026-11-01 15:35–15:36 生成**的第二阶段文件（`case-expansion-v1.2-stage2-*.md/csv`），它们为 5 条候选补充了 S002–S004 新来源。本报告修订的是**第一阶段 S001 口径**，因此两套文件在下列位置不一致——这不是证据冲突，而是**阶段边界**，合并前不能混用：

| 候选 | 本报告（第一阶段，S001） | 第二阶段文件（S002+） | 差异性质 |
|---|---|---|---|
| CAND024 | `performer_identity_status=partial`；`event_date=1999`；`performance_status=program_listed` | 身份 `verified`；2010-04-08 有 zheng duo 节目 | 二阶段补到具体乐器与年份 |
| CAND026 | `performance_status=performed_confirmed`；`event_date=2025` | 2024-06-08 Manchester 两场；`scheduled` | 两阶段对"演出完成"口径不同 |
| CAND028 | `evidence_scope=performer_identity`；`date_status=unverified` | 悉尼音乐学院简介：2016 起教授二胡、巡演 | 二阶段补到机构简介 |
| CAND033 | `date_status=unverified`；`performance_status=program_listed` | 2022-09-07/08 场次页 + "已举行"日历 | 二阶段补到场次日 |
| CAND036 | `performance_status=partial`；`event_date=2018`（year） | 2018-06-17 演出后报道；`performed_confirmed` | 二阶段补到演出后记录 |

处理建议（本阶段不执行，列入未解决问题）：

1. 候选表应支持**一候选多来源**（`source_id` 由单值改为来源清单，或增加 `sources` 汇总列），否则 S002+ 无处落表；
2. 合并时以"来源可核 + 事实直接支持"为准，不以阶段序号为准；
3. 合并前不要把第二阶段的判断抄进第一阶段 CSV，否则会出现"表里有 verified、来源列表里却没有 S002"的新冲突。

补充：`docs/` 下另有 2026-11-01 15:39 生成的**第三阶段身份复核**文件（`case-expansion-v1.2-stage3-identity-review.csv` 等），其对 5 条候选的结论是：

| 候选 | 第三阶段身份复核结论 | 与本表（第一阶段）的差异 |
|---|---|---|
| CAND024 | `nationality_verified`（Canada，依据 CAND024-S003）；`eligible_for_strict_review` | 本表 `strict_sample_status=pending`、`performer_identity_status=partial` |
| CAND026 | `identity_pending`；`ineligible_identity_pending` | 一致（本表 `pending`/`partial`） |
| CAND028 | `identity_pending`；`ineligible_identity_pending` | 一致 |
| CAND033 | `identity_pending`；`ineligible_identity_pending` | 一致（本表 `pending`/`unverified`） |
| CAND036 | `group_not_individual`；`ineligible_not_individual` | 一致（本表 `not_eligible`，扩展 `pending_more_evidence`） |

第三阶段的 `strict_individual_eligibility` / `extended_sample_eligibility` **与本表 `strict_sample_status` / `extended_sample_status` 是两套枚举**，合并时必须先对齐字典，不能直接拼接。

## 5. 结论

- 36 条候选在第一阶段证据口径内已无自相矛盾的状态、无无来源的核实标记、无混装日期。
- 未发现虚构来源或凭空证据；所有改动可回溯到 `CANDxxx-S001` 原文描述。
- 与第二阶段的差异已单独列出，不构成数据错误，但必须在合并阶段统一处理。
