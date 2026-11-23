# P17-E 第七批 B 结果采纳报告

> 状态：**CONDITIONAL_PASS**  
> batch_01_sealed = false  
> batch_02_started = false  
> P18_started = false

## 1. 采纳结果

| song_id | 曲目 | 最终状态 |
|---:|---|---|
| 1 | 三寸天堂 | ambiguous_match |
| 5 | 倩女幽魂 | ambiguous_match |
| 8 | 江南 | **rejected_match** |
| 12 | 葬花吟 | ambiguous_match |
| 17 | 万蝶振翅 | ambiguous_match |
| 19 | 关山月 | ambiguous_match |
| 22 | 卧龙吟 | ambiguous_match |

《江南》拒绝理由：

来源文章列出《金蛇狂舞》《世间始终你好》《二泉映月》《红河谷》《百鸟朝凤》《夜深沉》《十面埋伏》，没有歌曲《江南》。

“江南音韵”是江南丝竹风格，不是目标流行歌曲。

## 2. batch_01 最终统计

```text
performance_confirmed：3
ambiguous_match：6
rejected_match：1
no_relevant_result_after_search：15
not_searched：0
合计：25
```

三条演出确认保留：

```text
3  一生所爱
13 赛马
24 广陵散
```

```text
outcome_evidenced = 0
candidate_links = 0
```

## 3. 更新文件

- `batch_01_search_results_all_final.csv`
- `batch_01_search_coverage_all_final.csv`
- `song_search_log.csv`
- `song_search_coverage.csv`
- `batch_01_ambiguous_review_batch7B.csv`
- `batch_01_ambiguous_evidence_batch7B.csv`

## 4. 未修改

- active_version=v1.6；
- v1.6 正式数据；
- manifest；
- 40 案例；
- 302 曲目；
- 400 指标记录；
- SQL Server / Neo4j；
- 原审计版 CSV。

## 5. 结论

```text
CONDITIONAL_PASS
batch_01_sealed=false
batch_02_started=false
P18_started=false
```
