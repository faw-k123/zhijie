# P17-E 证据缺口报告（第一批）

## 1. 案例缺口

```text
40 个案例
内容已逐页确认：1（CASE008）
URL 可访问但内容未核验：19
来源不可访问：19
HTTP 202：1
```

因此：

- 39 个案例仍不能声称外部原文已核实；
- 0 个案例新增“实际活动确认”；
- 0 个案例新增“传播结果证据”。

## 2. CASE008 曲目缺口

```text
梅花三弄：performance_confirmed
流水：performance_confirmed
平沙落雁：program_listed
酒狂：program_listed
阳关三叠：program_listed
```

缺口：

- 3 首仍只有节目单级证据；
- 2 首有演出后报道，但无受众结果；
- 所有 5 首均无 outcome_evidenced。

## 3. 302 首曲目

```text
外部检索：0/302
状态：NOT_STARTED
```

没有把 `not_searched` 写成 `no_result`。

## 4. 严格个人

```text
新候选：0
合格：0
```

## 5. 下一批优先

1. 20 个可访问来源逐页核验；
2. 19 个失败来源人工重试/存档；
3. 3 首 CASE008 曲目继续找演出后证据；
4. 启动 302 首外部检索，分批记录；
5. 再做严格个人候选检索。

## 6. 输出

- `02_case_reverification/case_reverification.csv`
- `04_case008_performance/case008_song_recheck.csv`
- `01_song_evidence/song_search_coverage.csv`
