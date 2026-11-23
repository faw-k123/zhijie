# 最终研究报告：研究模块整合与验收

> **2026-10-30 后续更新：** v1.1 已由负责人确认激活，当前为 10 个案例、100 条指标记录、25 条来源；本文 P8 段落中的 3/40、3 案例等数字是当时的历史状态。


> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P0—P8
> 日期：2026-10-30
> 状态：P8 技术整合完成；真实歌曲列表端到端验证未完成
> 数据版本：v1.0 · reviewed

---

## 1. 系统改造总览

P0—P7 建立了一个独立的“国际传播研究模块”：

```text
research/data/manifest.json + v1.0/*.json
        ↓
Django 研究数据层（哈希校验、版本状态、记录隔离）
        ↓
7 个基础研究 API + P6 单曲上下文 + P7 方案生成
        ↓
全球传播效果 / 海外案例库 / 案例详情 / 研究洞察
音乐详情海外传播 Tab / 区域传播方案
```

P8 做的是整合，不是新增研究功能：

- 将 5 个研究入口加入 AppNav；
- 修复 390 窄屏导航横向溢出；
- 增加移动端菜单，研究入口可直接点击；
- 统一桌面/平板/手机导航行为；
- 完成最终页面截图与回归检查；
- 没有新建数据库表，没有 migration；
- 没有修改原有业务接口；
- 没有伪造研究数据。

---

## 2. 导航与路由整合

AppNav 新增一级分组“国际传播”，包含：

| 入口 | 路由 |
|---|---|
| 全球传播效果 | `/global-effect` |
| 海外案例库 | `/global-cases` |
| 案例详情 | `/global-cases/:caseId` |
| 研究洞察 | `/research-insights` |
| 区域传播方案 | `/promo-plan` |

原有“宣传专栏”保留“视频配乐”入口；“区域传播方案”不再重复挂在旧分组下。

### 2.1 选中状态

- 桌面端“国际传播”一级项在任一研究页面高亮；
- 子菜单当前页面单独高亮；
- 案例详情高亮“海外案例库”；
- 移动端菜单按当前路由高亮对应链接。

### 2.2 移动端导航

此前 390px 下导航操作区宽度超出视口。P8 的处理：

- ≤900px 隐藏桌面横向菜单；
- 显示菜单按钮；
- 打开后展示纵向移动菜单；
- 隐藏测试模式控件，保留语言与头像；
- 关闭测试控件后，390px 文档宽度回到 390px；
- 桌面端仍保留原有横向菜单。

实测：

| 宽度 | 导航形态 | 文档 `scrollWidth` |
|---:|---|---:|
| 1440 | 桌面横向菜单 | 1440 |
| 1024 | 桌面横向菜单 | 1024 |
| 834 | 移动菜单 | 834 |
| 768 | 移动菜单 | 768 |
| 600 | 移动菜单 | 600 |
| 390 | 移动菜单 | 390 |

移动菜单包含 12 个入口，其中 4 个研究入口可直接点击。

---

## 3. 前后端文件改动清单

### 3.1 前端

| 文件 | 改动 |
|---|---|
| `frontend/src/components/AppNav.vue` | 新增“国际传播”分组、移动菜单、当前页高亮 |
| `frontend/src/assets/premium.css` | 修复 ≤900px 导航溢出；隐藏测试控件；移动端导航布局 |
| `frontend/src/views/GlobalEffectView.vue` | P3 全球传播效果页 |
| `frontend/src/views/GlobalCaseLibraryView.vue` | P4 案例库 |
| `frontend/src/views/GlobalCaseDetailView.vue` | P4 案例详情 |
| `frontend/src/views/ResearchInsightsView.vue` | P5 三 Tab 研究洞察 |
| `frontend/src/views/MusicDetailView.vue` | P6 第四个“海外传播”Tab |
| `frontend/src/views/PromoReportView.vue` | P7 区域传播方案页 |
| `frontend/src/api/research.ts` | 7 个基础 API + P6/P7 调用封装 |
| `frontend/src/types/research.ts` | 研究数据类型 |
| `frontend/src/data/researchFramework.ts` | P5 研究指标与区域框架静态说明 |
| `frontend/src/router/index.ts` | 研究页面路由 |

