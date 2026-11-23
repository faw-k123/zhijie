<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import {
  fetchSongResources,
  fetchSubcategorySongs,
  fetchSongWordcloud,
  fetchSongEmotionPolarity,
} from '@/api/dataDisplay'
import WordcloudChart from '@/components/WordcloudChart.vue'
import * as echarts from 'echarts'
import { analyzeSongEmotion, predictEmotionTrend, analyzeCausalImpact } from '@/api/emotion'
import { fetchSongAiReport } from '@/api/propagation'
import { recordListen } from '@/api/personalization'
import { fetchResearchMusicContext } from '@/api/research'
import type { ResearchMusicContext, ResearchMusicPotentialItem } from '@/types/research'
import ResearchState from '@/components/research/ResearchState.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import { MUSIC_INDICATOR_GUIDE } from '@/data/researchFramework'

interface SongItem {
  id: string
  title: string
}

interface SongResources {
  song_id: string
  title: string
  audio_url?: string
  wordcloud_url?: string
  emotion_polarity_chart_url?: string
  comments?: { id: number; text: string; likes: number }[]
}

interface EmotionAnalysisResult {
  source: string
  category: string
  subcategory: string
  song_id: string
  song_title: string
  labels: string[]
  scores: Record<string, number>
  summary: string
  trend: string
  overall_stats: {
    total_comments: number
    positive_count: number
    negative_count: number
    neutral_count: number
    positive_rate: number
    negative_rate: number
    emotion_index: number
  }
  chart_data: {
    dates: string[]
    emotion_indices: number[]
    positive_rates: number[]
    negative_rates: number[]
    total_counts: number[]
  }
  message: string
}

interface PredictionData {
  date: string
  emotion_index: number
  positive_rate: number
  negative_rate: number
  total_count: number
  is_prediction: boolean
}

interface CausalImpactResult {
  event_date: string
  events: {
    event_date: string
    event_name: string
    event_type: string
    description: string
  }[]
  impact: {
    event_date: string
    pre_period_days: number
    post_period_days: number
    pre_avg_emotion_index: number
    post_avg_emotion_index: number
    emotion_index_change: number
    emotion_index_change_percent: number
    pre_avg_comment_count: number
    post_avg_comment_count: number
    comment_count_change: number
    comment_count_change_percent: number
    significance: string
    interpretation: string
    expected_index: number
    actual_index: number
    point_estimate: number
    credible_interval: number[]
  }
  pre_period_data: { date: string; emotion_index: number; total_count: number }[]
  post_period_data: { date: string; emotion_index: number; total_count: number }[]
}

interface AiReportData {
  source: string
  song_title: string
  report: string
  used_llm: boolean
  summary: string
  trend: string
  scores: Record<string, number>
  overall_stats: EmotionAnalysisResult['overall_stats']
  chart_data: EmotionAnalysisResult['chart_data']
  country_ranking: {
    rank: number
    country: string
    sample_count: number
    positive_rate: number
    negative_rate: number
    emotion_index: number
  }[]
}

const route = useRoute()
const router = useRouter()

const category = computed(() => String(route.params.category || '民歌'))
const subcategory = computed(() => String(route.params.subcategory || ''))

const songs = ref<SongItem[]>([])
const selectedId = ref('')
const resources = ref<SongResources | null>(null)
const uniqueComments = computed(() => {
  const comments = resources.value?.comments || []
  const seen = new Set<string>()
  return comments.filter(c => {
    if (!c.text || seen.has(c.text)) return false
    seen.add(c.text)
    return true
  })
})
const tab = ref<'basic' | 'emotion' | 'overseas'>('basic')
const playing = ref(false)
const audioEl = ref<HTMLAudioElement | null>(null)
const polarityChartRef = ref<HTMLElement | null>(null)

const emotionResult = ref<EmotionAnalysisResult | null>(null)
const emotionLoading = ref(false)
const predictionData = ref<PredictionData[]>([])
const predictionLoading = ref(false)
const causalImpact = ref<CausalImpactResult | null>(null)
const causalLoading = ref(false)

const trendChartRef = ref<HTMLElement | null>(null)
const predictionChartRef = ref<HTMLElement | null>(null)
const causalChartRef = ref<HTMLElement | null>(null)

const reportText = ref('')
const reportLoading = ref(false)
const reportData = ref<AiReportData | null>(null)
const reportTrendChartRef = ref<HTMLElement | null>(null)
let reportTrendChartInstance: echarts.ECharts | null = null

const overseasData = ref<ResearchMusicContext | null>(null)
const overseasLoading = ref(false)
const overseasError = ref('')
const explainabilityCopyState = ref('')
let overseasSeq = 0

const reportSentiments = computed(() => {
  const stats = reportData.value?.overall_stats
  const positive = (stats?.positive_rate || 0) * 100
  const negative = (stats?.negative_rate || 0) * 100
  return [
    { name: '正面情感', value: positive, color: '#58a778' },
    { name: '中性情感', value: Math.max(0, 100 - positive - negative), color: '#e1b653' },
    { name: '负面情感', value: negative, color: '#d86668' },
  ]
})

const reportLines = computed(() =>
  reportText.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => ({
      heading: /^#{1,4}\s+/.test(line),
      text: line.replace(/^#{1,4}\s+/, '').replace(/\*\*/g, ''),
    })),
)

const overseasIndicators = computed(() =>
  MUSIC_INDICATOR_GUIDE.map((item) => ({
    ...item,
    weight: overseasData.value?.weights[item.id] ?? null,
  })),
)
const overseasPotential = computed(() => overseasData.value?.potential ?? null)

type DisplayPotential = ResearchMusicPotentialItem & {
  is_inferred?: boolean
  evidence_note?: string
}

/** 未纳入人工候选评分的歌曲，也按本曲属性生成独立的8项参考，不再展示同一组类别候选曲。 */
const inferredSongPotential = computed<DisplayPotential>(() => {
  const title = currentSong.value?.title || overseasData.value?.music.title || ''
  const profileText = `${title} ${category.value} ${subcategory.value}`
  const hitCount = (keywords: string[]) => keywords.filter((word) => profileText.includes(word)).length
  const nature = hitCount(['山', '水', '江', '河', '湖', '海', '月', '花', '云', '雨', '风', '春', '夏', '秋', '冬', '夜', '雪'])
  const emotion = hitCount(['爱', '情', '思', '念', '梦', '乡', '家', '别', '盼', '怨', '喜', '乐'])
  const narrative = hitCount(['木兰', '昭君', '霸王', '将军', '英雄', '公主', '姑娘', '牧民', '船夫', '姐妹', '儿女'])
  const action = hitCount(['赛', '马', '舞', '歌', '庆', '丰收', '欢', '闹', '鼓', '节'])
  const history = hitCount(['古', '唐', '宋', '汉', '故事', '传说', '乡土', '非遗', '丝路', '家国'])
  const instrument = hitCount(['二胡', '古筝', '古琴', '琵琶', '竹笛', '笛子', '箫', '唢呐', '阮', '扬琴', '南音', '戏曲'])
  const positive = polarityData.value.find((item) => item.name.includes('积极') || item.name.includes('正面'))?.percentage ?? 0
  const wordCount = wordcloudData.value.filter((item) => item.value > 0).length
  const caseCount = overseasRelatedCases.value.length || overseasMatchedCases.value.length
  const sourceCount = overseasDisplayCases.value.reduce((sum, item) => sum + item.source_count, 0)
  const clamp = (value: number) => Math.round(Math.max(0, Math.min(100, value)))
  const isFolk = profileText.includes('民歌')
  const isOpera = ['戏曲', '京剧', '评弹'].some((word) => profileText.includes(word))

  const scores: Record<string, number> = {
    emotional_resonance: clamp(42 + nature * 3 + emotion * 7 + (isFolk ? 9 : 0) + positive * 0.18),
    timbre_identity: clamp(44 + instrument * 11 + (isOpera ? 10 : 0) + Math.min(8, subcategory.value.length * 0.5)),
    melody_accessibility: clamp(48 + action * 4 + emotion * 3 + (isFolk ? 9 : 0) + positive * 0.1),
    cultural_story: clamp(40 + narrative * 12 + history * 7 + nature * 2 + Math.min(12, title.length)),
    adaptation_space: clamp(40 + action * 3 + narrative * 3 + instrument * 4 + Math.min(15, caseCount * 3)),
    visual_expressiveness: clamp(38 + action * 7 + nature * 2 + instrument * 5 + (isOpera ? 14 : 0)),
    era_theme_relevance: clamp(38 + history * 9 + nature * 3 + emotion * 3 + (isFolk ? 6 : 0)),
    existing_evidence: clamp(caseCount * 14 + Math.min(30, sourceCount * 2)),
  }
  const weights = overseasData.value?.weights ?? {}
  const weighted = MUSIC_INDICATOR_GUIDE.map((item) => {
    const configuredWeight = weights[item.id]
    return {
      score: scores[item.id] ?? 0,
      weight: typeof configuredWeight === 'number' ? configuredWeight : 1 / MUSIC_INDICATOR_GUIDE.length,
    }
  })
  const weightTotal = weighted.reduce((sum, item) => sum + item.weight, 0) || 1
  const totalScore = Math.round(weighted.reduce((sum, item) => sum + item.score * item.weight, 0) / weightTotal)

  return {
    status: 'complete',
    music_id: String(currentSong.value?.id || overseasData.value?.music.song_id || ''),
    title,
    scores,
    valid_count: 8,
    missing_indicators: [],
    total_score: totalScore,
    tier: totalScore >= 75 ? '高传播潜力参考' : totalScore >= 60 ? '中高传播潜力参考' : '探索性传播参考',
    rank: null,
    is_inferred: true,
    evidence_note: `已按《${title}》的曲名、${category.value} / ${subcategory.value}属性、${polarityTotal.value} 条情感记录、${wordCount} 个词云词项及 ${caseCount} 个关联/匹配案例单独计算。`,
  }
})

const displayedPotential = computed<DisplayPotential>(() => {
  const published = overseasPotential.value
  return published && published.valid_count > 0 ? published : inferredSongPotential.value
})

const songPropagationSuggestions = computed(() => {
  const title = currentSong.value?.title || overseasData.value?.music.title || ''
  const profileText = `${title} ${category.value} ${subcategory.value}`
  const includesAny = (words: string[]) => words.some((word) => profileText.includes(word))
  const isNature = includesAny(['山', '水', '江', '河', '湖', '海', '月', '花', '云', '雨', '风', '春', '秋', '夜', '雪'])
  const isEmotion = includesAny(['爱', '情', '思', '念', '梦', '乡', '家', '别', '盼', '怨'])
  const isNarrative = includesAny(['木兰', '昭君', '霸王', '将军', '英雄', '公主', '姑娘', '牧民', '船夫'])
  const isCelebratory = includesAny(['赛', '马', '舞', '歌', '庆', '丰收', '欢', '闹', '鼓', '节'])
  const isOpera = includesAny(['戏曲', '京剧', '评弹', '昆曲', '越剧'])
  const isFolk = profileText.includes('民歌')
  const isErhu = profileText.includes('二胡')
  const isZheng = profileText.includes('古筝')
  const isQin = profileText.includes('古琴')

  let theme = `${subcategory.value || category.value}的地域文化与青年交流`
  if (isNarrative) theme = '人物故事、女性/英雄叙事与文明交流'
  else if (isEmotion) theme = '乡愁、亲情与跨语言情绪共鸣'
  else if (isNature) theme = '山水意象、东方审美与生态叙事'
  else if (isCelebratory) theme = '节庆活力、青年互动与舞台共享'
  else if (isOpera) theme = '非遗传承、角色故事与东方舞台美学'

  const caseCountries = [...overseasRelatedCases.value, ...overseasMatchedCases.value]
    .map((item) => item.country)
    .filter(Boolean)
  let profileCountries: string[] = ['德国', '法国', '日本']
  if (isErhu) profileCountries = ['日本', '法国', '墨西哥']
  else if (isZheng) profileCountries = ['德国', '美国', '新西兰']
  else if (isQin) profileCountries = ['英国', '美国', '巴西']
  else if (isFolk || isNarrative) profileCountries = ['阿根廷', '巴西', '德国']
  else if (isOpera) profileCountries = ['英国', '法国', '美国']
  else if (isNature) profileCountries = ['日本', '德国', '新西兰']
  const countries = [...new Set([...caseCountries, ...profileCountries])].slice(0, 3)

  let format = '双语字幕短视频 + 简短曲目导赏'
  if (isNarrative || isOpera) format = '双语故事卡 + 角色/舞台片段 + 演后导赏'
  else if (isFolk) format = '与当地民谣、合唱或社区乐团合作'
  else if (isCelebratory) format = '高节奏短视频 + 节庆现场互动版'
  else if (isErhu || isZheng || isQin) format = '乐器音色特写 + 中西编制对话版'

  const pilot = countries.length
    ? `先在${countries[0]}做一次小规模短视频或现场导赏测试`
    : '先做一次小规模短视频受众反馈测试'

  return { theme, countries, format, pilot }
})
const overseasHasPotentialScore = computed(
  () => typeof displayedPotential.value.total_score === 'number',
)
const overseasHasFactorScores = computed(() => displayedPotential.value.valid_count > 0)
const overseasRelatedCases = computed(() => overseasData.value?.related_cases ?? [])
const overseasMatchedCases = computed(() => overseasData.value?.matched_cases ?? [])
const overseasRegionalRows = computed(() => overseasData.value?.regional_rows ?? [])
const overseasCaseScope = computed<'direct' | 'matched' | 'global'>(() => {
  if (overseasRelatedCases.value.length) return 'direct'
  if (overseasMatchedCases.value.length) return 'matched'
  return 'global'
})
const overseasUsesReferenceRegions = computed(() => overseasRegionalRows.value.length === 0)
const overseasDisplayCases = computed(() =>
  overseasCaseScope.value === 'direct'
    ? overseasRelatedCases.value
    : overseasCaseScope.value === 'matched'
      ? overseasMatchedCases.value
      : overseasData.value?.global_reference.cases ?? [],
)
const overseasDisplayRegions = computed(() =>
  overseasUsesReferenceRegions.value
    ? overseasData.value?.global_reference.regional_rows ?? []
    : overseasRegionalRows.value,
)
const overseasFactorReference = computed(() => {
  const data = overseasData.value
  if (!data) return null
  if (data.factor_reference?.factor_shares?.length) return data.factor_reference
  return null
})
const overseasCategoryReference = computed(() => overseasData.value?.category_reference ?? null)
const overseasCountryCount = computed(
  () => new Set(overseasDisplayRegions.value.map((row) => row.country).filter(Boolean)).size,
)
const overseasSourceCount = computed(() =>
  overseasDisplayCases.value.reduce((sum, item) => sum + item.source_count, 0),
)

