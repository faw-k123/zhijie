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
const tab = ref<'basic' | 'emotion' | 'report'>('basic')
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
  if (t === 'report' && !reportData.value) loadAiReport()
  if (t === 'report' && reportData.value) nextTick(renderReportTrendChart)
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
        </div>

        <div v-else class="emotion-empty">
          <p>暂无情感分析数据</p>
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
      <button type="button" :class="{ active: tab === 'report' }" @click="tab = 'report'">
        国际传播分析
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
</style>
