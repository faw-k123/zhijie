# v1.2 第四阶段：候选证据闭环与正式准入建议报告

> 日期：2026-11-01  
> 依据：v1.2 第一阶段候选池、第二阶段五例补证、第三阶段身份标准  
> 范围：只形成准入建议；不创建 v1.2 正式案例、不分配 CASE 编号、不生成评分

---

## 1. 本轮结论

| 准入状态 | 数量 |
|---|---:|
| `approved_strict` | **0** |
| `approved_extended` | **26** |
| `pending_evidence` | **7** |
| `excluded` | **3** |
| 合计 | **36** |

关键结论：

- **没有候选达到 `approved_strict`。**
- CAND024 仍为 `pending_evidence`：身份、乐器、地点、日期有来源，但演出完成只有 program 记录。
- 26 条进入扩展样本建议，不等于正式 CASE，也不等于负责人已批准。
- 3 条重复（CAND021、CAND034、CAND035）不新建独立案例。

---

## 2. 严格个人样本

| 候选 | 身份 | 乐器 | 实际演奏 | 海外地点 | 日期 | 严格准入 |
|---|---|---|---|---|---|---|
| CAND024 Randy Raine-Reusch | Canada（CMC 标题） | 古筝（Western Front program） | `program_listed` | 温哥华 | 2010-04-08 | `pending_evidence` |

原因：

- 加拿大身份有 CMC 标题支持，但正文 403；
- 古筝二人演出有档案 program；
- 未找到演出后报道/录像/现场记录；
- 不能把 `program_listed` 改成 `performed_confirmed`；
- 不能把演出记录写成传播效果。

所以 **CAND024 仍可进入严格复核，但本轮不批准 `approved_strict`**。

---

## 3. 扩展样本池

共 26 条 `approved_extended`：

| 类别 | 数量 |
|---|---:|
| `overseas_institution_education` | 12 |
| `overseas_ensemble_performance` | 7 |
| `cross_cultural_collaboration` | 4 |
| `community_music_activity` | 3 |

包括：

- 机构/教育：Duke、UCLA、Qingyun、IU、Illinois、Pitt、OSU、Williams、Toronto、Vancouver、UK Chinese Music、CAND019 等；
- 乐团/演出：NY Chinese Music Ensemble、Ba Ban、Melody of China、Harmony Guzheng、Seattle Chinese Orchestra、Chung Wah、Chao Feng、Australian Chinese Music Ensemble、Grand Chinese New Year Berlin 等；
- 跨文化合作：CAND026 Belle、CAND028 Nicholas Ng、CAND031 Wu Fei/Abigail、CAND033 Mona Li；
- 社区活动：CAND010、CAND016、CAND019；
- 乐团/教育：CAND036 东京古筝乐团。

扩展样本准入不等于：

- 已核实成员国籍；
- 已核实演出完成；
- 已核实传播效果。

---

## 4. 待补证与排除

### pending_evidence（7）

- CAND023 Chinese Music Society of North America：研究组织，缺具体演出；
- CAND024 Randy Raine-Reusch：缺演出完成记录；
- CAND025 Shane Spurgeon：中国境内活动；
- CAND027 Chris Stephens：中国乐器/演奏未核；
- CAND029 Sydney 非华裔学习者研究：匿名，无具名演奏者；
- CAND030 Libertas Folk Sessions：演奏者/乐器未知；
- CAND032 Jia Ling：国籍/项目身份标准未确认。

### excluded（3）

- CAND021 London Youlan：与 CASE008 重复；
- CAND034 Bard Chinese Ensemble：与 CASE002 重复；
- CAND035 Bard East/West：与 CASE009 重复。

---

## 5. 来源与差异

- 本轮新增来源仅 1 条：CAND026-S003（San Marino RTV，2026-09-12，演出报道；不含国籍）；
- CAND024 搜索后未找到演出后记录，保留 `program_listed`；
- CAND028/033/036 无新增国籍证据，维持 `identity_pending` / 扩展样本；
- 第二阶段、第三阶段结论均保留，不删除。

---

## 6. 准入建议 vs 正式批准

```text
准入建议：approved_extended 26 条
正式负责人批准：0 条
正式 CASE 编号：未分配
v1.2 cases.json：未创建
```

`approved_extended` 只是研究管理建议，不等于正式案例。

---

## 7. 当前状态

```text
active_version = v1.1
v1.0 / v1.1 未修改
v1.2 正式数据未创建
严格正式样本新增 = 0
```