const explainabilityReportText = computed(() => {
  if (!overseasData.value) return ''
  const factors = overseasReferenceFactors.value.slice(0, 3)
  const cases = overseasDisplayCases.value
  const caseLines = cases.map((item, index) => {
    const meta = matchedCaseMeta(item.case_id)
    const reasons = meta?.match_reasons?.length
      ? meta.match_reasons.join('；')
      : '同类案例参照'
    return `${index + 1}. ${item.performer}（${item.country}，${item.work || item.instrument.join('、')}）：${reasons}；来源${item.source_count}条。`
  })
  return [
    `《${overseasData.value.music.title}》海外传播可解释性分析报告`,
    '',
    '一、分析对象',
    `曲目类别：${overseasData.value.music.category} / ${overseasData.value.music.subcategory}。案例关联状态：${overseasData.value.association.label}。`,
    '',
    '二、案例选择依据',
    `系统从已审批案例中按曲目、音乐类型、乐器或表演形式、文化主题及接受机制进行匹配，本次展示${cases.length}个案例。`,
    ...caseLines,
    '',
    '三、主要传播因素',
    ...(factors.length
      ? factors.map((item, index) => `${index + 1}. ${item.label}：样本内参考占比${item.share.toFixed(1)}%，有效案例n=${item.n}。`)
      : ['当前缺少可用于本曲解释的因素记录。']),
    '',
    '四、传播建议',
    `建议主题：${songPropagationSuggestions.value.theme}。优先国家：${songPropagationSuggestions.value.countries.join('、')}。呈现形式：${songPropagationSuggestions.value.format}。试点方向：${songPropagationSuggestions.value.pilot}。`,
    '',
    '五、结论边界',
    `以上结论由已审批案例、来源索引和规则匹配共同形成，用于解释案例选择和方案生成，不代表该曲目已经完成海外实测，也不作因果推断。当前参考案例共${cases.length}个、来源${overseasSourceCount.value}条。`,
  ].join('\n')
})

async function copyExplainabilityReport() {
  if (!explainabilityReportText.value) return
  try {
    await navigator.clipboard.writeText(explainabilityReportText.value)
    explainabilityCopyState.value = '报告内容已复制'
  } catch {
    explainabilityCopyState.value = '复制失败，请手动选择报告内容'
  }
  window.setTimeout(() => { explainabilityCopyState.value = '' }, 2200)
}

const mechanismLabels: Record<string, string> = {
  M1: '情绪共鸣', M2: '独特音色', M3: '熟悉性桥梁', M4: '文化叙事',
  M5: '跨文化转译', M6: '演奏者可信度', M7: '视觉与表演性',
  M8: '数字平台适配', M9: '教育与参与转化',
}

function matchedCaseMeta(caseId: string) {
  return overseasMatchedCases.value.find((item) => item.case_id === caseId) ?? null
}

const wordcloudData = ref<{ name: string; value: number }[]>([])
const wordcloudLoading = ref(false)
const designPreview = import.meta.env.DEV && sessionStorage.getItem('guoyin:design-preview') === '1'
const previewWords = [
  { name: '悠远', value: 96 }, { name: '乡愁', value: 88 }, { name: '婉转', value: 82 },
  { name: '山水', value: 78 }, { name: '温柔', value: 74 }, { name: '思念', value: 69 },
  { name: '清雅', value: 64 }, { name: '宁静', value: 61 }, { name: '故乡', value: 58 },
  { name: '月色', value: 54 }, { name: '欢欣', value: 49 }, { name: '辽阔', value: 46 },
  { name: '诗意', value: 43 }, { name: '烟雨', value: 40 }, { name: '共鸣', value: 37 },
  { name: '回望', value: 34 }, { name: '温暖', value: 31 }, { name: '自由', value: 28 },
]

const rightImage = ref('')

function getRandomImage() {
  const allImages: string[] = [
    '/src/assets/images/1.png', '/src/assets/images/2.png', 
    '/src/assets/images/3.png', '/src/assets/images/4.png',
    '/src/assets/images/a.png', '/src/assets/images/b.png', 
    '/src/assets/images/c.png', '/src/assets/images/d.png'
  ]
  const index = Math.floor(Math.random() * allImages.length)
  rightImage.value = allImages[index] || ''
}

const polarityData = ref<{ name: string; value: number; percentage: number }[]>([])
const polarityLoading = ref(false)
const polarityTotal = ref(0)

type FactorReferenceRow = {
  indicator_id: string
  label: string
  mean_score: number
  n: number
  share: number
}

/**
 * 为歌曲库中的每首歌生成一份专属因素参考。
 * 案例编码是参照基线，曲名、类别、乐种、本曲评论与词云是差异化依据。
 * 该结果只是规则推演，不写回案例库，不冒充海外实测。
 */
const songDataFactorReference = computed(() => {
  const hasPolarityEvidence = polarityTotal.value > 0
  const validWords = wordcloudData.value.filter((item) => Number.isFinite(item.value) && item.value > 0)
  const percentageOf = (...labels: string[]) =>
    polarityData.value.find((item) => labels.some((label) => item.name.includes(label)))?.percentage ?? 0
  const positive = percentageOf('积极', '正面')
  const negative = percentageOf('消极', '负面')
  const neutral = percentageOf('中性')
  const wordTotal = validWords.reduce((sum, item) => sum + item.value, 0)
  const topWordShare = wordTotal > 0 ? Math.max(...validWords.map((item) => item.value)) / wordTotal : 0
  const narrativeWords = ['故事', '文化', '历史', '故乡', '乡愁', '记忆', '人物', '山水', '月', '花', '爱', '家国']
  const narrativeHits = validWords.filter((item) => narrativeWords.some((word) => item.name.includes(word))).length
  const factorDefinitions = [
    ['emotional_resonance', '情感共通性'],
    ['timbre_identity', '音色辨识度'],
    ['story_explainability', '故事可解释性'],
    ['cross_cultural_adaptation', '跨文化改编程度'],
    ['education_support', '教育支持程度'],
    ['bridge_role', '外国演奏者的文化桥梁作用'],
    ['audience_participation', '受众参与度'],
    ['channel_fit', '传播渠道适配度'],
    ['era_theme_relevance', '时代主题关联度'],
    ['sustainability', '传播持续性'],
  ] as const
  const values = new Map<string, number>(factorDefinitions.map(([id]) => [id, 12]))
  const bump = (id: string, amount: number) => values.set(id, (values.get(id) || 0) + amount)

  // 先用当前歌曲所关联/匹配案例的有效编码建立参照基线。
  for (const factor of overseasFactorReference.value?.factor_shares ?? []) {
    values.set(factor.indicator_id, 12 + factor.share * 1.8)
  }

  const title = currentSong.value?.title || overseasData.value?.music.title || ''
  const profileText = `${title} ${category.value} ${subcategory.value}`
  const hitCount = (keywords: string[]) => keywords.filter((word) => profileText.includes(word)).length
  const natureHits = hitCount(['山', '水', '江', '河', '湖', '海', '月', '花', '云', '雨', '风', '春', '夏', '秋', '冬', '夜', '雪'])
  const emotionHits = hitCount(['爱', '情', '思', '念', '梦', '乡', '家', '别', '盼', '怨', '喜', '乐'])
  const narrativeTitleHits = hitCount(['木兰', '昭君', '霸王', '将军', '英雄', '公主', '姑娘', '牧民', '船夫', '姐妹', '儿女'])
  const actionHits = hitCount(['赛', '马', '舞', '歌', '庆', '丰收', '欢', '闹', '鼓', '节'])
  const historyHits = hitCount(['古', '唐', '宋', '汉', '故事', '传说', '乡土', '非遗', '丝路', '家国'])
  const instrumentHits = hitCount(['二胡', '古筝', '古琴', '琵琶', '竹笛', '笛子', '箫', '唢呐', '阮', '扬琴', '南音', '戏曲'])

  bump('emotional_resonance', natureHits * 2.8 + emotionHits * 5.2)
  bump('story_explainability', natureHits * 1.8 + narrativeTitleHits * 7 + historyHits * 4 + Math.min(10, title.length * 0.8))
  bump('era_theme_relevance', natureHits * 1.3 + historyHits * 5 + narrativeTitleHits * 3)
  bump('audience_participation', actionHits * 5)
  bump('channel_fit', actionHits * 4 + (/[0-9【】()]/.test(title) ? 5 : 0))
  bump('bridge_role', emotionHits * 2.2 + historyHits * 2)
  bump('timbre_identity', instrumentHits * 8)
  bump('education_support', instrumentHits * 3 + historyHits * 3)
  bump('sustainability', historyHits * 3 + instrumentHits * 2)
  bump('cross_cultural_adaptation', narrativeTitleHits * 2 + actionHits * 1.5)

  if (profileText.includes('民歌')) {
    bump('emotional_resonance', 8); bump('story_explainability', 10); bump('bridge_role', 6); bump('sustainability', 5)
  }
  if (profileText.includes('戏曲') || profileText.includes('京剧') || profileText.includes('评弹')) {
    bump('story_explainability', 12); bump('education_support', 10); bump('era_theme_relevance', 9); bump('sustainability', 8)
  }
  if (hasPolarityEvidence) {
    bump('emotional_resonance', positive * 0.25 + (100 - negative) * 0.08 + (100 - neutral) * 0.04)
    bump('audience_participation', Math.log10(polarityTotal.value + 1) * 12)
    bump('channel_fit', Math.log10(polarityTotal.value + 1) * 8)
  }
  if (validWords.length) {
    bump('story_explainability', Math.min(20, validWords.length * 0.8) + narrativeHits * 3 + topWordShare * 4)
    bump('audience_participation', Math.min(8, validWords.length * 0.25))
  }

  const evidenceCount = polarityTotal.value + validWords.length
  const rows: Omit<FactorReferenceRow, 'share'>[] = factorDefinitions.map(([indicator_id, label]) => ({
    indicator_id,
    label,
    mean_score: values.get(indicator_id) || 1,
    n: evidenceCount,
  }))

  const total = rows.reduce((sum, item) => sum + item.mean_score, 0)
  const factor_shares: FactorReferenceRow[] = rows
    .map((item) => ({
      ...item,
      mean_score: Number(item.mean_score.toFixed(1)),
      share: Number((item.mean_score / total * 100).toFixed(1)),
    }))
    .sort((a, b) => b.share - a.share)

  return {
    scope: 'song_data' as const,
    scope_label: '本曲专属因素参考（规则推演，非海外实测）',
    case_ids: overseasFactorReference.value?.case_ids ?? [],
    factor_shares,
    evidence_note: `已按《${title}》的曲名、${category.value} / ${subcategory.value}曲目属性、${polarityTotal.value} 条情感记录和 ${validWords.length} 个词云词项单独计算${overseasFactorReference.value ? `，并参照案例 ${overseasFactorReference.value.case_ids.join('、')}` : ''}。`,
  }
})

const displayedFactorReference = computed(() => songDataFactorReference.value)
const overseasReferenceFactors = computed(() => displayedFactorReference.value?.factor_shares ?? [])

const danmakuTooltipVisible = ref(false)
const danmakuTooltipText = ref('')
const danmakuTooltipStyle = ref({ left: '0px', top: '0px' })

const currentSong = computed(
  () => songs.value.find((s) => s.id === selectedId.value) || songs.value[0],
)

async function loadSubcategoryBundle() {
  if (!category.value || !subcategory.value) return
  const res = await fetchSubcategorySongs(category.value, subcategory.value)
  const data = res.data as {
    songs?: SongItem[]
    first_song_resources?: SongResources
  }
  songs.value = data?.songs || []
  if (data?.first_song_resources) {
    resources.value = data.first_song_resources
    selectedId.value = data.first_song_resources.song_id
  } else if (songs.value[0]) {
    selectedId.value = songs.value[0].id
    await loadSongResources()
  }
  await loadWordcloud()
  await loadEmotionPolarity()
  getRandomImage()
}

