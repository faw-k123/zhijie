# P17-E 第八批：六条 ambiguous 专项补证报告

> 日期：2026-11-05  
> 范围：song_id 1、5、12、17、19、22  
> 结论：**CONDITIONAL_PASS（补证完成，证据仍未解决）**

## 1. 总体

```text
处理曲目：6
实际检索：6
新增有效证据：0
confirmed_relevant：0
rejected_match：0
remain_ambiguous：6
打开有效原始网页：0
```

这 6 条没有一条被强行升级。

## 2. 逐条结果

| song_id | 曲目 | 当前状态 | 原因 |
|---:|---|---|---|
| 1 | 三寸天堂 | ambiguous_match | 胡琴学院页面抓取失败；无海外活动页 |
| 5 | 倩女幽魂 | ambiguous_match | 仅微信视频线索；无原始 URL/正文 |
| 12 | 葬花吟 | ambiguous_match | 小红书 404；无牛津活动主办方页 |
| 17 | 万蝶振翅 | ambiguous_match | B站/古筝网验证码；无官方活动记录 |
| 19 | 关山月 | ambiguous_match | 微信环境验证；无法打开伯克利活动正文 |
| 22 | 卧龙吟 | ambiguous_match | B站验证码；无法核对雅集主体与日期 |

## 3. 关键边界

- 404 不等于活动不存在；
- 验证码/抓取失败不等于无证据；
- 视频标题不等于正文确认；
- 机构名含地名不等于活动在当地举行；
- 没有新增 `performance_confirmed`；
- 没有新增 `outcome_evidenced`；
- 没有新增正式歌曲—案例关联。

## 4. batch_01 状态不变

```text
performance_confirmed：3（3、13、24）
ambiguous_match：6（1、5、12、17、19、22）
rejected_match：1（8）
no_relevant_result_after_search：15
not_searched：0
outcome_evidenced：0
合计：25
```

`batch_01_sealed=false`。

## 5. 数据安全

```text
active_version = v1.6
v1.6 文件哈希未变化
manifest 未变化
40 案例未修改
302 曲目未修改
400 指标记录未修改
SQL Server / Neo4j 未写入
```

## 6. 输出

- `batch_01_ambiguous_supplement_batch8.csv`
- `batch_01_ambiguous_evidence_batch8.csv`
- `batch_01_ambiguous_coverage_batch8.csv`
- `batch_01_ambiguous_manual_review_batch8.csv`

## 7. 结论

```text
CONDITIONAL_PASS
```

6 首均完成补证检索，但没有新增可确认证据；仍不封存。  
不启动 batch_02，不启动 P18。
