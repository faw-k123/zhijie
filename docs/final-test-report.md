# 最终测试报告

> **2026-10-30 后续更新：** v1.1 已由负责人确认激活，当前为 10 个案例、100 条指标记录、25 条来源；本文 P8 段落中的 3/40、3 案例等数字是当时的历史状态。


> 项目：智解国音 · 国际传播研究模块
> 阶段：P8 全系统整合
> 日期：2026-10-30
> 数据版本：v1.0 · reviewed
> 结论：构建、类型、研究测试、API smoke、页面截图通过；真实歌曲列表端到端验证未完成

---

## 1. 测试环境

```text
项目目录：D:\zhijieguoyin_backend - 副本 - 副本
前端：Vue 3 + Vite 8 + TypeScript
后端：Django 6 + DRF
研究数据：research/data/manifest.json + v1.0
数据库：SQL Server（MSSQLSERVER 服务为 Stopped）
浏览器截图：Microsoft Edge headless + CDP
```

---

## 2. 自动化检查

### 2.1 前端类型检查

```text
npm run type-check
vue-tsc --build
```

结果：通过。

### 2.2 前端生产构建

```text
npm run build-only
✓ built
```

结果：通过。

已知警告：

```text
(!) Some chunks are larger than 500 kB after minification.
```

这是既有 chunk size warning，P8 未做大范围拆包。

### 2.3 Django 检查

```text
python manage.py check
System check identified no issues (0 silenced).
```

结果：通过。

### 2.4 研究数据校验

```text
python manage.py validate_research_data
OK active_version=v1.0 status=reviewed cases=3 scores=30 warnings=0
```

结果：通过。

### 2.5 后端研究测试

```text
python manage.py test propagation.tests
Found 25 test(s)
Ran 25 tests
OK
```

结果：25/25 通过。

构成：

- 原有 17 个测试；
- P6 新增 3 个（无关联、必填校验、显式 `related_case_ids` 关联）；
- P7 新增 2 个（9 模块与类型分层、缺失输入校验）；
- P8 后新增 1 个（指标级门禁 0/4/5/19/20 阈值）；
- 双样本体系新增 2 个（无效样本参数 400、strict/extended 互斥筛选）。

---

## 3. 研究 API smoke

实测 9 个研究接口：

| # | 接口 | 结果 |
|---:|---|---|
| 1 | `GET /api/research/status/` | 200 |
| 2 | `GET /api/research/cases/` | 200 |
| 3 | `GET /api/research/cases/CASE001/` | 200 |
| 4 | `GET /api/research/statistics/` | 200 |
| 5 | `GET /api/research/success-factors/` | 200 |
| 6 | `GET /api/research/music-potential/` | 200 |
| 7 | `GET /api/research/regional-matrix/` | 200 |
| 8 | `GET /api/research/music-context/` | 200 |
| 9 | `POST /api/research/promo-plan/` | 200 |

关键结果：

```text
status: sample.n = 3, status = insufficient
success-factors: availability = unavailable, rankings = null
music-potential: availability = pending, items = []
regional-matrix: availability = pending, rows = []
music-context: association.status = unmapped, potential = null
promo-plan: module_count = 9
promo-plan counts: evidence 0 / suggestions 16 / hypotheses 9 / gaps 9
```

旧接口：

```text
POST /api/global/propagation/ → 200
```

---

## 4. 页面检查

最终截图均使用整合后的 AppNav。

### 4.1 桌面 1440

| 页面 | 文件 | 结果 |
|---|---|---|
| 全球传播效果 | `global-effect.png` | 通过 |
| 海外案例库 | `global-cases.png` | 通过 |
| 案例详情 | `case-detail.png` | 通过 |
| 研究洞察 | `research-insights.png` | 通过 |
| 音乐详情海外传播 | `music-overseas.png` | UI 通过；真实歌曲列表未联调 |
| 区域传播方案（前） | `promo-report-form.png` | 通过 |
| 区域传播方案（后） | `promo-report-result.png` | 通过 |

### 4.2 窄屏 390

