# P5 研究洞察页报告

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P5（研究洞察：成功机制 / 音乐潜力 / 区域矩阵）
> 日期：2026-10-30
> 状态：P5 完成，等待验收
> 范围：只新增 `/research-insights`，不进入 P6

---

## 1. 本阶段完成内容

1. 新增 `/research-insights` 页面，包含三个 Tab：
   - 成功传播机制
   - 音乐传播潜力
   - 区域传播适配
2. Tab 与 URL query 同步：`?tab=mechanism|potential|matrix`。
3. 只消费 P2 的只读 API，没有新增或修改后端接口。
4. 没有为了页面丰富而填充模拟数据：
   - 成功机制不显示 TOP 排行；
   - 音乐潜力保持 `pending`；
   - 区域矩阵保持 `rows=0`。
5. 三个 Tab 均完成 1440 与 390 截图。

---

## 2. 页面与数据来源

路由：

```text
/research-insights?tab=mechanism
/research-insights?tab=potential
/research-insights?tab=matrix
```

数据来源：

| 数据 | API |
|---|---|
| 样本、版本、等级计数 | `/api/research/status/` |
| 指标覆盖、国家/乐器分布 | `/api/research/statistics/` |
| 成功因素门禁状态 | `/api/research/success-factors/` |
| 案例列表 | `/api/research/cases/` |
| 10 项指标与来源 | `/api/research/cases/{id}/` |
| 音乐潜力规则与 pending 状态 | `/api/research/music-potential/` |
| 区域/受众/主题枚举与 pending 状态 | `/api/research/regional-matrix/` |

指标定义、评分锚点、8 项音乐指标名称、区域矩阵字段说明属于研究方法文本，来自《指标编码手册 v1.0》和 P0 数据契约；案例分数、覆盖数、权重、区域枚举和状态全部来自 API。

---

## 3. Tab 一：成功传播机制

### 3.1 页面内容

- 当前样本状态：`3 / 40`，`insufficient`
- 后端门禁状态：`unavailable`
- 后端返回的原因：样本不足 5 例
- 指标单元覆盖：`26 / 30`
- 完整覆盖指标：`7 / 10`
- 个案有效指标：`10 / 7 / 9`
- 10 项指标解释、评分锚点、每项覆盖数
- 指标 × 案例矩阵：10 行 × 3 案例
- 个案对比：按案例编号排列，不按均分排序
- 证据摘录：4 条，含案例编号与来源编号
- “当前不能得出的结论”清单

### 3.2 排行门禁

- `success-factors` 当前返回 `availability="unavailable"`、`rankings=null`。
- 页面不展示 TOP 排行，不展示国家/区域偏好。
- 个案均分只作事实展示，并明确“不是成功程度排名”。
- 国家比较明确禁止：当前每个国家只有 1 个案例。

### 3.3 证据追溯

每条证据摘录包含：

- 案例编号（CASE001 等）
- 指标名称
- 评分 / 3
- 原始证据说明
- `source_ids`

来源编号链接到案例详情的来源锚点：

```text
/global-cases/CASE001#source-C001-S001
```

### 3.4 未知值

矩阵单元格：

- 有评分：显示 0—3
- 无评分：显示“未知”
- 悬停显示 `missing_reason` 或证据

没有把 `null` 渲染为 0。

---

## 4. Tab 二：音乐传播潜力

### 4.1 页面内容

- 当前 `pending / 待补充`
- `0 / 20` 已评分
- 8 项指标及权重（权重来自 API）
- 每项指标的定义
- 总分公式
- 4 档分级规则（来自 API）
- 当前候选曲目状态：0 已评分、20 候选目标、0 可排名

### 4.2 当前不展示

- 不生成 20 首曲目分数
- 不生成综合排名
- 不使用 0 分补齐缺失指标
- 不把“待补充”说成“没有传播潜力”

---

## 5. Tab 三：区域传播适配

### 5.1 页面内容

- 当前 `pending / 待补充`
- 6 个既定研究区域
- 6 个受众枚举
- 10 个时代主题枚举
- 矩阵字段框架：
  - 目标国家/区域
  - 目标受众
  - 主要语言
  - 文化背景
  - 宗教与习俗注意
  - 适配理由 `match_reason`
  - 时代主题
  - 平台与形式
  - 参考案例
  - 作品来源城市
  - 城市文化叙事
  - 风险提示
