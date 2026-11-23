<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import AppNav from '@/components/AppNav.vue'
import ModelViewer from '@/components/ModelViewer.vue'
import vLightTilt from '@/directives/lightTilt'
import { askHomeQa, fetchHomeGraph, fetchMusicTaxonomy } from '@/api/dataDisplay'
import { getLocale } from '@/i18n'


const router = useRouter()

const carouselIndex = ref(0)
const bgOverlay = new URL('@/assets/images/bg-overlay.png', import.meta.url).href
const aiBgImage = new URL('@/assets/images/问答背景图.jpg', import.meta.url).href
const modelUrl = '/moxing.glb'

const slides = [
  {
    video: new URL('@/assets/videos/bj.mp4', import.meta.url).href,
    overlay: bgOverlay
  },
  { image: new URL('@/assets/images/banner2.jpg', import.meta.url).href },
  { image: new URL('@/assets/images/banner3.jpg', import.meta.url).href },
  { image: new URL('@/assets/images/banner4.jpg', import.meta.url).href },
  { image: new URL('@/assets/images/banner5.jpg', import.meta.url).href },
  { image: new URL('@/assets/images/banner6.jpg', import.meta.url).href },
]
/** 记录每张图片的真实宽高比，容器高度会跟随当前显示的图片比例变化 */
const slideAspects = ref<number[]>(slides.map(() => 16 / 9))
const activeAspect = computed(() => slideAspects.value[carouselIndex.value] || 16 / 9)
function onSlideImgLoad(e: Event, idx: number) {
  const img = e.target as HTMLImageElement
  if (img.naturalWidth && img.naturalHeight) {
    slideAspects.value[idx] = img.naturalWidth / img.naturalHeight
  }
}
let timer: ReturnType<typeof setInterval> | null = null

/** 首页右下：音乐大类 / 小类（对接 Neo4j 图谱） */
const taxonomy = ref<Record<string, Record<string, string[]>>>({})
const category = ref('')
const subcategory = ref('')
const graphStatus = ref('请选择音乐大类与小类后点击确认')
const graphLoading = ref(false)
const graphNodeCount = ref(0)
const graphLinkCount = ref(0)

const categories = computed(() => Object.keys(taxonomy.value))
const subcategories = computed(() => Object.keys(taxonomy.value[category.value] || {}))

const aiReply = ref('你好，我是国风音乐助手，有什么可以帮你的？')
const aiQuestion = ref('')
const aiLoading = ref(false)
const qaMeta = ref<{ usedLlm: boolean; nodes: number; relations: number } | null>(null)
const isRecording = ref(false)
const voiceButtonText = ref('🎤 语音')

/** echarts 图谱 */
const chartContainer = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

/** 点击节点后展示的信息 */
const selectedNode = ref<{
  name: string
  type: string
  properties: Record<string, unknown>
  relations: Array<{ rel: string; target: string }>
} | null>(null)

watch(category, () => {
  subcategory.value = subcategories.value[0] || ''
})

function nextSlide() {
  carouselIndex.value = (carouselIndex.value + 1) % slides.length
}

function prevSlide() {
  carouselIndex.value = (carouselIndex.value - 1 + slides.length) % slides.length
}

/** 参考文化知识图谱的高识别度分类配色 */
type GraphTypeStyle = { color: string; size: number; legend: string }

const DEFAULT_TYPE_STYLE: GraphTypeStyle = { color: '#91a6a0', size: 40, legend: '关联实体' }

const TYPE_STYLES: Record<string, GraphTypeStyle> = {
  TradMusicRoot: { color: '#536fc5', size: 70, legend: '传统音乐' },
  MusicCategory: { color: '#68b8d6', size: 58, legend: '音乐大类' },
  Opera: { color: '#f5c24f', size: 48, legend: '戏曲流派' },
  FolkSong: { color: '#f5c24f', size: 48, legend: '民歌流派' },
  Instrument: { color: '#f5c24f', size: 48, legend: '乐器类型' },
  MusicWork: { color: '#ef6264', size: 42, legend: '代表作品' },
}

const graphLegend: GraphTypeStyle[] = [
  { color: '#536fc5', size: 70, legend: '传统音乐' },
  { color: '#68b8d6', size: 58, legend: '音乐大类' },
  { color: '#f5c24f', size: 48, legend: '流派与类型' },
  { color: '#ef6264', size: 42, legend: '代表作品' },
]

