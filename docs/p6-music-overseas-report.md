# P6 音乐详情「海外传播」Tab 报告

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P6（音乐详情海外传播 Tab + 单曲精确关联）
> 日期：2026-10-30
> 状态：P6 完成，等待验收
> 范围：在现有 MusicDetailView 增加第四个 Tab；不改原三个 Tab；不进入 P7

---

## 1. 本阶段完成内容

1. 先做关联检查：现有 P2 没有单曲上下文接口，`cases.json` 没有 `music_id` 字段，`music_scores.json` 仍为 `pending` 且 `items=[]`。
2. 新增只读接口 `GET /api/research/music-context/`，用于单曲精确关联；原有 7 个接口不变。
3. 在 `MusicDetailView.vue` 增加第四个 Tab“海外传播”。
4. 展示单曲的：
   - 基本曲目信息
   - 传播潜力待评估状态
   - 8 项权重与评分规则
   - 关联案例
   - 区域适配策略
   - 关联说明与待验证的下一步
5. 当前曲目没有精确关联时，明确显示“暂无关联案例”“区域适配研究待补充”，不塞入无关案例。
6. 新增 3 个后端测试（总计 20 个），验证无关联与显式关联两条路径。

---

## 2. 为什么新增单曲上下文接口

现有 7 个接口的职责：

- `music-potential` 返回全部音乐潜力，不是单曲上下文；
- `cases` 返回案例列表，不能判断某案例是否属于当前歌曲；
- `regional-matrix` 返回全部区域策略，不能按当前歌曲筛选。

数据层现状：

```text
music_scores.status = pending
music_scores.items = []
cases.json 没有 music_id 字段
regional_strategies.rows = 0
```

因此不能在前端按曲名或乐器模糊匹配案例。新增一个只读上下文接口，统一在服务端做精确关联，避免 P6 前端自行猜测。

新增接口：

```text
GET /api/research/music-context/?title=...&category=...&subcategory=...&song_id=...
```

契约已追加到：

[P2 API 契约 · P6 增补](<p2-api-contract.md>)

---

## 3. 精确关联规则

### 3.1 音乐评分

只按以下顺序匹配：

1. `music_scores.items[].music_id == song_id`
2. 曲名归一化后精确相等，且 category/subcategory 匹配

不使用模糊相似、关键词包含或乐器推断。

### 3.2 海外案例

只认：

```text
music_scores.items[].related_case_ids
```

当前没有曲目评分条目，也没有 `related_case_ids`，所以：

```json
{
  "association": {
    "status": "unmapped",
    "matched_by": null,
    "label": "未建立曲目关联"
  },
  "related_cases": []
}
```

不会把 CASE001—CASE003 全部展示到每首歌下面。

### 3.3 区域策略

只认：

```text
regional_strategies.rows[].music_ids
```

当前 `rows=0`，因此：

```json
{
  "regional_rows": []
}
```

---

## 4. 页面结构

### 4.1 顶部

- 曲名：`春江花月夜`
- 分类：`乐器 / 古筝`
- 曲目编号
- 样本徽标：`证据不足 · 3/40`
- 关联状态：`未建立曲目关联`

### 4.2 关联说明

逐条说明：

- `music_scores` 没有精确匹配评分记录；
- 未使用曲名/乐器模糊匹配案例；
- 区域策略当前没有可关联记录。

### 4.3 传播潜力评估

- 状态：`待评估`
- `0 / 8` 项有评分
- `8` 项待补
- 8 项权重卡：
  - 情感共通性 20%
  - 音色辨识度 15%
  - 旋律易接受度 15%
  - 文化故事可解释性 10%
  - 跨文化改编空间 10%
  - 视觉表现力 10%
  - 时代主题关联度 10%
  - 已有案例或海外反馈 10%
- 所有指标显示“待评分”，不写成 0 分。
- 不显示总分、排名或分级。

### 4.4 相关海外演奏案例

- 空状态：`暂无关联案例`
- 说明：没有找到与该曲目精确关联的案例，本页不会把无关案例放进来。
- 当前 `0` 个案例。

### 4.5 区域适配研究

- 空状态：`区域适配研究待补充`
- 说明：没有 `music_ids` 包含该曲的已审核策略，不根据曲名或乐器推断目标国家。
- 当前 `0` 条策略。

### 4.6 单曲关联侧栏

展示：

