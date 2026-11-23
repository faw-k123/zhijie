# P1 数据转换报告

> 项目：智解国音 · 中国传统音乐国际传播分析与智能决策系统
> 阶段：P1（只做 3 个现有案例的数据转换、manifest 与校验）
> 日期：2026-10-30
> 状态：P1 验收通过；manifest 已从 `draft` 更新为 `reviewed`
> 约束：未修改前端、后端业务代码；未创建数据库表；未修改现有接口；未扩采、未补造案例

---

## 1. 执行摘要

| 项目 | 结果 |
|---|---|
| 转换案例 | 3 个（CASE001—CASE003） |
| 来源记录 | 7 条（C001 三条、C002 两条、C003 两条） |
| 指标评分 | 30 条（3 案例 × 10 项） |
| 已知评分 | 26 条 |
| 未知评分 | 4 条，保持 `null`，未转成 0 |
| 音乐潜力 | `pending / 待补充`，`items=[]`，未编造曲目和分数 |
| 区域矩阵 | `pending / 待补充`，`rows=[]`，未编造区域推荐 |
| 自动校验 | 367 项全部通过，0 失败，0 警告 |
| 代码变更 | 0 个前端/后端业务代码文件 |
| 数据文件 | v1.0 四个文件已设 Windows 只读 |
| manifest | `active_version=v1.0`，`status=reviewed` |

三个案例的有效编码均分：

| 案例 | 有效指标 | 缺失指标 | 有效均分 |
|---|---:|---:|---:|
| CASE001 法国二胡 | 10 | 0 | 2.60 |
| CASE002 美国巴德古筝 | 7 | 3 | 2.29 |
| CASE003 日本二胡群英会 | 9 | 1 | 2.11 |

说明：这 3 个案例仍处于 `insufficient`（n<5）。本报告只确认数据转换正确，不据此得出成功因素排行或国家/区域偏好结论。

---

## 2. 交付物清单

```text
research/data/
├─ README.md
├─ manifest.json
└─ v1.0/
   ├─ cases.json
   ├─ success_factors.json
   ├─ music_scores.json
   └─ regional_strategies.json

docs/
└─ p1-data-conversion-report.md
```

### 2.1 文件大小与 SHA256

| 文件 | 字节 | SHA256 | 只读 |
|---|---:|---|---|
| `v1.0/cases.json` | 13,315 | `07f8f38ac330122f494b9bdff37b13d64cb690d2ce58f9379078fbce1cf07940` | 是 |
| `v1.0/success_factors.json` | 17,968 | `32196e0bfa661b2f5ce43e0d753b9e31cefc3bfc40868014bbc39fb07268b675` | 是 |
| `v1.0/music_scores.json` | 972 | `345e101dd07995b0734e69f591aba3a5275ac01887f10861983614bbcc2a28d6` | 是 |
| `v1.0/regional_strategies.json` | 923 | `20a6bbc84ec65df54bc7dcc43fc1f84dd870347bc2b0765227b0da6882710245` | 是 |
| `manifest.json` | 1,026 | 不写入自身 | 否（需保留版本切换能力） |

manifest 中的四个文件哈希与上表一致；加载前的 SHA256 校验已通过。

---

## 3. 数据概览

### 3.1 案例

| 编号 | 演奏者/机构 | 国家 | 区域 | 乐器 | 证据等级 | 来源数 |
|---|---|---|---|---|---|---:|
| CASE001 | Eliott Tordo（艾略特·托多） | 法国 | 欧洲 / 西欧 | 二胡 | B | 3 |
| CASE002 | 美国巴德学院音乐学院 美中音乐研习院 / Bard Chinese Ensemble | 美国 | 北美 / 纽约 | 古筝 | B | 2 |
| CASE003 | 2026二胡群英会：巫谢慧与 5 名日本青年二胡演奏者 | 日本 | 东亚 / 东京 | 二胡 | B | 2 |

全部 3 个案例 `display_allowed=true`，因为均为 B 级；没有 C/D 级案例进入数据集。

### 3.2 来源

7 条来源均已写入对应案例的 `sources[]`，并带 `source_ids`：

