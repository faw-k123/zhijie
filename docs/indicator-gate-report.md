# 指标级统计门禁实施报告

> 阶段：P8 后研究数据质量修复
> 日期：2026-10-30
> 范围：`success-factors` API、P5 研究洞察页、测试与契约
> 版本状态：v1.1 reviewed / active（2026-10-30 激活）；v1.0 保留为历史版本

---

## 1. 问题

v1.1 达到 10 例后，原实现会把任何有评分的指标放入排行榜：

- `emotional_resonance` 只有 1 例有评分；
- 该指标仍可能以均值 3.0 排第 1；
- 这会把“低覆盖”误判为“重要传播因素”。

原门禁只看总样本 n≥5，没有看单个指标的有效评分数量。

---

## 2. 新门禁

单个指标有效评分 `n`：

| n | status | 含义 | 是否排序 |
|---:|---|---|---|
| 0 | `empty` | 暂无数据 | 否 |
| 1—4 | `insufficient` | 证据不足 | 否 |
| 5—19 | `exploratory` | 探索性展示 | 否；显示 n、缺失量、均值 |
| ≥20 | `descriptive` | 描述性 | 是 |

总样本：

- `<5`：`availability=unavailable`，`rankings=null`；
- `5—19`：`availability=exploratory`，`rankings=[]`；
- `≥20`：`availability=descriptive`，只把 `n≥20` 的指标放入 `rankings`。

---

## 3. API 变化

`GET /api/research/success-factors/` 的每个 `factor` 新增：

```json
{
  "status": "insufficient",
  "status_label": "证据不足",
  "ranking_allowed": false,
  "gate_note": "有效评分少于5例，不参与排行榜；仅可作为单案例记录。",
  "rank": null
}
```

新增：

- `thresholds.indicator_exploratory_min = 5`
- `thresholds.indicator_rank_min = 20`
- `gate_counts: { empty, insufficient, exploratory, descriptive }`

`rankings` 只包含 `status=descriptive` 的指标；`n=1—19` 均不进入排行榜。

契约已更新：

- [p2-api-contract.md](<p2-api-contract.md>)
- [final-api-contract.md](<final-api-contract.md>)

---

## 4. v1.1 实测

临时把 active_version 指向 v1.1 后：

```text
availability = exploratory
rankings = []
gate_counts = {
  insufficient: 3,
  exploratory: 7,
  descriptive: 0
}
```

关键指标：

```text
emotional_resonance: n=1, status=insufficient, rank=null
timbre_identity:     n=3, status=insufficient, rank=null
audience_participation: n=3, status=insufficient, rank=null
story_explainability: n=10, status=exploratory, rank=null
sustainability:       n=10, status=exploratory, rank=null
```

结论：n=1 的情感共通性不再排第一；v1.1 只做探索性展示，不生成排行榜。

2026-10-30 负责人确认后，v1.1 已正式激活：

```text
active_version = v1.1
v1.1.status = reviewed
```

---

## 5. P5 页面

研究洞察 → 成功传播机制新增“指标级统计门禁”区：

- 10 项指标逐项展示；
- 显示 `有效 n`、`缺失数`、`均值`；
- 显示状态：暂无数据 / 证据不足 / 探索性 / 描述性；
- 只有描述性指标才有排名；
- 顶部状态：“描述性可排序 / 探索性展示 / 证据不足”。

---

## 6. 测试

```text
python manage.py check
System check identified no issues (0 silenced).

python manage.py validate_research_data
OK active_version=v1.0 status=reviewed cases=3 scores=30 warnings=0

python manage.py test propagation.tests
Found 25 test(s)
Ran 25 tests
OK

npm run type-check
通过

npm run build-only
通过（既有 chunk size warning）
```

新增测试：

- `indicator_gate(0/4/5/19/20)` 阈值；
- v1.0 下 10 个 factor 均为 insufficient，`rankings=null`；
- v1.1 下 `emotional_resonance` n=1 为 insufficient，`rankings=[]`。

---

## 7. 版本结论

| 版本 | 状态 |
|---|---|
| v1.0 | 历史版本 / reviewed |
| v1.1 | active / reviewed |

门禁问题已解决，但 v1.1 仍不激活，原因是案例口径：CASE008/009 是机构/教育传播，CASE004/010 含中国境内活动，不能直接混入“严格外国个人海外演出”样本。

下一步不是继续加代码，而是先确认案例分类口径，再决定 v1.1 是否 reviewed。
