# P2 后端研究数据服务层报告

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P2（研究数据服务层 + 7 个只读 API）
> 日期：2026-10-30
> 状态：P2 完成，等待验收
> 范围：只做数据读取、哈希校验、基础统计、样本充分性判断和只读 API
> 未做：前端页面、Vue 组件、数据库表、migration、现有接口改造

---

## 1. 本阶段完成内容

1. 将 manifest 的 `v1.0` 状态由 `draft` 改为 `reviewed`，记录审核人和审核日期。
2. 新增统一数据加载器 `research_data.py`。
3. 新增统计与充分性判断层 `research_analytics.py`。
4. 新增 7 个只读 API，并接入 `api/views.py`、`api/urls.py`。
5. 新增 17 个单元/接口测试。
6. 新增管理命令 `python manage.py validate_research_data`。
7. 保持旧接口 `/api/global/propagation/` 行为不变，并用测试验证。
8. 未修改 `research/data/v1.0/` 四个数据文件；其哈希仍与 manifest 一致。

---

## 2. 数据加载器

文件：

[backend/propagation/research_data.py](<backend/propagation/research_data.py>)

对外函数：

| 函数 | 作用 |
|---|---|
| `load_manifest()` | 读取并校验 manifest 结构 |
| `get_active_version()` | 返回当前 `active_version` |
| `load_cases()` | 返回清洗后的案例数据 |
| `load_success_factors()` | 返回清洗后的指标评分 |
| `load_music_scores()` | 返回音乐潜力文档 |
| `load_regional_matrix()` | 返回区域矩阵文档 |
| `validate_hash()` | 校验单个文件大小与 SHA256 |
| `load_bundle()` | 一次加载并校验四个文件，供 API 使用 |
| `clear_cache()` | 测试/版本切换时清空缓存 |

加载流程：

```text
manifest.json
  ↓ 结构校验
active_version
  ↓ 必须存在且 status=reviewed
v1.0/
  ↓ 四个文件逐一校验 bytes + SHA256
cases / success_factors / music_scores / regional_strategies
  ↓ 单条记录清洗
bundle
```

关键行为：

- **只接受 `reviewed`。** `draft` 返回 503 `version_not_reviewed`，不会“边写边被接口读到”。
- **哈希失败不加载。** 文件大小或 SHA256 不一致返回 503 `hash_mismatch` / `file_size_mismatch`。
- **缓存带数据签名。** 缓存键包含 manifest 哈希和四个文件的 mtime/size；文件变化会重新校验。
- **单条坏数据隔离。** 缺字段、重复 ID、来源数量不一致、评分越界、来源不存在的记录会被跳过并进入 `warnings`，不会拖垮整个模块。
- **来源关联校验。** 评分的 `source_ids` 必须是该案例 `sources` 的子集；已知评分必须有至少一个来源。
- **未知值保持 `null`。** 数据层不会把 `null` 转成 0。

---

## 3. 统计层

文件：

[backend/propagation/research_analytics.py](<backend/propagation/research_analytics.py>)

### 3.1 样本充分性

所有接口统一返回：

```json
{
  "sample": {
    "n": 3,
    "target": 40,
    "status": "insufficient",
    "label": "证据不足：样本少于5例",
    "progress_percent": 7.5,
    "thresholds": { "exploratory": 5, "descriptive": 20 }
  }
}
```

| n | status |
|---|---|
| 0 | `empty` |
| 1—4 | `insufficient` |
| 5—19 | `exploratory` |
| ≥20 | `descriptive` |

前端不需要计算状态；直接用 `sample.status` 和 `sample.label`。

### 3.2 禁止隐式排名

- `n<5` 时，`success-factors` 返回：
  - `availability="unavailable"`
  - `rankings=null`
  - `factors=[]`
  - 明确 `reason`
- `statistics` 只返回计数分布和指标覆盖数：
  - 不返回成功率排行；
  - 不返回国家偏好排行；
  - `rankings_allowed=false`；
  - `success_factors_available=false`。
- 只有 `n≥5` 时，成功因素才可能返回 `availability="available"` 和 `rankings`。
- `music-potential` 与 `regional-matrix` 当前 `pending`，返回 `items=[]`、`rankings=null` 或 `rows=[]`、`matrix=null`。

### 3.3 其他统计

- 案例均分 = 有效指标合计 ÷ 有效指标数；未知不补 0。
- 有效指标 <6 时标记 `low_coverage=true`。
- 相似案例规则：同乐器 40、同音乐类型 15、同国 15/同区域 10、共同主题每个 8（最多 24）、共同渠道每个 4（最多 12）。
- 相似案例返回匹配理由，不只返回 ID。

---

## 4. 7 个只读 API

详细字段、查询参数与错误码见：

[P2 研究数据 API 契约](<docs/p2-api-contract.md>)

| # | 方法 | 路径 | 当前结果 |
|---|---|---|---|
| 1 | GET | `/api/research/status/` | 200，3/40，insufficient，7.5% |
| 2 | GET | `/api/research/cases/` | 200，3 条案例，支持筛选/分页 |
| 3 | GET | `/api/research/cases/CASE001/` | 200，10 项编码 + 相似案例 |
| 4 | GET | `/api/research/statistics/` | 200，分布 + 指标覆盖，无排行 |
| 5 | GET | `/api/research/success-factors/` | 200，`unavailable`，`rankings=null` |
| 6 | GET | `/api/research/music-potential/` | 200，`pending`，`items=[]` |
| 7 | GET | `/api/research/regional-matrix/` | 200，`pending`，`rows=[]` |

实测状态：

```text
/api/research/status/             200 True
/api/research/cases/              200 True
/api/research/cases/CASE001/      200 True
/api/research/statistics/         200 True
/api/research/success-factors/    200 True
/api/research/music-potential/    200 True
/api/research/regional-matrix/    200 True
```

