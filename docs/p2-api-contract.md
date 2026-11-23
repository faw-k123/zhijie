# P2 研究数据 API 契约

> 阶段：P2
> 状态：已完成，等待 P2 验收
> Base URL：`/api`
> 数据源：`research/data/manifest.json` → `v1.0/` 四个 JSON
> 依赖：不访问 SQL Server / Neo4j，不写数据库

---

## 1. 通用约定

### 1.1 成功响应

```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

### 1.2 失败响应

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "hash_mismatch",
    "message": "文件 SHA256 与 manifest 不一致：v1.0/cases.json",
    "details": {
      "expected": "...",
      "actual": "..."
    }
  },
  "message": "文件 SHA256 与 manifest 不一致：v1.0/cases.json"
}
```

HTTP 状态：

| 状态码 | 场景 |
|---|---|
| 200 | 正常 |
| 400 | 查询参数非法（page、page_size、grade、q 超长、case_id 格式错误） |
| 404 | 案例不存在或不在可展示范围 |
| 503 | manifest/JSON/哈希/版本/权重等文件级错误 |

### 1.3 所有接口统一返回 `sample`

每个 200 响应都带：

```json
{
  "sample": {
    "n": 3,
    "target": 40,
    "status": "insufficient",
    "label": "证据不足：样本少于5例",
    "progress_percent": 7.5,
    "thresholds": {
      "exploratory": 5,
      "descriptive": 20
    }
  }
}
```

规则：

| n | status |
|---|---|
| 0 | `empty` |
| 1—4 | `insufficient` |
| 5—19 | `exploratory` |
| ≥20 | `descriptive` |

`sample.n` 是“已审核且允许展示”的案例数，当前为 3；不是当前筛选结果数。筛选结果数由 `total` / `result_count` 表示。前端不得自行计算 status。

---

