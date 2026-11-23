# P17-E 第二批内容核验报告

## 1. 核验范围

除 CASE008 外，19 个 HTTP 200 来源逐页抓取：

```text
content_partially_verified：8
content_unreadable：7
content_not_relevant：4
content_verified：0
```

注意：8 个 partial 是“页面抓取成功且出现案例关键词”，不是人工全文确认。

## 2. 部分核验（8）

```text
CASE001、CASE005、CASE009、CASE010、
CASE012、CASE030、CASE032、CASE038
```

这些页面出现人物/机构/活动等匹配词，可支持“页面涉及该案例”的部分事实；  
未逐项确认活动完成、具体曲目、受众反馈或传播结果。

## 3. 正文不可读（7）

```text
CASE026、CASE028、CASE031、CASE033、
CASE034、CASE037、CASE039
```

可能原因：

- JS 渲染；
- PDF/二进制；
- 反爬/空白页；
- 编码/正文抽取失败。

不能据此判定来源不存在。

## 4. 不相关（4）

```text
CASE014、CASE017、CASE035、CASE036
```

抓取到页面，但未出现与目标案例匹配的关键词，或页面是泛机构/活动列表页。

## 5. CASE008

保持已人工核验：

```text
梅花三弄、流水：performance_confirmed
平沙落雁、酒狂、阳关三叠：program_listed
outcome_evidenced：0
```

## 6. 结论

```text
无新增 content_verified
8 个 content_partially_verified
7 个 content_unreadable
4 个 content_not_relevant
```

全部 19 个非 CASE008 来源仍需人工或替代来源复核。

## 7. 输出

- `source_content_verification.csv`
- `source_manual_review_queue.csv`