### 4.1 关键响应

状态：

```json
{
  "sample": { "n": 3, "target": 40, "status": "insufficient", "progress_percent": 7.5 },
  "version": { "active_version": "v1.0", "status": "reviewed" },
  "counts": { "cases": 3, "sources": 7, "countries": 3, "instruments": 2 },
  "grade_counts": { "A": 0, "B": 3, "C": 0, "D": 0 }
}
```

成功因素（当前）：

```json
{
  "sample": { "n": 3, "target": 40, "status": "insufficient" },
  "availability": "unavailable",
  "rankings": null,
  "factors": [],
  "reason": "样本不足5例，统计层不提供成功因素排行；仅展示单案例评分。"
}
```

音乐潜力（当前）：

```json
{
  "availability": "pending",
  "status": "pending",
  "status_label": "待补充",
  "music_sample": { "n": 0, "target": 20, "status": "empty" },
  "items": [],
  "rankings": null
}
```

区域矩阵（当前）：

```json
{
  "availability": "pending",
  "status": "pending",
  "rows": [],
  "matrix": null
}
```

---

## 5. 测试结果

命令：

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test propagation.tests -v 2
```

结果：

```text
Found 17 test(s)
Ran 17 tests
OK
```

测试覆盖：

| 类别 | 数量 |
|---|---:|
| 7 个接口正常返回 | 7 |
| 每个接口都返回 `sample` | 1 |
| 案例筛选/分页 | 2 |
| 非法分页参数 | 1 |
| 案例详情/404 | 2 |
| 统计无排行 + 指标覆盖 | 1 |
| 成功因素 `unavailable` | 1 |
| 音乐潜力 pending | 1 |
| 区域矩阵 pending | 1 |
| 旧接口行为不变 | 1 |
| 样本阈值 0/1/4/5/19/20/40 | 1 |
| draft 版本拒绝 | 1 |
| SHA256 不一致拒绝 | 1 |
| 非法 JSON 拒绝 | 1 |
| 空案例 → `empty` | 1 |

其他检查：

```text
python manage.py check                 → System check identified no issues
python manage.py validate_research_data → OK active_version=v1.0 status=reviewed cases=3 scores=30 warnings=0
npm run type-check                     → exit 0
```

---

## 6. 代码变更清单

### 6.1 新增

| 文件 | 行数 | 作用 |
|---|---:|---|
| `backend/propagation/research_data.py` | 482 | 统一数据加载、哈希、清洗、缓存 |
| `backend/propagation/research_analytics.py` | 490 | 样本充分性、统计、排行门禁、相似案例 |
| `backend/propagation/tests.py` | 229 | 17 个测试 |
| `backend/propagation/management/commands/validate_research_data.py` | 30 | 管理命令：校验 manifest、哈希与记录 |
| `backend/propagation/management/__init__.py` | 1 | management 包 |
| `backend/propagation/management/commands/__init__.py` | 1 | commands 包 |

### 6.2 修改

| 文件 | 改动 |
|---|---|
| `backend/api/views.py` | 新增研究模块 import 与 7 个只读视图；未改动旧视图逻辑 |
| `backend/api/urls.py` | 新增 7 条 `/api/research/.../` 路由；未改动旧路由 |
| `research/data/manifest.json` | `v1.0` 状态改为 `reviewed`，记录审核人/日期 |
| `docs/p1-data-conversion-report.md` | 同步 manifest 状态与文件大小 |
| `research/data/README.md` | 同步 reviewed 状态与 P2 说明 |
| `docs/data-contract-v1.md` | 补充 P2 样本阈值、版本状态语义 |
| `docs/research-module-plan-v1.md` | 将 API 表更新为 P2 的 7 个接口 |

### 6.3 未修改

- 前端业务代码：0 个文件。
- `backend/propagation/services.py`：未改。
- 数据库表、migration：0 个。
- `research/data/v1.0/` 四个文件：未改，SHA256 与 manifest 一致。
- SQL Server / Neo4j：未启动、未修改。

---

## 7. P2 验收对照

- [x] `research_data.py` 统一读取 manifest 和 active_version。
- [x] 四个 JSON 全部通过 SHA256 校验后再加载。
- [x] 7 个 API 返回结构符合数据契约。
- [x] 每个接口都返回 `sample.n/status`。
- [x] `n<5` 时排行榜返回 `unavailable`，不是空排行榜。
- [x] `pending` 文件仍返回待补充状态。
- [x] 没有修改现有接口行为（旧传播接口测试通过）。
- [x] `manage.py check` 通过。
- [x] 新接口单元测试通过（17/17）。
- [x] 前端类型检查通过（未改前端）。
- [x] `validate_research_data` 管理命令通过，warnings=0。

---

## 8. 已知限制

1. 当前只有 3 个案例，所有排行/机制结论仍不可用。
2. 音乐潜力与区域矩阵仍为 `pending`，接口按待补充返回。
3. P2 不提供单曲上下文接口和方案生成接口，分别留到 P6、P7。
4. 数据服务只读，不提供审核、编辑、上传功能。
5. `v1.0` 数据文件为只读；修正数据必须新建 `v1.1/` 并切换 manifest。

---

## 9. P3 进入条件

P3 只做前端共用组件与全球传播页，不再改后端结构。进入 P3 前确认：

1. 接受 7 个接口路径与字段。
2. 接受 `sample.status/insufficient` 和 `rankings=null` 的返回方式。
3. 接受音乐潜力/区域矩阵当前只显示“待补充”。
4. 接受 P3 只消费 P2 接口，不新增后端接口；如确需新增，先更新本报告和 API 契约。

P2 到此停止，不开始写 Vue。
