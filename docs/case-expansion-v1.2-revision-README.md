# v1.2 第一阶段候选数据一致性修订 · 交付说明（索引）

- 版本：`v1.2-candidates-rev.1`
- 日期：2026-11-01
- 一句话：只修订了**候选表、审核报告、字段字典**，没有创建 v1.2 正式案例，没有改动 v1.0/v1.1 与 `active_version`。

## 1. 交付清单

| # | 交付物 | 文件 | 说明 |
|---:|---|---|---|
| 1 | 修订后的候选 CSV | `case-expansion-v1.2-screening.csv`<br>`case-expansion-v1.2-evidence-chain.csv` | 46 列 × 36 行，两文件字节一致（sha256 `8273ae8c…`） |
| 1a | 逐单元格变更记录 | `case-expansion-v1.2-revision-changes.csv` | 386 条：原值 / 新值 / 原因 / 来源依据 |
| 2 | 字段数据字典 | `case-expansion-v1.2-fields-dictionary.md` | 46 个字段的类型、枚举、规则；含新增 `community_activity_record` |
| 3 | 修订前后差异报告 | `case-expansion-v1.2-revision-diff.md` | 范围、总量、7 条重点候选、36 条逐项、规则性改动 |
| 4 | 36 条候选状态统计报告 | `case-expansion-v1.2-status-report.md` | 所有分布可复算，含修订前后对比 |
| 5 | 证据冲突检查报告 | `case-expansion-v1.2-evidence-conflicts.md` | 10 项完整性检查 + 已修复冲突 + 跨文件版本差 |
| 6 | 未解决问题清单 | `case-expansion-v1.2-open-issues.md` | 15 项，含多来源建模建议 |
| 附 | 修订后的审核报告 | `case-expansion-v1.2-candidates.md`<br>`case-expansion-v1.2-evidence-chain.md` | 已改口径文字、重算分布表、补 CAND031 说明 |
| 附 | 修订前原件备份 | `_backup-v1.2-pre-revision-20261101/` | 供回滚与比对 |
| 附 | 可复算统计 | `case-expansion-v1.2-revision-summary.json` | 全部计数与校验结果 |

## 2. 六项指定修订的落点

| 任务书要求 | 落点 | 结果 |
|---|---|---|
| CAND031 资格拆分 | `strict_sample_status=not_eligible`、`extended_sample_status=eligible_cross_cultural_only` | 不进 strict_individual，保留跨文化合作扩展资格 |
| CAND033 保留 `program_listed` | `performance_status=program_listed`、`evidence_scope=event_program`、`date_status` 降为 `unverified` | 未写成"演出已确认" |
| CAND035 改 `event_announcement` | `evidence_scope=event_announcement|organization_existence` | 来源为 events 活动页 |
| CAND034 机构存在 vs 活动公告 | `evidence_scope=organization_existence`、`performance_status=unverified` | 乐团介绍页无场次 |
| CAND028 核实 `performance_record` | 撤掉 `performance_record`，只留 `performer_identity` | 访谈页无具体场次 |
| CAND023 `organization_existence`/`research_record` | 保留 `organization_existence`，不采用 `research_record` | 档案 PDF 是机构史料 |
| CAND024 `individual_performance` 材料 | `evidence_scope=performance_record`、`event_date=1999`、`date_status=partial` | 有演出条目、缺具体中国乐器 |
| 身份与机构拆分 | `organization_status` / `performer_identity_status` | 12 条机构案不再冒充个人身份 |
| 日期拆分 | `source_published_at` / `event_date` / `event_date_precision` | 11 条演出日期与 10 条来源日期分离 |
| 可靠性拆分 | `source_reliability` / `fact_support_level` / `fact_verification_status` | 18 条 high 来源中仍有 11 条事实只到 partial |
| 报告文字修订 | `candidates.md` §4 一句话 | 已改为"21 条通过初步筛选……尚不能据此直接认定传播效果" |

## 3. 未改动（保护范围）

- `research/data/v1.0/**`、`research/data/v1.1/**`：8 个文件的 sha256 与 `manifest.json` 记录逐项一致（已校验）。
- `research/data/manifest.json`：未修改，`active_version` 仍为 `v1.1`。
- 正式 `cases.json`：未新增任何案例。
- 未生成任何评分、排名或传播效果指标。

## 4. 复算方式

```bash
# 从备份恢复原始 CSV 后重新生成（幂等；输入已是修订版时会拒绝运行）
python build_revision.py
```

校验项（全部通过）：行数 36、去重新增 33、`candidate_id`/`source_id` 唯一、枚举合法、非 `unverified` 状态必须有来源、`organization_status=verified` 必须伴随 `organization_existence`、日期与精度一致。

## 5. 需要知道的版本边界（重要）

`docs/` 下另有**第二阶段**文件（`case-expansion-v1.2-stage2-*`，15:35 生成）与**第三阶段**文件（`case-expansion-v1.2-stage3-*`，15:39 生成），后者为 CAND024/026/028/033/036 补充了 S002–S004 新来源并重做身份复核。本次修订只覆盖**第一阶段 S001 口径**，与二/三阶段在 5 条候选上存在阶段差，且资格枚举不同（已在 `case-expansion-v1.2-evidence-conflicts.md` §4 逐条列出）。

合并建议：先把候选表升级为"一候选多来源"结构，再按"来源可核 + 事实直接支持"合并，不要把第二阶段的结论直接抄进第一阶段表。

## 6. 结论

本次只完成候选材料修订，未改变正式研究数据版本：新增正式案例 0，直接批准 `strict_individual` 0，所有候选的传播结果仍未核实，v1.2 正式案例数据尚未创建。
