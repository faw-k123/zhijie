# P17-E 来源质量报告

## 1. 范围

```text
正式来源关系：62
本批首要来源检查：40
次级来源未检查：22
```

## 2. 40 个首要来源

| 状态 | 数量 |
|---|---:|
| HTTP 200 | 20 |
| HTTP 202 | 1 |
| 请求失败 | 19 |

失败类型：

```text
SSL 错误：12
502：5
403：2
其他：1
```

## 3. 内容核验

```text
已逐页确认内容：1（CASE008）
URL可访问但内容未核验：19
HTTP202未核验：1
来源不可用：19
```

不能把 URL 可访问等同于内容支持案例。  
不能把来源数量等同于独立来源数量。

## 4. 同源

`source_clusters.csv` 按 publisher/机构建立 cluster：

- Xinhua 多语种/多页面需归同组；
- 同一活动多平台转载需归同组；
- 22 个次级来源尚未外部核验。

## 5. 输出

- `02_case_reverification/source_recheck.csv`
- `02_case_reverification/source_clusters.csv`
