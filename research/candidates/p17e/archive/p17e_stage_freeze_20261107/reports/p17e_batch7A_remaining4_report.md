# P17-E 第七批 A：补检索 batch_01 剩余 4 首报告

> 处理范围：song_id 9–12  
> 结论：**PASS（补检索完成）**  
> batch_01 检索覆盖：25/25  
> 封存：仍不封存（7 条 ambiguous 未人工确认）

## 1. 4 首结果

| song_id | 曲目 | 检索组数 | 结果 | 页面 |
|---:|---|---:|---|---|
| 9 | 牵丝戏（二胡&京胡版） | 2 | no_relevant_result_after_search | 无 |
| 10 | 神经病之歌（二胡） | 2 | no_relevant_result_after_search | 无 |
| 11 | 花田错（二胡版） | 2 | no_relevant_result_after_search | 无 |
| 12 | 葬花吟（二胡版） | 2 | ambiguous_match | 小红书候选页当前 404 |

本轮：

```text
实际检索：4/4
打开有效原始网页：0
新增有效证据：0
新增 performance_confirmed：0
ambiguous_match：1
no_relevant_result_after_search：3
not_searched：0
```

## 2. 葬花吟

搜索到线索：

```text
小红书帖：在牛津把葬花吟和音乐人类学放上舞台
https://www.xiaohongshu.com/discovery/item/67a168ca000000002a00fa1a
```

当前访问返回 404，无法核实：

- 活动主体；
- 演出日期；
- 曲目版本；
- 是否为实际演出；
- 是否与正式 302 曲目为同一作品。

因此只标记：

```text
ambiguous_match
evidence_grade = C
```

不进入 evidence 表，不升级为 performance_confirmed。

## 3. batch_01 重新计算

```text
曲目：25
实际检索：25
未检索：0
覆盖率：100%

performance_confirmed：3
ambiguous_match：7
no_relevant_result_after_search：15
outcome_evidenced：0

打开原始网页：3
有效证据：3
候选关联：0
```

7 条 ambiguous：

```text
1 三寸天堂
5 倩女幽魂
8 江南
12 葬花吟
17 万蝶振翅
19 关山月
22 卧龙吟
```

## 4. 全局

```text
302 首中已检索：25
覆盖率：25/302 = 8.28%
未检索：277
```

## 5. 封存判断

```text
不封存
```

原因：

- 7 条 ambiguous 尚未人工处理；
- 3 条 performance_confirmed 仍是单来源；
- 3 个原始页面当前重访失败（历史正文已核验）；
- 候选证据尚未人工审核。

检索覆盖完成不等于证据封存完成。

## 6. 数据安全

```text
active_version = v1.6
v1.6 文件哈希未变化
manifest 未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 7. 输出

- `batch_01_search_results_batch7A.csv`
- `batch_01_source_evidence_batch7A.csv`（0条）
- `batch_01_search_coverage_batch7A.csv`
- `batch_01_manual_review_batch7A.csv`
- `batch_01_search_results_all_final.csv`
- `batch_01_search_coverage_all_final.csv`

## 8. 结论

```text
PASS（4首补检索完成；batch_01 25/25）
```

但 batch_01 仍不能封存；不处理其他 ambiguous，不启动 batch_02，不启动 P18。
