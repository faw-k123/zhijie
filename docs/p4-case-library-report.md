# P4 案例库与案例详情报告

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P4（案例库 + 案例详情）
> 日期：2026-10-30
> 状态：P4 完成，等待验收
> 范围：只做 `/global-cases` 与 `/global-cases/:caseId`，不进入 P5

---

## 1. 本阶段完成内容

1. 新增案例库 `/global-cases`：
   - 搜索、国家筛选、乐器筛选、证据等级筛选、分页
   - 只展示 A/B 已审核案例
   - 展示案例名称、国家、乐器、编码均分、证据等级、来源数量
2. 新增案例详情 `/global-cases/:caseId`：
   - 基本信息与背景
   - 10 项指标评分
   - 每项指标证据与来源编号
   - 传播过程与传播结果
   - 来源链接
   - 后端返回的相似案例
3. 注册两条路由，未改 AppNav。
4. 将 P3 代表案例卡从“P4 开放”改为真实详情入口。
5. 未新增后端接口，全部复用 P2 的 7 个只读 API。

---

## 2. 路由与文件

### 2.1 路由

```text
/global-cases              -> GlobalCaseLibraryView.vue
/global-cases/:caseId      -> GlobalCaseDetailView.vue
```

已加入 [frontend/src/router/index.ts](<../frontend/src/router/index.ts>)。

### 2.2 新增页面

- [GlobalCaseLibraryView.vue](<../frontend/src/views/GlobalCaseLibraryView.vue>)
- [GlobalCaseDetailView.vue](<../frontend/src/views/GlobalCaseDetailView.vue>)

### 2.3 新增组件

- [CaseLibraryRow.vue](<../frontend/src/components/research/CaseLibraryRow.vue>)
- [PaginationBar.vue](<../frontend/src/components/research/PaginationBar.vue>)
- [ScoreIndicator.vue](<../frontend/src/components/research/ScoreIndicator.vue>)
- [SourceItem.vue](<../frontend/src/components/research/SourceItem.vue>)

### 2.4 修改

- `frontend/src/router/index.ts`：新增 2 条路由。
- `frontend/src/components/research/CasePreviewCard.vue`：P3 代表案例卡接通 P4 详情。

### 2.5 未修改

- 后端、数据库、migration。
- P2 API 行为。
- AppNav。
- P3 GlobalEffect 页面主体。
- P5/P6/P7 页面。

---

## 3. 案例库

### 3.1 页面结构

- 顶部：`CASE LIBRARY / 研究证据`、标题“案例库”、样本徽标。
- 概况：已纳入 3、覆盖国家 3、涉及乐器 2、来源 7。
- 筛选：关键词、国家、乐器、证据等级。
- 结果：共 3 例，CASE001—CASE003 列表。
- 分页：上一页、页码、下一页。
- 页脚口径：编码均分不是证据等级，也不是传播效果排名。

### 3.2 数据来源

| 页面数据 | API |
|---|---|
| 样本、国家数、乐器数、来源数、证据等级计数 | `/api/research/status/` |
| 国家、乐器筛选项及计数 | `/api/research/statistics/` |
| 案例列表、总数、分页 | `/api/research/cases/` |

筛选参数直接传给后端：

```text
q, country, instrument, grade, page, page_size
```

没有在前端用本地数组假装筛选全部数据。

### 3.3 筛选与状态说明

- 国家、乐器选项来自统计接口的真实分布。
- 证据等级只提供 A/B：
  - A：证据充分
  - B：基本可信
- 当前 P2 接口不返回 C/D 待核实案例列表，因此 P4 **不提供 C/D 状态筛选**，避免前端假装支持。
- 页面明确写明“当前 API 不提供 C/D 待核实案例列表”。

### 3.4 列表字段

每行展示：

- 乐器图（本地乐器海报；无封面时回退文字）
- CASE 编号
- 演奏者 / 机构
- 国家 / 区域 / 子区域
- 乐器 / 音乐类型 / 时间
- 摘要
- 时代主题与文化钩子
- 编码均分 / 3
- 有效指标 / 未知指标
- 证据等级
- 来源数量
- “查看详情”入口

### 3.5 分页

- 默认每页 10 条，当前 3 条为 1 页。
- 服务端分页；翻页重新请求 API。
- 页码写入 URL query，刷新可保留。
- 非法页码会回落到有效页。

---

## 4. 案例详情

### 4.1 页面结构

1. 顶部：返回案例库、CASE 路径、样本徽标。
2. Hero：演奏者、摘要、国家/区域/乐器/证据等级、编码均分。
3. 案例摘要与背景：
   - 摘要
   - 学习 / 接触动机
   - 改编与呈现
   - 研究备注
4. 10 项指标评分：
   - 每项分数 / 3
   - 进度条
   - 证据说明
   - `source_ids` 链接到下方来源卡片
   - 未知项显示“未知”，不使用 0 分
5. 传播过程与结果：
   - 接触与学习
   - 传播方式
   - 传播结果
   - 受众反馈