| 来源编号 | 机构 | 类型 | 可靠性 |
|---|---|---|---|
| C001-S001 | 人民网-国际频道 | 主流媒体 | 高 |
| C001-S002 | CGTN | 主流媒体 | 高 |
| C001-S003 | Eliott Tordo YouTube 频道 | 视频平台 | 高 |
| C002-S001 | CGTN | 主流媒体 | 高 |
| C002-S002 | 巴德学院美中音乐研习院官网 | 机构官网 | 高 |
| C003-S001 | 日本中文导报 | 主流媒体 | 中 |
| C003-S002 | 巫谢慧官方网站 | 演奏者本人 | 中 |

### 3.3 指标评分

- 10 项指标定义、0—3 分锚点、证据规则全部来自现有《指标编码手册 v1.0》。
- 30 条评分中，26 条已知、4 条未知。
- 26 条已知评分全部有 `evidence` 和至少 1 个真实 `source_ids`。
- 4 条未知评分全部为 `null`，并写 `missing_reason`：
  - CASE002 情感共通性：无受众评论或情感反应证据。
  - CASE002 音色辨识度：无受众侧描述，不得用研究者判断代替。
  - CASE002 受众参与度：仅知到场 200 余人，无互动或评论证据。
  - CASE003 情感共通性：报道未引述任何观众评论。

### 3.4 待补充文件

| 文件 | 状态 | 数量 | 说明 |
|---|---|---|---|
| `music_scores.json` | `pending / 待补充` | `items=[]` | 20 首候选曲目尚未完成 8 项评分，未生成任何分数 |
| `regional_strategies.json` | `pending / 待补充` | `rows=[]` | 区域—文化—宗教—时代主题矩阵尚未完成研究和审核 |

这两个文件的 8 项权重、分级阈值、6 个区域、6 类受众、10 个主题已写入，但没有任何虚构的曲目、分数或推荐行。

---

## 4. 数据样例

### 4.1 案例样例（CASE001，节选）

```json
{
  "case_id": "CASE001",
  "performer": "Eliott Tordo（艾略特·托多）",
  "performer_type": "外国个人演奏者",
  "country": "法国",
  "region": "欧洲",
  "subregion": "西欧",
  "instrument": ["二胡"],
  "music_type": "民族器乐（跨文化改编）",
  "channel": ["网络视频", "线下音乐会", "教学"],
  "era_theme": ["数字技术与传统音乐", "青年文化交流", "丝绸之路与文明交流"],
  "review_status": "B",
  "display_allowed": true,
  "source_count": 3,
  "source_ids": ["C001-S001", "C001-S002", "C001-S003"],
  "origin_city": null,
  "cover_url": null
}
```

### 4.2 评分样例

```json
{
  "case_id": "CASE001",
  "indicator_id": "emotional_resonance",
  "score": 3,
  "evidence": "6条可核验评论中，多条明确表达感动/流泪（C001-C01）与“语言不同但音乐共通”（C001-C02、C001-C05）；满足≥5条原文。",
  "source_ids": ["C001-S001", "C001-S003"],
  "missing_reason": null,
  "coder": "编码者A",
  "coded_at": "2026-10-25"
}
```

### 4.3 待补充样例

```json
{
  "schema_version": "1.0.0",
  "data_version": "v1.0",
  "status": "pending",
  "status_label": "待补充",
  "note": "P1 只转换3个案例；20首候选曲目尚未完成8项评分，不生成任何分数。",
  "target_count": 20,
  "score_scale": 100,
  "items": []
}
```

---

## 5. 字段映射与标准化

### 5.1 区域拆分

原始表只有“所属区域”：

| 原始值 | `region` | `subregion` |
|---|---|---|
| 西欧 | 欧洲 | 西欧 |
| 北美 | 北美 | 纽约 |
| 东亚 | 东亚 | 东京 |

这样既保留原始区域，又能与目标区域矩阵的 6 大区域对齐。

### 5.2 时代主题

原始主题是短词，统一映射到 10 个标准主题：

| 案例 | 原始表述 | 写入值 |
|---|---|---|
| CASE001 | 数字文化、青年交流、文明交流 | 数字技术与传统音乐、青年文化交流、丝绸之路与文明交流 |
| CASE002 | 文明交流、非遗（古筝）、青年交流、教育 | 丝绸之路与文明交流、非遗保护、青年文化交流 |
| CASE003 | 青年交流、文明交流、数字文化（动漫/摇滚） | 青年文化交流、丝绸之路与文明交流、数字技术与传统音乐 |

