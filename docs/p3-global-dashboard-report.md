# P3 全球传播驾驶舱报告

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P3（前端研究基础设施 + 全球传播效果页）
> 日期：2026-10-30
> 状态：P3 完成，等待验收
> 范围：只做前端类型/API/共用组件/GlobalEffectView，不进入 P4

---

## 1. 本阶段完成内容

1. 新增 `frontend/src/types/research.ts`，覆盖 P2 七个接口的返回结构。
2. 新增 `frontend/src/api/research.ts`，封装全部 7 个只读 API。
3. 新增 6 个研究页共用组件：
   - `SampleBadge.vue`
   - `ResearchKpi.vue`
   - `SectionCard.vue`
   - `DistributionList.vue`
   - `ResearchState.vue`
   - `CasePreviewCard.vue`
4. 重写 `GlobalEffectView.vue`：删除评论球和原始 JSON 面板，改为全球传播驾驶舱。
5. 所有页面数据来自 P2 API；Vue 中不硬编码案例、国家分布或统计数字。
6. 未修改后端、数据库、migration、路由或 AppNav。
7. 生成 1440 桌面与 390 窄屏两张完整页面截图。

---

## 2. API 封装

文件：

[frontend/src/api/research.ts](<../frontend/src/api/research.ts>)

| 函数 | 接口 | P3 是否使用 |
|---|---|---|
| `fetchResearchStatus()` | `/api/research/status/` | 是 |
| `fetchResearchCases()` | `/api/research/cases/` | 是，取前 3 条 |
| `fetchResearchCase()` | `/api/research/cases/{id}/` | 否，留给 P4 案例详情 |
| `fetchResearchStatistics()` | `/api/research/statistics/` | 是 |
| `fetchResearchSuccessFactors()` | `/api/research/success-factors/` | 是 |
| `fetchResearchMusicPotential()` | `/api/research/music-potential/` | 是 |
| `fetchResearchRegionalMatrix()` | `/api/research/regional-matrix/` | 是 |

7 个封装已完成；页面实际消费 6 个，案例详情封装为 P4 预留。

---

## 3. 页面结构

路由：`/global-effect`

### 3.1 顶部

- 标题：全球传播效果分析
- 英文 kicker：`GLOBAL PROPAGATION DASHBOARD`
- 样本徽标：`证据不足 · 3/40`
- 样本说明：`证据不足：样本少于5例`
- 数据版本：`v1.0 · 2026-10-30`

### 3.2 KPI

| KPI | 当前值 | 来源 |
|---|---:|---|
| 案例收录进度 | 3 / 40 | `status.sample` |
| 研究完成进度 | 7.5% | `status.sample.progress_percent` |
| 覆盖国家 | 3 | `status.counts.countries` |
| 涉及乐器种类 | 2 | `status.counts.instruments` |

### 3.3 全球案例分布

- 国家计数来自 `statistics.distributions.country`。
- 区域 chips 来自 `statistics.distributions.region`。
- 样本完成度进度条来自 `status.sample`。
- 明确标注“仅代表当前样本构成，不代表偏好或传播效果排名”。

### 3.4 成功传播因素

当前接口返回：

```json
{
  "availability": "unavailable",
  "rankings": null,
  "factors": [],
  "reason": "样本不足5例，统计层不提供成功因素排行；仅展示单案例评分。"
}
```

页面显示：

- `暂不可用`
- “当前样本少于 5 例，暂不生成成功因素排行”
- 缺口进度：`3 / 5`
- “达到 5 例后，后端才会返回探索性结果”

没有 TOP 排行、没有国家偏好、没有空数组伪装成排行榜。

### 3.5 数据状态

来自 `status`：

- 数据版本 `v1.0 · reviewed`
- 来源记录 7 条
- 证据等级 A 0 / B 3 / C 0 / D 0
- 数据隔离 0 条
- 最后更新 2026-10-30

### 3.6 音乐潜力 / 区域矩阵

两者都按 `pending` 展示：

- 音乐潜力：`0 / 20`，`items=[]`，不显示分数或排名。
- 区域矩阵：`6` 个已定义区域、`0` 条已审核策略，不显示推荐行。

### 3.7 代表性案例

- 来自 `/api/research/cases/?page=1&page_size=3`。
- 展示 CASE001—CASE003 的真实摘要、国家、区域、乐器、主题、证据等级、编码均分、来源数量。
- 案例详情按钮禁用，标注“P4 开放”，没有提前实现 P4 页面。

### 3.8 页脚口径

- 当前样本 3/40，状态 `insufficient`。
- 不展示成功因素 TOP、国家偏好或全球接受度排行。
- 数据源 `research/data/v1.0`，只读。

---

## 4. 状态处理

