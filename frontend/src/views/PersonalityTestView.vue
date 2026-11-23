<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { personalityQuestions, dimensionNames } from '@/data/music'

interface Question {
  id: number
  text: string
  dimension: string
  options: string[]
}

interface CircleResult {
  name: string
  similarity: number
  factors: number[]
}

const questions = ref<Question[]>([])
const current = ref(0)
const answers = ref<Record<number, number>>({})
const submitted = ref(false)
const loading = ref(false)
const loadingProfile = ref(true)
const errorMsg = ref('')
const userVector = ref<number[]>([])
const matchedCircles = ref<CircleResult[]>([])
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const total = computed(() => questions.value.length)
const question = computed(() => questions.value[current.value])
const isLast = computed(() => current.value === total.value - 1)
const allAnswered = computed(() => Object.keys(answers.value).length === total.value)

function getUserId(): string {
  return localStorage.getItem('user_id') || '1004'
}

function tryRenderRadar() {
  if (submitted.value && userVector.value.length > 0 && chartRef.value) {
    renderRadar()
  }
}

async function fetchProfile() {
  const user_id = getUserId()
  try {
    const res = await fetch(`/api/fun/cultural-circle/profile/?user_id=${user_id}`)
    const data = await res.json()
    if (data.success && data.data?.has_test) {
      userVector.value = data.data.user_vector
      matchedCircles.value = data.data.matched_circles
      submitted.value = true
    }
  } catch {
    errorMsg.value = '获取测试结果失败'
  } finally {
    loadingProfile.value = false
  }
}

onMounted(async () => {
  questions.value = personalityQuestions
  await fetchProfile()
})

watch([submitted, loadingProfile], async ([sub, loading]) => {
  if (sub && !loading) {
    await nextTick()
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        tryRenderRadar()
      })
    })
  }
})

function selectOption(index: number) {
  if (question.value) {
    answers.value[question.value.id] = index + 1
  }
}

function prev() {
  if (current.value > 0) current.value -= 1
}

function next() {
  if (current.value < total.value - 1) current.value += 1
}

async function submit() {
  if (!allAnswered.value) return
  loading.value = true
  const user_id = getUserId()
  try {
    const res = await fetch('/api/fun/cultural-circle/submit/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id,
        answers: answers.value,
      }),
    })
    const data = await res.json()
    if (data.success && data.data) {
      userVector.value = data.data.user_vector
      matchedCircles.value = data.data.matched_circles
      submitted.value = true
      await nextTick()
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          tryRenderRadar()
        })
      })
    } else {
      errorMsg.value = data.message || '提交失败'
    }
  } catch (e: unknown) {
    const err = e as { message?: string }
    errorMsg.value = `提交失败：${err.message || '网络错误'}`
  } finally {
    loading.value = false
  }
}

function disposeChart() {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

function renderRadar() {
  if (!chartRef.value) {
    disposeChart()
    return
  }

  const rect = chartRef.value.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) {
    disposeChart()
    return
  }

  disposeChart()

  chartInstance = echarts.init(chartRef.value)
  const indicator = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7'].map((f) => ({
    name: dimensionNames[f],
    max: 100,
  }))
  chartInstance.setOption({
    radar: {
      indicator,
      shape: 'polygon',
      splitNumber: 5,
      axisName: { color: '#5a4a3a', fontSize: 12 },
      splitLine: { lineStyle: { color: '#e0d3c0' } },
      splitArea: { areaStyle: { color: ['#faf6f0', '#f5ede0'] } },
      axisLine: { lineStyle: { color: '#d0c5b5' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: userVector.value,
            name: '文化圈层匹配',
            areaStyle: { color: 'rgba(139, 58, 42, 0.25)' },
            lineStyle: { color: '#8b3a2a', width: 2 },
            itemStyle: { color: '#8b3a2a' },
          },
        ],
      },
    ],
  })

  setTimeout(() => {
    chartInstance?.resize()
  }, 100)
}