“教育”不是 10 个主题之一，CASE002 的教育信息保留在 `learning_motivation`、`success_evidence` 和评分证据中，不硬塞成主题。

### 5.3 传播渠道

原始渠道是自由文本，统一到枚举：

| 案例 | 原始表述 | 写入值 |
|---|---|---|
| CASE001 | 网络视频 + 线下音乐会 + 教学 | 网络视频、线下音乐会、教学 |
| CASE002 | 线下音乐会 + 学术会议 + 学院教育 | 线下音乐会、学校教育、媒体 |
| CASE003 | 线下音乐会 + 媒体报道 + 系列演出 | 线下音乐会、媒体 |

CASE002 的“学术会议”信息保留在 `event_name`（年度中国音乐会议期间）与 `success_evidence`；CASE003 的“系列演出”保留在 `event_name` 与 `success_evidence`（系列演出机制）。没有丢失原始事实。

### 5.4 来源类型

原始“正规媒体采访 / 正规媒体报道 / 视频平台一手数据 / 机构官网 / 演奏者本人渠道”统一为：

- 主流媒体
- 视频平台
- 机构官网
- 演奏者本人

可靠性“高/中”原样保留。

### 5.5 来源数量

`source_count` 不再直接抄原表，而是按实际 `sources.length` 重算并校验：

- CASE001：3
- CASE002：2
- CASE003：2

---

## 6. 转换异常与处理

| # | 异常/差异 | 处理 | 是否丢失原始信息 |
|---|---|---|---|
| 1 | 原始“所属区域”只有西欧/北美/东亚，无法直接对应 6 大区域 | 拆成 `region` + `subregion` | 否，原词保留在 subregion |
| 2 | 主题是短词，不完全匹配 10 个标准主题 | 按语义映射，教育不硬塞 | 否，教育信息保留在动机/证据 |
| 3 | 渠道是自由文本，枚举不覆盖“学术会议/系列演出” | 映射到现有枚举；细节保留在 event_name / success_evidence | 否 |
| 4 | CASE002 目标受众原为“文化爱好者（200余人）” | 把“200余人”视为人数而非受众类型，从 audience 移除 | 否，人数保留在 success_evidence |
| 5 | CASE002 乐器原表含“古筝（主）；学院乐团另有琵琶、二胡、笛子、笙、中阮、箜篌” | `instrument` 保留古筝；其余写入 `research_notes` 的“原表补充” | 否 |
| 6 | C001-S003 只有“约6年前发布”，无精确日期 | `published_at=null`，`notes` 说明 | 否，原描述在 notes |
| 7 | C002-S002 官网未标注发布日期 | `published_at=null`，`notes` 说明 | 否 |
| 8 | CASE001 只有“2016年起学习”等时间描述，无精确日 | `event_start_date/end_date=null`，保留 `event_date_text` | 否 |
| 9 | CASE002 音色辨识度、情感共通性、受众参与度无证据 | `score=null`，写 `missing_reason`，不按 0 分 | 否 |
| 10 | CASE003 情感共通性无观众评论 | `score=null`，写 `missing_reason` | 否 |
| 11 | CASE003 受众参与度 2 分依据是记者描述的现场笑声，不是受众原话 | 保留 2 分与证据原文，未擅自改分；报告标注为弱证据 | 否 |
| 12 | 案例封面尚未复制到后端媒体目录 | `cover_url=null`，不填不存在的路径 | 无原始信息，P4 再处理 |
| 13 | 3 个案例均无“作品来源城市”字段 | `origin_city=null`，不推断北京/上海 | 否 |
| 14 | 20 首音乐评分与区域矩阵尚无研究结果 | 两个文件标记 `pending / 待补充`，数组为空 | 未编造 |

### 6.1 明确未做的事

- 没有把 4 个未知评分补成 0。
- 没有为 20 首曲目编造分数或排名。
- 没有为 6 个区域编造推荐行、宗教注意事项或城市叙事。
- 没有把 B 级案例升级为 A 级。
- 没有把“到场 200 余人”写成“受众正面反馈”。
- 没有把记者描述写成受众原话。

---

## 7. 校验结果