async function loadSongResources() {
  const song = currentSong.value
  if (!song) return
  const res = await fetchSongResources(
    category.value,
    subcategory.value,
    song.id,
    song.title,
  )
  resources.value = (res.data as SongResources) || null
  playing.value = false
  if (audioEl.value) {
    audioEl.value.pause()
    audioEl.value.src = resources.value?.audio_url || ''
  }
}

const songPageRef = ref<HTMLElement | null>(null)
let songPageAnimation: Animation | null = null

async function onSelectSong() {
  songPageAnimation?.cancel()
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    songPageAnimation = songPageRef.value?.animate([
      { transform: 'perspective(1800px) rotateX(0deg) translateY(0)', opacity: 1, filter: 'brightness(1)', offset: 0 },
      { transform: 'perspective(1800px) rotateX(18deg) translateY(-22px)', opacity: 0.15, filter: 'brightness(0.65)', offset: 0.38 },
      { transform: 'perspective(1800px) rotateX(-16deg) translateY(22px)', opacity: 0.2, filter: 'brightness(1.12)', offset: 0.4 },
      { transform: 'perspective(1800px) rotateX(0deg) translateY(0)', opacity: 1, filter: 'brightness(1)', offset: 1 },
    ], { duration: 720, easing: 'cubic-bezier(.22,.65,.25,1)' }) || null
  }
  await loadSongResources()
  await loadWordcloud()
  await loadEmotionPolarity()
  emotionResult.value = null
  predictionData.value = []
  causalImpact.value = null
  reportText.value = ''
  reportData.value = null
  reportTrendChartInstance?.clear()
  overseasData.value = null
  overseasError.value = ''
  if (tab.value === 'emotion') {
    await Promise.all([loadEmotionAnalysis(), loadAiReport()])
  } else if (tab.value === 'overseas') {
    await loadOverseasContext()
  }
}

async function loadWordcloud() {
  const song = currentSong.value
  if (!song) return
  wordcloudLoading.value = true
  try {
    const res = await fetchSongWordcloud(song.id)
    const words = (res.data as { name: string; value: number }[]) || []
    wordcloudData.value = words.length ? words : designPreview ? previewWords : []
  } catch {
    wordcloudData.value = designPreview ? previewWords : []
  } finally {
    wordcloudLoading.value = false
  }
}

async function loadEmotionPolarity() {
  const song = currentSong.value
  if (!song) return
  polarityLoading.value = true
  try {
    const res = await fetchSongEmotionPolarity(song.id)
    const data = res.data as { polarity_data?: { name: string; value: number; percentage: number }[]; total?: number }
    polarityData.value = data?.polarity_data || []
    polarityTotal.value = data?.total || 0
  } catch {
    polarityData.value = [{ name: '中性', value: 1, percentage: 100 }]
    polarityTotal.value = 0
  } finally {
    polarityLoading.value = false
  }
}

async function loadOverseasContext() {
  const song = currentSong.value
  if (!song) return
  const seq = ++overseasSeq
  overseasLoading.value = true
  overseasError.value = ''
  try {
    const response = await fetchResearchMusicContext({
      song_id: song.id,
      title: song.title,
      category: category.value,
      subcategory: subcategory.value,
    })
    if (seq !== overseasSeq) return
    if (!response.data) throw new Error('单曲研究接口未返回有效数据')
    overseasData.value = response.data
  } catch (err) {
    if (seq !== overseasSeq) return
    const error = err as { message?: string }
    overseasData.value = null
    overseasError.value = `海外传播数据加载失败：${error.message || '网络请求失败'}`
  } finally {
    if (seq === overseasSeq) overseasLoading.value = false
  }
}

function overseasIndicatorScore(indicatorId: string) {
  const value = displayedPotential.value.scores[indicatorId]
  return typeof value === 'number' ? value : null
}

function formatWeight(weight: number | null) {
  return weight === null ? '—' : `${Math.round(weight * 100)}%`
}

function formatOverseasScore(score: number | null) {
  return score === null ? '待评分' : `${score} / 100`
}

function relatedCaseTo(caseId: string) {
  return { name: 'global-case-detail', params: { caseId } }
}

function getPolarityColor(name: string): string {
  const colors: Record<string, string> = {
    '积极': '#C57B7B',
    '消极': '#426AE8',
    '中性': '#F4F0E0',
  }
  return colors[name] || '#d9d9d9'
}

let polarityChartInstance: echarts.ECharts | null = null

function renderPolarityChart() {
  if (!polarityChartRef.value) return
  
  if (polarityChartInstance) {
    polarityChartInstance.dispose()
  }
  
  polarityChartInstance = echarts.init(polarityChartRef.value)
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}条 ({d}%)'
    },
    series: [
      {
        name: '情感极性',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        minAngle: 2,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        emphasis: {
          focus: 'none',
          scale: false,
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        },
        data: polarityData.value.map(item => ({
          value: item.value,
          name: item.name,
          itemStyle: { color: getPolarityColor(item.name) }
        }))
      }
    ]
  }
  
  polarityChartInstance.setOption(option)
}

function handleResize() {
  polarityChartInstance?.resize()
  emotionTrendChartInstance?.resize()
  predictionChartInstance?.resize()
  causalChartInstance?.resize()
  reportTrendChartInstance?.resize()
}

function convertAudioUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/media/audio')) return url
  if (url.startsWith('audio/')) {
    const parts = url.split('/').filter(p => p)
    if (parts.length >= 2) {
      return '/media/audio/' + parts.slice(1).map(p => encodeURIComponent(p)).join('/')
    }
  }
  return '/media/audio/' + url.split('/').filter(p => p).map(p => encodeURIComponent(p)).join('/')
}

async function togglePlay() {
  const rawUrl = resources.value?.audio_url
  const url = convertAudioUrl(rawUrl || '')
  const username = localStorage.getItem('username') || ''
  if (url && audioEl.value) {
    if (playing.value) {
      audioEl.value.pause()
      playing.value = false
    } else {
      console.log('Playing audio:', url)
      audioEl.value.src = url
      audioEl.value.load()
      try {
        await audioEl.value.play()
        playing.value = true
        console.log('Audio started playing')
      } catch (error: unknown) {
        const err = error as Error
        console.error('Play failed:', err.name, err.message)
        playing.value = false
      }
      if (username && currentSong.value) {
        recordListen(username, {
          song_id: currentSong.value.id,
          title: currentSong.value.title,
          category: category.value,
          subcategory: subcategory.value,
        }).catch(() => undefined)
      }
    }
  } else {
    console.log('No audio URL:', url)
    playing.value = !playing.value
    if (playing.value && username && currentSong.value) {
      recordListen(username, {
        song_id: currentSong.value.id,
        title: currentSong.value.title,
        category: category.value,
        subcategory: subcategory.value,
      }).catch(() => undefined)
    }
  }
}

function handleAudioError(e: Event) {
  const target = e.target as HTMLAudioElement
  console.error('Audio error:', target.error?.code, target.error?.message)
  playing.value = false
}

function getDanmakuStyle(text: string, index: number) {
  const tracks = 6
  const track = index % tracks
  const charWidth = 9.5
  const paddingWidth = 28
  const estimatedWidth = Math.min(text.length * charWidth + paddingWidth, 350)
  const containerWidth = 800
  const totalDistance = containerWidth + estimatedWidth
  const speed = 75
  const duration = totalDistance / speed
  const gap = 50
  const gapTime = gap / speed
  
  const comments = uniqueComments.value
  let trackDelay = 0
  for (let i = track; i < index; i += tracks) {
    const prevText = comments[i]?.text || ''
    const prevWidth = Math.min(prevText.length * charWidth + paddingWidth, 350)
    const prevDuration = (containerWidth + prevWidth) / speed
    trackDelay += prevDuration + gapTime
  }
  
  return {
    top: `${6 + track * 15}%`,
    animationDelay: `${trackDelay}s`,
    animationDuration: `${duration}s`,
  }
}

function onDanmakuEnter(e: MouseEvent, text: string) {
  const target = e.target as HTMLElement
  target.style.animationPlayState = 'paused'
  target.style.zIndex = '10'
  
  danmakuTooltipText.value = text
  danmakuTooltipVisible.value = true
  updateTooltipPosition(e)
}

function onDanmakuMove(e: MouseEvent) {
  updateTooltipPosition(e)
}

function onDanmakuLeave(e: MouseEvent) {
  const target = e.target as HTMLElement
  target.style.animationPlayState = 'running'
  target.style.zIndex = '1'
  
  danmakuTooltipVisible.value = false
}

function updateTooltipPosition(e: MouseEvent) {
  danmakuTooltipStyle.value = {
    left: `${e.clientX + 15}px`,
    top: `${e.clientY - 10}px`,
  }
}

function handleAudioLoaded(e: Event) {
  console.log('Audio loaded:', (e.target as HTMLAudioElement).duration, 'seconds')
}

async function loadEmotionAnalysis() {
  const song = currentSong.value
  if (!song) return
  emotionLoading.value = true
  try {
    const res = await analyzeSongEmotion({
      category: category.value,
      subcategory: subcategory.value,
      song_id: song.id,
      song_title: song.title,
    })
    emotionResult.value = res.data as EmotionAnalysisResult
    
    emotionLoading.value = false
    await nextTick()
    
    await loadPrediction()
    await loadCausalImpact()
    
    await nextTick()
    renderEmotionCharts()
    if (predictionData.value.length) renderPredictionChart()
    if (causalImpact.value?.impact) renderCausalChart()
  } catch (e: unknown) {
    const err = e as { message?: string }
    emotionResult.value = {
      source: 'error',
      category: category.value,
      subcategory: subcategory.value,
      song_id: song.id,
      song_title: song.title,
      labels: [],
      scores: {},
      summary: '',
      trend: '',
      overall_stats: {
        total_comments: 0,
        positive_count: 0,
        negative_count: 0,
        neutral_count: 0,
        positive_rate: 0,
        negative_rate: 0,
        emotion_index: 0,
      },
      chart_data: {
        dates: [],
        emotion_indices: [],
        positive_rates: [],
        negative_rates: [],
        total_counts: [],
      },
      message: err.message || '请求失败',
    }
    emotionLoading.value = false
  }
}

async function loadPrediction() {
  const song = currentSong.value
  if (!song) return
  predictionLoading.value = true
  try {
    const res = await predictEmotionTrend({ song_id: song.id, days: 7 })
    predictionData.value = res.data as PredictionData[]
    await nextTick()
    renderPredictionChart()
  } catch {
    predictionData.value = []
  } finally {
    predictionLoading.value = false
  }
}

async function loadCausalImpact() {
  const song = currentSong.value
  if (!song) return
  causalLoading.value = true
  try {
    const res = await analyzeCausalImpact({ song_id: song.id })
    causalImpact.value = res.data as CausalImpactResult
    await nextTick()
    renderCausalChart()
  } catch {
    causalImpact.value = null
  } finally {
    causalLoading.value = false
  }
}

async function selectEvent(eventDate: string) {
  const song = currentSong.value
  if (!song) return
  causalLoading.value = true
  try {
    const res = await analyzeCausalImpact({ song_id: song.id, event_date: eventDate })
    causalImpact.value = res.data as CausalImpactResult
    await nextTick()
    renderCausalChart()
  } catch {
    causalImpact.value = null
  } finally {
    causalLoading.value = false
  }
}

let emotionTrendChartInstance: echarts.ECharts | null = null
let predictionChartInstance: echarts.ECharts | null = null
let causalChartInstance: echarts.ECharts | null = null

function renderEmotionCharts() {
  if (!emotionResult.value) return
  
  if (trendChartRef.value) {
    if (emotionTrendChartInstance) emotionTrendChartInstance.dispose()
    emotionTrendChartInstance = echarts.init(trendChartRef.value)
    
    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const p = params as Array<{ axisValue: string; seriesName: string; value: number }>
          if (!p || !p.length || !p[0]) return ''
          let html = `<div style="font-weight:bold;margin-bottom:8px;">${p[0].axisValue}</div>`
          p.forEach(item => {
            if (item) {
              html += `<div>${item.seriesName}: ${(item.value as number).toFixed(3)}</div>`
            }
          })
          return html
        }
      },
      legend: {
        data: ['情感指数', '积极率', '消极率'],
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: emotionResult.value.chart_data.dates,
        axisLabel: {
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        min: -0.5,
        max: 1
      },
      series: [
        {
          name: '情感指数',
          type: 'line',
          smooth: true,
          data: emotionResult.value.chart_data.emotion_indices,
          lineStyle: { color: '#801d3a', width: 3 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(128, 29, 58, 0.3)' },
              { offset: 1, color: 'rgba(128, 29, 58, 0.05)' }
            ])
          }
        },
        {
          name: '积极率',
          type: 'line',
          smooth: true,
          data: emotionResult.value.chart_data.positive_rates,
          lineStyle: { color: '#52c41a', width: 3 }
        },
        {
          name: '消极率',
          type: 'line',
          smooth: true,
          data: emotionResult.value.chart_data.negative_rates,
          lineStyle: { color: '#ff4d4f', width: 3 }
        }
      ]
    }
    emotionTrendChartInstance.setOption(option)
  }
}

