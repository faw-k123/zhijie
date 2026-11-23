# 研究数据血缘（v1.2）

## 1. 链路

```text
research/data/v1.1（既有 10 案）
        +
stage4 approved_extended（26 案）
        ↓
research/data/v1.2/cases.json（36 案）
research/data/v1.2/success_factors.json（360 条）
        ↓
research/analysis/v1.2-case-dataset.csv
        ↓
SQL Server 分析表
  research_case_analysis / research_score_analysis / research_source_analysis
        ↓
GET /api/research/mining/
        ↓
/research-mining
```

## 2. 转换规则

| 步骤 | 输入 | 输出 | 规则 |
|---|---|---|---|
| 版本组装 | v1.1 + 26 扩展 | v1.2 cases | 保留 CASE001–010，新增 CASE011–036 |
| 指标记录 | 10 + 26 案 | 360 条 | 新案例全部 null |
| 来源归一 | 候选来源 | v1.2 sources | source_type 映射到契约 7 类 |
| 数据集 | cases + scores | CSV 36 行 | 一行一个 case_id |
| 入库 | v1.2 JSON | 3 张分析表 | 独立表，不碰业务表 |
| 相关分析 | 指标矩阵 | Spearman | 成对 n≥5，探索性 |

## 3. 当前数字

```text
案例：36
指标记录：360
有效值：73
null：287
来源记录：56
SQL Server 曲目：302
分析表：36 / 360 / 56
music_id 映射：0
```

## 4. 版本边界

- v1.1 原始文件未改写；
- v1.2 是当前 active_version；
- v1.0 保留；
- 分析表是派生层，可删除重建；
- 业务表 `traditional_song` 未修改。

## 5. 可追溯性

- 每个案例保留 `candidate_id`；
- 每个指标保留 `source_ids` / `missing_reason`；
- 每个来源保留 case_id；
- 页面可从案例回看来源与指标缺口。
