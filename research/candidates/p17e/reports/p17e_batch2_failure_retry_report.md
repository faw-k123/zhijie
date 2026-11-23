# P17-E 第二批失败来源重试报告

## 1. 重试总量

```text
失败来源：19
重试：19 次（每个 1 次）
恢复访问：7
仍失败：12
HTTP 202：1（单独处理，不重试）
```

## 2. 按原始失败类型

| 原始失败 | 数量 | 重试恢复 | 仍失败 |
|---|---:|---:|---:|
| SSL/TLS 中断（排除 CASE008） | 12 | 5 | 7 |
| HTTP 502 | 5 | 2 | 3 |
| HTTP 403 | 2 | 0 | 2 |
| HTTP 202 | 1 | — | 挑战页 |

CASE008 首次 SSL 失败后已人工打开，不纳入“仍失败”。

## 3. 恢复的 7 个

重试后恢复访问，但正文尚未逐页核验：

- 5 个 SSL 恢复；
- 2 个 502 恢复。

因此标记：

```text
needs_more_evidence
```

不是 `content_verified`。

## 4. 仍失败的 12 个

```text
CASE002、CASE003、CASE004、CASE006、CASE013、CASE015、
CASE018、CASE019、CASE021、CASE022、CASE024、CASE029
```

保持：

```text
source_unavailable
```

并进入人工复核队列，不写成“来源不存在”。

## 5. HTTP 202

```text
CASE025
url_access_status = challenge_or_pending
content_review_status = content_not_reviewed
case_conclusion = needs_more_evidence
```

## 6. 输出

- `source_recheck_batch2.csv`
- `source_manual_review_queue.csv`