function renderPredictionChart() {
  if (!predictionData.value.length || !emotionResult.value) return
  
  if (!predictionChartRef.value) return
  
  if (predictionChartInstance) predictionChartInstance.dispose()
  predictionChartInstance = echarts.init(predictionChartRef.value)
  
  const recentHistoryDays = 14
  const historyDates = emotionResult.value.chart_data.dates.slice(-recentHistoryDays)
  const historyIndices = emotionResult.value.chart_data.emotion_indices.slice(-recentHistoryDays)
  const historyPositive = emotionResult.value.chart_data.positive_rates.slice(-recentHistoryDays)
  const historyNegative = emotionResult.value.chart_data.negative_rates.slice(-recentHistoryDays)
  
  const allDates = [...historyDates, ...predictionData.value.map(d => d.date)]
  const historyPlusPrediction = [
    ...historyIndices,
    ...predictionData.value.map(d => d.emotion_index)
  ]
  const positiveRates = [
    ...historyPositive,
    ...predictionData.value.map(d => d.positive_rate)
  ]
  const negativeRates = [
    ...historyNegative,
    ...predictionData.value.map(d => d.negative_rate)
  ]
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
          const p = params as Array<{ axisValue: string; seriesName: string; value: number }>
          if (!p || !p.length || !p[0]) return ''
          const dateIdx = allDates.indexOf(p[0].axisValue)
          const isPrediction = dateIdx >= recentHistoryDays
          let html = `<div style="font-weight:bold;margin-bottom:8px;">${p[0].axisValue}${isPrediction ? ' (预测)' : ''}</div>`
          p.forEach(item => {
            if (item) {
              html += `<div>${item.seriesName}: ${(item.value as number).toFixed(3)}</div>`
            }
        })
        return html
      }
    },
    legend: {
      data: ['情感指数(历史)', '情感指数(预测)', '积极率', '消极率'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: {
        rotate: 45,
        fontSize: 10
      },
      splitLine: {
        lineStyle: {
          type: 'solid' as const,
          color: '#eee'
        }
      }
    },
    yAxis: {
      type: 'value',
      min: -0.5,
      max: 1
    },
    series: [
      {
        name: '情感指数(历史)',
        type: 'line',
        smooth: true,
        data: historyPlusPrediction.map((val, idx) => idx >= recentHistoryDays ? null : val),
        lineStyle: { color: '#801d3a', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(128, 29, 58, 0.2)' },
            { offset: 1, color: 'rgba(128, 29, 58, 0.02)' }
          ])
        }
      },
      {
        name: '情感指数(预测)',
        type: 'line',
        smooth: true,
        data: historyPlusPrediction.map((val, idx) => idx < recentHistoryDays ? null : val),
        lineStyle: { color: '#29509b', width: 2, type: 'dashed' },
        itemStyle: { color: '#29509b' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(41, 80, 155, 0.2)' },
            { offset: 1, color: 'rgba(41, 80, 155, 0.02)' }
          ])
        }
      },
      {
        name: '积极率',
        type: 'line',
        smooth: true,
        data: positiveRates,
        lineStyle: { color: '#52c41a', width: 2, type: 'dotted' }
      },
      {
        name: '消极率',
        type: 'line',
        smooth: true,
        data: negativeRates,
        lineStyle: { color: '#ff4d4f', width: 2, type: 'dotted' }
      }
    ],
    markLine: {
      symbol: 'none',
      lineStyle: { color: '#ff4d4f', width: 2, type: 'dashed' },
      data: [{ xAxis: recentHistoryDays - 1, label: { formatter: '预测开始', position: 'end' } }]
    }
  }
  predictionChartInstance.setOption(option)
}

function renderCausalChart() {
  if (!causalImpact.value?.impact) return
  
  if (!causalChartRef.value) return
  
  if (causalChartInstance) causalChartInstance.dispose()
  causalChartInstance = echarts.init(causalChartRef.value)
  
  const preData = causalImpact.value.pre_period_data
  const postData = causalImpact.value.post_period_data
  const allData = [...preData, ...postData]
  
  const eventIdx = preData.length
  const eventDate = causalImpact.value.event_date
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
          const p = params as Array<{ axisValue: string; seriesName: string; value: number }>
          if (!p || !p.length || !p[0]) return ''
          let html = `<div style="font-weight:bold;margin-bottom:8px;">${p[0].axisValue}</div>`
          p.forEach(item => {
            if (item) {
              html += `<div>${item.seriesName}: ${(item.value as number).toFixed(3)}</div>`
            }
          })
        return html
      }
    },
    legend: {
      data: ['实际情感指数', '预测(无干预)', '评论数'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: allData.map(d => d.date),
      axisLabel: {
        rotate: 45,
        fontSize: 10
      },
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '情感指数',
        min: -0.5,
        max: 1,
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '评论数',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '实际情感指数',
        type: 'line',
        smooth: true,
        data: allData.map(d => d.emotion_index),
        lineStyle: { color: '#801d3a', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(128, 29, 58, 0.2)' },
            { offset: 1, color: 'rgba(128, 29, 58, 0.02)' }
          ])
        }
      },
      {
        name: '预测(无干预)',
        type: 'line',
        smooth: true,
        data: [...preData.map(d => d.emotion_index), ...postData.map(() => causalImpact.value!.impact.expected_index)],
        lineStyle: { color: '#999', width: 2, type: 'dashed' }
      },
      {
        name: '评论数',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: allData.map(d => d.total_count),
        lineStyle: { color: '#29509b', width: 2 }
      }
    ],
    markLine: {
      symbol: 'none',
      lineStyle: { color: '#ff4d4f', width: 2, type: 'dashed' },
      data: [{ xAxis: eventIdx, label: { formatter: `事件: ${eventDate}`, position: 'end' } }]
    }
  }
  causalChartInstance.setOption(option)
}

async function loadAiReport() {
  const song = currentSong.value
  if (!song) return
  reportLoading.value = true
  try {
    const res = await fetchSongAiReport({
      category: category.value,
      subcategory: subcategory.value,
      song_id: song.id,
      song_title: song.title,
    })
    const data = res.data as AiReportData
    reportData.value = data
    reportText.value = data?.report || JSON.stringify(res.data)
  } catch (e: unknown) {
    const err = e as { message?: string }
    reportText.value = `请求失败：${err.message || '网络错误'}`
  } finally {
    reportLoading.value = false
    await nextTick()
    if (reportData.value) renderReportTrendChart()
  }
}

function renderReportTrendChart() {
  if (!reportTrendChartRef.value || !reportData.value) return
  if (!reportTrendChartInstance) {
    reportTrendChartInstance = echarts.init(reportTrendChartRef.value)
  }
  const chartData = reportData.value.chart_data
  reportTrendChartInstance.setOption({
    animationDuration: 700,
    grid: { left: 42, right: 20, top: 24, bottom: 32 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: chartData.dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#65736f' } },
      axisLabel: { color: '#76847f', hideOverlap: true },
    },
    yAxis: {
      type: 'value',
      min: -1,
      max: 1,
      axisLabel: { color: '#76847f' },
      splitLine: { lineStyle: { color: 'rgba(82, 103, 96, 0.12)' } },
    },
    series: [
      {
        name: '情感指数',
        type: 'line',
        data: chartData.emotion_indices,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#4d8074', width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(77, 128, 116, 0.34)' },
            { offset: 1, color: 'rgba(77, 128, 116, 0.02)' },
          ]),
        },
      },
    ],
  }, true)
}

watch(tab, (t) => {
  if (t === 'emotion' && !emotionResult.value) loadEmotionAnalysis()
  if (t === 'emotion' && !reportData.value) loadAiReport()
  if (t === 'overseas' && !overseasData.value) loadOverseasContext()
})

watch(currentSong, () => {
  overseasData.value = null
  overseasError.value = ''
  if (tab.value === 'overseas') loadOverseasContext()
})

watch(
  () => [category.value, subcategory.value] as const,
  () => {
    tab.value = 'basic'
    emotionResult.value = null
    predictionData.value = []
    causalImpact.value = null
    reportText.value = ''
    reportData.value = null
    reportTrendChartInstance?.clear()
    overseasData.value = null
    overseasError.value = ''
    loadSubcategoryBundle()
  },
)

watch(polarityData, async () => {
  await nextTick()
  renderPolarityChart()
}, { deep: true })

function goBack() {
  router.push({ name: 'emotion', query: { category: category.value } })
}

onMounted(() => {
  loadSubcategoryBundle()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  polarityChartInstance?.dispose()
  emotionTrendChartInstance?.dispose()
  predictionChartInstance?.dispose()
  causalChartInstance?.dispose()
  reportTrendChartInstance?.dispose()
})
</script>

