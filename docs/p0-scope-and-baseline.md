# P0 范围、备份与基线记录

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P0（仅备份、范围确认、数据结构确认）
> 日期：2026-10-30
> 状态：P0 完成，等待验收后进入 P1
> 决策：页面范围 A / 视觉 A / 受众原声 A
> 关联文档：[改造方案](research-module-plan-v1.md) · [数据契约](data-contract-v1.md)

---

## 1. 本阶段做了什么

- 按评审意见锁定 A / A / A，不推翻原方案。
- 将六项补充要求写入方案和验收标准：
  1. 统一数据字段规范；
  2. 数据充分性判断；
  3. 数据来源追溯；
  4. 编码有效数量；
  5. 区域匹配解释；
  6. 版本与回滚。
- 备份 16 个计划修改/依赖文件，生成 SHA256 清单。
- 保存前端类型检查与 Django system check 基线日志。
- 定义 `research/data/` 版本化目录和数据契约。
- **没有修改任何前后端业务代码。**

---

## 2. 范围清单

### 2.1 本阶段允许创建

| 路径 | 用途 |
|---|---|
| `backup/p0_pre_research_20261030_101626/` | 回滚备份 |
| `docs/data-contract-v1.md` | 数据结构契约 |
| `docs/p0-scope-and-baseline.md` | 本文件 |
| `research/data/README.md` | 数据目录说明 |

### 2.2 后续阶段计划修改

| 文件 | 阶段 | 处理 |
|---|---|---|
| `frontend/src/views/GlobalEffectView.vue` | P3 | 重写页面主体 |
| `frontend/src/views/MusicDetailView.vue` | P6 | 只加第四个 Tab |
| `frontend/src/views/PromoReportView.vue` | P7 | 重写为方案生成器 |
| `frontend/src/components/AppNav.vue` | P8 | 新增“国际传播”分组 |
| `frontend/src/router/index.ts` | P3/P4/P5 | 新增 3 条路由 |
| `frontend/src/assets/premium.css` | P3 | 追加研究页作用域样式 |
| `frontend/src/api/propagation.ts` | P3 | 保留旧接口，补新调用或迁移 |
| `frontend/src/api/dataDisplay.ts` | P6 | 仅在需要时补类型，不破坏旧调用 |
| `frontend/package.json` | P3 | 原则上不改依赖 |
| `frontend/vite.config.ts` | P3 | 原则上不改；地图资源走本地 |
| `backend/api/urls.py` | P2 | 新增 7 条研究接口 |
| `backend/api/views.py` | P2 | 新增研究接口视图 |
| `backend/propagation/services.py` | P2 | 保留旧逻辑，新增转发 |
| `backend/myproject/urls.py` | P2 | 原则上不改；沿用 `/api/` |
| `backend/myproject/settings.py` | P2 | 原则上不改；不新增 app/migration |
| `docs/research-module-plan-v1.md` | P0 | 已按评审意见更新 |

### 2.3 后续阶段计划新增

| 路径 | 阶段 | 用途 |
|---|---|---|
| `research/data/manifest.json` | P1 | 数据版本清单 |
| `research/data/v1.0/cases.json` | P1 | 案例主表 |
| `research/data/v1.0/success_factors.json` | P1 | 10 项编码长表 |
| `research/data/v1.0/music_scores.json` | P1 | 音乐潜力评分 |
| `research/data/v1.0/regional_strategies.json` | P1 | 区域矩阵 |
| `research/07_系统导入数据/*.csv` | P1 | 研究侧可编辑入口 |
| `backend/propagation/research_data.py` | P2 | 加载、校验、缓存 |
| `backend/propagation/research_analytics.py` | P2 | 统计与充分性判断 |
| `backend/propagation/plan_generator.py` | P7 | 方案生成 |
| `frontend/src/views/GlobalCaseLibraryView.vue` | P4 | 案例库 |
| `frontend/src/views/GlobalCaseDetailView.vue` | P4 | 案例详情 |
| `frontend/src/views/ResearchInsightsView.vue` | P5 | 研究洞察三 Tab |
| `frontend/src/api/research.ts` | P3 | API 客户端 |
| `frontend/src/types/research.ts` | P3 | 类型定义 |
| `frontend/src/components/research/*` | P3 | 共用组件 |
| `backend/media/research/cases/*` | P4 | 案例封面 |

### 2.4 明确不动

- 不新增数据库表，不新增 migration。
- 不修改 SQL Server 表结构。
- 不修改 Neo4j 数据。
- 不修改首页、音乐展示、情感分析、私人空间、AI 音乐等无关页面。
- 不重写 `MusicDetailView.vue` 原有三个 Tab。
- 不删除旧接口 `/api/global/propagation/`、`/api/promo/report/`。
- 不引入新的前端框架或图表库；沿用 Vue 3 + ECharts。
- 不在 P0 写入 3 个案例 JSON（P1 才做）。

---

## 3. 备份记录

备份目录：

```text
backup/p0_pre_research_20261030_101626/
```

清单文件：

```text
backup/p0_pre_research_20261030_101626/MANIFEST.json
```

备份统计：