function typeStyle(type?: string): GraphTypeStyle {
  return (type && TYPE_STYLES[type]) || DEFAULT_TYPE_STYLE
}

const RELATION_LABELS: Record<string, string> = {
  HAS_CATEGORY: '分为',
  CONTAIN: '包含',
  REPRESENT_WORK: '代表作品',
  BELONG_TO: '属于',
  RELATED_TO: '关联',
}

function relationLabel(rel?: string) {
  if (!rel) return '关联'
  return RELATION_LABELS[rel] || rel.replaceAll('_', ' ')
}

/** 用 echarts 渲染 Neo4j 图谱 */
function renderGraph(data: {
  nodes?: Array<{ id: string; label: string; type?: string; properties?: Record<string, unknown> }>
  links?: Array<{ source: string; target: string; rel?: string }>
}) {
  if (!chartContainer.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartContainer.value)
  }
  selectedNode.value = null
  chartInstance.resize()

  // 构建 id->label 映射，把 link 的 source/target 从 id 转成 label
  const idToLabel: Record<string, string> = {}
  for (const n of data.nodes || []) {
    idToLabel[n.id] = n.label
  }
  // 按节点 label 收集出边关系，供点击时展示
  const labelToRelations: Record<string, Array<{ rel: string; target: string }>> = {}
  for (const l of data.links || []) {
    const srcLabel = idToLabel[l.source] || l.source
    const dstLabel = idToLabel[l.target] || l.target
    if (!labelToRelations[srcLabel]) labelToRelations[srcLabel] = []
    labelToRelations[srcLabel].push({ rel: relationLabel(l.rel), target: dstLabel })
  }

  const categoryNames = [
    ...new Set((data.nodes || []).map((n) => typeStyle(n.type).legend)),
  ]
  const categoryIndex = new Map(categoryNames.map((name, index) => [name, index]))

  // 用 label 作为 name，附加完整信息到 data 字段供点击读取
  const nodes = (data.nodes || []).map((n) => {
    const isSelected = n.label === subcategory.value
    const style = typeStyle(n.type)
    return {
      name: n.label,
      symbolSize: isSelected ? style.size + 10 : style.size,
      category: categoryIndex.get(style.legend) || 0,
      itemStyle: {
        color: style.color,
        borderColor: isSelected ? '#253f72' : '#ffffff',
        borderWidth: isSelected ? 4 : 2,
        shadowBlur: isSelected ? 22 : 8,
        shadowColor: isSelected ? `${style.color}aa` : 'rgba(48, 72, 86, 0.16)',
      },
      label: {
        show: true,
        position: 'right',
        distance: 8,
        color: '#344341',
        fontSize: isSelected ? 14 : 12,
        fontWeight: isSelected ? 700 : 500,
      },
      nodeType: n.type || 'node',
      nodeProps: n.properties || {},
      nodeRelations: labelToRelations[n.label] || [],
    }
  })

  const links = (data.links || []).map((l) => ({
    source: idToLabel[l.source] || l.source,
    target: idToLabel[l.target] || l.target,
    rel: relationLabel(l.rel),
  }))

  graphNodeCount.value = nodes.length
  graphLinkCount.value = links.length

  chartInstance.setOption({
    animationDuration: 700,
    animationEasingUpdate: 'quinticInOut',
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#d8dfdc',
      borderWidth: 1,
      textStyle: { color: '#263a38', fontSize: 12 },
      formatter: (p: { dataType: string; data: { name?: string; rel?: string } }) =>
        p.dataType === 'edge' ? p.data.rel || '关联' : p.data.name || '',
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        left: 28,
        right: 28,
        top: 72,
        bottom: 36,
        zoom: 0.86,
        roam: true,
        draggable: true,
        categories: categoryNames.map((name) => ({ name })),
        label: { show: true, position: 'right' },
        edgeLabel: {
          show: true,
          formatter: (p: { data: { rel?: string } }) => p.data.rel || '',
          color: '#87918e',
          fontSize: 10,
        },
        force: {
          repulsion: [300, 560],
          edgeLength: [110, 190],
          gravity: 0.045,
          friction: 0.18,
          layoutAnimation: true,
        },
        data: nodes,
        links,
        lineStyle: { color: '#b8bfbc', width: 1.2, opacity: 0.86, curveness: 0.08 },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 7],
        emphasis: {
          focus: 'adjacency',
          scale: 1.12,
          lineStyle: { width: 2.5, color: '#738a84' },
        },
      },
    ],
  }, true)
}