## 2. 接口总表

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/research/status/` | 版本、样本、覆盖、等级 |
| GET | `/api/research/cases/` | 案例列表与筛选 |
| GET | `/api/research/cases/<case_id>/` | 案例详情与 10 项编码 |
| GET | `/api/research/statistics/` | 基础分布与指标覆盖 |
| GET | `/api/research/success-factors/` | 成功因素；不足时 unavailable |
| GET | `/api/research/music-potential/` | 音乐潜力；当前 pending |
| GET | `/api/research/regional-matrix/` | 区域矩阵；当前 pending |

---

## 3. `GET /api/research/status/`

### 响应示例

```json
{
  "success": true,
  "data": {
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
  },
  "message": ""
}
```

用途：P3 全球传播驾驶舱的顶部 KPI、数据状态、版本标识。

---

## 4. `GET /api/research/cases/`

### 查询参数

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `q` | string | `""` | 搜索案例编号、演奏者、国家、作品、乐器、主题；最长 100 字符 |
| `country` | string | `""` | 精确匹配，如“法国” |
| `region` | string | `""` | 精确匹配，如“欧洲” |
| `instrument` | string | `""` | 精确匹配数组元素，如“二胡” |
| `channel` | string | `""` | 精确匹配，如“线下音乐会” |
| `theme` | string | `""` | 精确匹配，如“青年文化交流” |
| `grade` | string | `""` | A/B/C/D；当前数据只有 B |
| `page` | int | 1 | ≥1 |
| `page_size` | int | 12 | 1—50 |
| `include_unverified` | — | — | P2 不提供；C/D 默认不展示 |

### 响应示例

```json
{
  "success": true,
  "data": {
    "sample": { "n": 3, "target": 40, "status": "insufficient" },
    "items": [
      {
        "case_id": "CASE001",
        "performer": "Eliott Tordo（艾略特·托多）",
        "country": "法国",
        "region": "欧洲",
        "subregion": "西欧",
        "instrument": ["二胡"],
        "work": "影视/游戏配乐改编为主……",
        "music_type": "民族器乐（跨文化改编）",
        "event_date_text": "2016年起学习；2020年起视频走红；2023年11月中国12城巡演",
        "channel": ["网络视频", "线下音乐会", "教学"],
        "era_theme": ["数字技术与传统音乐", "青年文化交流", "丝绸之路与文明交流"],
        "review_status": "B",
        "source_count": 3,
        "mean_score": 2.6,
        "score_scale": 3,
        "valid_count": 10,
        "missing_count": 0,
        "low_coverage": false,
        "summary": "法国二胡演奏者……"
      }
    ],
    "total": 2,
    "result_count": 1,
    "pagination": {
      "page": 1,
      "page_size": 1,
      "pages": 2,
      "has_next": true,
      "has_previous": false
    },
    "filters": {
      "q": "二胡",
      "country": "",
      "region": "",
      "instrument": "",
      "channel": "",
      "theme": "",
      "grade": ""
    }
  },
  "message": ""
}
```

说明：

- 只返回 `review_status A/B` 且 `display_allowed=true`。
- `mean_score` 是有效指标均分（0—3），不是证据等级。
- `missing_count` 是 `null` 评分数量；`low_coverage` 表示有效指标 <6。

---

## 5. `GET /api/research/cases/<case_id>/`

### 路径参数

`case_id` 必须是 `CASE001` 格式。

### 响应示例（sources 为节选，实际返回全部来源）

```json
{
  "success": true,
  "data": {
    "sample": { "n": 3, "target": 40, "status": "insufficient" },
    "case": {
      "case_id": "CASE001",
      "performer": "Eliott Tordo（艾略特·托多）",
      "review_status": "B",
      "sources": [
        {
          "source_id": "C001-S001",
          "title": "法国二胡音乐人演绎中国风",
          "publisher": "人民网-国际频道（盛霜）",
          "url": "http://world.people.com.cn/n1/2021/0926/c1002-32237068.html",
          "published_at": "2021-09-26",
          "accessed_at": "2026-10-25",
          "reliability": "高"
        }
      ]
    },
    "coding": {
      "mean_score": 2.6,
      "score_scale": 3,
      "valid_count": 10,
      "missing_count": 0,
      "low_coverage": false,
      "indicators": [
        {
          "indicator_id": "emotional_resonance",
          "label": "情感共通性",
          "order": 1,
          "score": 3,
          "evidence": "6条可核验评论中……",
          "source_ids": ["C001-S001", "C001-S003"],
          "missing_reason": null
        }
      ]
    },
    "similar_cases": [
      {
        "case_id": "CASE003",
        "match_score": 68,
        "match_reasons": [
          "使用相同乐器",
          "共同主题：丝绸之路与文明交流、数字技术与传统音乐、青年文化交流",
          "共同渠道：线下音乐会"
        ],
        "mean_score": 2.11
      }
    ],
    "warnings": []
  },
  "message": ""
}
```

说明：

- `indicators` 固定 10 项；缺失评分 `score=null`，并带 `missing_reason`。
- `similar_cases` 最多 3 个，不含自己；匹配分和理由是规则结果，不是“相似度概率”。
- 只返回 A/B 且可展示案例，否则 404。

---

## 6. `GET /api/research/statistics/`

### 响应示例

```json
{
  "success": true,
  "data": {
    "sample": { "n": 3, "target": 40, "status": "insufficient" },
    "distributions": {
      "country": [
        { "key": "日本", "count": 1 },
        { "key": "法国", "count": 1 },
        { "key": "美国", "count": 1 }
      ],
      "region": [
        { "key": "东亚", "count": 1 },
        { "key": "北美", "count": 1 },
        { "key": "欧洲", "count": 1 }
      ],
      "instrument": [
        { "key": "二胡", "count": 2 },
        { "key": "古筝", "count": 1 }
      ],
      "channel": [
        { "key": "线下音乐会", "count": 3 },
        { "key": "媒体", "count": 2 },
        { "key": "学校教育", "count": 1 },
        { "key": "教学", "count": 1 },
        { "key": "网络视频", "count": 1 }
      ],
      "theme": [
        { "key": "丝绸之路与文明交流", "count": 3 },
        { "key": "青年文化交流", "count": 3 },
        { "key": "数字技术与传统音乐", "count": 2 },
        { "key": "非遗保护", "count": 1 }
      ],
      "evidence_grade": [
        { "key": "B", "count": 3 }
      ]
    },
    "indicator_coverage": [
      {
        "indicator_id": "emotional_resonance",
        "label": "情感共通性",
        "valid_count": 2,
        "missing_count": 1
      }
    ],
    "rankings_allowed": false,
    "success_factors_available": false,
    "warnings": []
  },
  "message": ""
}
```

说明：

- `distributions` 是计数，不是偏好排行。
- `indicator_coverage` 只给有效/缺失数量，不给均值排序。
- 当前 `rankings_allowed=false`（需单个指标 n≥20）；`success_factors_available` 表示是否进入探索性展示（总样本 n≥5）。
- 不提供“全球接受度排行”“国家偏好排行”。

---

## 7. `GET /api/research/success-factors/`

### 7.1 指标级门禁

排行不是只看总样本，而是逐指标判断：

| 单个指标有效评分 n | `status` | 是否排序 |
|---:|---|---|
| 0 | `empty` | 否 |
| 1—4 | `insufficient` | 否 |
| 5—19 | `exploratory` | 否；只展示均值、n、缺失量 |
| ≥20 | `descriptive` | 是 |

总样本仍使用 5 / 20 两级门禁：

- 总样本 <5：`availability=unavailable`，`rankings=null`；
- 5—19：`availability=exploratory`，`rankings=[]`；
- ≥20：`availability=descriptive`，只把 `n≥20` 的指标放入 `rankings`。

### 7.2 当前 n=3 的响应

```json
{
  "success": true,
  "data": {
    "sample": {
      "n": 3,
      "target": 40,
      "status": "insufficient",
      "label": "证据不足：样本少于5例"
    },
    "availability": "unavailable",
    "rankings": null,
    "factors": [
      {
        "indicator_id": "emotional_resonance",
        "label": "情感共通性",
        "order": 1,
        "n": 3,
        "missing_count": 0,
        "mean_score": 2.33,
        "score_scale": 3,
        "status": "insufficient",
        "status_label": "证据不足",
        "ranking_allowed": false,
        "gate_note": "有效评分少于5例，不参与排行榜；仅可作为单案例记录。",
        "rank": null
      }
    ],
    "reason": "整体样本不足5例，统计层不提供成功因素排行；指标级门禁仍列出覆盖情况。",
    "thresholds": {
      "exploratory": 5,
      "descriptive": 20,
      "indicator_exploratory_min": 5,
      "indicator_rank_min": 20
    },
    "gate_counts": {
      "empty": 0,
      "insufficient": 10,
      "exploratory": 0,
      "descriptive": 0
    }
  },
  "message": ""
}
```

### 7.3 说明

- `factors` 固定 10 项，即使总样本不足也返回，用于解释缺口；
- `rankings` 只包含 `status=descriptive` 且 `n≥20` 的指标；
- `n=1—4` 的指标即使均值很高，也不得进入排行榜；
- `n=5—19` 必须同时展示 `n` 和 `missing_count`，不得写成“第一名”；
- `rank` 只对进入 `rankings` 的指标赋值，其余为 `null`。


### 7.4 分析样本筛选

以下接口支持 `analysis_sample` 查询参数：

- `GET /api/research/cases/`
- `GET /api/research/statistics/`
- `GET /api/research/success-factors/`

取值：

| 值 | 含义 |
|---|---|
| `all`（默认） | 全部扩展案例 |
| `strict_candidate` | 严格样本候选（待审批，3 例） |
| `strict_individual` | 正式严格样本（仅 approved；当前 2 例） |
| `extended_cross_cultural` | 扩展跨文化传播样本 |
| `pending_review` | 待核实案例 |

响应新增：

```json
{
  "analysis_scope": {
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
}
```

口径：

- `case_count`：当前样本范围内的独立案例数；
- `valid_score_count`：当前样本范围内非空评分记录数；
- `n` / `valid_count`：该指标有有效评分的独立案例数，不按来源数或证据条数放大；
- `missing_count`：当前样本案例数 − 有效评分数；
- `coverage_rate`：`valid_count / case_count`；
- `owner_approved_count` / `strict_approved_case_count`：`owner_approval_status=approved` 的严格案例数；
- `strict_candidate_count`：`analysis_sample=strict_individual` 的候选案例数；
- `pending_owner_review_count` / `rejected_count` / `needs_more_evidence_count`：审批状态计数。

不同 `analysis_sample` 的统计结果不得混合解释。无效值返回 400。


---

## 8. `GET /api/research/music-potential/`

### 当前 pending 的响应

```json
{
  "success": true,
  "data": {
    "sample": { "n": 3, "target": 40, "status": "insufficient" },
    "availability": "pending",
    "status": "pending",
    "status_label": "待补充",
    "note": "P1 只转换3个案例；20首候选曲目尚未完成8项评分，不生成任何分数。",
    "music_sample": {
      "n": 0,
      "target": 20,
      "status": "empty"
    },
    "weights": {
      "emotional_resonance": 0.20,
      "timbre_identity": 0.15,
      "melody_accessibility": 0.15,
      "cultural_story": 0.10,
      "adaptation_space": 0.10,
      "visual_expressiveness": 0.10,
      "era_theme_relevance": 0.10,
      "existing_evidence": 0.10
    },
    "tiers": [
      { "min": 80, "max": 100, "label": "优先传播" },
      { "min": 65, "max": 79.99, "label": "适合传播，但需要适配" },
      { "min": 50, "max": 64.99, "label": "需要较多文化解释" },
      { "min": 0, "max": 49.99, "label": "暂不作为主要国际传播对象" }
    ],
    "items": [],
    "rankings": null
  },
  "message": ""
}
```

说明：

- 当前没有 20 首曲目评分，`items=[]`、`rankings=null`。
- 权重合计 1.0；缺项不重算权重。
- P3 只能显示“待补充”，不能显示 0 分或空排行榜。

---

## 9. `GET /api/research/regional-matrix/`

### 当前 pending 的响应

```json
{
  "success": true,
  "data": {
    "sample": { "n": 3, "target": 40, "status": "insufficient" },
    "availability": "pending",
    "status": "pending",
    "status_label": "待补充",
    "note": "P1 只转换案例；区域—文化—宗教—时代主题矩阵尚未完成研究与审核，不生成推荐行。",
    "regions": ["东亚", "东南亚", "欧洲", "北美", "中东及部分伊斯兰文化地区", "拉丁美洲"],
    "audiences": ["音乐学院学生", "华裔社群", "青年短视频用户", "世界音乐爱好者", "博物馆与文化机构", "综合"],
    "themes": ["丝绸之路与文明交流", "和平与友谊", "自然生态与山水审美", "乡愁、迁徙与故乡", "非遗保护", "青年文化交流", "女性艺术表达", "城市化与传统记忆", "数字技术与传统音乐", "心理疗愈与情绪共鸣"],
    "rows": [],
    "matrix": null,
    "independent_of_case_sample": true,
    "scope_note": "区域矩阵是独立的研究框架，不随案例样本筛选变化；当前 rows=0。"
  },
  "message": ""
}
```

说明：

- `rows=[]`、`matrix=null`；P3 显示“矩阵待补充”。
- 不提供任何未经验证的区域偏好。
- 区域矩阵独立于案例样本，不支持 `analysis_sample` 筛选；页面必须明确标注。

---

## 10. 错误码

| code | HTTP | 说明 |
|---|---|---|
| `manifest_missing` | 503 | manifest 不存在 |
| `manifest_unreadable` | 503 | manifest 无法读取 |
| `invalid_json` | 503 | JSON 解析失败 |
| `invalid_json_root` | 503 | JSON 顶层不是对象 |
| `schema_version_mismatch` | 503 | schema_version 不匹配 |
| `data_version_mismatch` | 503 | data_version 与 active_version 不匹配 |
| `missing_active_version` | 503 | manifest 缺 active_version |
| `active_version_not_found` | 503 | active_version 不在版本列表 |
| `version_not_reviewed` | 503 | 版本不是 reviewed |
| `invalid_version_path` | 503 | 版本目录名非法 |
| `manifest_files_mismatch` | 503 | 文件清单不是四个文件 |
| `invalid_target_count` | 503 | target_case_count 非正 |
| `data_file_missing` | 503 | 数据文件缺失 |
| `data_file_unreadable` | 503 | 数据文件不可读 |
| `file_size_mismatch` | 503 | 文件大小与 manifest 不一致 |
| `hash_mismatch` | 503 | SHA256 不一致 |
| `invalid_cases` | 503 | cases 不是数组 |
| `invalid_scores` | 503 | scores 不是数组 |
| `invalid_music_status` | 503 | 音乐状态非法 |
| `invalid_music_weights` | 503 | 权重非法或合计不为 1 |
| `invalid_regional_status` | 503 | 区域矩阵状态非法 |

查询参数错误返回 400；案例不存在返回 404；不返回 500 堆栈给前端。

---

## 11. P2 未包含的接口

以下接口属于后续阶段，P2 不提前实现：

- P6：单曲“海外传播”上下文接口；
- P7：区域传播方案生成接口；
- 任何写操作、审核操作、案例编辑接口。

P3 做全球传播驾驶舱时，只消费本文件中的 7 个只读接口。


---

## 12. P6 增补：`GET /api/research/music-context/`

### 12.1 为什么新增

P2 的 7 个接口没有“单曲研究上下文”，而 P6 需要按当前曲目精确回答：

- 这首歌有没有 `music_scores` 评分；
- 有没有由 `related_case_ids` 明确关联的海外案例；
- 有没有 `music_ids` 明确包含该曲的区域策略。

现有 `cases.json` 没有 `music_id` 字段，`work` 是不可靠的自由文本；不能在前端按曲名/乐器模糊匹配，否则会把无关案例挂到错误歌曲下面。因此增加一个只读上下文接口，**不修改原有 7 个接口行为**。

### 12.2 查询参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `title` | 是 | 当前曲目名称，最长 120 字符 |
| `category` | 否 | 音乐库大类，如“乐器” |
| `subcategory` | 否 | 音乐库子类，如“古筝” |
| `song_id` | 否 | 音乐库曲目编号；只用于匹配 `music_scores.music_id` |

### 12.3 关联规则

- 评分：`music_id` 精确匹配，或曲名归一化后精确匹配；不使用模糊相似。
- 案例：只使用 `music_scores.items[].related_case_ids`。
- 区域：只使用 `regional_strategies.rows[].music_ids`。
- 不把曲名、乐器、国家或主题作为案例/区域的推断关联依据。
- 没有关联时返回 `unmapped` 和空数组，不返回 0 分或相似案例。

### 12.4 当前响应（无评分关联）

```json
{
  "success": true,
  "data": {
    "sample": {
      "n": 3,
      "target": 40,
      "status": "insufficient",
      "label": "证据不足：样本少于5例"
    },
    "music": {
      "song_id": "123",
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
    "music_status_label": "待补充",
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
    ]
  },
  "message": ""
}
```

### 12.5 字段语义

| 字段 | 说明 |
|---|---|
| `association.status` | `linked` 或 `unmapped`；不等于“成功/失败”评价 |
| `association.matched_by` | `music_id`、`exact_title` 或 `null` |
| `potential` | 有精确评分条目时返回；没有时为 `null` |
| `related_cases` | 只来自 `related_case_ids`，可为空 |
| `regional_rows` | 只来自 `music_ids`，可为空 |
| `music_status` | `pending / partial / complete` |
| `weights` / `tiers` | 评分规则；即使无评分也返回，供前端解释“待评估” |

旧 7 个接口的路径、参数、响应保持不变。


---

## 13. P7 增补：`POST /api/research/promo-plan/`

### 13.1 用途

将 12 项用户输入与 P6 单曲上下文组合，生成 9 个结构化传播方案模块。方案不调用大模型，采用规则模板；重点是把：

- 已有证据
- 策略建议
- 待验证假设
- 证据缺口

分开返回，避免模板文字被误读为研究事实。

### 13.2 请求体

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

- `title`、`target_country`、`target_city`
- `target_audience`、`age_range`
- `purpose`
- `platform`、`content_format`
- `adaptation_allowed`（`yes/no/undecided`）
- `budget_range`、`duration`、`language`

可选：

- `origin_city`：北京 / 上海 / 其他；作为作品来源城市元数据，不替代目标城市。

### 13.3 响应结构

```json
{
  "success": true,
  "data": {
    "meta": {
      "plan_id": "PLAN-...",
      "generation_mode": "rule_template",
      "ai_generated": false,
      "data_version": "v1.0",
      "module_count": 9,
      "inputs": {}
    },
    "sample": {},
    "evidence_summary": {
      "potential": {},
      "case_count": 0,
      "regional_count": 0,
      "source_count": 0
    },
    "counts": {
      "evidence": 0,
      "suggestions": 16,
      "hypotheses": 9,
      "gaps": 9
    },
    "modules": [
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
    ],
    "warnings": [],
    "disclaimer": "本方案由规则模板生成，不调用大模型..."
  },
  "message": ""
}
```

### 13.4 9 个模块

1. `01_music_positioning` 音乐与文化定位
2. `02_target_region` 目标区域分析
3. `03_audience` 目标受众分析
4. `04_music_fit` 音乐适配分析
5. `05_adaptation` 跨文化表达策略
6. `06_theme` 传播主题设计
7. `07_channels` 渠道与内容规划
8. `08_execution` 执行计划
9. `09_evaluation` 效果评估

### 13.5 真实性规则

- `evidence` 只来自音乐评分、`related_case_ids` 案例、`music_ids` 区域策略。
- 没有证据时，模块的 `evidence` 为空，不得用模板文字冒充证据。
- `suggestions` 必须写 `basis`，标明来自用户输入还是通用执行原则。
- `hypotheses` 必须写 `validation`，说明如何验证。
- `gaps` 必须写 `action`，说明缺什么、下一步补什么。
- 不生成具体宗教禁忌、受众偏好或效果提升百分比。
- 旧 `POST /api/promo/report/` 保留，行为不变；P7 页面使用新接口。

