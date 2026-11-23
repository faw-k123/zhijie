# 研究数据字段说明（v1.1 当前案例）

> 数据版本：v1.1  
> 案例数：10；指标记录：100；有效值：73；null：27  
> 独立研究数据仓库：`research/data/v1.1/`  
> 分析数据集：`research/analysis/v1.1-case-dataset.csv`

## 1. 三层数据

| 层 | 位置 | 作用 |
|---|---|---|
| 研究数据 | `research/data/v1.1/*.json` | 案例、来源、十项指标、版本校验 |
| 分析数据 | `research/analysis/v1.1-case-dataset.csv/.json` | 供统计/挖掘的扁平表 |
| 业务库 | SQL Server `traditional_song` | 只读音乐库；当前 302 首 |

研究 JSON 是事实来源；SQL Server 是业务数据来源；两者不互相替代。

## 2. 案例字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `case_id` | string | CASE001–CASE010 |
| `performer` | string | 演奏者/主体 |
| `performer_type` | string | 个人/乐团/机构 |
| `country` / `region` | string | 国家/地区 |
| `instrument` | string[] | 乐器；未知不填 |
| `work` | string | 作品/曲目；未知写“未知” |
| `music_type` | string | 音乐类型 |
| `event_date_text` | string | 活动日期文本 |
| `event_start_date` | date/null | 结构化日期；未知 null |
| `channel` | string[] | 传播渠道 |
| `feedback` | string | 受众/反馈证据；无证据写“未采集（未知）” |
| `success_evidence` | string | 支持成功判断的具体事实 |
| `research_notes` | string | 证据缺口 |
| `review_status` | A/B/C/D | 证据等级；当前仅 A/B 可展示 |
| `source_ids` / `sources` | array | 来源 ID 与来源对象 |
| `case_type` | enum | 严格个人/跨文化乐团/海外机构等 |
| `analysis_sample` | enum | 分析样本范围 |

## 3. 指标字段

| 字段 | 说明 |
|---|---|
| `indicator_id` | 十项指标之一 |
| `score` | 0–3；证据不足为 null，不是 0 |
| `evidence` | 评分理由 |
| `source_ids` | 支持该评分的来源 |
| `missing_reason` | 为什么 null |
| `coder` / `coded_at` | 编码人/时间 |

## 4. 分析数据集列

- 元数据：`case_id,candidate_id,performer,case_type,analysis_sample,country,region,instrument,activity_type,performance_status,evidence_grade`
- 十项指标：每项一列；空值代表 null，不是 0。
- 一行 = 一个独立案例；不是一条来源或一条评分记录。

## 5. 状态与门槛

```text
n=0          unavailable
n=1–4        insufficient
n=5–19       exploratory（不排名）
n≥20         descriptive（才允许排名）
```

## 6. 使用边界

- 不能把来源数当样本量；
- 不能把 73 条有效值当 73 个案例；
- 不能把相关系数解释为因果；
- 不能把机构存在/活动预告/节目单当演出完成或传播效果；
- 没有精确曲目匹配时，`music_id` 保持 null。