function resetGraphView() {
  chartInstance?.setOption({ series: [{ zoom: 0.86, center: undefined }] })
}

/** 对接：POST /api/home/graph/ → 数据展示模块 · Neo4j 图谱 */
async function confirmGraph() {
  if (!category.value || !subcategory.value) {
    graphStatus.value = '请先选择大类与小类'
    return
  }
  graphLoading.value = true
  graphStatus.value = '加载中...'
  try {
    const res = await fetchHomeGraph(category.value, subcategory.value)
    const payload = res.data as {
      nodes?: Array<{ id: string; label: string; type?: string; properties?: Record<string, unknown> }>
      links?: Array<{ source: string; target: string; rel?: string }>
      message?: string
      error?: string
    } | undefined
    if (payload?.error) {
      graphStatus.value = '知识图谱服务暂未连接；案例库、研究洞察与其他研究数据不受影响。'
      if (chartInstance) chartInstance.clear()
    } else if (payload?.nodes && payload.nodes.length > 0) {
      renderGraph(payload)
      graphStatus.value = payload.message || `已展示 ${payload.nodes.length} 个节点`
    } else {
      graphStatus.value = payload?.message || '未检索到图谱节点'
      if (chartInstance) chartInstance.clear()
    }
  } catch (e: unknown) {
    const err = e as { message?: string }
    graphStatus.value = '知识图谱服务暂不可用；案例库、研究洞察与其他研究数据不受影响。'
    if (chartInstance) chartInstance.clear()
  } finally {
    graphLoading.value = false
  }
}

/** 对接：POST /api/home/qa/ → 数据展示模块 · KG-RAG */
async function askAi() {
  const q = aiQuestion.value.trim()
  if (!q) return
  aiLoading.value = true
  qaMeta.value = null
  try {
    const res = await askHomeQa(q, getLocale())
    const payload = res.data as {
      answer?: string
      used_llm?: boolean
      references?: { nodes_count?: number; relations_count?: number }
    } | undefined
    aiReply.value = payload?.answer || JSON.stringify(res.data)
    qaMeta.value = {
      usedLlm: !!payload?.used_llm,
      nodes: payload?.references?.nodes_count || 0,
      relations: payload?.references?.relations_count || 0,
    }
  } catch (e: unknown) {
    const err = e as { message?: string }
    aiReply.value = `问答请求失败：${err.message || '网络错误'}`
  } finally {
    aiLoading.value = false
    aiQuestion.value = ''
  }
}

function toggleVoiceInput() {
  if (isRecording.value) {
    stopVoiceInput()
  } else {
    startVoiceInput()
  }
}

let recognition: any = null

function startVoiceInput() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  
  if (!SpeechRecognition) {
    aiReply.value = '正在模拟语音识别（浏览器不支持）...'
    setTimeout(() => {
      const mockTexts = [
        '推荐几首古琴曲',
        '什么是国风音乐',
        '青花瓷的歌词是什么',
        '帮我找一首欢快的民歌',
        '传统乐器有哪些'
      ]
      const randomText = mockTexts[Math.floor(Math.random() * mockTexts.length)] ?? mockTexts[0]!
      aiQuestion.value = randomText
      aiReply.value = `识别结果：${randomText}`
      isRecording.value = false
      voiceButtonText.value = '🎤 语音'
    }, 1500)
    return
  }

  recognition = new SpeechRecognition()
  recognition.continuous = false
  recognition.interimResults = false
  recognition.lang = 'zh-CN'

  recognition.onstart = () => {
    isRecording.value = true
    voiceButtonText.value = '🔴 录音中...'
    aiReply.value = '请说话（说完自动停止）...'
  }

  recognition.onresult = (event: any) => {
    const result = event.results[0][0].transcript
    aiQuestion.value = result
    aiReply.value = `识别结果：${result}`
    stopVoiceInput()
  }

  recognition.onerror = (event: any) => {
    if (event.error === 'network') {
      aiReply.value = '网络连接问题，正在使用模拟识别...'
      setTimeout(() => {
        const mockTexts = [
          '推荐几首古琴曲',
          '什么是国风音乐',
          '青花瓷的歌词是什么',
          '帮我找一首欢快的民歌',
          '传统乐器有哪些'
        ]
        const randomText = mockTexts[Math.floor(Math.random() * mockTexts.length)] ?? mockTexts[0]!
        aiQuestion.value = randomText
        aiReply.value = `识别结果：${randomText}`
      }, 1500)
    } else {
      aiReply.value = `语音识别错误：${event.error}`
    }
    stopVoiceInput()
  }

  recognition.onend = () => {
    if (isRecording.value) {
      stopVoiceInput()
    }
  }

  recognition.start()
}