onUnmounted(() => {
  disposeChart()
})

function resetTest() {
  submitted.value = false
  current.value = 0
  answers.value = {}
  userVector.value = []
  matchedCircles.value = []
  errorMsg.value = ''
}
</script>

<template>
  <div class="page">
    <!-- 加载中 -->
    <div v-if="loadingProfile" class="center-msg">
      <p>加载中...</p>
    </div>

    <!-- 错误 -->
    <div v-else-if="errorMsg" class="center-msg">
      <p class="error">{{ errorMsg }}</p>
    </div>

    <!-- 问卷阶段 -->
    <div v-else-if="!submitted" class="test-stage">
      <div class="card">
        <div class="progress-bar">
          <div class="fill" :style="{ width: `${((current + 1) / total) * 100}%` }" />
        </div>
        <p class="progress-text">第 {{ current + 1 }} / {{ total }} 题</p>
        <p class="dimension-tag">{{ dimensionNames[question?.dimension || 'F1'] }}</p>

        <h2>{{ question?.text || '' }}</h2>
        <div class="options">
          <button
            v-for="(opt, idx) in question?.options"
            :key="idx"
            type="button"
            :class="{ active: question && answers[question.id] === idx + 1 }"
            @click="selectOption(idx)"
          >
            <span class="opt-score">{{ idx + 1 }}</span>
            <span class="opt-label">{{ opt }}</span>
          </button>
        </div>

        <div class="nav-row">
          <button type="button" class="ghost" :disabled="current === 0" @click="prev">上一题</button>
          <span class="answered-count">{{ Object.keys(answers).length }} / {{ total }} 已答</span>
          <button
            v-if="isLast"
            type="button"
            class="primary"
            :disabled="!allAnswered || loading"
            @click="submit"
          >
            {{ loading ? '分析中...' : '提交' }}
          </button>
          <button v-else type="button" class="primary" :disabled="!question || !answers[question.id]" @click="next">下一题</button>
        </div>
      </div>
    </div>

    <!-- 结果阶段 -->
    <div v-else class="result-stage">
      <div class="result-header">
        <h1>文化圈层匹配结果</h1>
        <p class="subtitle">基于你的回答，我们为你匹配了最契合的文化圈层</p>
      </div>

      <div class="result-grid">
        <div class="chart-card">
          <h3>七维得分画像</h3>
          <div ref="chartRef" class="chart" />
          <div class="scores-list">
            <div v-for="(dim, idx) in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']" :key="dim" class="score-item">
              <span>{{ dimensionNames[dim] }}</span>
              <span class="score-val">{{ userVector[idx] }}</span>
            </div>
          </div>
        </div>

        <div class="circles-card">
          <h3>匹配的文化圈层</h3>
          <div class="circle-list">
            <div v-for="(circle, idx) in matchedCircles" :key="circle.name" class="circle-item" :class="{ top: idx === 0 }">
              <div class="circle-rank">#{{ idx + 1 }}</div>
              <div class="circle-info">
                <h4>{{ circle.name }}</h4>
                <div class="similarity-bar">
                  <div class="similarity-fill" :style="{ width: `${circle.similarity}%` }" />
                </div>
                <span class="similarity-text">匹配度 {{ circle.similarity }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="action-row">
        <button type="button" class="primary" @click="resetTest">重新测试</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100%;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(139, 58, 42, 0.12), transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(31, 42, 56, 0.12), transparent 45%),
    #e8e0d4;
}

