# v1.7 教师意见专项候选库

> 建立日期：2026-11-08  
> 状态：已审批并正式激活为 `active_version=v1.7`  
> 第一批目标：10 个严格外国个人演奏案例

## 当前结果

```text
第一批严格案例：10
沿用并重新核验的正式案例：5
新增候选：5
现有正式严格样本：2
新达到严格证据门槛并获负责人审批：8
受众反馈记录：20（10例各2条）
接受机制编码：10例 × 9类机制
首批候选音乐：20首（均与程序音频资产核对）
区域适配：6国 × 20首
```

10 例均通过“外国个人身份 + 中国传统乐器/曲目 + 实际公开演奏 + 可追溯来源”证据门槛。这里的“严格案例”只表示案例事实成立，不表示传播成功，也不表示受众已经接受。

## 文件

- `strict_case_admission_rules.md`：准入规则、字段与决策门槛；
- `strict_case_admission_template.csv`：后续案例复用的空白准入表；
- `batch_01_strict_cases.csv`：第一批 10 例审核结果；
- `batch_01_sources.csv`：21 条来源及其支持范围；
- `batch_01_review_report.md`：本批结论、结构和限制。
- `04_audience_feedback.csv` / `04_audience_feedback_report.md`：逐例反馈及证据分级；
- `05_acceptance_mechanism_codebook.md` / `05_acceptance_mechanism_coding.csv` / `05_acceptance_mechanism_summary.md`：九类机制与一次完整编码；
- `06_candidate_music_20.csv` / `06_candidate_music_selection_report.md`：基于机制选择的20首候选；
- `07_country_evidence_sources.csv`：六国策略依据；
- `07_six_country_strategy_matrix.csv` / `07_music_country_fit_matrix.csv`：六国策略和20×6适配矩阵。

## 与正式数据的关系

- `SC001`、`SC002` 对应 v1.6 已批准严格样本 `CASE005`、`CASE006`；
- `SC003`、`SC006`、`SC010` 分别补强现有 `CASE001`、`CASE010`、`CASE007`；
- `SC004`、`SC005`、`SC007`、`SC008`、`SC009` 为新增候选；
- 未覆盖 `research/data/v1.6/cases.json`，历史版本保持只读；
- 8 个新增/升级案例已写入 v1.7，正式严格样本合计10例。

## 当前边界

后四项已随审批激活为 v1.7 正式研究数据。20条反馈仍属于目的抽样且直接原话比例有限；20首与六国矩阵是获批的下一轮测试设计，而非已证实的国家偏好。完成六国真实小样后，才能生成程序中的100分制曲目评分。