- 北京 / 上海：作品来源城市维度
- “当前不能展示”清单

### 5.2 6 个区域的含义

页面明确写明：

> 6 个区域 = 研究范围，不是 6 个已验证策略

当前：

```text
regions = 6
rows = 0
```

所以没有生成任何“某音乐适合某区域”的适配关系，也没有写具体的宗教/文化禁忌。

### 5.3 北京 / 上海

- 仅作为 `origin_city` 的候选值展示。
- 文化锚点、可用场景、城市叙事、来源全部标注“待补”。
- 不把城市维度替代目标国家。
- 没有写具体文化判断，避免无来源概括。

---

## 6. 截图

### 6.1 成功传播机制 1440

![P5 成功机制 1440](<screenshots/p5-mechanism-1440.png>)

文件：[p5-mechanism-1440.png](<screenshots/p5-mechanism-1440.png>)
尺寸：1440 × 3464。

### 6.2 音乐传播潜力 1440

![P5 音乐潜力 1440](<screenshots/p5-potential-1440.png>)

文件：[p5-potential-1440.png](<screenshots/p5-potential-1440.png>)
尺寸：1440 × 1637。

### 6.3 区域传播适配 1440

![P5 区域适配 1440](<screenshots/p5-matrix-1440.png>)

文件：[p5-matrix-1440.png](<screenshots/p5-matrix-1440.png>)
尺寸：1440 × 2177。

### 6.4 窄屏 390

- [成功机制 390](<screenshots/p5-mechanism-390.png>)
- [音乐潜力 390](<screenshots/p5-potential-390.png>)
- [区域适配 390](<screenshots/p5-matrix-390.png>)

说明：截图使用 headless Edge + CDP 生成；截图时仅移除开发态 route loader 与 Vue DevTools 浮层，页面代码未因此修改。

---

## 7. 验证结果

| 检查 | 结果 |
|---|---|
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过，仅有既有 chunk size warning |
| `python manage.py check` | 通过 |
| `python manage.py test propagation.tests` | 17/17 通过 |
| 成功机制指标卡 | 10 |
| 指标矩阵行数 | 10 |
| 证据摘录 | 4 |
| 音乐权重卡 | 8 |
| 区域卡 | 6 |
| 成功因素 TOP 排行 | 0 |
| 虚假音乐评分/排名 | 0 |
| 虚假区域适配关系 | 0 |
| 后端/数据库/AppNav 改动 | 0 |

---

## 8. 已知限制

1. 当前只有 3 个案例、均为 B 级，成功机制只能做描述性覆盖与个案对比。
2. 音乐潜力与区域矩阵仍为 `pending`，页面只能展示规则、字段和缺口。
3. 指标定义/评分锚点属于研究方法文本，不来自 API；案例分数与覆盖数来自 API。
4. AppNav 未接入本页；当前通过 `/research-insights` 访问，导航留到 P8。
5. 390 窄屏页面主体可用；AppNav 仍有全站既有横向溢出。
6. 区域矩阵的 6 个区域是研究范围，不是已完成的实证策略。

---

## 9. P5 验收对照

- [x] 新增 `/research-insights`
- [x] 三个 Tab
- [x] 成功机制展示 10 项指标解释与覆盖
- [x] 案例指标矩阵
- [x] 个案对比，非排行
- [x] 证据摘录带案例编号和来源
- [x] 不显示成功因素 TOP 排行
- [x] 音乐潜力展示 8 项权重与规则
- [x] 音乐潜力不生成假评分/排名
- [x] 区域矩阵展示 6 个研究区域与字段框架
- [x] 区域矩阵不生成假适配关系
- [x] 北京/上海作为来源城市维度
- [x] null 不按 0 分
- [x] 所有结论可追溯
- [x] 桌面与 390 窄屏均可用
- [x] `type-check`、`build-only`、`check`、17 个测试通过
- [x] 未新增/修改后端接口
- [x] 未提前开发 P6/P7
- [x] 未重构 AppNav

P5 到此停止，不进入 P6。
