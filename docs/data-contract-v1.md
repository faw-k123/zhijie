# 研究数据契约 v1.0

> 阶段：P0—P2
> 状态：P1/P2 已完成；当前数据版本 `v1.0`，`reviewed`
> 适用范围：全球传播页、案例库、案例详情、研究洞察、音乐详情“海外传播”、区域传播方案
> 关联方案：[research-module-plan-v1.md](research-module-plan-v1.md)

> 说明：本文中的 JSON 均为结构示例，用来确认字段与规则；真实数据已由 P1 按现有 3 个案例写入 `research/data/v1.0/`。

---

## 1. 目的与原则

这份契约解决四个问题：

1. 研究 Excel、后端 API、前端字段使用同一套命名，避免“案例编号 / caseId / id”混用。
2. 任何分数都能追溯到案例与来源，任何结论都能追溯到案例编号。
3. 数据不足时，程序知道该隐藏什么、该提示什么。
4. 研究数据可以版本化更新和回滚，不因为一次误改影响答辩。

五条硬规则：

- **未知不是 0。** 缺失分数写 `null`，并写 `missing_reason`；不得用 0 分代替。
- **分数不是证据等级。** `mean_score` 表示编码表现，`review_status` 表示证据可靠性，两者分开存储、分开展示。
- **没有来源不给分。** 非空分数必须有 `evidence` 和至少一个 `source_ids`。
- **没有充分样本不做排行。** `n<5` 只展示案例事实，不展示成功因素排行榜或国家/区域偏好。
- **正式统计只用 A/B。** C/D 默认不进入统计和推荐；页面可手动查看，但必须有警示。

---

## 2. 目录与版本

```text
research/
└─ data/
   ├─ README.md
   ├─ manifest.json
   └─ v1.0/
      ├─ cases.json
      ├─ success_factors.json
      ├─ music_scores.json
      └─ regional_strategies.json
```

规则：

- `v1.0/` 发布后只读。修正数据时新建 `v1.1/`，不原地改旧版本。
- `manifest.json` 的 `active_version` 决定后端读哪个版本。
- 每个版本的文件都记录 SHA256；加载前校验，校验失败不进入统计。
- 回滚只改 `active_version`，不删除新版本。
- P1 先创建 `v1.0`，状态为 `draft`；P1 验收通过后已改为 `reviewed`。
- P2 的数据服务只加载 `reviewed` 版本；`draft` 会被拒绝并返回 503。

---

## 3. 通用约定

### 3.1 命名

- JSON 字段统一 `snake_case`。
- 案例编号：`CASE001` 起，三位数字。
- 来源编号：`C001-S001`，与案例编号对应。
- 曲目编号：`MUS001` 起。
- 区域策略编号：`REG-<REGION>-<COUNTRY>-<AUDIENCE>-<NNN>`，例如 `REG-EU-DE-CONS-001`。
- 指标 ID 固定为 10 个英文 key，中文只用于展示。

### 3.2 时间

- 机器可读日期：`YYYY-MM-DD`。
- 时间戳：ISO 8601，带时区，例如 `2026-10-30T10:00:00+08:00`。
- 无法精确到日的原始信息（如“2016年起学习”）放 `date_text`，精确日期字段填 `null`，不强行编造。

### 3.3 未知值

- 字符串未知：`null` 或 `"未知"`，按字段定义。
- 分数未知：`null`。
- 数组未知：`[]`，并在 `missing_reason` 说明。
- 禁止用 `0`、`""`、`"暂无"` 伪装未知。

### 3.4 审核状态

| 值 | 含义 | 是否进入正式统计 |
|---|---|---|
| `A` | 证据充分 | 是 |
| `B` | 基本可信，部分信息缺失 | 是 |
| `C` | 待核实 | 否，默认隐藏 |
| `D` | 排除 | 否，默认隐藏 |

---

## 4. `manifest.json`