- 曲目
- 分类
- 音乐库编号
- 关联方式（未匹配）
- 相关案例 0
- 区域策略 0

### 4.7 传播建议（待验证）

只给数据补齐步骤：

- 完成 8 项音乐潜力评分；
- 在 `music_scores` 中补充 `related_case_ids`；
- 补充 `music_ids` 明确的区域策略和 `match_reason`；
- 人工复核后再转成方案。

页面明确说明：这些是数据补齐步骤，不是区域适配结论。

---

## 5. 原页面兼容

- 原有三个 Tab 保持不变：
  - 基本信息
  - 情感分析
  - 国际传播分析
- 只在底部导航增加第四个按钮“海外传播”。
- 现有 Tab 的数据请求、图表和样式未改。
- 新 Tab 请求失败不会影响原三个 Tab。
- 切歌时清除旧单曲上下文，避免显示上一首歌的数据。
- 切分类/子类时清除上下文。

---

## 6. 截图

### 6.1 桌面 1440

![P6 海外传播 1440](<screenshots/p6-overseas-1440.png>)

文件：[p6-overseas-1440.png](<screenshots/p6-overseas-1440.png>)
尺寸：1440 × 1712。

### 6.2 窄屏 390

![P6 海外传播 390](<screenshots/p6-overseas-390.png>)

文件：[p6-overseas-390.png](<screenshots/p6-overseas-390.png>)
尺寸：390 × 3164。

### 6.3 截图说明

- 当前本机 SQL Server 未启动，无法让原有“歌曲列表”接口返回真实曲目。
- 截图时只在浏览器层临时 mock 了既有 `/api/emotion/subcategory-songs/` 与相关展示接口，用于把当前曲目渲染出来。
- P6 的 `/api/research/music-context/` **走的是真实后端接口**，没有 mock。
- mock 只存在于截图脚本，没有写入应用代码，也没有写入 `research/data`。
- 截图时把固定底部导航改为静态，以便完整长页展示；实际页面仍保持原有固定底部导航。

---

## 7. 验证结果

| 检查 | 结果 |
|---|---|
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过，仅有既有 chunk size warning |
| `python manage.py check` | 通过 |
| `python manage.py test propagation.tests` | 20/20 通过 |
| 原有 17 个测试 | 全部通过 |
| 原 7 个研究接口 | 行为未改 |
| 新增单曲上下文接口 | 200，unmapped 正确 |
| 显式 `related_case_ids` 测试 | 正确关联 CASE001 |
| 海外传播 Tab | 4 个 Tab 正常 |
| 相关案例数 | 0（当前无精确关联） |
| 区域策略数 | 0（当前 rows=0） |
| 音乐权重卡 | 8 |
| 虚假案例/评分/区域关系 | 0 |
| 数据库/migration | 0 |
| AppNav | 未改 |

测试命令输出：

```text
Found 20 test(s)
Ran 20 tests
OK
```

---

## 8. 已知限制

1. 当前 `music_scores.items=[]`，所有曲目都会显示“传播潜力待评估”。
2. 当前 `cases.json` 没有 `music_id`，也没有 `related_case_ids`，所以所有曲目暂时显示“暂无关联案例”。
3. 当前 `regional_strategies.rows=0`，所有曲目显示“区域适配研究待补充”。
4. 音乐详情页原有歌曲列表依赖 SQL Server；本机未启动，截图使用浏览器层临时 mock 渲染曲目。应用代码没有 mock 数据。
5. AppNav 未改；仍通过详情页路由访问。
6. 390 下页面主体可用；AppNav 仍有全站既有横向溢出。

---

## 9. P6 验收对照

- [x] 现有音乐详情页增加第四个 Tab
- [x] 原有三个 Tab 保持原样
- [x] 每首歌只展示精确关联的案例
- [x] 无关联时显示“暂无关联案例”
- [x] 传播潜力待评估时不显示假分数/排名
- [x] 区域策略为空时显示“待补充”
- [x] 缺失评分不用 0 分
- [x] 不按曲名/乐器推断国家适配
- [x] 传播建议区分数据补齐步骤与结论
- [x] 单曲上下文接口有契约和测试
- [x] 原 7 个接口行为未改
- [x] 数据库/migration 未改
- [x] AppNav 未改
- [x] `type-check`、`build-only`、`check`、20 个测试通过
- [x] 未提前开发 P7

P6 到此停止，不进入 P7。