.center-msg {
  min-height: calc(100vh - 100px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5a4a3a;
}

.error {
  color: #c0392b;
}

/* 问卷阶段 */
.test-stage {
  min-height: calc(100vh - 100px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.card {
  width: min(650px, 100%);
  background: rgba(255, 253, 249, 0.97);
  border: 1px solid #ddd2c4;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
  padding: 1.5rem 1.4rem 1.2rem;
}

.progress-bar {
  height: 8px;
  background: #eee4d8;
  border-radius: 4px;
  overflow: hidden;
}

.fill {
  height: 100%;
  background: linear-gradient(90deg, #8b3a2a, #c47a4a);
  transition: width 0.25s ease;
}

.progress-text {
  margin: 0.55rem 0 0.4rem;
  font-size: 0.85rem;
  color: #8a7a6a;
}

.dimension-tag {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  background: rgba(139, 58, 42, 0.1);
  border: 1px solid rgba(139, 58, 42, 0.2);
  color: #8b3a2a;
  font-size: 0.82rem;
  margin: 0 0 1rem;
}

h2 {
  margin: 0 0 1rem;
  font-size: 1.15rem;
  color: #2f2a26;
  line-height: 1.5;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.options button {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  text-align: left;
  padding: 0.7rem 0.9rem;
  border: 1px solid #e0d3c0;
  background: #faf6f0;
  cursor: pointer;
  color: #3d2f24;
  transition: all 0.15s;
}

.options button:hover {
  border-color: #c4a87a;
}

.options button.active {
  border-color: #8b3a2a;
  background: rgba(139, 58, 42, 0.08);
  color: #8b3a2a;
}

.opt-score {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e8dccb;
  font-size: 0.85rem;
  font-weight: 600;
  flex-shrink: 0;
  margin-top: 2px;
}

.options button.active .opt-score {
  background: #8b3a2a;
  color: #fff;
}

.opt-label {
  font-size: 0.9rem;
  line-height: 1.4;
}

.nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.answered-count {
  font-size: 0.82rem;
  color: #8a7a6a;
}

.ghost,
.primary {
  padding: 0.55rem 1.1rem;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
}

.ghost {
  background: transparent;
  border: 1px solid #cfc5b8;
  color: #5a4a3a;
}

.ghost:disabled,
.primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.primary {
  background: #8b3a2a;
  color: #fff;
}

/* 结果阶段 */
.result-stage {
  padding: 1.5rem;
  max-width: 1000px;
  margin: 0 auto;
}

.result-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.result-header h1 {
  margin: 0 0 0.5rem;
  font-size: 1.6rem;
  color: #2f2a26;
}

.subtitle {
  margin: 0;
  color: #7a6a5a;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .result-grid {
    grid-template-columns: 1fr;
  }
}

.chart-card,
.circles-card {
  background: rgba(255, 253, 249, 0.95);
  border: 1px solid #ddd2c4;
  padding: 1.5rem;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
}

h3 {
  margin: 0 0 1rem;
  font-size: 1.15rem;
  color: #8b3a2a;
}

.chart {
  width: 100%;
  height: 280px;
}

.scores-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 1rem;
}

.score-item {
  display: flex;
  justify-content: space-between;
  padding: 0.35rem 0.5rem;
  background: #faf6f0;
  border: 1px solid #ede0d0;
  font-size: 0.88rem;
}

.score-val {
  font-weight: 700;
  color: #8b3a2a;
}

.circle-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.circle-item {
  display: flex;
  gap: 0.8rem;
  padding: 0.7rem;
  background: #faf6f0;
  border: 1px solid #ede0d0;
}

.circle-item.top {
  border-color: #8b3a2a;
  background: rgba(139, 58, 42, 0.06);
}

.circle-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e8dccb;
  font-size: 0.85rem;
  font-weight: 700;
  flex-shrink: 0;
  color: #5a4a3a;
}

.circle-item.top .circle-rank {
  background: #8b3a2a;
  color: #fff;
}

.circle-info h4 {
  margin: 0 0 0.4rem;
  font-size: 0.95rem;
  color: #2f2a26;
}

.similarity-bar {
  height: 6px;
  background: #e8dccb;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.similarity-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b3a2a, #c47a4a);
  transition: width 0.3s ease;
}

.similarity-text {
  font-size: 0.82rem;
  color: #7a6a5a;
}

.action-row {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
}
</style>
