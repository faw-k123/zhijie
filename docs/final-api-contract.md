# 最终 API 契约

> 项目：智解国音 · 国际传播研究模块
> 版本：v1.0
> 日期：2026-10-30
> 适用范围：P2 基础接口 + P6 单曲上下文 + P7 方案生成
> 详细字段级说明：[p2-api-contract.md](<p2-api-contract.md>)

---

## 1. 通用约定

### 1.1 前缀

```text
/api/research/
```

### 1.2 成功响应

```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

### 1.3 失败响应

```json
{
  "success": false,
  "message": "错误说明",
  "code": "错误代码"
}
```

### 1.4 状态码

| 状态码 | 含义 |
|---:|---|
| 200 | 成功 |
| 400 | 参数缺失或非法 |
| 404 | 案例不存在 |
| 503 | 研究数据不可用、manifest 非 reviewed、哈希/大小校验失败、JSON 损坏 |

### 1.5 数据版本

- `active_version`：当前 manifest 指定的版本；
- 只有 `status=reviewed` 的版本允许对外展示；
- 每个文件有 SHA256 与字节数校验；
- 不读取 `research/data` 之外的研究数据。

### 1.6 样本门禁

| 样本数 | 状态 | 允许 |
|---:|---|---|
| 0 | empty | 空状态 |
| 1—4 | insufficient | 单案例展示，不生成排行榜/总体推断 |
| 5—19 | exploratory | 探索性统计，标注样本不足 |
| ≥20 | descriptive | 描述性统计 |

当前 `n=3`，所有接口返回 `insufficient`。

---

## 2. 接口清单

| # | 方法 | 路径 | 用途 |
|---:|---|---|---|
| 1 | GET | `/api/research/status/` | 数据版本、样本、来源、更新时间 |
| 2 | GET | `/api/research/cases/` | 案例搜索/筛选/分页 |
| 3 | GET | `/api/research/cases/<case_id>/` | 案例详情、指标、来源、相关案例 |
| 4 | GET | `/api/research/statistics/` | 国家/乐器/区域/证据等级/评分覆盖 |
| 5 | GET | `/api/research/success-factors/` | 成功因素门禁与排行榜 |
| 6 | GET | `/api/research/music-potential/` | 音乐潜力模型、权重、条目 |
| 7 | GET | `/api/research/regional-matrix/` | 区域—文化—主题矩阵 |
| 8 | GET | `/api/research/music-context/` | P6 单曲精确上下文 |
| 9 | POST | `/api/research/promo-plan/` | P7 结构化传播方案 |
| 10 | GET | `/api/research/mining/` | 当前案例数据挖掘、成对相关、音乐库只读连接 |

P8 新增 `/api/research/mining/`；旧 `POST /api/promo/report/` 保留，行为不变。

---

## 2.1 `GET /api/research/mining/`

用途：当前激活版本的案例画像、十项指标覆盖、成对 Spearman 相关、音乐库只读连接。

查询参数：

- `analysis_sample`：`all`（默认）/ `strict_candidate` / `strict_individual` / `extended_cross_cultural` / `pending_review`。

返回要点：

- `case_count`：独立案例数；
- `score_count` / `valid_score_count`：指标记录与有效值；
- `cases[]`：案例元数据与十项分数；
- `indicators[]`：n、缺失、均值、门槛；
- `correlations[]`：45 对；`n<5` 不计算，`n<20` 仅 exploratory；
- `library`：SQL Server `traditional_song` 只读状态、曲目数、映射数；
- `scope_note`：样本限制。

不返回排名、因果结论或预测值。

## 3. 基础接口

### 3.1 `GET /api/research/status/`

返回：

```json
{
  "sample": {
    "n": 3,
    "target": 40,
    "status": "insufficient",
    "label": "证据不足：样本少于5例",
    "progress_percent": 7.5,
    "thresholds": { "exploratory": 5, "descriptive": 20 }
  },
  "version": {
    "active_version": "v1.0",
    "status": "reviewed",
    "updated_at": "2026-10-30",
    "created_at": "2026-10-30T10:30:00+08:00"
  },
  "counts": {
    "cases": 3,
    "sources": 7,
    "countries": 3,
    "instruments": 2
  },
  "countries": ["日本", "法国", "美国"],
  "instruments": ["二胡", "古筝"],
  "grade_counts": { "A": 0, "B": 3, "C": 0, "D": 0 },
  "warnings": []
}
```

### 3.2 `GET /api/research/cases/`

查询参数：

| 参数 | 说明 |
|---|---|
| `q` | 关键词：案例 ID、演奏者、曲目、摘要 |
| `country` | 国家 |
| `region` | 区域 |
| `instrument` | 乐器 |
| `channel` | 传播渠道 |
| `theme` | 时代主题 |
| `grade` | 证据等级 A/B |
| `page` | 页码 |
| `page_size` | 每页数量 |

只返回已审核、允许展示的案例。响应包含 `items`、`pagination`、`sample`、`filters`。

### 3.3 `GET /api/research/cases/<case_id>/`

返回：

- `case`：案例事实；
- `score_records`：10 项指标评分、来源、证据；
- `related_cases`：同乐器/同区域/同主题的相关案例；
- `sample`、`warnings`。

不存在的案例返回 404。

### 3.4 `GET /api/research/statistics/`

返回：

- `sample`
- `countries`
- `instruments`
- `regions`
- `evidence_grades`
- `score_coverage`
- `warnings`

只做当前 3 个案例的描述性汇总；禁止外推总体。

### 3.5 `GET /api/research/success-factors/`

指标级门禁：

| 单个指标 n | 状态 | 排序 |
|---:|---|---|
| 0 | `empty` | 否 |
| 1—4 | `insufficient` | 否 |
| 5—19 | `exploratory` | 否；展示 n、缺失量、均值 |
| ≥20 | `descriptive` | 是 |

总样本门禁：

- `<5`：`availability=unavailable`，`rankings=null`；
- 5—19：`availability=exploratory`，`rankings=[]`；
- ≥20：`availability=descriptive`，仅 `n≥20` 的指标进入 `rankings`。

当前 `n=3` 的响应：

```json
{
  "availability": "unavailable",
  "reason": "整体样本不足5例，统计层不提供成功因素排行；指标级门禁仍列出覆盖情况。",
  "rankings": null,
  "factors": [
    {
      "indicator_id": "emotional_resonance",
      "n": 3,
      "missing_count": 0,
      "mean_score": 2.33,
      "status": "insufficient",
      "status_label": "证据不足",
      "ranking_allowed": false,
      "rank": null
    }
  ],
  "thresholds": {
    "exploratory": 5,
    "descriptive": 20,
    "indicator_exploratory_min": 5,
    "indicator_rank_min": 20
  },
  "sample": { "n": 3, "status": "insufficient" }
}
```

即使总样本达到 5 例，单个指标 n=1—4 也不得进入排行榜；n=5—19 只能探索性展示，不能写成“第一名”。

### 3.5.1 分析样本范围

`cases`、`statistics`、`success-factors` 支持：

```text
?analysis_sample=all
?analysis_sample=strict_candidate
?analysis_sample=strict_individual
?analysis_sample=extended_cross_cultural
?analysis_sample=pending_review
```

响应新增 `analysis_scope`：

```json
{
  "key": "strict_individual",
  "label": "严格海外个人演奏样本",
  "case_count": 2,
  "scored_case_count": 2,
  "valid_score_count": 14,
  "owner_approved_count": 2,
  "strict_candidate_count": 3,
  "strict_approved_case_count": 2,
  "pending_owner_review_count": 0,
  "rejected_count": 0,
  "needs_more_evidence_count": 1,
  "thresholds": { "exploratory": 5, "descriptive": 20 }
}
```

- `n` / `valid_count`：独立案例数，不按来源或证据条数放大；
- `missing_count`：当前样本案例数 − 有效评分数；
- `coverage_rate`：有效评分数 / 当前样本案例数；
- `owner_approved_count` / `strict_approved_case_count`：已批准严格案例数；
- `strict_candidate_count`：严格候选数；待审批/拒绝/需补证计数单独列出；
- 不同样本范围不得混合解释；无效值 400。


### 3.6 `GET /api/research/music-potential/`

当前返回：

```json
{
  "availability": "pending",
  "status": "pending",
  "status_label": "待补充",
  "note": "P1 只转换3个案例；20首候选曲目尚未完成8项评分，不生成任何分数。",
  "music_sample": { "n": 0, "target": 20, "status": "empty" },
  "items": [],
  "rankings": null,
  "weights": {
    "emotional_resonance": 0.2,
    "timbre_identity": 0.15,
    "melody_accessibility": 0.15,
    "cultural_story": 0.1,
    "adaptation_space": 0.1,
    "visual_expressiveness": 0.1,
    "era_theme_relevance": 0.1,
    "existing_evidence": 0.1
  },
  "tiers": [
    { "min": 80, "max": 100, "label": "优先传播" },
    { "min": 65, "max": 79.99, "label": "适合传播，但需要适配" },
    { "min": 50, "max": 64.99, "label": "需要较多文化解释" },
    { "min": 0, "max": 49.99, "label": "暂不作为主要国际传播对象" }
  ],
  "warnings": []
}
```

没有评分条目不生成 0 分。

### 3.7 `GET /api/research/regional-matrix/`

当前返回：

```json
{
  "availability": "pending",
  "regions": ["东亚", "东南亚", "欧洲", "北美", "中东及部分伊斯兰文化地区", "拉丁美洲"],
  "audiences": ["音乐学院学生", "华裔社群", "青年短视频用户", "世界音乐爱好者", "博物馆与文化机构", "综合"],
  "themes": ["丝绸之路与文明交流", "和平与友谊", "自然生态与山水审美", "乡愁、迁徙与故乡", "非遗保护", "青年文化交流", "女性艺术表达", "城市化与传统记忆", "数字技术与传统音乐", "心理疗愈与情绪共鸣"],
  "rows": [],
  "matrix": null,
  "warnings": []
}
```

6 个区域是研究范围，不是 6 条已验证策略。

---

## 4. P6 单曲上下文

### 4.1 `GET /api/research/music-context/`

查询参数：

| 参数 | 必填 | 说明 |
|---|---|---|
| `title` | 是 | 曲名 |
| `category` | 否 | 音乐库大类 |
| `subcategory` | 否 | 音乐库子类 |
| `song_id` | 否 | 音乐库曲目编号 |

### 4.2 关联规则

- 评分：`music_id` 精确匹配，或曲名归一化后精确相等；
- 案例：只认 `music_scores.items[].related_case_ids`；
- 区域：只认 `regional_strategies.rows[].music_ids`；
- 不使用曲名/乐器模糊匹配；
- 没有关联时返回 `unmapped` 和空数组。

### 4.3 当前响应

```json
{
  "music": {
    "song_id": "1",
    "title": "春江花月夜",
    "category": "乐器",
    "subcategory": "古筝"
  },
  "association": {
    "status": "unmapped",
    "matched_by": null,
    "label": "未建立曲目关联",
    "reasons": [
      "music_scores.json 中没有与《春江花月夜》精确匹配的评分记录。",
      "未使用曲名或乐器模糊匹配案例；下方不展示未确认的海外案例。",
      "regional_strategies.rows 当前没有可关联的区域策略。"
    ]
  },
  "music_status": "pending",
  "potential": null,
  "related_cases": [],
  "regional_rows": [],
  "weights": {
    "emotional_resonance": 0.2,
    "timbre_identity": 0.15,
    "melody_accessibility": 0.15,
    "cultural_story": 0.1,
    "adaptation_space": 0.1,
    "visual_expressiveness": 0.1,
    "era_theme_relevance": 0.1,
    "existing_evidence": 0.1
  },
  "tiers": [
    { "min": 80, "max": 100, "label": "优先传播" },
    { "min": 65, "max": 79.99, "label": "适合传播，但需要适配" },
    { "min": 50, "max": 64.99, "label": "需要较多文化解释" },
    { "min": 0, "max": 49.99, "label": "暂不作为主要国际传播对象" }
  ],
  "sample": {},
  "warnings": []
}
```

---

## 5. P7 方案生成

### 5.1 `POST /api/research/promo-plan/`

请求体：

```json
{
  "title": "春江花月夜",
  "target_country": "德国",
  "target_city": "柏林",
  "target_audience": "音乐学院学生",
  "age_range": "25-34",
  "purpose": "文化交流",
  "platform": "音乐学院 / 艺术节",
  "content_format": "音乐会",
  "adaptation_allowed": "yes",
  "budget_range": "中等",
  "duration": "3个月",
  "language": "Deutsch",
  "origin_city": "上海"
}
```

必填：

- 12 项：`title`、`target_country`、`target_city`、`target_audience`、`age_range`、`purpose`、`platform`、`content_format`、`adaptation_allowed`、`budget_range`、`duration`、`language`；
- `adaptation_allowed` 取值：`yes` / `no` / `undecided`。

可选：

- `origin_city`：北京 / 上海 / 其他；作为作品来源城市元数据，不替代目标城市。

### 5.2 响应

- `meta`：`plan_id`、`generation_mode=rule_template`、`ai_generated=false`、`data_version`、`module_count=9`、`inputs`；
- `sample`；
- `evidence_summary`：潜力、案例数、区域策略数、来源数；
- `counts`：证据/建议/假设/缺口数量；
- `modules`：固定 9 个模块；
- `disclaimer`；
- `warnings`。

每个模块固定：

```json
{
  "id": "01_music_positioning",
  "title": "音乐与文化定位",
  "evidence": [],
  "suggestions": [
    { "text": "...", "basis": "...", "kind": "suggestion" }
  ],
  "hypotheses": [
    { "text": "...", "validation": "...", "kind": "hypothesis" }
  ],
  "gaps": [
    { "text": "...", "action": "...", "kind": "gap" }
  ]
}
```

9 个模块：

1. `01_music_positioning`
2. `02_target_region`
3. `03_audience`
4. `04_music_fit`
5. `05_adaptation`
6. `06_theme`
7. `07_channels`
8. `08_execution`
9. `09_evaluation`

### 5.3 真实性约束

- `evidence` 只来自研究数据；
- 没有证据时返回空数组；
- `suggestions` 必须带 `basis`；
- `hypotheses` 必须带 `validation`；
- `gaps` 必须带 `action`；
- 不生成具体宗教禁忌、受众偏好、效果提升百分比；
- 不调用大模型，不写数据库。

---

## 6. 旧接口

以下接口保留，行为不变：

```text
POST /api/promo/report/
POST /api/global/propagation/
```

P7 页面使用新的 `/api/research/promo-plan/`，不复用旧接口的散文式输出。