```json
{
  "schema_version": "1.0.0",
  "active_version": "v1.0",
  "target_case_count": 40,
  "updated_at": "2026-10-30",
  "versions": [
    {
      "version": "v1.0",
      "path": "v1.0",
      "status": "reviewed",
      "created_at": "2026-10-30T10:30:00+08:00",
      "reviewed_by": "项目负责人",
      "reviewed_at": "2026-10-30",
      "files": {
        "cases.json": { "sha256": "<64 hex>", "bytes": 0 },
        "success_factors.json": { "sha256": "<64 hex>", "bytes": 0 },
        "music_scores.json": { "sha256": "<64 hex>", "bytes": 0 },
        "regional_strategies.json": { "sha256": "<64 hex>", "bytes": 0 }
      }
    }
  ]
}
```

字段要求：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schema_version` | string | 是 | 契约版本，当前 `1.0.0` |
| `active_version` | string | 是 | 必须存在于 `versions[].version` |
| `target_case_count` | integer | 是 | 目标案例数，当前 40 |
| `updated_at` | date | 是 | manifest 更新时间 |
| `versions[].status` | enum | 是 | `draft / reviewed / archived` |
| `versions[].files[].sha256` | string | 是 | 64 位十六进制 |
| `versions[].files[].bytes` | integer | 是 | 文件字节数 |

校验失败处理：

- `active_version` 不存在：整个研究模块返回 503，页面显示“数据版本配置错误”。
- 任一文件 SHA256 不匹配：返回 503，不加载该版本。
- `status=draft` 不进入 API；数据服务返回 503 `version_not_reviewed`，页面显示“数据待验收”。
- `status=reviewed` 才允许加载；`status=archived` 不加载。

---

## 5. `cases.json`

### 5.1 顶层

```json
{
  "schema_version": "1.0.0",
  "data_version": "v1.0",
  "generated_at": "2026-10-30T10:30:00+08:00",
  "case_count": 0,
  "cases": []
}
```

### 5.2 案例对象

```json
{
  "case_id": "CASE001",
  "performer": "Eliott Tordo（艾略特·托多）",
  "performer_type": "外国个人演奏者",
  "country": "法国",
  "region": "欧洲",
  "subregion": "西欧",
  "instrument": ["二胡"],
  "work": "影视/游戏配乐改编为主；完整曲目单未公开",
  "music_type": "民族器乐（跨文化改编）",
  "event_date_text": "2016年起学习；2020年起视频走红；2023年11月中国12城巡演",
  "event_start_date": null,
  "event_end_date": null,
  "event_name": "个人视频发布与2023中国巡演",
  "venue": "法国格勒诺布尔（学习地）；中国12座城市（巡演）",
  "channel": ["网络视频", "线下音乐会", "教学"],
  "target_audience": ["西方普通听众", "影视配乐听众", "二胡学习者"],
  "learning_motivation": "2016年在电影主题曲中首次听到二胡，被音色吸引",
  "adaptation": "用二胡演奏西方影视/游戏/摇滚曲目，自述风格更史诗、更宏大",
  "era_theme": ["数字文化", "青年交流", "文明交流"],
  "religion_culture": "无（材料未提及其与宗教群体的关联）",
  "feedback": "已获6条可核验评论原文；负面反馈未采集",
  "success_evidence": "单条视频400万+；915万次观看；2023年12城巡演；每周授课",
  "research_notes": "B级：课程与学位证据缺失，负面反馈未知",
  "summary": "法国二胡演奏者，以影视/游戏改编和短视频走红，并进入中国巡演与教学。",
  "cover_url": "/media/research/cases/CASE001/cover.jpg",
  "cultural_hooks": ["音色", "影视配乐", "史诗感"],
  "origin_city": null,
  "review_status": "B",
  "display_allowed": true,
  "source_count": 3,
  "source_ids": ["C001-S001", "C001-S002", "C001-S003"],
  "sources": [],
  "updated_at": "2026-10-25"
}
```

### 5.3 字段要求

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `case_id` | string | 是 | `^CASE[0-9]{3}$`，全库唯一 |
| `performer` | string | 是 | 个人或机构全名 |
| `performer_type` | enum | 是 | 外国个人演奏者 / 外国学校/音乐学院 / 外国乐团 / 中外合作演出 / 海外网络传播 / 其他 |
| `country` | string | 是 | 统一中文国名，如“法国”“美国”“日本” |
| `region` | enum | 是 | 东亚 / 东南亚 / 欧洲 / 北美 / 中东及部分伊斯兰文化地区 / 拉丁美洲 / 其他 |
| `subregion` | string/null | 否 | 如“西欧”“纽约都会区” |
| `instrument` | string[] | 是 | 至少 1 项；用“二胡”“古筝”等标准名 |
| `work` | string | 是 | 曲目或曲目组合；未知写“未知”并说明 |
| `music_type` | string | 是 | 民族器乐 / 民歌 / 戏曲 / 说唱 / 跨文化改编 / 其他 |
| `event_date_text` | string | 是 | 原始时间描述 |
| `event_start_date` | date/null | 否 | 能精确到日才填 |
| `event_end_date` | date/null | 否 | 能精确到日才填 |
| `event_name` | string | 是 | 演出/发布/课程/活动名称 |
| `venue` | string | 是 | 地点；线上写平台 |
| `channel` | string[] | 是 | 网络视频 / 线下音乐会 / 学校教育 / 工作坊 / 媒体 / 节庆 / 教学 / 其他 |
| `target_audience` | string[] | 是 | 可多个 |
| `learning_motivation` | string | 是 | 为什么学/为什么演奏；未知写明 |
| `adaptation` | string | 是 | 改编方式；无改编写“无” |
| `era_theme` | string[] | 是 | 从 10 个主题中选，可多选 |
| `religion_culture` | string | 是 | 只写材料支持的内容；无则“无（材料未提及）” |
| `feedback` | string | 是 | 受众反馈；无则“未采集（未知）” |
| `success_evidence` | string | 是 | 至少 1 项可核验结果 |
| `research_notes` | string | 否 | 研究判断、缺口、争议 |
| `summary` | string | 是 | 120 字以内 |
| `cover_url` | string/null | 否 | 本地 `/media/...` 或 `null` |
| `cultural_hooks` | string[] | 是 | 音色 / 故事 / 意象 / 场景 / 技法 / 影视游戏 等 |
| `origin_city` | enum/null | 否 | 北京 / 上海 / 其他 / null |
| `case_type` | enum | v1.1 起 | `foreign_individual_cross_cultural` / `overseas_institution_ensemble` / `overseas_institution_education` / `cross_cultural_ensemble` |
| `analysis_sample` | enum | v1.1 起 | `strict_individual` / `extended_cross_cultural` / `pending_review` |
| `performer_identity_status` | enum | v1.1 起 | `verified` / `partially_verified` / `unverified` |
| `performance_location` | enum | v1.1 起 | `overseas` / `mainland_china` / `mixed` / `online` / `unknown` |
| `overseas_activity` | boolean | v1.1 起 | 是否存在明确的海外演奏或传播活动 |
| `strict_sample_eligible` | boolean | v1.1 起 | 是否同时满足严格样本五项条件 |
| `owner_approval_status` | enum | v1.1 起 | `pending_owner_review` / `approved` / `rejected` / `needs_more_evidence` / `not_required` |
| `owner_approval_by` | string/null | v1.1 起 | 审批人；未审批为 null |
| `owner_approval_at` | date/null | v1.1 起 | 审批日期；未审批为 null |
| `owner_approval_note` | string | v1.1 起 | 审批意见 |
| `owner_approval_source_ids` | string[] | v1.1 起 | 审批依据来源 |
| `eligibility_reason` | string | v1.1 起 | 纳入/排除理由 |
| `evidence_limitations` | string[] | v1.1 起 | 证据限制，至少 1 项 |
| `review_status` | enum | 是 | A / B / C / D |
| `display_allowed` | boolean | 是 | A/B 才可为 true |
| `source_count` | integer | 是 | 必须等于 `sources.length`，由校验器核对 |
| `source_ids` | string[] | 是 | 必须与 `sources[].source_id` 一致 |
| `sources` | object[] | 是 | 至少 1 条；C/D 可只有 1 条 |
| `updated_at` | date | 是 | 最后更新日期 |

### 5.3.1 双样本规则（v1.1 起）

主研究库保留广义跨文化传播案例；分析时使用两个互斥样本：

- `strict_individual`：外国个人演奏者，实际演奏中国传统音乐/乐器，有明确海外演奏或传播活动，身份、地点、演奏行为均有可核验证据；
- `extended_cross_cultural`：外国个人跨文化实践、海外琴社/教育机构、中西混合编制乐团等广义传播案例；
- `pending_review`：关键条件缺失，暂不进入任一分析样本。

严格样本必须逐例审核，不能仅凭 `performer_type` 自动认定。机构、团体、中国境内活动默认只能进入扩展样本；除非逐项满足严格条件。

### 5.4 来源对象

```json
{
  "source_id": "C001-S001",
  "title": "法国二胡演奏者与中国音乐",
  "publisher": "人民网",
  "url": "https://example.com/article",
  "citation": null,
  "source_type": "主流媒体",
  "published_at": "2021-09-26",
  "accessed_at": "2026-10-25",
  "reliability": "高",
  "is_primary": true,
  "supports": "学习动机、视频传播、教学规模",
  "notes": null
}
```

规则：

- `source_id` 全库唯一，格式 `^C[0-9]{3}-S[0-9]{3}$`。
- `url` 与 `citation` 至少一个非空；`url` 必须是 `http/https`。
- `source_type`：主流媒体 / 机构官网 / 学术论文 / 演奏者本人 / 视频平台 / 演出主办方 / 其他。
- `reliability`：高 / 中 / 低。
- `accessed_at` 必填，平台数据必须带“截至日期”。

---

## 6. `success_factors.json`

### 6.1 顶层

```json
{
  "schema_version": "1.0.0",
  "data_version": "v1.0",
  "indicators": [],
  "scores": []
}
```

### 6.2 指标定义

固定 10 项，顺序不可变：

| `indicator_id` | 中文名 |
|---|---|
| `emotional_resonance` | 情感共通性 |
| `timbre_identity` | 音色辨识度 |
| `story_explainability` | 故事可解释性 |
| `cross_cultural_adaptation` | 跨文化改编程度 |
| `education_support` | 教育支持程度 |
| `bridge_role` | 外国演奏者的文化桥梁作用 |
| `audience_participation` | 受众参与度 |
| `channel_fit` | 传播渠道适配度 |
| `era_theme_relevance` | 时代主题关联度 |
| `sustainability` | 传播持续性 |

每个指标对象：

```json
{
  "indicator_id": "emotional_resonance",
  "label_zh": "情感共通性",
  "order": 1,
  "definition": "作品是否能触发跨语言的情绪共鸣，并有受众层面的证据。",
  "anchors": {
    "0": "无任何受众情感反应证据",
    "1": "仅演奏者或媒体转述",
    "2": "有1—4条受众情感反应原文",
    "3": "≥5条受众原文，且跨语言/国家"
  },
  "evidence_rule": "受众评论原文、采访中的受众引述；媒体形容词不计。"
}
```

### 6.3 评分记录

```json
{
  "case_id": "CASE001",
  "indicator_id": "emotional_resonance",
  "score": 3,
  "evidence": "6条可核验评论中，多条出现‘感动/流泪/共鸣’等明确表述。",
  "source_ids": ["C001-S001", "C001-S003"],
  "missing_reason": null,
  "coder": "编码者A",
  "coded_at": "2026-10-25"
}
```

规则：

- `score` 为 `0/1/2/3` 或 `null`。
- `score != null` 时：`evidence` 非空，`source_ids` 至少 1 个，`missing_reason` 必须为 `null`。
- `score == null` 时：`missing_reason` 必填，`evidence` 写“未知原因”，`source_ids` 可为空。
- 每个案例 10 条记录；缺记录按 `null` 处理，但校验器会报“指标记录缺失”。
- 同一 `case_id + indicator_id` 不得重复。
- 计算字段由后端生成，不写入 JSON：`valid_count`、`missing_count`、`mean_score`、`low_coverage`。

计算口径：

```text
mean_score = sum(非空 score) / valid_count
low_coverage = valid_count < 6
```

若 `valid_count = 0`，`mean_score = null`，不得写 0。

---

## 7. `music_scores.json`

### 7.1 顶层

```json
{
  "schema_version": "1.0.0",
  "data_version": "v1.0",
  "status": "pending",
  "status_label": "待补充",
  "note": "P1 只转换3个案例；20首候选曲目尚未完成8项评分，不生成任何分数。",
  "target_count": 20,
  "score_scale": 100,
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
  "items": []
}
```

权重之和必须为 `1.0`（允许误差 ±0.0001）。前端不得自行改权重。

`status`：`pending / partial / complete`。`pending` 表示尚无真实评分，`items` 必须为空数组；`partial` 表示有部分曲目评分，但未达 20 首；`complete` 表示 20 首均完成。P1 为 `pending`，不得为了填满文件编造曲目或分数。

### 7.2 曲目对象

```json
{
  "music_id": "MUS001",
  "title": "春江花月夜",
  "category": "乐器",
  "subcategory": "古筝",
  "instrument": "古筝",
  "scores": {
    "emotional_resonance": 88,
    "timbre_identity": 82,
    "melody_accessibility": 80,
    "cultural_story": 90,
    "adaptation_space": 78,
    "visual_expressiveness": 72,
    "era_theme_relevance": 85,
    "existing_evidence": 60
  },
  "rationale": "标题与意境可直接转译为自然、月色、江流，旋律线条清楚。",
  "cultural_hooks": ["山水意象", "月色", "古筝音色"],
  "related_case_ids": ["CASE002"],
  "regions": ["欧洲", "北美", "东亚"],
  "themes": ["自然生态与山水审美", "文明交流"],
  "adaptation": "可做古筝与弦乐/电子氛围的对话，保留核心旋律。",
  "risks": "避免只做成‘东方奇观’背景音乐，需解释标题与诗意。",
  "source_ids": ["C001-S001"],
  "review_status": "B"
}
```

规则：

- `scores` 固定 8 个 key，每项 0—100 或 `null`。
- 任一项为 `null`：后端返回 `total_score=null`、`tier="资料不足"`，不排名。
- `total_score`、`tier` 由后端计算，不写死在 JSON。
- `related_case_ids` 必须存在，且默认只用 A/B。
- `themes` 必须来自 10 个主题枚举。
- 20 首候选曲目目标，不代表已有 20 首完成评分。

---

## 8. `regional_strategies.json`

### 8.1 顶层

```json
{
  "schema_version": "1.0.0",
  "data_version": "v1.0",
  "status": "pending",
  "status_label": "待补充",
  "note": "P1 只转换案例；区域—文化—宗教—时代主题矩阵尚未完成研究与审核，不生成推荐行。",
  "regions": [
    "东亚",
    "东南亚",
    "欧洲",
    "北美",
    "中东及部分伊斯兰文化地区",
    "拉丁美洲"
  ],
  "audiences": [
    "音乐学院学生",
    "华裔社群",
    "青年短视频用户",
    "世界音乐爱好者",
    "博物馆与文化机构",
    "综合"
  ],
  "themes": [
    "丝绸之路与文明交流",
    "和平与友谊",
    "自然生态与山水审美",
    "乡愁、迁徙与故乡",
    "非遗保护",
    "青年文化交流",
    "女性艺术表达",
    "城市化与传统记忆",
    "数字技术与传统音乐",
    "心理疗愈与情绪共鸣"
  ],
  "rows": []
}
```

`status`：`pending / partial / complete`。P1 为 `pending`，`rows` 必须为空数组；不得用示例城市/国家组合冒充真实矩阵。

### 8.2 策略行

```json
{
  "strategy_id": "REG-EU-DE-CONS-001",
  "region": "欧洲",
  "subregion": "西欧",
  "country": "德国",
  "audience": "音乐学院学生",
  "language": "Deutsch",
  "cultural_background": "音乐学院以西方古典训练为主，对中国器乐的记谱与音准体系需要解释。",
  "religion_notes": "无特殊宗教禁忌；避免把作品直接包装成宗教音乐。",
  "origin_city": "上海",
  "city_anchor": "江南丝竹与海派城市文化",
  "city_scene": "音乐厅、大学工作坊、城市影像",
  "city_narrative": "从江南水乡到现代都市的声音迁徙。",
  "music_ids": ["MUS001"],
  "themes": ["自然生态与山水审美", "城市化与传统记忆"],
  "match_reason": "该区域音乐学院受众对室内乐与独奏编制接受度高；案例CASE002已证明学院工作坊能形成持续接触；曲目的山水意象可用德文导赏在8分钟内解释。",
  "platforms": ["大学音乐会", "工作坊", "纪录片"],
  "formats": ["60分钟音乐会", "90分钟工作坊", "8分钟短片"],
  "case_ids": ["CASE002"],
  "adaptation": "保留古筝独奏核心段落，加入简短英文/德文导赏。",
  "risks": [
    { "risk": "被误读为背景音乐", "mitigation": "演出前用3分钟解释曲式与意象" }
  ],
  "source_ids": ["C002-S001"],
  "city_source_ids": ["C002-S001"],
  "review_status": "B",
  "display_allowed": true
}
```

规则：

- `strategy_id` 全库唯一。
- `region`、`audience`、`themes` 必须来自枚举。
- `origin_city`：北京 / 上海 / 其他 / `null`；不得用城市替代目标国家。
- `country` 是目标国家，`origin_city` 是作品来源城市，两者分开。
- `match_reason` 必填：必须说明“为什么这个音乐适合这个区域/受众”，并引用 `case_ids` 或 `source_ids`；只写“适合传播”视为无效。
- `religion_notes` 与 `city_*` 没有来源时，`review_status` 不能为 A/B，且不进入正式方案。
- `risks` 必须是对象数组，不能只写一句“注意文化差异”。

---

## 9. 后端派生字段

这些字段不写入 JSON，由 `research_analytics.py` 计算并返回：

### 9.1 数据状态

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

### 9.2 样本充分性

每个统计块必须带：

```json
{
  "sample": {
    "n": 3,
    "status": "insufficient",
    "label": "证据不足：少于5例，仅展示案例事实",
    "thresholds": { "exploratory": 5, "descriptive": 20 }
  }
}
```

状态规则固定：

| n | status | 含义 |
|---|---|---|
| 0 | `empty` | 暂无已审核案例 |
| 1—4 | `insufficient` | 证据不足，只展示案例事实 |
| 5—19 | `exploratory` | 探索性观察，不作普遍性推断 |
| ≥20 | `descriptive` | 描述性统计，仍不作因果推断 |

`target` 来自 manifest 的 `target_case_count`，当前为 40；`progress_percent = n / target × 100`，保留一位小数。

### 9.3 案例编码摘要

```json
{
  "case_id": "CASE001",
  "mean_score": 2.6,
  "valid_count": 10,
  "missing_count": 0,
  "low_coverage": false,
  "review_status": "B",
  "case_ids": ["CASE001"],
  "source_ids": ["C001-S001", "C001-S002", "C001-S003"]
}
```

### 9.4 结论追溯

任何“结论/机制/推荐”对象必须包含：

```json
{
  "text": "在3个案例中，有2个出现‘音色吸引’表述。",
  "case_ids": ["CASE001", "CASE003"],
  "source_ids": ["C001-S001", "C003-S001"],
  "sample": { "n": 3, "status": "insufficient" }
}
```

没有 `case_ids` 的结论不得进入前端“研究结论”区域。

---

## 10. 校验与错误隔离

### 10.1 文件级

以下情况返回 503，页面显示可读错误，不进入统计：

- manifest 无法解析；
- `active_version` 不存在；
- 文件 SHA256 不匹配；
- 顶层 `schema_version/data_version` 不匹配；
- JSON 无法解析；
- 必需文件缺失。

### 10.2 记录级

以下情况隔离单条记录，其他记录继续加载：

- 必填字段缺失；
- 枚举值非法；
- 分数越界；
- 非空分数没有证据/来源；
- ID 重复；
- 引用不存在（`source_ids`、`case_ids`、`music_ids`）；
- `display_allowed=true` 但 `review_status` 为 C/D；
- `source_count` 与 `sources.length` 不一致。

隔离结果：

```json
{
  "quarantined_count": 1,
  "warnings": [
    {
      "file": "success_factors.json",
      "record": "CASE002/timbre_identity",
      "reason": "score=2 但缺少 source_ids"
    }
  ]
}
```

若某文件全部记录被隔离，接口返回空数据 + `warnings`，页面显示“数据校验未通过”，不显示 0 值图表。

### 10.3 启动/首请求校验

- 后端启动时执行一次 manifest 与文件校验，记录结果到日志。
- 首次请求再次按缓存校验；失败不缓存坏数据。
- 提供管理命令 `python manage.py validate_research_data`（P2 已实现），用于提交前检查。

---

## 11. 版本更新与回滚

### 11.1 新增版本

1. 复制 `v1.0/` 为 `v1.1/`。
2. 修改数据。
3. 运行校验。
4. 计算新 SHA256，写入 manifest。
5. 将 `active_version` 改为 `v1.1`。
6. 旧版本保留，不删除。

### 11.2 回滚

1. 将 manifest 的 `active_version` 改回上一个已审核版本。
2. 重启/刷新缓存。
3. 页面数据状态显示旧版本号。
4. 不删除问题版本，便于追查。

### 11.3 发布状态

- `draft`：正在编辑，不进入 API。
- `reviewed`：已审核，可供接口读取。
- `archived`：历史版本，不加载。

---

## 12. 与现有研究 Excel 的字段映射

| 现有列 | JSON 字段 | 处理 |
|---|---|---|
| 案例编号 | `case_id` | 直接映射 |
| 演奏者或机构 | `performer` | 直接映射 |
| 国籍/地区 | `country` | 统一国名 |
| 所属区域 | `region` + `subregion` | “西欧”拆为 `region=欧洲`、`subregion=西欧` |
| 身份类型 | `performer_type` | 映射到枚举 |
| 乐器 | `instrument[]` | 多乐器拆分 |
| 曲目 | `work` | 直接映射 |
| 音乐类型 | `music_type` | 直接映射 |
| 时间 | `event_date_text` + 可选日期 | 不强行补精确日期 |
| 地点 | `venue` | 直接映射 |
| 活动名称 | `event_name` | 直接映射 |
| 传播渠道 | `channel[]` | 拆分 |
| 目标受众 | `target_audience[]` | 拆分 |
| 学习原因 | `learning_motivation` | 直接映射 |
| 改编方式 | `adaptation` | 直接映射 |
| 时代主题 | `era_theme[]` | 映射到 10 主题 |
| 宗教文化背景 | `religion_culture` | 直接映射，保留“无/未知” |
| 受众反馈 | `feedback` | 直接映射 |
| 成功证据 | `success_evidence` | 直接映射 |
| 来源数量 | `source_count` | 校验器重算，不一致报警 |
| 可靠性 | `sources[].reliability` + `review_status` | 来源可靠性与案例等级分开 |
| 审核状态 | `review_status` | 直接映射 |
| 研究备注 | `research_notes` | 直接映射 |

编码总表的 10 项分数与证据列映射到 `success_factors.json` 的长表记录，一列分数 + 一列证据 = 一条记录。

---

## 13. 阶段状态

P0：

- [x] 备份目录与 SHA256 清单已生成。
- [x] `type-check`、`manage.py check` 基线已保存。
- [x] 页面范围、API 范围、数据文件范围已确认。
- [x] 数据结构契约已定义。
- [x] 六项强制约束已写入契约与方案。

P1：

- [x] 按本契约生成 `research/data/v1.0/*.json`。
- [x] 3 个案例、7 条来源、30 条评分转换完成。
- [x] 4 条未知评分保持 `null`，未按 0 分。
- [x] `manifest.json` 版本与 SHA256 校验通过。
- [x] 音乐潜力与区域矩阵标记 `pending / 待补充`，未编造内容。
- [x] 校验报告见 [p1-data-conversion-report.md](p1-data-conversion-report.md)。

P2：

- [x] 实现统一数据加载器、SHA256 校验、缓存和单条数据隔离。
- [x] 7 个只读 API 接入。
- [x] `sample` 状态阈值统一为 `empty / insufficient / exploratory / descriptive`。
- [x] `n<5` 时成功因素返回 `unavailable`，不返回空排行榜。
- [x] `pending` 的音乐潜力与区域矩阵按待补充返回。
- [x] 管理命令 `validate_research_data` 可用。
- [x] 17 个测试通过。
- [x] 报告见 [p2-backend-report.md](p2-backend-report.md)。

P3 尚未开始。