6. 案例信息侧栏：
   - 国家/区域、身份、乐器、音乐类型、时间、地点、活动、渠道、受众、主题、宗教文化背景
7. 来源索引 + 证据与来源：
   - 来源编号、标题、机构、类型、可靠性、发布日期、访问日期
   - `supports` 字段
   - 外链新窗口打开
8. 相似案例：
   - 后端 `similar_cases` 返回，不由前端计算
   - 展示匹配分、匹配理由、国家/地区/乐器、编码均分、证据等级
9. 页脚：
   - 说明未知值保持 `null`，不以 0 分或推断补齐

### 4.2 数据来源

```text
GET /api/research/cases/CASE001/
```

包括：

- `case`：原始案例字段与 `sources[]`
- `coding`：均分、有效/缺失数量、10 项指标
- `similar_cases`：后端规则结果
- `sample`：研究样本状态

### 4.3 证据追溯

- 每个指标卡片显示 `source_ids`。
- 点击来源编号跳到 `#source-C001-S001` 等锚点。
- 每条来源卡片展示原始 URL、发布机构、发布日期和访问日期。
- 没有来源时显示“无来源”，不补造。
- 未知指标显示 `missing_reason`，不以 0 分填充。

### 4.4 相似案例

- 直接消费后端 `similar_cases`。
- 前端只渲染 `match_score` 和 `match_reasons`。
- 页面明确写明“匹配分只表示规则相似度，不是概率或因果”。

---

## 5. 页面截图

### 5.1 案例库桌面 1440

![P4 案例库桌面](<screenshots/p4-case-library-1440.png>)

文件：[p4-case-library-1440.png](<screenshots/p4-case-library-1440.png>)
尺寸：1440 × 1649。

### 5.2 案例详情桌面 1440

![P4 案例详情桌面](<screenshots/p4-case-detail-1440.png>)

文件：[p4-case-detail-1440.png](<screenshots/p4-case-detail-1440.png>)
尺寸：1440 × 3486。

### 5.3 案例库窄屏 390

![P4 案例库窄屏](<screenshots/p4-case-library-390.png>)

文件：[p4-case-library-390.png](<screenshots/p4-case-library-390.png>)
尺寸：390 × 2640。

### 5.4 案例详情窄屏 390

![P4 案例详情窄屏](<screenshots/p4-case-detail-390.png>)

文件：[p4-case-detail-390.png](<screenshots/p4-case-detail-390.png>)
尺寸：390 × 6730。

说明：截图使用 headless Edge + CDP 生成；截图时仅移除开发态 route loader 与 Vue DevTools 浮层，页面代码未因此修改。

---

## 6. 验证结果

| 检查 | 结果 |
|---|---|
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过；仅有既有 chunk size warning |
| `python manage.py check` | 通过 |
| `python manage.py validate_research_data` | `OK ... cases=3 scores=30 warnings=0` |
| `python manage.py test propagation.tests` | 17/17 通过 |
| 案例库行数 | 3 |
| 案例详情指标数 | 10 |
| 详情来源数 | 3 |
| 占位文本 | 0 |
| 虚假成功排行 | 0 |
| 后端改动 | 0 |
| 数据库/migration | 0 |
| AppNav 改动 | 0 |

---

## 7. 与 P3 的衔接

- P3 的 `CasePreviewCard` 现在链接到真实 P4 详情路由。
- P3 报告与截图生成时，该按钮还是“P4 开放”占位；本阶段已接通。
- P4 没有重写 GlobalEffect 页面，只更新了共用案例卡的详情链接。

---

## 8. 已知限制

1. P2 不返回 C/D 待核实案例列表，因此 P4 没有 C/D 状态筛选。
2. 当前没有案例封面文件，列表使用本地乐器海报；`cover_url` 仍为 `null`。
3. 区域矩阵的“6 个区域”是既定研究区域范围，不是 6 个已完成的实证策略；P4 未展示区域矩阵。
4. 页面尚未挂入 AppNav；导航整合仍在 P8，当前通过 `/global-cases` 访问。
5. AppNav 在 390 有全站既有横向溢出；P4 未改导航。
6. 相似案例是后端规则结果，不是语义向量相似度，也不是因果推荐。

---

## 9. P4 验收对照

- [x] 案例列表、搜索、筛选、分页
- [x] 国家、乐器、证据等级筛选
- [x] 展示名称、国家、乐器、评分、证据等级
- [x] 案例详情基本信息与背景
- [x] 10 项指标评分
- [x] 每项评分依据与来源
- [x] 传播过程与结果
- [x] 来源链接
- [x] 后端返回的相似案例
- [x] 未知指标保持 `null`
- [x] 来源可追溯
- [x] 未新增数据库表 / migration
- [x] 未修改 P2 API 行为
- [x] 未提前开发 P5/P6/P7
- [x] 未擅自重构 AppNav

P4 到此停止，不进入 P5。
