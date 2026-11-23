# P17-E 第七批 B：batch_01 七条 ambiguous 人工复核报告

> 复核日期：2026-11-05  
> 结论：**CONDITIONAL_PASS（未封存）**  
> 结果：confirmed_relevant 0；remain_ambiguous 6；rejected_match 1

## 1. 复核结果

| song_id | 曲目 | 结论 | 依据 |
|---:|---|---|---|
| 1 | 三寸天堂 | remain_ambiguous | 台湾胡琴学院页面，无法确认海外活动 |
| 5 | 倩女幽魂 | remain_ambiguous | 只有微信视频线索，无原始活动页 |
| 8 | 江南 | **rejected_match** | 加拿大报道曲目单不含《江南》 |
| 12 | 葬花吟 | remain_ambiguous | 小红书 404，无法核对 |
| 17 | 万蝶振翅 | remain_ambiguous | B站验证码，无法核对 |
| 19 | 关山月 | remain_ambiguous | 小红书 404 |
| 22 | 卧龙吟 | remain_ambiguous | B站验证码 |

## 2. 唯一明确拒绝

### song_id 8《江南》

来源：澎湃号·政务/无锡发布  
标题：《远渡重洋，江南音韵惊艳加拿大！》  
日期：2026-07-17  
地点：加拿大渥太华、多伦多

正文曲目：

```text
《金蛇狂舞》
《世间始终你好》
《二泉映月》
《红河谷》
《百鸟朝凤》
《夜深沉》
《十面埋伏》
```

**没有出现歌曲《江南》。**  
“江南音韵”指江南丝竹风格，不是目标流行歌曲《江南》。

结论：

```text
rejected_match
```

不能把区域报道当作目标曲目证据。

## 3. 其余 6 条

保持 `ambiguous_match`：

- 三寸天堂：页面抓取失败；
- 倩女幽魂：无原始 URL/正文；
- 葬花吟：404；
- 万蝶振翅：B站验证码；
- 关山月：小红书 404；
- 卧龙吟：B站验证码。

页面无法访问不能判定活动不存在；  
但也不能据此确认演出或传播结果。

## 4. 三条演出确认保护

保留不变：

```text
song_id 3  一生所爱
song_id 13 赛马
song_id 24 广陵散
```

`outcome_evidenced=0`。

## 5. batch_01 复核后状态

如果采纳本轮结论：

```text
performance_confirmed：3
ambiguous_match：6
rejected_match：1
no_relevant_result_after_search：15
not_searched：0
```

仍不能封存：6 条 ambiguous 未确认。

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

- `batch_01_ambiguous_review_batch7B.csv`
- `batch_01_ambiguous_evidence_batch7B.csv`
- 本报告

## 8. 结论

```text
CONDITIONAL_PASS
```

1 条错误匹配已明确拒绝，6 条仍需人工证据。  
不启动 batch_02，不启动 P18，不封存 batch_01。

## 9. 结果采纳

本轮结论已被采纳：song_id 8 更新为 `rejected_match`，其余 6 条保持 `ambiguous_match`。

采纳后 batch_01 状态：

```text
performance_confirmed=3
ambiguous_match=6
rejected_match=1
no_relevant_result_after_search=15
not_searched=0
合计=25
```

`batch_01_sealed=false`，不启动 batch_02，不启动 P18。