### 3.2 后端

| 文件 | 改动 |
|---|---|
| `backend/propagation/research_data.py` | manifest 读取、哈希/大小校验、版本状态、记录隔离、缓存 |
| `backend/propagation/research_analytics.py` | 统计、成功因素门禁、潜力、区域矩阵、单曲上下文 |
| `backend/propagation/promo_plan.py` | P7 规则模板方案生成 |
| `backend/api/views.py` | 7 个基础研究接口 + P6/P7 接口 |
| `backend/api/urls.py` | 研究路由 |
| `backend/propagation/tests.py` | 25 个研究测试 |
| `backend/propagation/management/commands/validate_research_data.py` | 数据校验命令 |

### 3.3 数据与文档

- `research/data/manifest.json`
- `research/data/v1.0/cases.json`
- `research/data/v1.0/success_factors.json`
- `research/data/v1.0/music_scores.json`
- `research/data/v1.0/regional_strategies.json`
- `docs/p0-scope-and-baseline.md`
- `docs/data-contract-v1.md`
- `docs/p1-data-conversion-report.md`
- `docs/p2-backend-report.md`
- `docs/p2-api-contract.md`
- `docs/p3-global-dashboard-report.md`
- `docs/p4-case-library-report.md`
- `docs/p5-research-insights-report.md`
- `docs/p6-music-overseas-report.md`
- `docs/p7-promo-plan-report.md`
- `docs/final-research-module-report.md`
- `docs/final-api-contract.md`
- `docs/final-test-report.md`

---

## 4. 数据版本与完整性

### 4.1 当前数据

```text
active_version = v1.0
status = reviewed
target_case_count = 40
cases = 3
sources = 7
score_records = 30
known_scores = 26
null_scores = 4
music_scores = pending / 0 items
regional_strategies = pending / 0 rows
```

数据校验：

```text
python manage.py validate_research_data
OK active_version=v1.0 status=reviewed cases=3 scores=30 warnings=0
```

### 4.2 样本门禁

- 0：空
- 1—4：证据不足
- 5—19：探索性
- ≥20：可做描述性统计

当前 3 个案例，成功因素排行榜返回不可用，不生成 TOP 榜或国家偏好推断。

### 4.3 数据缺口

以下研究数据仍未完成，P8 不宣称已完成：

- 40 个案例：当前 3 个；
- 20 首候选曲目评分：当前 0 首完成 8 项评分；
- 区域策略：当前 0 条；
- 区域文化/宗教/习俗来源：尚未补充；
- 真实受众调研与传播效果基线：尚未开展。

---

## 5. 页面验收结果

| 页面 | 路由 | 验收结果 |
|---|---|---|
| 全球传播效果 | `/global-effect` | 通过；3/40 门禁、国家/乐器分布、案例预览正常 |
| 海外案例库 | `/global-cases` | 通过；搜索、筛选、分页、详情入口正常 |
| 案例详情 | `/global-cases/CASE001` | 通过；10 项指标、来源、相关案例正常 |
| 研究洞察 | `/research-insights` | 通过；机制/潜力/区域三 Tab 正常；390 矩阵不溢出 |
| 音乐详情海外传播 | 现有音乐详情路由 | 页面逻辑通过；真实歌曲列表 E2E **未完成**（见第 8 节） |
| 区域传播方案 | `/promo-plan` | 通过；12 项必填输入、9 模块、四类信息分层正常 |

### 5.1 截图

- [global-effect.png](<screenshots/global-effect.png>)
- [global-cases.png](<screenshots/global-cases.png>)
- [case-detail.png](<screenshots/case-detail.png>)
- [research-insights.png](<screenshots/research-insights.png>)
- [music-overseas.png](<screenshots/music-overseas.png>)
- [promo-report-form.png](<screenshots/promo-report-form.png>)
- [promo-report-result.png](<screenshots/promo-report-result.png>)

390 版本：

- [global-effect-390.png](<screenshots/global-effect-390.png>)
- [music-overseas-390.png](<screenshots/music-overseas-390.png>)
- [nav-mobile-390.png](<screenshots/nav-mobile-390.png>)