| 状态 | 处理 |
|---|---|
| 首屏加载 | 4 个 KPI 骨架 + 2 个面板骨架 |
| 研究状态失败 | 页面级错误态 + 重新加载 |
| 单个模块失败 | 顶部“部分模块未加载”提示；其余模块仍展示 |
| 统计失败 | 分布卡显示错误态 |
| 成功因素失败 | 成功因素卡显示错误态 |
| 案例失败 | 案例区显示错误态 |
| 无案例 | 案例区空状态 |
| 音乐/区域矩阵 pending | 待补充说明，不显示假数据 |

没有用 `try/catch` 吞掉错误后展示假数据。

---

## 5. 视觉与兼容

- 沿用现有墨绿、青玉、米金视觉体系。
- 标题使用宋体，数据使用无衬线，编号使用等宽字体。
- 桌面 1440：KPI 四列，主区 1.35fr / 0.9fr，案例三列。
- 1024 以下：主区单列，状态区两列，案例两列。
- 680 以下：KPI、状态区、案例全部单列。
- 390 窄屏：页面主体已单列，内容未被截断。
- 现有 AppNav 在 390 仍有全站既有的横向溢出（不是 P3 新增）；导航移动端重构建议放 P8，P3 未改 AppNav。

---

## 6. 截图

### 桌面 1440

![P3 全球传播效果页 1440](<screenshots/global-effect-p3-1440.png>)

文件：[global-effect-p3-1440.png](<screenshots/global-effect-p3-1440.png>)

尺寸：1440 × 2081；完整长页截图。

### 窄屏 390

![P3 全球传播效果页 390](<screenshots/global-effect-p3-390.png>)

文件：[global-effect-p3-390.png](<screenshots/global-effect-p3-390.png>)

尺寸：390 × 4927；完整长页截图。页面主体已单列；顶部导航的横向溢出属于现有 AppNav 问题。

说明：截图使用 headless Edge + CDP 生成；截图时移除了开发态 route loader 和 Vue DevTools 浮层，页面代码未因此修改。

---

## 7. 验证结果

| 检查 | 结果 |
|---|---|
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过；仅有既有 chunk size warning |
| `python manage.py check` | 通过 |
| `python manage.py test propagation.tests` | 17/17 通过 |
| 7 个研究 API | 全部 200 |
| 页面数据 | 全部来自 API |
| 排行门禁 | 未显示成功因素排行 |
| 音乐/区域矩阵 | 只显示待补充 |
| 后端改动 | 0 |
| 数据库/migration | 0 |
| 路由/AppNav 改动 | 0 |
| 其他页面 | 未改 |

---

## 8. 代码变更清单

### 新增

- `frontend/src/types/research.ts`
- `frontend/src/api/research.ts`
- `frontend/src/components/research/SampleBadge.vue`
- `frontend/src/components/research/ResearchKpi.vue`
- `frontend/src/components/research/SectionCard.vue`
- `frontend/src/components/research/DistributionList.vue`
- `frontend/src/components/research/ResearchState.vue`
- `frontend/src/components/research/CasePreviewCard.vue`

### 修改

- `frontend/src/views/GlobalEffectView.vue`（整体重写）

### 新增截图

- `docs/screenshots/global-effect-p3-1440.png`
- `docs/screenshots/global-effect-p3-390.png`

### 未修改

- 后端任何文件
- 数据库、migration
- `frontend/src/router/index.ts`
- `frontend/src/components/AppNav.vue`
- 案例库、研究洞察、音乐详情、区域方案页面
- 原有其他页面

---

## 9. P3 验收对照

- [x] 7 个接口封装完成
- [x] 页面数据全部真实接口驱动
- [x] 样本提示正确显示 3/40、insufficient
- [x] 排行门禁：不显示虚假排行榜
- [x] 有加载、错误、空数据状态
- [x] 不破坏原有路由和页面
- [x] `npm run type-check` 通过
- [x] `python manage.py check` 通过
- [x] 只涉及 P3 文件
- [x] 未修改后端 API、数据库、migration
- [x] 未提前开发 P4/P5/P6/P7 页面

---

## 10. 已知限制与 P4 入口

1. 案例详情按钮当前禁用，P4 才开放。
2. 全球页还没有挂到 AppNav；导航整合计划在 P8，当前可通过 `/global-effect` 访问。
3. AppNav 在 390 有全站既有横向溢出；P3 未改导航。
4. 音乐潜力与区域矩阵仍为 `pending`，只能显示待补充。
5. P4 需要新增案例库与案例详情路由、列表/详情页，并复用本阶段的 `CasePreviewCard`、`ResearchState`、`SampleBadge`。

P3 到此停止，不进入 P4。
