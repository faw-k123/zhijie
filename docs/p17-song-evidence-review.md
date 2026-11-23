# P17.3 302首曲目海外传播证据检索

## 1. 检索范围

本阶段完成：

- 302 首曲目逐曲建立检索记录；
- 检索渠道：现有研究语料、既有 5 条映射、P11 区域矩阵；
- 外部公开网页逐曲检索：**未执行**。

## 2. 结果

```text
曲目：302
内部语料扫描记录：302
外部网页检索：0
A 明确（既有）：5
B 弱关联：0
C 待核实：0
D 当前未发现：297
新增 A：0
明确关联覆盖率：5/302 = 1.66%
实际演出确认：0
仅节目单级：5
传播结果证据：0
```

## 3. 5 条既有 A 类

```text
23 平沙落雁
158 梅花三弄
26 流水
28 酒狂
29 阳关三叠
```

全部为 CASE008 `program_listed`，`performance_confirmed=NO`。

## 4. 297 首 D 类

```text
no_evidence_found_in_existing_corpus
```

不是：

```text
never_performed_overseas
```

只表示当前内部检索没有发现证据。

## 5. 外部检索状态

```text
external_web_status = NOT_EXECUTED
```

没有把搜索摘要、推测或同名曲目当作新证据。

## 6. 输出

- `research/candidates/p17/song_search_log.csv`（302行）
- `research/candidates/p17/song_evidence_candidates.csv`（0条新增）
- `research/analysis/p17/song_evidence_coverage.csv`
- [曲目覆盖图](<research/analysis/p17/charts/song_evidence_coverage.svg>)