### 5.2 窄屏结果

所有最终 390 截图文档宽度均为 390px：

```text
global-effect-390        scrollWidth 390
global-cases-390         scrollWidth 390
case-detail-390          scrollWidth 390
research-insights-390    scrollWidth 390
music-overseas-390       scrollWidth 390
promo-report-form-390    scrollWidth 390
promo-report-result-390  scrollWidth 390
```

此前 AppNav 的横向溢出已修复。

---

## 6. 原有功能回归

已完成：

- `npm run type-check` 通过；
- `npm run build-only` 通过；
- `python manage.py check` 通过；
- 25 个研究测试通过；
- 原 7 个研究接口 smoke 全部 200；
- 旧 `POST /api/global/propagation/` 200；
- 公共页面 `/music-show`、`/imagery`、`/personality-test`、`/about` 可渲染。

受限：

- `/` 会跳转 `/login`，这是原有鉴权行为；
- `/emotion` 等依赖 SQL Server 的原有业务页面未能完成完整交互回归；
- 本机 SQL Server 服务无法启动，见第 8 节。

因此 P8 不能宣称“全部原有业务功能已完成完整回归”。技术构建与研究模块回归是通过的。

---

## 7. API 清单

详见 [final-api-contract.md](<final-api-contract.md>)。

研究模块共 9 个接口：

1. `GET /api/research/status/`
2. `GET /api/research/cases/`
3. `GET /api/research/cases/<case_id>/`
4. `GET /api/research/statistics/`
5. `GET /api/research/success-factors/`
6. `GET /api/research/music-potential/`
7. `GET /api/research/regional-matrix/`
8. `GET /api/research/music-context/`（P6）
9. `POST /api/research/promo-plan/`（P7）

P8 没有新增研究接口。

---

## 8. 已知问题与未完成事项

### 8.1 真实歌曲列表端到端验证未完成

P8 尝试启动本机 SQL Server：

```text
Start-Service MSSQLSERVER
失败：无法打开计算机“.”上的 MSSQLSERVER 服务
```

服务仍为 `Stopped`。因此：

- 无法用真实 `/api/emotion/subcategory-songs/` 返回曲目；
- 无法完成“音乐详情页 → 真实歌曲列表 → P6 单曲上下文”的完整调用链；
- `music-overseas.png` 是 UI 截图，歌曲列表使用浏览器层临时替身；**不能视为真实联调完成**；
- P6 的 `/api/research/music-context/` 本身走真实后端，但缺少真实歌曲入口。

该事项保留为 P8 唯一未完成的端到端验证。

### 8.2 研究数据不足

- 案例 3/40；
- 音乐评分 0/20；
- 区域策略 0 条；
- 来源 7 条；
- 不能生成成功因素 TOP 榜；
- 不能生成区域适配结论；
- 不能宣称 40 案例、20 首评分或区域策略已完成。

### 8.3 构建警告

`npm run build-only` 有既有 chunk size warning（>500 kB），不影响构建成功，未在 P8 大范围拆包。

### 8.4 研究结论边界

- 规则模板方案不是实证推荐模型；
- 方案中的“建议/假设”不是研究结论；
- 3 个案例不能代表 40 个案例总体；
- 不能把当前页面结果解释为某首音乐适合某国的证明。

---

## 9. 最终验收结论

P8 的**技术整合**已完成：

- 研究入口已进入 AppNav；
- 390 导航溢出已修复；
- 移动菜单可用，研究入口可直接点击；
- 5 个研究页面与 P6/P7 调用链在页面层通过；
- 研究 API 9/9 smoke 通过；
- 25 个测试、类型检查、生产构建、Django 检查、数据校验通过；
- 数据库、migration、旧业务接口未被修改。

但 P8 不能宣称**全部端到端联调完成**。真实歌曲列表依赖 SQL Server，而本机服务无法启动；该事项明确保留为未完成验证。

**项目结论：**

> P0—P8 的研究模块技术建设与前端整合已完成；研究数据补充（40 案例、20 首评分、区域策略）和真实歌曲列表端到端联调仍是独立的未完成工作，不能因 P8 技术整合通过而宣称这些研究目标已完成。
