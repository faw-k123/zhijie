# v1.2 数据检查与数据库分析验收报告

> 日期：2026-11-01  
> 结论：v1.2 数据校验通过；36 个案例已写入独立 SQL Server 分析表；active_version=v1.2。

## 1. JSON 校验

```text
validate_research_data
OK active_version=v1.2 status=reviewed cases=36 scores=360 warnings=0
```

检查结果：

- 案例 36，CASE001–CASE036，无重复；
- 指标 360，36 × 10；
- 来源类型全部符合契约；
- 来源 ID 与 source_ids 一致；
- 来源数量与 source_count 一致；
- review_status 全部为 B，display_allowed=true；
- 没有 C/D 非法展示。

## 2. 数据写入

新增独立分析表：

```text
dbo.research_case_analysis
dbo.research_score_analysis
dbo.research_source_analysis
```

同步结果：

```text
OK version=v1.2 cases=36 scores=360 sources=56
```

核对查询：

```text
cases:   36 行 / 36 个唯一 case_id
scores:  360 行 / 287 个 null / 36 个案例
sources: 56 行 / 36 个案例
```

## 3. 数据边界

- 没有修改既有业务表；
- 没有新增 Django migration；
- 没有修改 v1.0 / v1.1 数据；
- v1.1 原文件保留；
- v1.2 新增的 260 条指标全部为 null；
- 严格新增案例为 0。

## 4. 前端验收

页面：`/research-mining`

验收数据：

```text
案例：36
有效指标值：73
来源记录：56
SQL Server 曲目：302
分析表案例：36
分析表评分：360（null 287）
分析表来源：56
```

截图：`docs/screenshots/research-mining-v1.2.png`

## 5. 测试

```text
propagation.tests: 26/26 passed
npm run type-check: passed
npm run build-only: passed
```

## 6. 注意事项

- 36 个案例不等于 36 个有完整评分的案例；
- 26 个新增案例的有效评分为 0；
- 指标 n 仍为 0–10，不能因为总案例数达到 36 就做描述性排名；
- 相关矩阵只在成对 n≥5 时计算；
- 音乐库映射仍为 0，不能伪造 `music_id`。