| 项目 | 值 |
|---|---|
| 文件数 | 16 |
| 总字节 | 225,819 |
| 校验方式 | 复制前后 SHA256 逐文件比对 |
| 结果 | 16/16 一致 |

已备份文件：

```text
frontend/src/views/GlobalEffectView.vue
frontend/src/views/MusicDetailView.vue
frontend/src/views/PromoReportView.vue
frontend/src/components/AppNav.vue
frontend/src/router/index.ts
frontend/src/assets/premium.css
frontend/src/api/propagation.ts
frontend/src/api/dataDisplay.ts
frontend/package.json
frontend/vite.config.ts
backend/api/urls.py
backend/api/views.py
backend/propagation/services.py
backend/myproject/urls.py
backend/myproject/settings.py
docs/research-module-plan-v1.md
```

说明：

- 没有复制 `node_modules`、`.venv`、`media`、数据库文件。
- 备份目录只用于回滚，不参与构建。
- 后续每阶段只改本阶段清单内文件；如果必须超出范围，先更新本文件再改。
- 说明：`docs/research-module-plan-v1.md` 的备份是 P0 修改前版本；该文件在 P0 内按评审意见更新后，当前版本为准。校验结果中只有这一份文档与备份不同，15 个代码/配置文件哈希仍与备份一致。

---

## 4. 基线检查

日志目录：

```text
backup/p0_pre_research_20261030_101626/_baseline/
```

| 检查 | 命令 | 结果 | 日志 |
|---|---|---|---|
| 前端类型 | `npm run type-check` | 通过，exit 0 | `frontend-type-check.log` |
| Django | `python manage.py check` | 通过，exit 0 | `backend-check.log` |

未执行 `manage.py test`：当前项目没有测试文件，且测试会依赖数据库；P2 新增单元测试后再执行。

---

## 5. 回滚方法

### 5.1 整体回滚

1. 确认要回滚到的备份目录：`backup/p0_pre_research_20261030_101626/`。
2. 按 `MANIFEST.json` 中的 `path` 逐文件复制回项目根目录。
3. 复制后重新计算 SHA256，与 manifest 比对。
4. 运行：
   - `cd frontend; npm run type-check`
   - `cd backend; .\.venv\Scripts\python.exe manage.py check`

### 5.2 单文件回滚

```powershell
$root = 'D:\zhijieguoyin_backend - 副本 - 副本'
$backup = Join-Path $root 'backup\p0_pre_research_20261030_101626'
Copy-Item -LiteralPath (Join-Path $backup 'frontend\src\views\GlobalEffectView.vue') `
  -Destination (Join-Path $root 'frontend\src\views\GlobalEffectView.vue') -Force
```

### 5.3 注意

- 回滚是覆盖操作，执行前先确认目标路径在项目根目录内。
- 不要回滚 `research/data/` 或 `docs/`，除非明确要撤销文档改动。
- 数据版本回滚另见 [data-contract-v1.md](data-contract-v1.md) 第 11 节，不通过文件覆盖实现。

---

## 6. 数据结构确认

采用评审建议的版本化目录：

```text
research/data/
├─ README.md
├─ manifest.json
└─ v1.0/
   ├─ cases.json
   ├─ success_factors.json
   ├─ music_scores.json
   └─ regional_strategies.json
```

核心字段与规则见 [data-contract-v1.md](data-contract-v1.md)。P0 只建立说明与结构，不写案例数据。

本阶段确认的关键口径：

- `mean_score` 与 `review_status` 分开。
- `score=null` 表示未知，不按 0 分。
- 非空分数必须有 `evidence` + `source_ids`。
- `n<5` 不展示成功因素排行榜、不做国家/区域偏好结论。
- `n=3` 时全球页只展示：`3/40`、`3 个 B 级`、`0 个 A 级`、`7.5%`、案例地图事实、单案例卡。
- 8 项潜力评分缺项时 `tier=资料不足`，不重新归一化、不参与排名。
- 方案输出固定 9 个模块；城市维度嵌在 01 和 06，不另加第 10 个模块。
- 区域矩阵必须区分“目标国家”和“作品来源城市”。

---

## 7. P0 验收清单

- [x] 备份目录已创建，路径在项目根目录内。
- [x] 16 个文件全部备份，SHA256 一致。
- [x] `MANIFEST.json` 含路径、字节数、SHA256、修改时间。
- [x] 前端类型检查基线已保存。
- [x] Django system check 基线已保存。
- [x] 修改/新增/不动范围已列清。
- [x] 数据结构契约已定义。
- [x] 六项强制约束已写入方案与契约。
- [x] 未修改前后端业务代码。
- [x] P1 未开始。

---

## 8. P1 进入条件

P1 只做一件事：把现有 3 个案例按契约转成 `research/data/v1.0/*.json`，并生成 manifest 与校验结果。

进入 P1 前需要确认：

1. 同意 `research/data/` 作为唯一数据源，后端不再保留第二份案例数据。
2. 同意 `v1.0/` 创建后只读，后续修正新建 `v1.1/`。
3. 同意 P1 不写前端页面，只产出数据与校验报告。
4. 同意 P1 只转换现有 3 个案例，不扩采、不补造第 4—40 个案例。

确认后执行 P1；P1 完成并提供校验报告后，再进入 P2。