function stopVoiceInput() {
  if (recognition) {
    recognition.stop()
    recognition = null
  }
  isRecording.value = false
  voiceButtonText.value = '🎤 语音'
}

onMounted(async () => {
  const designPreview = import.meta.env.DEV && sessionStorage.getItem('guoyin:design-preview') === '1'
  if (!localStorage.getItem('username') && !designPreview) {
    router.replace('/login')
    return
  }
  timer = setInterval(nextSlide, 5000)
  window.addEventListener('resize', handleResize)
  try {
    const res = await fetchMusicTaxonomy()
    taxonomy.value = (res.data as Record<string, Record<string, string[]>>) || {}
    category.value = categories.value[0] || ''
    subcategory.value = subcategories.value[0] || ''
  } catch {
    taxonomy.value = {}
  }
  
  await nextTick()
  if (chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value)
    // 点击节点 → 展示基本信息
    chartInstance.on('click', (params: { dataType?: string; data?: unknown }) => {
      if (params.dataType !== 'node' || !params.data) return
      const d = params.data as Record<string, unknown>
      selectedNode.value = {
        name: (d.name as string) || '未知节点',
        type: (d.nodeType as string) || 'node',
        properties: (d.nodeProps as Record<string, unknown>) || {},
        relations: (d.nodeRelations as Array<{ rel: string; target: string }>) || [],
      }
    })
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  chartInstance?.resize()
}

/** 关闭节点信息卡片 */
function closeNodeInfo() {
  selectedNode.value = null
}

/** 把 properties 对象格式化为可读的键值对列表 */
function formatProps(props: Record<string, unknown>): Array<{ key: string; value: string }> {
  const result: Array<{ key: string; value: string }> = []
  for (const [k, v] of Object.entries(props)) {
    if (k === 'name') continue // 名称已在标题展示
    const val = typeof v === 'object' ? JSON.stringify(v) : String(v)
    result.push({ key: k, value: val })
  }
  return result
}
</script>

<template>
  <div class="home-page">
    <AppNav />

    <section class="carousel" :style="{ aspectRatio: activeAspect }">
      <button class="arrow left" type="button" @click="prevSlide">‹</button>
      <div class="slides" :style="{ transform: `translateX(-${carouselIndex * 100}%)` }">
        <div v-for="(s, n) in slides" :key="n" class="slide">
          <template v-if="s.video">
            <video
              class="carousel-video"
              :src="s.video"
              autoplay
              muted
              playsinline
              loop
            />
            <img
              v-if="s.overlay"
              class="carousel-overlay"
              :src="s.overlay"
            />
          </template>
          <img
            v-else
            :class="['slide-img', n >= 3 ? 'slide-img-offset' : '']"
            :src="s.image"
            alt="轮播图"
            @load="onSlideImgLoad($event, n)"
          />
        </div>
      </div>
      <button class="arrow right" type="button" @click="nextSlide">›</button>
      <div class="dots">
        <button
          v-for="i in slides.length"
          :key="i - 1"
          type="button"
          :class="{ active: i - 1 === carouselIndex }"
          @click="carouselIndex = i - 1"
        />
      </div>
      <div class="hero-copy">
        <p class="hero-kicker">声音里的中国</p>
        <h1 data-no-auto-translate>智解国音</h1>
        <p class="hero-subtitle">沉入中国音乐的深处，在旋律、情绪与文化之间自由漫游。</p>
        <div class="hero-actions">
          <button type="button" class="hero-primary" @click="router.push({ name: 'music-show', params: { category: '民歌' } })">
            开始聆听
          </button>
          <button type="button" class="hero-secondary" @click="router.push({ name: 'emotion' })">
            探索情绪场
          </button>
        </div>
      </div>
    </section>

    <section class="main-content">
      <div class="features-panel">
        <div class="features-header">
          <span class="features-line"></span>
          <h2>我们的功能</h2>
        </div>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 28v16"/>
                <path d="M28 28v16"/>
                <path d="M12 36c0-4.418 3.582-8 8-8"/>
                <path d="M28 36c0-4.418 3.582-8 8-8"/>
                <path d="M12 20c0-4.418 3.582-8 8-8"/>
                <path d="M28 20c0-4.418 3.582-8 8-8"/>
              </svg>
            </div>
            <h3>音乐展示</h3>
            <p>探索丰富的国风音乐库，涵盖民歌、戏曲、说唱、乐器四大类，每首音乐配有曲目资料和文化解读，让您领略中华传统音乐的魅力。</p>
            <button
              type="button"
              class="feature-more"
              @click="router.push({ name: 'music-show', params: { category: '民歌' } })"
            >更多 →</button>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="24" cy="24" r="16"/>
                <path d="M16 24c0-4.418 3.582-8 8-8"/>
                <path d="M24 24c0-4.418 3.582-8 8-8"/>
                <path d="M16 24c0 4.418 3.582 8 8 8"/>
                <path d="M24 24c0 4.418 3.582 8 8 8"/>
              </svg>
            </div>
            <h3>情绪分析</h3>
            <p>基于AI技术分析音乐情绪特征，可视化展示不同音乐类型的情绪分布，帮助您理解音乐与情感之间的深层关联。</p>
            <button type="button" class="feature-more" @click="router.push({ name: 'emotion' })">更多 →</button>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 36h40"/>
                <path d="M8 36v-8h8v-4H8v-8h32v8h-8v4h8v8"/>
                <path d="M16 20h-4"/>
                <path d="M36 20h4"/>
                <path d="M24 12v-8"/>
                <path d="M20 8h8"/>
              </svg>
            </div>
            <h3>国风意象评析</h3>
            <p>深入挖掘国风音乐中的文化意象，通过知识图谱展示音乐与传统文化符号的关联，解读背后蕴含的历史与美学内涵。</p>
            <button type="button" class="feature-more" @click="router.push({ name: 'imagery' })">更多 →</button>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="24" cy="20" r="12"/>
                <path d="M18 16h-4"/>
                <path d="M34 16h-4"/>
                <path d="M16 24h16"/>
                <path d="M20 28h8"/>
                <rect x="8" y="32" width="32" height="8" rx="2"/>
                <path d="M12 32v4"/>
                <path d="M36 32v4"/>
              </svg>
            </div>
            <h3>AI音乐生成</h3>
            <p>输入风格、情绪和主题，AI将为您量身定制国风音乐作品，体验人工智能与传统音乐的碰撞融合。</p>
            <button type="button" class="feature-more" @click="router.push({ name: 'ai-music' })">更多 →</button>
          </div>
        </div>
      </div>
      <div class="model-panel">
        <div class="model-wrapper">
          <ModelViewer :model-url="modelUrl" :auto-rotate="true" />
        </div>
      </div>
    </section>

    <section class="mid">
      <div v-light-tilt class="ai-panel light-tilt-card">
        <div class="ai-reply">
          <div class="ai-answer">{{ aiReply }}</div>
          <div v-if="qaMeta" class="qa-meta">
            <span :class="{ active: qaMeta.usedLlm }">
              {{ qaMeta.usedLlm ? '知识图谱检索 + 大模型生成' : '知识图谱检索回答' }}
            </span>
            <span>{{ qaMeta.nodes }} 个节点</span>
            <span>{{ qaMeta.relations }} 条关系</span>
          </div>
        </div>
        <div class="ai-ask chat-composer">
          <div class="chat-bot">
          <textarea
            v-model="aiQuestion"
            placeholder="向 AI 提问... ✦"
            :disabled="aiLoading"
            @keyup.enter="askAi"
          />
          </div>
          <div class="chat-options">
            <div class="chat-tags"><span>国风音乐</span><span>情绪解读</span></div>
            <div class="chat-actions">
              <button class="voice-btn" type="button" :disabled="aiLoading" @click="toggleVoiceInput">{{ voiceButtonText }}</button>
              <button class="chat-submit" type="button" :disabled="aiLoading" @click="askAi">{{ aiLoading ? '思考中' : '发送' }}</button>
            </div>
          </div>
        </div>
      </div>

      <div v-light-tilt class="graph-panel light-tilt-card">
        <div class="graph-heading">
          <div>
            <span class="graph-eyebrow">KNOWLEDGE GRAPH</span>
            <h3>中国传统音乐知识图谱</h3>
          </div>
          <div class="graph-meta" aria-label="图谱数据统计">
            <span><strong>{{ graphNodeCount }}</strong> 节点</span>
            <span><strong>{{ graphLinkCount }}</strong> 关系</span>
          </div>
        </div>
        <div class="graph-toolbar">
          <div class="graph-controls">
            <label>
              <span>音乐大类</span>
              <select v-model="category">
                <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
              </select>
            </label>
            <label>
              <span>细分类别</span>
              <select v-model="subcategory">
                <option v-for="s in subcategories" :key="s" :value="s">{{ s }}</option>
              </select>
            </label>
            <button type="button" :disabled="graphLoading" @click="confirmGraph">
              {{ graphLoading ? '加载中' : '查看图谱' }}
            </button>
          </div>
          <button class="graph-reset" type="button" title="恢复图谱视图" @click="resetGraphView">
            <span aria-hidden="true">↻</span>复位
          </button>
        </div>
        <div class="graph-display">
          <div class="graph-legend" aria-label="节点类型图例">
            <span v-for="item in graphLegend" :key="item.legend">
              <i :style="{ backgroundColor: item.color }"></i>{{ item.legend }}
            </span>
          </div>
          <div ref="chartContainer" class="chart-container"></div>
          <p v-if="graphStatus" class="graph-status">{{ graphStatus }}</p>
          <!-- 点击节点后展示的信息卡片 -->
          <div v-if="selectedNode" class="node-info-card">
            <div class="node-info-header">
              <span class="node-info-title">{{ selectedNode.name }}</span>
              <span class="node-info-type">{{ selectedNode.type }}</span>
              <button type="button" class="node-info-close" @click="closeNodeInfo">✕</button>
            </div>
            <div class="node-info-body">
              <div v-if="formatProps(selectedNode.properties).length" class="node-info-section">
                <p class="node-info-section-title">基本属性</p>
                <div v-for="item in formatProps(selectedNode.properties)" :key="item.key" class="node-info-prop">
                  <span class="prop-key">{{ item.key }}</span>
                  <span class="prop-val">{{ item.value }}</span>
                </div>
              </div>
              <div v-if="selectedNode.relations.length" class="node-info-section">
                <p class="node-info-section-title">关联关系（{{ selectedNode.relations.length }}）</p>
                <div v-for="(r, i) in selectedNode.relations" :key="i" class="node-info-rel">
                  <span class="rel-type">{{ r.rel }}</span>
                  <span class="rel-arrow">→</span>
                  <span class="rel-target">{{ r.target }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <footer class="footer">
      <div>
        <p>联系邮箱：contact@guofeng-music.demo</p>
        <p>联系电话：400-000-0000</p>
      </div>
      <div>
        <p>地址：中国 · 演示城市</p>
        <p>© 2026 国风音乐平台 · 仅供学习演示</p>
      </div>
    </footer>

    <RouterView />
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  color: var(--gf-text, #411c35);
  position: relative;
}

.carousel {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 70vh;
  overflow: hidden;
  background: var(--gf-blue, #426aae);
  transition: aspect-ratio 0.4s ease;
}

.slides {
  display: flex;
  height: 100%;
  transition: transform 0.5s ease;
}

.slide {
  min-width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f6d9c9;
  color: var(--gf-text, #411c35);
  font-size: 1.2rem;
  position: relative;
  overflow: hidden;
}

.slide-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.slide-img-offset {
  object-position: center 20%;
}

.carousel-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.carousel-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: 100% center;
  pointer-events: none;
  transform: translateX(3%);
}

.arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  font-size: 1.6rem;
  cursor: pointer;
}

.arrow.left {
  left: 12px;
}

.arrow.right {
  right: 12px;
}

.dots {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}

.dots button {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.5);
  cursor: pointer;
}

.dots button.active {
  background: linear-gradient(135deg, var(--gf-blush, #ec7696), var(--gf-maroon, #801d3a));
  box-shadow: 0 0 8px rgba(245, 222, 179, 0.6);
  transform: scale(1.2);
}

.mid {
  display: grid;
  grid-template-columns: 4fr 6fr;
  gap: 1rem;
  padding: 1.25rem;
  flex: 1;
}

.ai-panel {
  display: flex;
  flex-direction: column;
  min-height: 320px;
  background: #ffffff;
  border: 1px solid var(--gf-border, #ddd6c8);
}

.ai-reply {
  flex: 6;
  padding: 0.85rem;
  overflow: auto;
  line-height: 1.55;
  border-bottom: 1px solid var(--gf-border, #ddd6c8);
  white-space: pre-wrap;
  font-size: 0.92rem;
  background: #ffffff;
}

.ai-answer {
  min-height: 120px;
}

.qa-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(86, 111, 102, 0.2);
}

.qa-meta span {
  padding: 0.24rem 0.5rem;
  border: 1px solid #c7d4ce;
  border-radius: 3px;
  color: #697a74;
  background: rgba(255, 255, 255, 0.56);
  font-size: 0.68rem;
}

.qa-meta span.active {
  border-color: #89aa9d;
  color: #315f55;
  background: #dceae4;
}

.ai-ask {
  flex: 1;
  display: flex;
  gap: 0.5rem;
  padding: 0.6rem;
  align-items: center;
  background: #ffffff;
}

.ai-ask input {
  flex: 1;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--gf-border, #ddd6c8);
  outline: none;
}

.ai-ask button,
.graph-controls button {
  padding: 0.55rem 1rem;
  border: none;
  background: var(--gf-maroon, #801d3a);
  color: #fff;
  cursor: pointer;
}

.ai-ask .voice-btn {
  background: var(--gf-green, #3d723a);
}

.graph-panel {
  display: flex;
  flex-direction: column;
  min-height: 590px;
  border: 1px solid #cfd9d4;
  background: #f8faf7;
  overflow: hidden;
}

.graph-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.15rem 1.25rem 0.9rem;
  background: #f8faf7;
}

.graph-eyebrow {
  display: block;
  margin-bottom: 0.25rem;
  color: #8d6e47;
  font-size: 0.68rem;
  font-weight: 700;
}

.graph-heading h3 {
  margin: 0;
  color: #253a37;
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 1.18rem;
  font-weight: 700;
}

.graph-meta {
  display: flex;
  gap: 0.9rem;
  color: #71807b;
  font-size: 0.76rem;
}

.graph-meta strong {
  color: #3b5b55;
  font-size: 1rem;
}

.graph-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.8rem 1.25rem;
  border-top: 1px solid #e1e7e3;
  border-bottom: 1px solid #d9e1dd;
  background: #edf2ef;
}

.graph-controls {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.graph-controls label {
  display: grid;
  gap: 0.28rem;
  color: #64736e;
  font-size: 0.7rem;
}

.graph-controls select {
  min-width: 128px;
  height: 36px;
  padding: 0 2rem 0 0.7rem;
  border: 1px solid #c6d1cc;
  border-radius: 4px;
  background: #fff;
  color: #2f4541;
}

.graph-controls button,
.graph-reset {
  height: 36px;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}

.graph-controls button {
  padding: 0 1rem;
  background: #3f7165;
  color: #fff;
}

.graph-controls button:hover {
  background: #315f55;
}

.graph-controls button:disabled {
  cursor: wait;
  opacity: 0.62;
}

.graph-reset {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0 0.75rem;
  border: 1px solid #c9d3cf;
  background: #fff;
  color: #526661;
}

.graph-reset:hover {
  border-color: #93aaa3;
  color: #315f55;
}

.graph-display {
  flex: 1;
  position: relative;
  overflow: hidden;
  padding: 0;
  color: #566964;
  font-size: 0.85rem;
  background-color: #fbfcfa;
  background-image: radial-gradient(circle, rgba(71, 105, 96, 0.12) 1px, transparent 1px);
  background-size: 22px 22px;
}

.graph-legend {
  position: absolute;
  z-index: 3;
  top: 14px;
  left: 50%;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.9rem;
  width: max-content;
  max-width: calc(100% - 32px);
  padding: 0.45rem 0.7rem;
  transform: translateX(-50%);
  border: 1px solid rgba(206, 216, 211, 0.8);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 5px 18px rgba(45, 72, 65, 0.08);
  backdrop-filter: blur(8px);
  pointer-events: none;
}

.graph-legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: #56635f;
  font-size: 0.7rem;
  white-space: nowrap;
}

.graph-legend i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px #fff;
}

.chart-container {
  width: 100%;
  height: 500px;
  min-height: 500px;
}

.graph-status {
  position: absolute;
  right: 12px;
  bottom: 10px;
  margin: 0;
  padding: 0.35rem 0.55rem;
  border: 1px solid rgba(205, 216, 211, 0.82);
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.82);
  color: #71807b;
  font-size: 0.7rem;
  pointer-events: none;
}

/* 节点信息卡片 */
.node-info-card {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 240px;
  max-height: 280px;
  overflow-y: auto;
  background: rgba(255, 253, 249, 0.96);
  border: 1px solid var(--gf-border, #ddd6c8);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  z-index: 10;
  font-size: 0.82rem;
}

.node-info-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--gf-border, #f0d9c0);
  background: var(--gf-pink-light, #f0a1a8);
  border-radius: 6px 6px 0 0;
}

.node-info-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--gf-blue-deep, #29509b);
  flex: 1;
}

.node-info-type {
  font-size: 0.7rem;
  color: var(--gf-text-muted, #8a8378);
  background: var(--gf-pink-light, #f0a1a8);
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
}

.node-info-close {
  border: none;
  background: none;
  color: var(--gf-text-muted, #8a8378);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0;
  line-height: 1;
}

.node-info-close:hover {
  color: var(--gf-maroon, #801d3a);
}

.node-info-body {
  padding: 0.6rem 0.75rem;
}

.node-info-section {
  margin-bottom: 0.6rem;
}

.node-info-section:last-child {
  margin-bottom: 0;
}

.node-info-section-title {
  margin: 0 0 0.35rem;
  font-size: 0.74rem;
  color: var(--gf-text-muted, #8a8378);
  font-weight: 500;
}

.node-info-prop {
  display: flex;
  gap: 0.4rem;
  padding: 0.15rem 0;
  line-height: 1.4;
}

.prop-key {
  color: var(--gf-text-muted, #8a8378);
  min-width: 50px;
  flex-shrink: 0;
}

.prop-val {
  color: var(--gf-text, #3d3a35);
  word-break: break-all;
}

.node-info-rel {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.15rem 0;
  line-height: 1.4;
}

.rel-type {
  color: var(--gf-blue, #426aae);
  font-size: 0.76rem;
  flex-shrink: 0;
}

.rel-arrow {
  color: var(--gf-border, #ddd6c8);
  font-size: 0.76rem;
}

.rel-target {
  color: var(--gf-text, #3d3a35);
  word-break: break-all;
}

.main-content {
  display: grid;
  grid-template-columns: 4fr 1fr;
  grid-template-rows: auto 1fr;
  gap: 1rem;
  padding: 1.5rem 3rem;
  width: 100%;
}

.features-panel {
  display: contents;
  background: linear-gradient(to bottom, rgba(101, 42, 35, 0.95) 0%, rgba(128, 29, 58, 0.7) 50%, rgba(142, 59, 47, 0.3) 100%);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 1.75rem;
  border: 1px solid rgba(254, 235, 192, 0.15);
}

.features-header {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.features-line {
  width: 2px;
  height: 2rem;
  background: #ec7696;
}

.features-header h2 {
  margin: 0;
  font-size: 2.2rem;
  color: #feebc0;
  font-weight: 600;
}

.features-grid {
  grid-column: 1;
  grid-row: 2;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(254, 235, 192, 0.15);
  padding: 1.25rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.feature-icon {
  width: 3.2rem;
  height: 3.2rem;
  margin-bottom: 0.75rem;
  color: #ec7696;
}

.feature-card h3 {
  margin: 0 0 0.5rem;
  font-size: 1.4rem;
  color: #feebc0;
  font-weight: 600;
}

.feature-card p {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  color: rgba(254, 235, 192, 0.85);
  line-height: 1.6;
}

.feature-more {
  align-self: flex-start;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 0.88rem;
  color: #6ba368;
  cursor: pointer;
}

.feature-more:hover {
  color: #8bc988;
}

.model-panel {
  grid-column: 2;
  grid-row: 2;
  min-height: 0;
  background: transparent;
  border-radius: 12px;
  padding: 0;
  border: none;
}

.model-wrapper {
  height: 100%;
  min-height: 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

@media (max-width: 1000px) {
  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }

  .features-panel {
    display: block;
  }

  .model-panel {
    grid-column: 1;
    grid-row: auto;
  }

  .model-wrapper {
    min-height: 500px;
  }
}

.footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 1.25rem 1.5rem;
  background: var(--gf-navy, #181e38);
  color: var(--gf-cream, #feebc0);
  font-size: 0.88rem;
}

.footer p {
  margin: 0.25rem 0;
}

@media (max-width: 900px) {
  .mid {
    grid-template-columns: 1fr;
  }
}
</style>
