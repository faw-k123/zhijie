# P17.1 正式数据基线复核

> 审计时间：2026-11-03  
> 只读；未修改正式版本。

## 1. 版本

```text
active_version = v1.6
```

## 2. 记录

```text
案例：40
来源关系：62
指标记录：400
有效评分：94
null：306
曲目：302
明确曲目—案例关联：5
区域矩阵：1,812
```

## 3. 案例完整性

- CASE001–CASE040 完整；
- case_id 唯一；
- case_type、analysis_sample、strict_sample_eligible、owner_approval_status 存在；
- CASE007 仍为 pending_review；
- 来源 ID 均可关联。

## 4. 曲目

- 302 首；
- song_id 唯一；
- 5 条关联仍全部对应 CASE008；
- 区域矩阵仍为 1,812。

## 5. 哈希

主 manifest：

```text
ad789f89352c7e73f7d1d3f5f2ff4d9cf014f1fe04a7d8cfe1d1f95a7dd5741a
```

v1.6 五个数据文件哈希见：

```text
research/analysis/p17/p17-baseline-audit.json
```

## 6. 结论

```text
PASS
```

正式基线未变化。
