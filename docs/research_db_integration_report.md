# 研究数据与 SQL Server 分析层报告

## 1. 结论

- SQL Server 当前可连接；
- `traditional_song` 共 **302** 首；
- v1.2 研究数据已写入 **独立分析表**，没有改业务表结构；
- 没有新增 Django migration；
- 音乐库仍只读；当前 `music_id` 精确映射 **0 条**，未模糊匹配。

## 2. 三层架构落地

| 层 | 实现 | 状态 |
|---|---|---|
| 研究数据 | `research/data/v1.2` JSON | 已激活 |
| 分析数据集 | `research/analysis/v1.2-case-dataset.csv` | 36 行 |
| 业务库 | SQL Server `traditional_song` | 只读，302 首 |
| 分析库 | `research_case_analysis` / `research_score_analysis` / `research_source_analysis` | 36 / 360 / 56 |
| 前端 | `/research-mining` | 已上线 |

## 3. 分析表

| 表 | 行数 | 用途 |
|---|---:|---|
| `research_case_analysis` | 36 | 案例元数据 |
| `research_score_analysis` | 360 | 十项指标，287 条 null |
| `research_source_analysis` | 56 | 案例-来源关系 |

同步命令：

```text
python manage.py sync_research_analysis --target-version v1.2
```

## 4. 为什么不改业务表

- 现有 `traditional_song` 是业务表，不承载研究指标；
- 直接加字段会污染业务结构；
- 采用独立 `research_*` 分析表，可回滚、可重建；
- JSON 仍是版本化事实来源，分析表是派生层；
- 只有未来经过确认的 `music_id` 关联，才考虑接入业务层。

## 5. 为什么没有强行映射 music_id

当前案例的 `work` 字段没有可与 `traditional_song.title` 精确匹配的曲目；不按乐器、国家、活动规模或名称相似度猜配。

```text
music_id = null
mapping_status = no_exact_work_match
```

## 6. 只读与写边界

- `traditional_song` 只读；
- `research_*` 分析表由 `sync_research_analysis` 重建；
- 不修改 Neo4j；
- 不修改 v1.0 / v1.1 原始文件；
- 不修改业务表结构。
