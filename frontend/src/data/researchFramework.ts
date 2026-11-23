export interface IndicatorGuide {
  id: string
  label: string
  description: string
  anchor: string
}

/** 指标定义来自《指标编码手册 v1.0》，不是案例数据。 */
export const INDICATOR_GUIDE: IndicatorGuide[] = [
  {
    id: 'emotional_resonance',
    label: '情感共通性',
    description: '作品是否能触发跨语言的情绪共鸣（喜悦、乡愁、悲怆、壮阔等），并有受众层面的证据。',
    anchor: '0 无受众证据 · 1 仅转述 · 2 有 1—4 条原文 · 3 ≥5 条原文',
  },
  {
    id: 'timbre_identity',
    label: '音色辨识度',
    description: '乐器音色本身是否被受众或演奏者作为记忆点明确提出。',
    anchor: '0 无描述 · 1 仅演奏者自述 · 2 自述 + 受众证据 · 3 专业评论或多条受众证据',
  },
  {
    id: 'story_explainability',
    label: '故事可解释性',
    description: '案例是否能被讲成一个可跨文化理解的故事（学习动机、文化背景、人物经历）。',
    anchor: '0 只有演出记录 · 1 有背景无动机 · 2 动机可核 · 3 动机、背景、过程完整',
  },
  {
    id: 'cross_cultural_adaptation',
    label: '跨文化改编程度',
    description: '是否对曲目、编制、演奏方式做了跨文化处理。',
    anchor: '0 无改编 · 1 轻微调整 · 2 明显跨文化选择 · 3 系统性重构',
  },
  {
    id: 'education_support',
    label: '教育支持程度',
    description: '是否有稳定的教学、课程、学位项目或工作坊支撑。',
    anchor: '0 无教学 · 1 零散授课 · 2 公开持续教学 · 3 课程/学位/机构化',
  },
  {
    id: 'bridge_role',
    label: '外国演奏者的文化桥梁作用',
    description: '演奏者是否在机构或公共层面承担了连接两种文化的中介角色。',
    anchor: '0 无证据 · 1 仅自我表述 · 2 媒体/机构承认 · 3 长期合作机制',
  },
  {
    id: 'audience_participation',
    label: '受众参与度',
    description: '受众是否从“观看”进入“互动/学习/再创作”。',
    anchor: '0 无互动 · 1 播放/点赞 · 2 评论/现场互动 · 3 翻奏/教学/二创',
  },
  {
    id: 'channel_fit',
    label: '传播渠道适配度',
    description: '所选渠道与该乐器/作品的呈现方式是否匹配。',
    anchor: '0 不匹配 · 1 单一薄弱 · 2 匹配且稳定 · 3 多渠道协同',
  },
  {
    id: 'era_theme_relevance',
    label: '时代主题关联度',
    description: '与和平、文明交流、生态、非遗、青年交流、乡愁、数字文化等主题的关联强度。',
    anchor: '0 无关联 · 1 间接 · 2 明确表述 · 3 核心叙事 + 行动',
  },
  {
    id: 'sustainability',
    label: '传播持续性',
    description: '传播是否跨越单次事件，形成持续输出。',
    anchor: '0 单次 · 1 间隔长 · 2 稳定 1—2 年 · 3 3 年以上或系列化',
  },
]

export interface MusicIndicatorGuide {
  id: string
  label: string
  description: string
}

/** 音乐潜力的 8 项指标名称；权重以 API 返回为准。 */
export const MUSIC_INDICATOR_GUIDE: MusicIndicatorGuide[] = [
  { id: 'emotional_resonance', label: '情感共通性', description: '是否能触发跨语言的情绪共鸣。' },
  { id: 'timbre_identity', label: '音色辨识度', description: '乐器音色是否具有清晰记忆点。' },
  { id: 'melody_accessibility', label: '旋律易接受度', description: '旋律是否容易被非中国听众记住和跟随。' },
  { id: 'cultural_story', label: '文化故事可解释性', description: '能否用简短语言说明曲目背景与意象。' },
  { id: 'adaptation_space', label: '跨文化改编空间', description: '是否适合与当地乐器、编制或风格对话。' },
  { id: 'visual_expressiveness', label: '视觉表现力', description: '演奏形态与舞台/视频画面是否有辨识度。' },
  { id: 'era_theme_relevance', label: '时代主题关联度', description: '能否连接和平、生态、非遗、青年等主题。' },
  { id: 'existing_evidence', label: '已有案例或海外反馈', description: '是否已有可核验的海外演出、评论或传播记录。' },
]

export interface RegionFieldGuide {
  key: string
  label: string
  description: string
}

/** 区域矩阵字段说明；当前 rows=0，不填充具体文化判断。 */
export const REGION_FIELD_GUIDE: RegionFieldGuide[] = [
  { key: 'country', label: '目标国家 / 区域', description: '传播目标地，不等于作品来源城市。' },
  { key: 'audience', label: '目标受众', description: '音乐学院、华裔社群、青年短视频用户等。' },
  { key: 'language', label: '主要语言', description: '输出语言与字幕语言。' },
  { key: 'cultural_background', label: '文化背景', description: '必须带来源，不凭印象概括。' },
  { key: 'religion_notes', label: '宗教与习俗注意', description: '只写有来源支持的具体注意事项。' },
  { key: 'match_reason', label: '适配理由', description: '为什么这首音乐适合这个区域/受众，必须引用案例或来源。' },
  { key: 'themes', label: '时代主题', description: '从 10 个主题中选择，不能强行套用。' },
  { key: 'platforms', label: '平台与形式', description: '平台、活动、教育渠道与内容形式。' },
  { key: 'case_ids', label: '参考案例', description: '来自案例库的 A/B 案例编号。' },
  { key: 'origin_city', label: '作品来源城市', description: '北京 / 上海 / 其他；与目标国家分开。' },
  { key: 'city_narrative', label: '城市文化叙事', description: '城市文化锚点、场景和可复用叙事，必须有来源。' },
  { key: 'risks', label: '风险提示', description: '文化误读、宗教禁忌、平台适配等。' },
]

export interface CityDimensionGuide {
  city: '北京' | '上海'
  label: string
  description: string
}

export const CITY_DIMENSION_GUIDE: CityDimensionGuide[] = [
  {
    city: '北京',
    label: '北京 · 作品来源城市',
    description: '作为 origin_city 的候选值；城市文化锚点、可用场景、叙事与来源均待研究补充。',
  },
  {
    city: '上海',
    label: '上海 · 作品来源城市',
    description: '作为 origin_city 的候选值；城市文化锚点、可用场景、叙事与来源均待研究补充。',
  },
]