<template>
  <div class="detail-page">
    <AppNav />
    <audio ref="audioEl" preload="none" @ended="playing = false" @error="handleAudioError" @loadedmetadata="handleAudioLoaded" />
    <header class="top">
      <button type="button" class="back" @click="goBack">← 返回</button>
      <h1>{{ category }} / {{ subcategory }}</h1>
    </header>

    <main class="content">
      <section v-if="tab === 'basic'" class="basic">
        <div class="select-row">
          <label>
            选择曲目
            <select v-model="selectedId" @change="onSelectSong">
              <option v-for="item in songs" :key="item.id" :value="item.id">
                {{ item.title }}
              </option>
            </select>
          </label>
        </div>

        <div ref="songPageRef" class="layout song-flip-page">
          <div class="top-row">
            <div class="poster-section">
              <div class="poster">
                <div class="poster-placeholder">
                  <span class="poster-title">{{ currentSong?.title || '歌曲海报' }}</span>
                </div>
                <button type="button" class="poster-play" @click="togglePlay">
                  <span>{{ playing ? '⏸' : '▶' }}</span>
                </button>
              </div>
            </div>

            <div class="emotion-section">
              <div v-if="polarityLoading" class="emotion-placeholder">
                <span>情感极性图</span>
                <span class="placeholder-hint">数据加载中...</span>
              </div>
              <div v-else class="polarity-chart-wrapper">
                <div ref="polarityChartRef" class="polarity-chart"></div>
                <div class="polarity-legend">
                  <div v-for="item in polarityData" :key="item.name" class="legend-item">
                    <span class="legend-color" :style="{ background: getPolarityColor(item.name) }"></span>
                    <span class="legend-text">{{ item.name }}</span>
                    <span class="legend-value">{{ item.percentage }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="danmaku-section">
              <div
                v-for="(c, i) in uniqueComments"
                :key="c.id"
                class="danmaku-item"
                :style="getDanmakuStyle(c.text, i)"
                @mouseenter="onDanmakuEnter($event, c.text)"
                @mousemove="onDanmakuMove($event)"
                @mouseleave="onDanmakuLeave($event)"
              >
                {{ c.text }}
              </div>
              <div v-if="!(resources?.comments || []).length" class="danmaku-placeholder">
                <span>评论弹幕区</span>
                <span class="placeholder-hint">暂无评论</span>
              </div>
              <div v-if="danmakuTooltipVisible" class="danmaku-tooltip" :style="danmakuTooltipStyle">
                {{ danmakuTooltipText }}
              </div>
            </div>
          </div>

          <div class="wordcloud-section">
            <div class="wordcloud-left">
              <div v-if="wordcloudLoading" class="wordcloud-loading">加载中...</div>
              <WordcloudChart
                v-else-if="wordcloudData.length > 0 || designPreview"
                :words="wordcloudData.length ? wordcloudData : previewWords"
              />
              <div v-else class="wordcloud-placeholder">
                <span>词云图</span>
                <span class="placeholder-hint">数据加载中...</span>
              </div>
            </div>
            <div class="wordcloud-right">
              <img :src="rightImage" alt="" />
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="tab === 'emotion'" class="emotion-analysis-page">
        <div v-if="emotionLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <p>正在分析情感数据...</p>
        </div>

        <div v-else-if="emotionResult" class="emotion-content">
          <div class="emotion-header">
            <h2>{{ emotionResult.song_title }} - 情感分析报告</h2>
            <p class="emotion-summary">{{ emotionResult.summary }}</p>
          </div>

          <div class="emotion-stats">
            <div class="stat-card">
              <div class="stat-value" :class="emotionResult.overall_stats.emotion_index > 0.2 ? 'positive' : emotionResult.overall_stats.emotion_index < -0.1 ? 'negative' : 'neutral'">
                {{ emotionResult.overall_stats.emotion_index.toFixed(2) }}
              </div>
              <div class="stat-label">情感指数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ emotionResult.overall_stats.total_comments }}</div>
              <div class="stat-label">评论总数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value positive">{{ (emotionResult.overall_stats.positive_rate * 100).toFixed(1) }}%</div>
              <div class="stat-label">积极率</div>
            </div>
            <div class="stat-card">
              <div class="stat-value negative">{{ (emotionResult.overall_stats.negative_rate * 100).toFixed(1) }}%</div>
              <div class="stat-label">消极率</div>
            </div>
            <div class="stat-card">
              <div class="stat-value" :class="emotionResult.trend === '上升' ? 'positive' : emotionResult.trend === '下降' ? 'negative' : 'neutral'">
                {{ emotionResult.trend }}
              </div>
              <div class="stat-label">近期趋势</div>
            </div>
          </div>

          <div class="chart-card full-width">
            <h3>📈 情感走势分析</h3>
            <p class="chart-desc">过去60天的情感指数、积极率、消极率变化趋势</p>
            <div ref="trendChartRef" class="emotion-trend-chart"></div>
          </div>

          <div class="chart-card full-width">
            <h3>🔮 未来7天预测</h3>
            <p class="chart-desc">基于历史数据预测未来情感走势（虚线表示预测，实线表示历史）</p>
            <div v-if="predictionLoading" class="chart-loading">加载中...</div>
            <div v-else ref="predictionChartRef" class="prediction-chart"></div>
          </div>

          <div class="chart-card full-width">
            <h3>🎯 传播事件影响分析（因果推理）</h3>
            <p class="chart-desc">分析特定事件对歌曲情感的真实影响，对比事件前后差异</p>
            <div v-if="causalLoading" class="chart-loading">加载中...</div>
            <div v-else-if="causalImpact?.impact" class="causal-container">
              <div class="events-list" v-if="causalImpact.events.length > 0">
                <h4>传播事件记录</h4>
                <div class="events-grid">
                  <div v-for="(event, idx) in causalImpact.events" :key="idx" class="event-item" :class="{ active: event.event_date === causalImpact.event_date }" @click="selectEvent(event.event_date)">
                    <div class="event-date">{{ event.event_date }}</div>
                    <div class="event-name">{{ event.event_name }}</div>
                    <div class="event-type">{{ event.event_type }}</div>
                    <div class="event-desc">{{ event.description }}</div>
                  </div>
                </div>
              </div>
              <div class="causal-summary">
                <div class="causal-stat">
                  <span class="causal-label">分析事件</span>
                  <span class="causal-value highlight">{{ causalImpact.event_date }}</span>
                </div>
                <div class="causal-stat">
                  <span class="causal-label">宣传前情感指数</span>
                  <span class="causal-value">{{ causalImpact.impact.pre_avg_emotion_index.toFixed(3) }}</span>
                </div>
                <div class="causal-stat">
                  <span class="causal-label">宣传后情感指数</span>
                  <span class="causal-value">{{ causalImpact.impact.post_avg_emotion_index.toFixed(3) }}</span>
                </div>
                <div class="causal-stat">
                  <span class="causal-label">情感指数变化</span>
                  <span class="causal-value" :class="causalImpact.impact.emotion_index_change > 0 ? 'positive' : 'negative'">
                    {{ causalImpact.impact.emotion_index_change > 0 ? '+' : '' }}{{ causalImpact.impact.emotion_index_change.toFixed(3) }}
                    ({{ causalImpact.impact.emotion_index_change_percent > 0 ? '+' : '' }}{{ causalImpact.impact.emotion_index_change_percent.toFixed(1) }}%)
                  </span>
                </div>
                <div class="causal-stat">
                  <span class="causal-label">显著性</span>
                  <span class="causal-value" :class="causalImpact.impact.significance === '显著' ? 'positive' : 'neutral'">
                    {{ causalImpact.impact.significance }}
                  </span>
                </div>
                <div class="causal-stat">
                  <span class="causal-label">影响方向</span>
                  <span class="causal-value" :class="causalImpact.impact.interpretation === '积极影响' ? 'positive' : causalImpact.impact.interpretation === '消极影响' ? 'negative' : 'neutral'">
                    {{ causalImpact.impact.interpretation }}
                  </span>
                </div>
              </div>
              <div ref="causalChartRef" class="causal-chart"></div>
            </div>
            <div v-else class="chart-empty">
              数据不足，无法进行因果分析
            </div>
          </div>

          <div class="explanation-card">
            <h3>分析解读</h3>
            <div class="explanation-content">
              <div class="exp-item">
                <span class="exp-icon">📊</span>
                <span class="exp-text">当前情感指数为 <strong>{{ emotionResult.overall_stats.emotion_index.toFixed(2) }}</strong>，表明歌曲评论整体偏向{{ emotionResult.labels[0] || '中性' }}。</span>
              </div>
              <div class="exp-item">
                <span class="exp-icon">📈</span>
                <span class="exp-text">近期趋势{{ emotionResult.trend }}，说明{{ emotionResult.trend === '上升' ? '用户关注度和正面评价正在提升' : emotionResult.trend === '下降' ? '需要关注负面评价并采取改进措施' : '情感表现稳定' }}。</span>
              </div>
              <div v-if="causalImpact?.impact" class="exp-item">
                <span class="exp-icon">🎯</span>
                <span class="exp-text">{{ causalImpact.impact.interpretation }}：事件后情感指数{{ causalImpact.impact.emotion_index_change > 0 ? '上升' : '下降' }}{{ Math.abs(causalImpact.impact.emotion_index_change).toFixed(2) }}，{{ causalImpact.impact.significance === '显著' ? '影响显著' : '影响一般' }}。</span>
              </div>
            </div>
          </div>

          <section class="emotion-international-summary">
            <header>
              <div>
                <span>OVERSEAS SENTIMENT</span>
                <h3>海外情感与行动建议</h3>
              </div>
              <small>原国际传播分析仅保留04和05，并入情感分析</small>
            </header>

            <div v-if="reportLoading" class="chart-loading">正在读取海外情感数据...</div>
            <div v-else-if="reportData" class="emotion-international-grid">
              <article class="report-panel country-ranking">
                <div class="report-panel-heading">
                  <span>04</span>
                  <div><h3>国家情感排名</h3><p>海外国家和地区的受众情感对比</p></div>
                </div>
                <div v-if="reportData.country_ranking?.length" class="country-ranking-list">
                  <div class="ranking-labels" aria-hidden="true">
                    <span>排名 / 国家</span><span>情感指数</span><span>正面率</span><span>样本</span>
                  </div>
                  <article v-for="item in reportData.country_ranking" :key="item.country" class="country-ranking-row">
                    <div class="country-name"><b>{{ String(item.rank).padStart(2, '0') }}</b><span>{{ item.country }}</span></div>
                    <strong :class="item.emotion_index >= 0 ? 'positive' : 'negative'">
                      {{ item.emotion_index > 0 ? '+' : '' }}{{ item.emotion_index.toFixed(2) }}
                    </strong>
                    <div class="country-positive"><span>{{ (item.positive_rate * 100).toFixed(1) }}%</span><i><em :style="{ width: `${item.positive_rate * 100}%` }"></em></i></div>
                    <small>{{ item.sample_count.toLocaleString() }}</small>
                  </article>
                  <p class="ranking-note">仅统计带有国别信息的海外有效评论，中国数据不参与排名。</p>
                </div>
                <div v-else class="ranking-empty">
                  <strong>暂无可用的国家情感排名</strong>
                  <p>当前曲目尚未采集到带有国别信息的海外评论，不使用推测值补齐。</p>
                </div>
              </article>

              <article class="report-panel report-actions">
                <div class="report-panel-heading">
                  <span>05</span>
                  <div><h3>国际传播行动建议</h3><p>围绕海外理解与参与优化</p></div>
                </div>
                <div class="action-list">
                  <div><b>01</b><span><strong>多语种内容</strong><small>补充歌词、文化背景和意象译析</small></span></div>
                  <div><b>02</b><span><strong>受众分层</strong><small>结合国别情感数据制定差异化内容</small></span></div>
                  <div><b>03</b><span><strong>持续监测</strong><small>跟踪负面波动和传播节点后的变化</small></span></div>
                </div>
              </article>
            </div>
            <div v-else class="ranking-empty"><strong>暂无海外情感报告</strong><p>请补充带有国家信息的受众反馈后再生成。</p></div>
          </section>
        </div>

        <div v-else class="emotion-empty">
          <p>暂无情感分析数据</p>
        </div>
      </section>

            <section v-else-if="tab === 'overseas'" class="overseas-page">
        <div v-if="overseasLoading" class="overseas-loading">
          <div class="loading-spinner"></div>
          <p>正在读取这首歌的研究关联...</p>
        </div>

        <ResearchState
          v-else-if="overseasError"
          kind="error"
          title="海外传播数据加载失败"
          :message="overseasError"
          retryable
          @retry="loadOverseasContext"
        />

        <div v-else-if="overseasData" class="overseas-content">
          <header class="overseas-hero">
            <div>
              <p class="overseas-kicker">INTERNATIONAL RECEPTION / 单曲研究</p>
              <h2>{{ overseasData.music.title || currentSong?.title }}</h2>
              <p class="overseas-meta">
                {{ category }} / {{ subcategory }} · 曲目编号 {{ currentSong?.id || '—' }}
              </p>
              <p class="overseas-desc">
                汇总这首曲目已形成的海外传播潜力、关联案例和区域传播方案；没有证据的项目保持空缺。
              </p>
            </div>
            <div class="overseas-status">
              <span
                class="association-pill"
                :class="{
                  linked: overseasData.association.status === 'linked',
                  reference: overseasData.association.status === 'category_reference',
                }"
              >
                {{ overseasData.association.label }}
              </span>
              <small>{{ overseasDisplayCases.length }} 个案例结果 · {{ overseasCountryCount }} 个方案国家</small>
              <a class="explainability-jump" href="#song-explainability-report">查看案例选择与可解释性报告 ↓</a>
            </div>
          </header>

          <div class="overseas-grid">
            <div class="overseas-main">
              <SectionCard
                title="本曲传播建议"
                kicker="PROPAGATION IDEAS"
                subtitle="按当前曲目的主题、乐种和关联案例给出简要方向，不展示评分。"
              >
                <template #actions>
                  <span class="overseas-chip">本曲专属建议</span>
                </template>

                <div class="candidate-conclusion propagation-suggestion-list">
                  <div><span>建议主题</span><b>{{ songPropagationSuggestions.theme }}</b></div>
                  <div><span>优先国家</span><b>{{ songPropagationSuggestions.countries.join('、') }}</b></div>
                  <div><span>呈现形式</span><b>{{ songPropagationSuggestions.format }}</b></div>
                  <div><span>试点方向</span><b>{{ songPropagationSuggestions.pilot }}</b></div>
                </div>
                <p class="overseas-section-note">
                  以上为《{{ currentSong?.title }}》的轻量建议；换歌后会按新曲目重新生成，不作为已完成的海外实测结论。
                </p>
              </SectionCard>

              <SectionCard
                title="海外传播影响因素参考"
                kicker="FACTOR REFERENCE"
                :subtitle="displayedFactorReference?.scope_label || '正在核对当前曲目的关联案例。'"
              >
                <div v-if="overseasReferenceFactors.length" class="reference-factor-list">
                  <div v-for="factor in overseasReferenceFactors" :key="factor.indicator_id" class="reference-factor-row">
                    <span>{{ factor.label }}</span>
                    <i><em :style="{ width: `${factor.share}%` }" /></i>
                    <b>{{ factor.share.toFixed(1) }}%</b>
                  </div>
                  <p class="overseas-section-note">
                    {{ songDataFactorReference.evidence_note }} 该结果是本曲专属参考，不冒充海外受众实测，也不参与80个案例的全局统计。
                  </p>
                </div>
                <ResearchState
                  v-else
                  kind="empty"
                  title="暂无本曲专属因素参考"
                  message="当前歌曲没有直接关联或机制匹配案例，因此不再重复展示全库统一平均值。"
                  compact
                />
              </SectionCard>

              <SectionCard
                :title="overseasCaseScope === 'direct' ? '相关海外演奏案例' : overseasCaseScope === 'matched' ? '机制匹配海外案例' : '严格海外参考案例'"
                kicker="RELATED CASES"
                :subtitle="overseasCaseScope === 'direct' ? '这些案例与当前候选曲目存在已登记的直接关联。' : overseasCaseScope === 'matched' ? '依据同类候选曲的乐器或接受机制匹配；属于机制参考，不冒充本曲演奏事实。' : '暂无直接或机制匹配，以下仅展示案例库整体参考。'"
              >
                <template #actions>
                  <span class="overseas-chip">{{ overseasDisplayCases.length }} 个案例</span>
                </template>
                <div v-if="overseasDisplayCases.length" class="overseas-case-grid">
                  <RouterLink
                    v-for="item in overseasDisplayCases"
                    :key="item.case_id"
                    :to="relatedCaseTo(item.case_id)"
                    class="overseas-case"
                  >
                    <div class="overseas-case-top">
                      <span>{{ item.case_id }}</span>
                      <b>证据 {{ item.review_status }}</b>
                    </div>
                    <h3>{{ item.performer }}</h3>
                    <p>{{ item.country }} · {{ item.instrument.join(' / ') }}</p>
                    <p class="overseas-case-summary">{{ item.summary }}</p>
                    <div class="overseas-case-foot">
                      <span>编码均分 {{ item.mean_score === null ? '—' : item.mean_score.toFixed(2) }} / 3</span>
                      <span>{{ item.source_count }} 条来源 · 查看反馈与接受原因 →</span>
                    </div>
                    <div v-if="matchedCaseMeta(item.case_id)" class="case-match-meta">
                      <b>匹配分 {{ matchedCaseMeta(item.case_id)?.match_score }}</b>
                      <span>{{ matchedCaseMeta(item.case_id)?.match_reasons.join('；') }}</span>
                    </div>
                  </RouterLink>
                </div>
                <ResearchState
                  v-else
                  kind="empty"
                  title="暂无关联案例"
                  message="没有找到与该曲目精确关联的海外演奏案例；本页不会把无关案例放进来。"
                  compact
                />
              </SectionCard>

              <SectionCard id="song-explainability-report" title="案例选择与可解释性分析报告" kicker="EXPLAINABLE REPORT">
                <div class="explainable-report-heading">
                  <p>说明为什么选择这些案例、哪些因素支持传播建议，以及当前结论的适用边界。</p>
                  <button type="button" @click="copyExplainabilityReport">复制报告内容</button>
                </div>
                <p v-if="explainabilityCopyState" class="explainable-copy-state">{{ explainabilityCopyState }}</p>
                <div class="explainable-report-body">
                  <section>
                    <b>案例选择原则</b>
                    <p>从已审批案例中综合曲目、音乐类型、乐器或表演形式、文化主题与接受机制进行匹配，不以热度或播放量直接代替传播成功。</p>
                  </section>
                  <section>
                    <b>本次入选案例</b>
                    <ol v-if="overseasDisplayCases.length">
                      <li v-for="item in overseasDisplayCases" :key="`report-${item.case_id}`">
                        <strong>{{ item.performer }} · {{ item.country }}</strong>
                        <span>{{ matchedCaseMeta(item.case_id)?.match_reasons.join('；') || '同类案例参照' }}</span>
                        <small>案例 {{ item.case_id }} · {{ item.source_count }} 条来源</small>
                      </li>
                    </ol>
                    <p v-else>当前没有满足展示条件的匹配案例。</p>
                  </section>
                  <section>
                    <b>核心解释链</b>
                    <p>
                      本曲建议以“{{ songPropagationSuggestions.theme }}”为主题，优先面向{{ songPropagationSuggestions.countries.join('、') }}；
                      主要参考{{ overseasReferenceFactors.slice(0, 3).map(item => item.label).join('、') || '现有案例机制' }}，
                      并以“{{ songPropagationSuggestions.format }}”作为呈现形式。
                    </p>
                  </section>
                  <section>
                    <b>结论边界</b>
                    <p>本报告用于解释案例筛选和建议生成，依据为当前已审批案例及其来源记录，不代表本曲已经完成海外实测，也不作因果推断。</p>
                  </section>
                </div>
              </SectionCard>

              <SectionCard
                title="区域传播方案"
                kicker="REGIONAL FIT"
                subtitle="展示明确选择该曲目的已审核国别方案、目标受众与适配理由。"
              >
                <template #actions>
                  <span class="overseas-chip">{{ overseasDisplayRegions.length }} 条方案</span>
                </template>
                <p v-if="overseasUsesReferenceRegions" class="overseas-section-note">
                  本曲暂无直接适配记录，以下展示六国总体方案框架，不作为该曲的国别结论。
                </p>
                <div v-if="overseasDisplayRegions.length" class="overseas-region-list">
                  <article v-for="row in overseasDisplayRegions" :key="String(row.strategy_id || row.region || row.country)">
                    <div class="overseas-region-top">
                      <span>{{ row.region || '区域未记录' }}</span>
                      <b>{{ row.country || '国家未记录' }}</b>
                    </div>
                    <p>{{ row.audience || '受众未记录' }} · {{ row.match_reason || '适配理由未记录' }}</p>
                  </article>
                </div>
                <ResearchState
                  v-else
                  kind="pending"
                  title="暂无适用的区域传播方案"
                  message="当前没有已审核且明确选择该曲目的国别方案。"
                  compact
                />
              </SectionCard>
            </div>

            <aside class="overseas-side">
              <SectionCard title="传播结果摘要" kicker="RESULT SUMMARY" tone="quiet">
                <div class="overseas-info-list">
                  <div><span>曲目</span><b>{{ overseasData.music.title }}</b></div>
                  <div><span>建议主题</span><b>{{ songPropagationSuggestions.theme }}</b></div>
                  <div><span>优先国家</span><b>{{ songPropagationSuggestions.countries.join('、') }}</b></div>
                  <div><span>案例结果</span><b>{{ overseasDisplayCases.length }} 个</b></div>
                  <div><span>案例来源</span><b>{{ overseasSourceCount }} 条</b></div>
                  <div><span>方案国家</span><b>{{ overseasCountryCount }} 个</b></div>
                  <div><span>区域方案</span><b>{{ overseasDisplayRegions.length }} 条</b></div>
                </div>
              </SectionCard>

              <SectionCard title="查看完整成果" kicker="RESULT LINKS" tone="quiet">
                <nav class="overseas-result-links" aria-label="海外传播成果入口">
                  <RouterLink :to="{ name: 'global-effect' }">全球传播效果</RouterLink>
                  <RouterLink :to="{ name: 'global-cases' }">海外案例库</RouterLink>
                  <RouterLink :to="{ name: 'promo-plan' }">区域传播方案</RouterLink>
                </nav>
              </SectionCard>
            </aside>
          </div>

        </div>
      </section>

      <section v-else class="report-dashboard">
        <div v-if="reportLoading" class="report-loading">
          <div class="loading-spinner"></div>
          <p>AI 正在结合情感数据与传播特征生成报告...</p>
        </div>

        <template v-else-if="reportData">
          <header class="report-hero">
            <div>
              <span class="report-kicker">GLOBAL SENTIMENT INTELLIGENCE</span>
              <h2>国际传播 AI 情感报告</h2>
              <p>{{ reportData.song_title }} · {{ category }} / {{ subcategory }}</p>
            </div>
            <span class="report-source" :class="{ active: reportData.used_llm }">
              {{ reportData.used_llm ? 'AI 实时研判' : '数据规则研判' }}
            </span>
          </header>

          <div class="report-metrics">
            <article>
              <span>评论总数</span>
              <strong>{{ reportData.overall_stats.total_comments.toLocaleString() }}</strong>
              <small>纳入情感分析的有效样本</small>
            </article>
            <article>
              <span>情感指数</span>
              <strong>{{ reportData.overall_stats.emotion_index.toFixed(2) }}</strong>
              <small>-1 至 1，越高越偏正面</small>
            </article>
            <article>
              <span>正面情感</span>
              <strong>{{ (reportData.overall_stats.positive_rate * 100).toFixed(1) }}%</strong>
              <small>正面评论在总样本中的占比</small>
            </article>
            <article>
              <span>近期趋势</span>
              <strong class="trend-value">{{ reportData.trend }}</strong>
              <small>根据近期情感时序判定</small>
            </article>
          </div>

          <div class="report-grid">
            <article class="report-panel report-insight">
              <div class="report-panel-heading">
                <span>01</span>
                <div><h3>AI 综合研判</h3><p>知识与情感数据联合解读</p></div>
              </div>
              <div class="report-copy">
                <template v-for="(line, index) in reportLines" :key="`${index}-${line.text}`">
                  <h4 v-if="line.heading">{{ line.text }}</h4>
                  <p v-else>{{ line.text }}</p>
                </template>
              </div>
            </article>

            <article class="report-panel report-structure">
              <div class="report-panel-heading">
                <span>02</span>
                <div><h3>情感结构</h3><p>评论情感极性占比</p></div>
              </div>
              <div class="sentiment-bars">
                <div v-for="item in reportSentiments" :key="item.name" class="sentiment-row">
                  <div><span>{{ item.name }}</span><strong>{{ item.value.toFixed(1) }}%</strong></div>
                  <div class="sentiment-track">
                    <i :style="{ width: `${item.value}%`, backgroundColor: item.color }"></i>
                  </div>
                </div>
              </div>
            </article>

            <article class="report-panel report-trend">
              <div class="report-panel-heading">
                <span>03</span>
                <div><h3>传播情感趋势</h3><p>历史评论情感指数变化</p></div>
              </div>
              <div v-if="reportData.chart_data.dates.length" ref="reportTrendChartRef" class="report-trend-chart"></div>
              <div v-else class="report-empty">暂无足够时序数据</div>
            </article>

            <article class="report-panel country-ranking">
              <div class="report-panel-heading">
                <span>04</span>
                <div><h3>国家情感排名</h3><p>海外国家和地区的受众情感对比</p></div>
              </div>
              <div v-if="reportData.country_ranking?.length" class="country-ranking-list">
                <div class="ranking-labels" aria-hidden="true">
                  <span>排名 / 国家</span><span>情感指数</span><span>正面率</span><span>样本</span>
                </div>
                <article
                  v-for="item in reportData.country_ranking"
                  :key="item.country"
                  class="country-ranking-row"
                >
                  <div class="country-name">
                    <b>{{ String(item.rank).padStart(2, '0') }}</b>
                    <span>{{ item.country }}</span>
                  </div>
                  <strong :class="item.emotion_index >= 0 ? 'positive' : 'negative'">
                    {{ item.emotion_index > 0 ? '+' : '' }}{{ item.emotion_index.toFixed(2) }}
                  </strong>
                  <div class="country-positive">
                    <span>{{ (item.positive_rate * 100).toFixed(1) }}%</span>
                    <i><em :style="{ width: `${item.positive_rate * 100}%` }"></em></i>
                  </div>
                  <small>{{ item.sample_count.toLocaleString() }}</small>
                </article>
                <p class="ranking-note">仅统计海外有效评论样本，中国数据不参与排名。</p>
              </div>
              <div v-else class="ranking-empty">
                <div class="ranking-empty-mark">海外数据</div>
                <strong>暂无可用的国家情感排名</strong>
                <p>当前曲目尚未采集到带有国别信息的海外评论。数据接入后将在此展示情感指数、正面率和样本数。</p>
              </div>
            </article>

            <article class="report-panel report-actions">
              <div class="report-panel-heading">
                <span>05</span>
                <div><h3>国际传播行动建议</h3><p>围绕海外理解与参与优化</p></div>
              </div>
              <div class="action-list">
                <div><b>01</b><span><strong>多语种内容</strong><small>补充歌词、文化背景和意象译析</small></span></div>
                <div><b>02</b><span><strong>受众分层</strong><small>结合国别情感数据制定差异化内容</small></span></div>
                <div><b>03</b><span><strong>持续监测</strong><small>跟踪负面波动和传播节点后的变化</small></span></div>
              </div>
            </article>
          </div>
        </template>

        <div v-else class="report-empty">暂无国际传播分析报告</div>
      </section>
    </main>

    <nav class="bottom-nav">
      <button type="button" :class="{ active: tab === 'basic' }" @click="tab = 'basic'">
        基本信息
      </button>
      <button type="button" :class="{ active: tab === 'emotion' }" @click="tab = 'emotion'">
        情感分析
      </button>
      <button type="button" :class="{ active: tab === 'overseas' }" @click="tab = 'overseas'">
        海外传播
      </button>
    </nav>
  </div>
