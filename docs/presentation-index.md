# 智解国音成果展示清单

> 当前基线：v1.6 / 40 案例 / 94 有效评分 / 302 首曲目  
> 展示日期：2026-11-04

## 一、建议截图的页面

前端地址：

```text
http://localhost:5175
```

### 必截 6 张

1. **案例库总览**

```text
http://localhost:5175/global-cases?designPreview=1
```

应显示：

```text
共 40 例
描述性样本 · 40/40
第 1 / 4 页
```

2. **CASE039 科威特**

```text
http://localhost:5175/global-cases/CASE039?designPreview=1
```

应显示：

```text
9 项有效
1 项未知
已批准
```

3. **CASE040 阿根廷**

```text
http://localhost:5175/global-cases/CASE040?designPreview=1
```

应显示：

```text
6 项有效
4 项未知
已批准
```

4. **CASE007 分类整改**

```text
http://localhost:5175/global-cases/CASE007?designPreview=1
```

应显示：

```text
7 项有效
3 项未知
不再作为严格个人样本
```

5. **研究洞察**

```text
http://localhost:5175/research-insights?designPreview=1
```

应显示：

```text
数据版本 v1.6
40 个案例
94 条有效评分
```

6. **全球传播效果 / 区域传播方案**

```text
http://localhost:5175/global-effect?designPreview=1
http://localhost:5175/promo-plan?designPreview=1
```

用于说明现有系统仍可承载研究展示，不用于证明传播效果。

### 可选 API 截图

```text
http://127.0.0.1:8000/api/research/status/
```

应显示：

```text
active_version = v1.6
cases = 40
```

## 二、必看的文件

### 1. 正式发布

- `docs/p13.8-release-notes.md`
- `docs/p13.8-v1.6-activation-report.md`
- `docs/p13.8-post-activation-validation.md`

### 2. 研究分析

- `docs/p14-final-research-analysis-report.md`
- `docs/p15-final-report.md`
- `docs/p16-final-report.md`

### 3. 证据审计

- `docs/p16_mapping_coverage_report.md`
- `docs/p16_readiness_summary.md`
- `research/candidates/p17e/reports/p17e_batch2_report.md`
- `research/candidates/p17e/reports/p17e_batch2_failure_retry_report.md`
- `research/candidates/p17e/reports/p17e_batch2_content_review_report.md`

### 4. 最值得展示的 CSV

- `research/analysis/p14/indicator_statistics.csv`
- `research/analysis/p15/sample_profile_comparison.csv`
- `research/analysis/p16/p16_song_case_mapping_audit.csv`
- `research/analysis/p16/p16_song_readiness_classification.csv`
- `research/candidates/p17e/04_case008_performance/case008_song_recheck.csv`
- `research/candidates/p17e/02_case_reverification/source_recheck_batch2.csv`

## 三、展示主线

```text
v1.6 正式发布（40 案例 / 94 有效评分 / 0 warnings）
→ CASE039/040 新增案例与审批状态
→ CASE007 退出严格样本（数据/API 一致）
→ P14 描述性统计（不是因果结论）
→ P15 严格 2 例 vs 扩展 36 例（不能混算）
→ P16 302 首曲目只有 5 条节目单级关联、0 首完整潜力分
→ P17E 外部核查：2 首演出确认、3 首仍待核实
```

## 四、展示时不要说的话

- 不要说“302 首都有海外传播证据”；
- 不要说“5 首已确认实际演出”，只有 2 首；
- 不要说“40 个案例都是严格个人样本”，严格样本只有 2 个；
- 不要说“CASE007 已核实”，它是 pending_review；
- 不要把评论量/情感当作传播成功；
- 不要把 P17E 的 12 个不可访问来源写成“来源不存在”；
- 不要把 P17E 第一批/第二批说成已经完成 302 首外部检索。

## 十三、v1.7 六国实测工作台

```text
http://localhost:5175/research/pilot?designPreview=1
```

应显示：

```text
120 个国家×曲目单元
原版/适配版样本数
门槛配置（建议值，未审批）
样本不足 / 待证据 / 可评审 / 待审批评分
```

说明：页面不会把 0 条真实反馈显示成已有数据；没有真实量表和证据分时，正式评分与排名保持关闭。