校验脚本按 `docs/data-contract-v1.md` 执行，共 367 项检查：

| 校验类别 | 结果 |
|---|---|
| JSON 解析与 schema_version/data_version | 通过 |
| 3 个案例必填字段、ID 格式、枚举 | 通过 |
| 案例来源数量、来源唯一性、URL、访问日期 | 通过 |
| 10 项指标定义、顺序、0—3 锚点 | 通过 |
| 30 条评分记录、每案例 10 项、无重复 | 通过 |
| 评分范围 0—3 或 null | 通过 |
| 非空评分必须有 evidence + source_ids | 通过 |
| 所有 source_ids 均能对应真实来源 | 通过 |
| 未知评分保持 null 且有 missing_reason | 通过 |
| 有效均分计算 | 通过 |
| 音乐潜力权重合计 1.0、状态 pending、items 为空 | 通过 |
| 区域矩阵 6 区域/6 受众/10 主题、状态 pending、rows 为空 | 通过 |
| manifest 版本、文件大小、SHA256 | 通过 |

另做一项源表逐条比对：

- 原始《案例编码总表》共 30 条评分（3 × 10）。
- JSON 中 30 条评分的 `score` 与 `evidence` 逐条比对，**0 条不一致**。
- 4 条未知评分保持 `null`，未被写成 0。

汇总：

```text
checks=367
pass=367
fail=0
warnings=0
source_score_cross_check=30/30
```

4 条未知评分不是校验失败，而是研究事实；它们已被明确记录并保持 `null`。

---

## 8. 只读与版本

- `research/data/v1.0/` 四个文件已设置 Windows `IsReadOnly=True`。
- `manifest.json` 未设只读，因为需要维护 `active_version` 和版本列表。
- manifest 当前为：

```json
{
  "active_version": "v1.0",
  "target_case_count": 40,
  "versions": [
    {
      "version": "v1.0",
      "status": "reviewed",
      "reviewed_by": "项目负责人",
      "reviewed_at": "2026-10-30"
    }
  ]
}
```

- P1 验收通过后，`v1.0` 的 `status` 已改为 `reviewed`；数据文件本身未修改。
- 如需修正数据，复制为 `v1.1/`，重新计算哈希，切换 `active_version`，不改 `v1.0/`。
- 回滚只切换 `active_version`，不删除版本。

---

## 9. 代码变更情况

对比 P0 备份 `backup/p0_pre_research_20261030_101626/MANIFEST.json`：

| 范围 | 变化 |
|---|---|
| 前端业务代码 | 0 |
| 后端业务代码 | 0 |
| 数据库表 / migration | 0 |
| 现有接口 | 0 |
| 新增研究数据 | 4 个 JSON + manifest |
| 新增文档 | P1 报告、数据契约（P0 已建）、README 更新 |

具体确认：

- 15 个前端/后端代码与配置文件 SHA256 与 P0 备份一致。
- `node_modules`、`.venv`、`media` 未改动。
- 没有启动或修改 SQL Server / Neo4j。
- 没有新增 Django app、model 或 migration。

---

## 10. P1 验收对照

- [x] 3 个案例全部成功转换。
- [x] JSON 结构符合数据契约 v1.0。
- [x] 所有来源编号均能正确关联（7 条来源，30 条评分全部校验）。
- [x] 未知评分没有被转换成 0（4 条保持 null）。
- [x] SHA256 校验通过。
- [x] manifest 版本及文件哈希正确。
- [x] 校验报告记录全部异常及处理情况。
- [x] 前后端业务代码没有变化。
- [x] `music_scores.json` 与 `regional_strategies.json` 明确标记待补充，未编造内容。
- [x] `v1.0/` 创建后只读。

---

## 11. P2 进入条件

P2 只做后端数据层与 API，不写前端页面。进入 P2 前确认：

1. P1 数据验收已通过，manifest 已改为 `reviewed`。
2. 接受 `CASE002` 的 3 个未知评分、`CASE003` 的 1 个未知评分保持 `null`。
3. 接受音乐潜力与区域矩阵当前为空，等研究数据补齐后再写 `v1.1`。
4. 同意 P2 只新增 `research_data.py`、`research_analytics.py` 和 7 个 API，不改现有页面和接口行为。

P1 到此停止，不提前进入 P2。