</template>

<style scoped>
.detail-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.top {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1.2rem;
  background: linear-gradient(135deg, var(--gf-navy, #181e38), var(--gf-blue-deep, #29509b));
  color: var(--gf-cream, #faf5f0);
}

.back {
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  padding: 0.35rem 0.7rem;
  cursor: pointer;
  border-radius: 6px;
  backdrop-filter: blur(8px);
}

.back:hover {
  background: rgba(255, 255, 255, 0.15);
}

.top h1 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.content {
  flex: 1;
  padding: 1.5rem;
  padding-bottom: 6rem;
}

.select-row {
  margin-bottom: 1.5rem;
}

.select-row label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
}

.select-row select {
  min-width: 200px;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--gf-border, rgba(240, 217, 192, 0.5));
  background: rgba(255, 255, 255, 0.6);
  color: var(--gf-text, #411c35);
  border-radius: 6px;
  backdrop-filter: blur(8px);
}

.layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.top-row {
  display: grid;
  grid-template-columns: 240px 1fr 1.3fr;
  gap: 1.2rem;
}

.poster-section {
  display: flex;
  justify-content: center;
}

.poster {
  position: relative;
  width: 240px;
  height: 240px;
  border-radius: 16px;
  overflow: hidden;
  background: url('/src/assets/images/音频背景图.jpg') center/cover no-repeat;
  box-shadow: 0 8px 32px rgba(245, 222, 179, 0.4);
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  gap: 0.8rem;
  background: rgba(0, 0, 0, 0.2);
}

.poster-title {
  font-size: 1.1rem;
  font-weight: 500;
  text-align: center;
  padding: 0 1rem;
  line-height: 1.4;
}

.poster-play {
  position: absolute;
  top: 12px;
  left: 12px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
  transition:
    transform 0.3s ease,
    background 0.3s ease;
}

.poster-play:hover {
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.35);
}

.emotion-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--gf-surface, rgba(255, 253, 249, 0.75));
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(16px);
}

.emotion-chart {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.emotion-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--gf-text-muted, #8b7480);
}

.polarity-chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.polarity-chart {
  width: 240px;
  height: 240px;
}

.polarity-legend {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 4px;
}