| 页面 | 文件 | 文档宽度 |
|---|---|---:|
| 全球传播效果 | `global-effect-390.png` | 390 |
| 海外案例库 | `global-cases-390.png` | 390 |
| 案例详情 | `case-detail-390.png` | 390 |
| 研究洞察 | `research-insights-390.png` | 390 |
| 音乐详情海外传播 | `music-overseas-390.png` | 390 |
| 区域传播方案（前） | `promo-report-form-390.png` | 390 |
| 区域传播方案（后） | `promo-report-result-390.png` | 390 |
| 移动端导航展开 | `nav-mobile-390.png` | 390 |

所有最终 390 截图的 `scrollWidth` 均为 390px。

---

## 5. 导航检查

| 宽度 | 导航形态 | `scrollWidth` |
|---:|---|---:|
| 1440 | 桌面横向菜单 + 国际传播子菜单 | 1440 |
| 1024 | 桌面横向菜单 | 1024 |
| 834 | 移动菜单按钮 | 834 |
| 768 | 移动菜单按钮 | 768 |
| 600 | 移动菜单按钮 | 600 |
| 390 | 移动菜单按钮 | 390 |

390 实测：

```text
scrollWidth = 390
menu-toggle visible = true
desktop menu visible = false
mobile nav links = 12
research links = 4
```

移动菜单中的 4 个研究入口：

- 全球传播效果
- 海外案例库
- 研究洞察
- 区域传播方案

此前 AppNav 在 390 下的横向溢出已修复。

---

## 6. 回归范围

### 已完成

- 类型检查、生产构建；
- Django 检查；
- 研究数据校验；
- 25 个后端研究测试；
- 9 个研究 API smoke；
- 旧 `/api/global/propagation/` 200；
- 5 个研究页面 + P6/P7 页面浏览器渲染与截图；
- 桌面/平板/390 导航布局检查。

### 受限

- `/` 会跳转 `/login`，属于原有鉴权行为；
- `/emotion` 等依赖 SQL Server 的原有业务页面未完成完整交互回归；
- 本机 SQL Server 无法启动，见下节。

因此不能把 P8 写成“全部原有业务功能完整回归通过”。

---

## 7. 未完成的端到端验证

P8 尝试启动 SQL Server：

```text
Start-Service MSSQLSERVER
失败：无法打开计算机“.”上的 MSSQLSERVER 服务
```

服务状态仍为：

```text
MSSQLSERVER  Stopped
```

影响：

- 无法获取真实 `/api/emotion/subcategory-songs/` 歌曲列表；
- 无法完成“真实歌曲列表 → 音乐详情 → P6 海外传播”的完整调用链；
- `music-overseas.png` 的歌曲列表使用浏览器层临时替身，只用于展示已实现的 UI；
- P6 的 `/api/research/music-context/` 走真实后端，但没有真实歌曲入口；
- 该截图不能被当作真实歌曲列表联调结果。

结论：

> P6 音乐详情真实歌曲列表联调：**未完成**。
> 需要 SQL Server 可用后重新执行，并以真实接口返回的歌曲为准。

---

## 8. 数据真实性检查

当前研究数据：

```text
cases = 3
sources = 7
score_records = 30
known_scores = 26
null_scores = 4
music_scores = pending / 0 items
regional_strategies = pending / 0 rows
```

检查结果：

- 没有把 3 个案例包装成 40 个案例；
- 没有把 0 首评分包装成 20 首评分；
- 没有生成成功因素 TOP 榜；
- 没有生成区域适配结论；
- 没有虚构受众偏好、宗教禁忌、效果提升百分比；
- 方案中的证据/建议/假设/缺口保持分离；
- `null` 评分没有被写成 0；
- 区域策略为空时显示“待补充”。

---

## 9. 最终结论

通过项：

- 前端类型检查；
- 前端生产构建；
- Django 检查；
- 研究数据校验；
- 25 个研究测试；
- 9 个研究 API smoke；
- 5 个研究页面 + P6/P7 页面渲染；
- 1440/1024/834/768/600/390 导航布局；
- 390 文档宽度无横向溢出；
- 旧业务接口保持 200。

未完成项：

- 真实歌曲列表端到端联调（SQL Server 无法启动）；
- 原有业务页面完整交互回归；
- 40 案例、20 首音乐评分、区域策略等研究数据补充。

因此：

> **P8 的技术整合可以验收；研究数据目标与真实歌曲列表端到端验证不能一并宣称完成。**