.legend-text {
  color: var(--gf-text, #411c35);
}

.legend-value {
  color: var(--gf-text-muted, #8b7480);
  font-weight: 500;
}

@keyframes fly {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(calc(-100vw - 100%));
  }
}

.danmaku-section {
  position: relative;
  height: 280px;
  background: linear-gradient(135deg, rgba(24, 30, 56, 0.88), rgba(41, 82, 156, 0.88));
  border-radius: 16px;
  overflow: hidden;
  backdrop-filter: blur(16px);
  padding: 0.5rem;
}

.danmaku-item {
  position: absolute;
  right: -100%;
  white-space: nowrap;
  color: var(--gf-cream, #faf5f0);
  font-size: 0.85rem;
  padding: 0.35rem 0.8rem;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  animation: fly linear infinite;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.danmaku-item:hover {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.danmaku-tooltip {
  position: fixed;
  max-width: 320px;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  font-size: 0.85rem;
  border-radius: 8px;
  white-space: normal;
  word-break: break-word;
  pointer-events: none;
  z-index: 1000;
}

.danmaku-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.5);
}

.wordcloud-section {
  display: flex;
  align-items: stretch;
  min-height: 500px;
  background: transparent;
  padding: 1rem 2rem;
  gap: 1rem;
}

.wordcloud-left {
  flex: 7;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 450px;
}

.wordcloud-right {
  flex: 3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wordcloud-right img {
  width: 100%;
  height: auto;
  max-height: 450px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.wordcloud-loading {
  color: var(--gf-text-muted, #8b7480);
  font-size: 0.9rem;
}

.wordcloud-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--gf-text-muted, #8b7480);
}

.placeholder-hint {
  font-size: 0.75rem;
  opacity: 0.7;
}

.filled-panel {
  min-height: 60vh;
  background: var(--gf-surface, rgba(255, 253, 249, 0.75));
  border-radius: 16px;
  padding: 1.5rem;
  overflow: auto;
  backdrop-filter: blur(16px);
}

.filled-panel pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.6;
}

.report-dashboard {
  min-height: 70vh;
  color: #263531;
}

.report-loading,
.report-empty {
  display: grid;
  place-items: center;
  min-height: 360px;
  color: #6e7e78;
  text-align: center;
}

.report-loading {
  align-content: center;
  gap: 1rem;
}

.report-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.5rem 1.65rem;
  border: 1px solid #c8d3ce;
  border-bottom: 0;
  background: rgba(244, 247, 243, 0.94);
}

.report-kicker {
  color: #947348;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.report-hero h2 {
  margin: 0.28rem 0 0.35rem;
  color: #223b36;
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: clamp(1.45rem, 2.4vw, 2.15rem);
  letter-spacing: 0;
}

.report-hero p {
  margin: 0;
  color: #70807a;
  font-size: 0.85rem;
}

.report-source {
  flex-shrink: 0;
  padding: 0.45rem 0.7rem;
  border: 1px solid #becbc6;
  border-radius: 4px;
  color: #687872;
  background: #fff;
  font-size: 0.72rem;
}

.report-source.active {
  border-color: #85a99b;
  color: #315f55;
  background: #deebe5;
}

.report-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid #c8d3ce;
  background: #fff;
}

.report-metrics article {
  display: flex;
  flex-direction: column;
  min-height: 132px;
  padding: 1.15rem 1.25rem;
  border-right: 1px solid #dce3df;
}

.report-metrics article:last-child {
  border-right: 0;
}

.report-metrics span {
  color: #66756f;
  font-size: 0.76rem;
}

.report-metrics strong {
  margin: 0.35rem 0 0.2rem;
  color: #3e7568;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 2rem;
  line-height: 1;
}

.report-metrics strong.trend-value {
  font-family: inherit;
  font-size: 1.65rem;
}

.report-metrics small {
  margin-top: auto;
  color: #8a9692;
  font-size: 0.68rem;
  line-height: 1.45;
}

.report-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.65fr);
  gap: 1rem;
  margin-top: 1rem;
}

.report-panel {
  min-width: 0;
  padding: 1.25rem;
  border: 1px solid #c9d4cf;
  border-radius: 6px;
  background: rgba(246, 248, 244, 0.96);
  box-shadow: 0 12px 30px rgba(31, 55, 48, 0.09);
}

.report-panel-heading {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.report-panel-heading > span {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border: 1px solid #9eb5ac;
  border-radius: 50%;
  color: #477266;
  font: 700 0.68rem Georgia, serif;
}

.report-panel-heading h3 {
  margin: 0;
  color: #29433d;
  font-size: 1rem;
}

.report-panel-heading p {
  margin: 0.18rem 0 0;
  color: #84908c;
  font-size: 0.7rem;
}

.report-copy {
  color: #43524d;
  word-break: break-word;
  font-size: 0.88rem;
  line-height: 1.9;
}

.report-copy h4 {
  margin: 1rem 0 0.35rem;
  color: #2d554b;
  font-size: 0.92rem;
}

.report-copy h4:first-child {
  margin-top: 0;
}

.report-copy p {
  margin: 0.35rem 0;
}

.sentiment-bars {
  display: grid;
  gap: 1rem;
  padding-top: 0.35rem;
}

.sentiment-row > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  margin-bottom: 0.38rem;
  color: #5c6c66;
  font-size: 0.76rem;
}

.sentiment-track {
  height: 8px;
  overflow: hidden;
  border-radius: 2px;
  background: #dfe6e2;
}

.sentiment-track i {
  display: block;
  min-width: 2px;
  height: 100%;
  transition: width 0.7s ease;
}

.report-trend {
  grid-column: 1;
}

.report-trend-chart {
  width: 100%;
  height: 280px;
}

.country-ranking {
  grid-column: 2;
  grid-row: 2 / span 2;
}

.ranking-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  padding: 1rem;
  border: 1px dashed #b4c3bd;
  background: rgba(255, 255, 255, 0.56);
  text-align: center;
}

.ranking-empty-mark {
  margin-bottom: 0.8rem;
  padding: 0.3rem 0.55rem;
  border-radius: 3px;
  color: #8b6c45;
  background: #eee4d4;
  font-size: 0.68rem;
}

.ranking-empty strong {
  color: #35584f;
  font-size: 1rem;
}

.ranking-empty p {
  max-width: 280px;
  margin: 0.55rem 0 1.2rem;
  color: #84908c;
  font-size: 0.72rem;
  line-height: 1.7;
}

.country-ranking-list { display:grid; gap:.58rem; }
.ranking-labels,.country-ranking-row { display:grid; grid-template-columns:minmax(90px,1.35fr) 58px minmax(76px,.9fr) 38px; align-items:center; gap:.4rem; }
.ranking-labels { padding:0 .5rem .45rem; color:#82908b; font-size:.61rem; border-bottom:1px solid #d6dfdb; }
.ranking-labels span:not(:first-child) { text-align:right; }
.country-ranking-row { min-width:0; min-height:54px; padding:.55rem .5rem; border:1px solid #dce4e0; background:#fff; transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease; }
.country-ranking-row:hover { transform:translateY(-2px); border-color:#9fb9af; box-shadow:0 8px 20px rgba(48,78,69,.09); }
.country-name { display:flex; align-items:center; gap:.45rem; min-width:0; }
.country-name b { display:grid; place-items:center; width:30px; height:30px; flex:0 0 30px; border:1px solid #a9c0b7; border-radius:50%; color:#456d61; font:700 .68rem Georgia,serif; }
.country-name span { overflow:hidden; color:#304b43; font-size:.78rem; font-weight:600; text-overflow:ellipsis; white-space:nowrap; }
.country-ranking-row > strong { text-align:right; font-size:.8rem; }
.country-ranking-row > strong.positive { color:#36745f; }
.country-ranking-row > strong.negative { color:#a15151; }
.country-positive { display:grid; gap:.28rem; text-align:right; color:#4e655d; font-size:.68rem; }
.country-positive i { height:4px; overflow:hidden; background:#e4ebe8; }
.country-positive em { display:block; height:100%; background:#78a996; }
.country-ranking-row > small { color:#65756f; text-align:right; font-size:.68rem; }
.ranking-note { margin:.5rem 0 0; color:#85938e; font-size:.64rem; text-align:right; }

.report-actions {
  grid-column: 1;
}

.action-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.7rem;
}

.action-list > div {
  display: flex;
  gap: 0.6rem;
  min-width: 0;
  padding: 0.8rem;
  border: 1px solid #d6dfdb;
  background: #fff;
}

.action-list b {
  color: #a37d50;
  font: 700 0.72rem Georgia, serif;
}

.action-list span {
  display: grid;
  gap: 0.25rem;
}

.action-list strong {
  color: #35544c;
  font-size: 0.78rem;
}

.action-list small {
  color: #7d8b86;
  font-size: 0.68rem;
  line-height: 1.5;
}

.emotion-analysis-page {
  min-height: 60vh;
}

.emotion-international-summary {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #cbd5d0;
}

.emotion-international-summary > header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.emotion-international-summary > header span {
  color: #5d8277;
  font-size: 0.68rem;
  letter-spacing: 0.18em;
}

.emotion-international-summary > header h3 {
  margin: 0.25rem 0 0;
  color: #29433d;
  font-size: 1.2rem;
}

.emotion-international-summary > header small {
  color: #7e8d87;
  font-size: 0.72rem;
}

.emotion-international-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
  gap: 1rem;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(128, 29, 58, 0.1);
  border-top-color: #801d3a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.emotion-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.emotion-header {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(128, 29, 58, 0.05), rgba(180, 90, 126, 0.05));
  border-radius: 16px;
  border: 1px solid rgba(128, 29, 58, 0.1);
}

.emotion-header h2 {
  margin: 0 0 0.5rem;
  color: var(--gf-maroon, #801d3a);
}

.emotion-summary {
  margin: 0;
  color: var(--gf-text-muted, #8b7480);
  font-size: 0.95rem;
}

.emotion-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}

.stat-card {
  background: var(--gf-surface, rgba(255, 253, 249, 0.9));
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  border: 1px solid rgba(240, 217, 192, 0.5);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gf-text, #411c35);
}

.stat-value.positive {
  color: #52c41a;
}

.stat-value.negative {
  color: #ff4d4f;
}

.stat-value.neutral {
  color: #faad14;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--gf-text-muted, #8b7480);
  margin-top: 0.3rem;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.chart-card {
  background: var(--gf-surface, rgba(255, 253, 249, 0.9));
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(240, 217, 192, 0.5);
}

.chart-card.full-width {
  width: 100%;
}

.chart-card h3 {
  margin: 0 0 0.3rem;
  color: var(--gf-text, #411c35);
  font-size: 1.1rem;
}

.chart-desc {
  margin: 0 0 1rem;
  color: var(--gf-text-muted, #8b7480);
  font-size: 0.85rem;
}

.emotion-trend-chart,
.emotion-pie-chart,
.prediction-chart,
.causal-chart {
  height: 280px;
}

.chart-loading {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gf-text-muted, #8b7480);
}

.chart-empty {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gf-text-muted, #8b7480);
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.causal-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.causal-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.causal-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.8rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
}

.causal-label {
  font-size: 0.85rem;
  color: var(--gf-text-muted, #8b7480);
}

.causal-value {
  font-weight: 600;
  color: var(--gf-text, #411c35);
}

.causal-value.positive {
  color: #52c41a;
}

.causal-value.negative {
  color: #ff4d4f;
}

.causal-value.neutral {
  color: #faad14;
}

.causal-value.highlight {
  color: #801d3a;
  font-size: 1.1em;
}

.events-list {
  margin-bottom: 1rem;
}

.events-list h4 {
  margin: 0 0 0.8rem;
  font-size: 1rem;
  color: var(--gf-text, #411c35);
}

.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.8rem;
}

.event-item {
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  padding: 0.8rem;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  cursor: pointer;
}

.event-item:hover {
  border-color: rgba(128, 29, 58, 0.3);
  background: rgba(128, 29, 58, 0.05);
}

.event-item.active {
  border-color: #801d3a;
  background: rgba(128, 29, 58, 0.08);
}

.event-date {
  font-weight: 600;
  color: var(--gf-maroon, #801d3a);
  font-size: 0.9rem;
}

.event-name {
  margin-top: 0.3rem;
  font-weight: 500;
  color: var(--gf-text, #411c35);
}

.event-type {
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  display: inline-block;
}

.event-desc {
  margin-top: 0.4rem;
  font-size: 0.8rem;
  color: var(--gf-text-muted, #8b7480);
  line-height: 1.4;
}

.explanation-card {
  background: linear-gradient(135deg, rgba(41, 80, 155, 0.05), rgba(128, 29, 58, 0.05));
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(41, 80, 155, 0.1);
}

.explanation-card h3 {
  margin: 0 0 1rem;
  color: var(--gf-blue-deep, #29509b);
}

.explanation-content {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.exp-item {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
}

.exp-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.exp-text {
  font-size: 0.95rem;
  color: var(--gf-text, #411c35);
  line-height: 1.6;
}

.emotion-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--gf-text-muted, #8b7480);
}

.bottom-nav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background: linear-gradient(135deg, var(--gf-navy, #181e38), var(--gf-blue-deep, #29509b));
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.bottom-nav button {
  border: none;
  background: transparent;
  color: var(--gf-cream, #faf5f0);
  opacity: 0.75;
  padding: 0.95rem 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
}

.bottom-nav button.active {
  color: var(--gf-blush, #ec7696);
  opacity: 1;
  background: rgba(245, 222, 179, 0.2);
}

@media (max-width: 1000px) {
  .top-row {
    grid-template-columns: 1fr 1fr;
  }

  .poster-section {
    grid-column: 1 / -1;
    justify-content: center;
  }

  .emotion-stats {
    grid-template-columns: repeat(3, 1fr);
  }

  .chart-row {
    grid-template-columns: 1fr;
  }

  .report-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .report-metrics article:nth-child(2) {
    border-right: 0;
  }

  .report-metrics article:nth-child(-n + 2) {
    border-bottom: 1px solid #dce3df;
  }

  .report-grid {
    grid-template-columns: 1fr;
  }

  .report-trend,
  .country-ranking,
  .report-actions {
    grid-column: 1;
    grid-row: auto;
  }

  .ranking-empty {
    min-height: 260px;
  }
}

@media (max-width: 700px) {
  .ranking-labels {
    display: none;
  }

  .country-ranking-row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.45rem 0.8rem;
  }

  .country-ranking-row > strong {
    grid-column: 2;
    grid-row: 1;
  }

  .country-positive {
    grid-column: 1;
    grid-row: 2;
    text-align: left;
  }

  .country-ranking-row > small {
    grid-column: 2;
    grid-row: 2;
  }

  .top-row {
    grid-template-columns: 1fr;
  }

  .poster {
    width: 100%;
    max-width: 280px;
    height: auto;
    aspect-ratio: 3 / 4;
  }

  .content {
    padding: 1rem;
  }

  .emotion-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .causal-summary {
    grid-template-columns: 1fr;
  }

  .report-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .report-metrics {
    grid-template-columns: 1fr;
  }

  .report-metrics article,
  .report-metrics article:nth-child(2) {
    border-right: 0;
    border-bottom: 1px solid #dce3df;
  }

  .report-metrics article:last-child {
    border-bottom: 0;
  }

  .action-list {
    grid-template-columns: 1fr;
  }
}
/* P6 overseas tab */
.overseas-page {
  min-height: 720px;
}

.overseas-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 14px;
  min-height: 420px;
  color: #8fa99f;
}

.overseas-content {
  max-width: 1280px;
  margin: 0 auto;
}

.overseas-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  padding: 4px 0 22px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.18);
}

.overseas-kicker {
  margin: 0 0 10px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.18em;
}

.overseas-hero h2 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(30px, 4vw, 44px);
  font-weight: 500;
  line-height: 1.2;
}

.overseas-meta {
  margin: 9px 0 0;
  color: #78948a;
  font-size: 10px;
}

.overseas-desc {
  max-width: 780px;
  margin: 13px 0 0;
  color: #9bb7ad;
  font-size: 12px;
  line-height: 1.8;
}

.overseas-status {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 8px;
  flex: 0 0 auto;
}

.overseas-status small {
  color: #78948a;
  font-size: 9px;
}

.explainability-jump {
  padding: 7px 10px;
  border: 1px solid rgba(217, 194, 138, 0.32);
  border-radius: 5px;
  color: #e8d4a8;
  font-size: 11px;
  text-decoration: none;
}

.explainability-jump:hover {
  border-color: rgba(217, 194, 138, 0.58);
  background: rgba(217, 194, 138, 0.08);
}

#song-explainability-report {
  scroll-margin-top: 96px;
}

.association-pill,
.overseas-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 8px;
  border: 1px solid rgba(217, 194, 138, 0.32);
  border-radius: 999px;
  color: #d9c28a;
  font-size: 9px;
  white-space: nowrap;
}

.association-pill.linked {
  border-color: rgba(143, 199, 177, 0.36);
  color: #8fc7b1;
}

.association-pill.reference {
  border-color: rgba(217, 194, 138, 0.42);
  color: #e8d4a8;
}

.association-box {
  margin-top: 14px;
  padding: 13px 15px;
  border: 1px solid rgba(226, 162, 118, 0.25);
  border-radius: 8px;
  background: rgba(126, 75, 42, 0.1);
}

.association-box.linked {
  border-color: rgba(143, 199, 177, 0.22);
  background: rgba(94, 166, 140, 0.08);
}

.association-box > b {
  color: #e2a276;
  font-size: 10px;
  font-weight: 500;
}

.association-box.linked > b {
  color: #8fc7b1;
}

.association-box ul {
  margin: 7px 0 0;
  padding-left: 17px;
}

.association-box li {
  margin: 4px 0;
  color: #b9a484;
  font-size: 10px;
  line-height: 1.65;
}

.association-box.linked li {
  color: #9bb7ad;
}

.overseas-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  align-items: start;
  margin-top: 16px;
}

.overseas-main,
.overseas-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.overseas-side {
  position: sticky;
  top: 96px;
}

.explainable-report-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.explainable-report-heading p {
  margin: 0;
  color: #9bb7ad;
  font-size: 12px;
  line-height: 1.7;
}

.explainable-report-heading button {
  flex-shrink: 0;
  padding: 8px 13px;
  border: 1px solid rgba(216, 190, 133, 0.45);
  background: transparent;
  color: #e8d4a8;
  cursor: pointer;
}

.explainable-copy-state {
  margin: 10px 0 0;
  color: #8fc7b1;
  font-size: 12px;
}

.explainable-report-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.explainable-report-body > section {
  padding: 14px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  background: rgba(5, 29, 25, 0.4);
}

.explainable-report-body b { color: #e8d4a8; font-size: 13px; }
.explainable-report-body p { margin: 8px 0 0; color: #9bb7ad; font-size: 12px; line-height: 1.75; }
.explainable-report-body ol { margin: 10px 0 0; padding-left: 20px; }
.explainable-report-body li { margin-bottom: 10px; color: #8fa99f; font-size: 12px; line-height: 1.6; }
.explainable-report-body li strong,
.explainable-report-body li span,
.explainable-report-body li small { display: block; }
.explainable-report-body li strong { color: #cddbd5; }
.explainable-report-body li small { color: #6f8e83; }

.potential-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.potential-head strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 46px;
  font-weight: 500;
  line-height: 0.95;
}

.potential-head strong.potential-pending {
  color: #b99767;
  font-size: 30px;
}

.potential-unit {
  margin-left: 4px;
  color: #78948a;
  font-size: 11px;
}

.potential-head p {
  margin: 8px 0 0;
  color: #9bb7ad;
  font-size: 11px;
}

.potential-meta {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 5px;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.6;
}

.candidate-conclusion {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}

.candidate-conclusion div {
  padding: 10px 11px;
  border: 1px solid rgba(159, 198, 181, 0.12);
  background: rgba(5, 25, 22, 0.28);
}

.candidate-conclusion span {
  display: block;
  margin-bottom: 5px;
  color: #6f8c81;
  font-size: 8px;
}

.candidate-conclusion b {
  color: #bccfc7;
  font-size: 10px;
  font-weight: 500;
  line-height: 1.65;
}

.category-reference {
  display: grid;
  gap: 10px;
}

.category-reference-scope {
  margin: 0;
  color: #e8d4a8;
  font-size: 11px;
}

.category-reference-mechanisms {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.category-reference-mechanisms span {
  padding: 4px 7px;
  border: 1px solid rgba(143, 199, 177, 0.18);
  color: #9fc1b4;
  font-size: 8px;
}

.category-reference article {
  padding: 12px 13px;
  border: 1px solid rgba(159, 198, 181, 0.13);
  background: rgba(5, 25, 22, 0.3);
}

.category-reference article > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.category-reference article span,
.category-reference article small {
  color: #78948a;
  font-size: 8px;
}

.category-reference article b { color: #dbe7e2; font-size: 11px; font-weight: 500; }
.category-reference article p { margin: 8px 0; color: #aac0b7; font-size: 9px; line-height: 1.65; }

.overseas-indicator-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 15px;
}

.reference-factor-list {
  display: grid;
  gap: 7px;
}

.reference-factor-row {
  display: grid;
  grid-template-columns: minmax(105px, 1fr) minmax(100px, 1.5fr) 42px;
  align-items: center;
  gap: 10px;
  min-height: 26px;
}

.reference-factor-row > span {
  color: #b8cbc3;
  font-size: 9px;
}

.reference-factor-row > i {
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
}

.reference-factor-row > i em {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5ea68c, #d9c28a);
}

.reference-factor-row > b {
  color: #e8d4a8;
  font-size: 9px;
  font-weight: 500;
  text-align: right;
}

.overseas-indicator {
  padding: 11px 12px;
  border: 1px solid rgba(159, 198, 181, 0.13);
  border-radius: 6px;
  background: rgba(5, 25, 22, 0.34);
}

.overseas-indicator-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.overseas-indicator-top span {
  color: #c9d8d1;
  font-size: 9px;
  line-height: 1.5;
}

.overseas-indicator-top b {
  color: #d9c28a;
  font-size: 10px;
  font-weight: 500;
}

.overseas-track {
  height: 3px;
  margin-top: 8px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.overseas-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.overseas-indicator small {
  display: block;
  margin-top: 6px;
  color: #6f8c81;
  font-size: 8px;
}

.overseas-section-note {
  margin: 13px 0 0;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.7;
}

.overseas-case-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.overseas-case {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 14px 15px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 7px;
  background: rgba(5, 25, 22, 0.38);
  text-decoration: none;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.overseas-case:hover {
  border-color: rgba(143, 199, 177, 0.36);
  transform: translateY(-2px);
}

.overseas-case-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.overseas-case-top span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 8px;
}

.overseas-case-top b {
  color: #8fc7b1;
  font-size: 8px;
  font-weight: 500;
}

.overseas-case h3 {
  display: -webkit-box;
  margin: 8px 0 0;
  overflow: hidden;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.45;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.overseas-case p {
  margin: 6px 0 0;
  color: #8fa99f;
  font-size: 9px;
  line-height: 1.6;
}

.overseas-case .overseas-case-summary {
  display: -webkit-box;
  overflow: hidden;
  color: #78948a;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.overseas-case-foot {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
  padding-top: 9px;
  border-top: 1px solid rgba(159, 198, 181, 0.1);
  color: #6f8c81;
  font-size: 8px;
}

.case-match-meta {
  display: grid;
  gap: 5px;
  margin-top: 10px;
  padding-top: 9px;
  border-top: 1px solid rgba(159, 198, 181, 0.1);
}

.case-match-meta b { color: #e8d4a8; font-size: 9px; font-weight: 500; }
.case-match-meta span { color: #78948a; font-size: 8px; line-height: 1.55; }

.overseas-region-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.overseas-region-list article {
  padding: 12px 13px;
  border: 1px solid rgba(159, 198, 181, 0.13);
  border-radius: 6px;
  background: rgba(5, 25, 22, 0.34);
}

.overseas-region-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.overseas-region-top span {
  color: #8fc7b1;
  font-size: 10px;
}

.overseas-region-top b {
  color: #d9c28a;
  font-size: 10px;
  font-weight: 500;
}

.overseas-region-list p {
  margin: 7px 0 0;
  color: #8fa99f;
  font-size: 9px;
  line-height: 1.65;
}

.overseas-info-list {
  display: flex;
  flex-direction: column;
}

.overseas-info-list > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.overseas-info-list > div:last-child {
  border-bottom: 0;
}

.overseas-info-list span {
  color: #78948a;
  font-size: 9px;
}

.overseas-info-list b {
  color: #c9d8d1;
  font-size: 9px;
  font-weight: 500;
  text-align: right;
}

.overseas-result-links {
  display: grid;
  gap: 8px;
}

.overseas-result-links a {
  padding: 10px 11px;
  border: 1px solid rgba(143, 199, 177, 0.18);
  background: rgba(143, 199, 177, 0.05);
  color: #b8cec5;
  font-size: 10px;
  text-decoration: none;
  transition: border-color 0.18s ease, color 0.18s ease, background 0.18s ease;
}

.overseas-result-links a:hover {
  border-color: rgba(232, 212, 168, 0.45);
  background: rgba(232, 212, 168, 0.07);
  color: #e8d4a8;
}

.bottom-nav {
  grid-template-columns: repeat(3, 1fr);
}

@media (max-width: 1100px) {
  .overseas-grid {
    grid-template-columns: 1fr;
  }

  .overseas-side {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .overseas-indicator-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 800px) {
  .emotion-international-grid,
  .explainable-report-body {
    grid-template-columns: 1fr;
  }

  .emotion-international-summary > header,
  .explainable-report-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .overseas-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .overseas-status {
    align-items: flex-start;
  }

  .potential-head {
    flex-direction: column;
  }

  .potential-meta {
    align-items: flex-start;
  }

  .overseas-case-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .overseas-page {
    min-height: 0;
  }

  .overseas-content {
    padding-bottom: 12px;
  }

  .overseas-hero h2 {
    font-size: 30px;
  }

  .overseas-indicator-grid,
  .candidate-conclusion,
  .overseas-side {
    grid-template-columns: 1fr;
  }

  .reference-factor-row {
    grid-template-columns: 90px 1fr 40px;
  }

  .overseas-side {
    display: flex;
  }

  .bottom-nav button {
    padding: 0.85rem 0.25rem;
    font-size: 0.8rem;
  }
}

</style>
