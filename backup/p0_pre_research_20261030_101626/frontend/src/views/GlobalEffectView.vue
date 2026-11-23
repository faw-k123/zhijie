<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import AppNav from '@/components/AppNav.vue'
import {
  fetchGlobalComments,
  fetchMusicTaxonomy,
} from '@/api/dataDisplay'
import { fetchPropagationAnalysis } from '@/api/propagation'

const taxonomy = ref<Record<string, Record<string, string[]>>>({})
const category = ref('')
const subcategory = ref('')
const songTitle = ref('')

const categories = computed(() => Object.keys(taxonomy.value))
const subNames = computed(() => Object.keys(taxonomy.value[category.value] || {}))
const songs = computed(() => taxonomy.value[category.value]?.[subcategory.value] || [])

const allComments = ref<{ id: number; text: string; likes?: number }[]>([])
const batchIndex = ref(0)
const spreadText = ref('请选择歌曲后加载传播数据分析')
const anomalyText = ref('请选择歌曲后加载传播异常分析')

const visibleComments = computed(() => {
  const start = batchIndex.value * 7
  const slice = allComments.value.slice(start, start + 7)
  if (slice.length < 7 && allComments.value.length) {
    return [...slice, ...allComments.value.slice(0, Math.max(0, 7 - slice.length))]
  }
  return slice
})

let timer: ReturnType<typeof setInterval> | null = null

watch(category, () => {
  subcategory.value = subNames.value[0] || ''
})

watch([category, subcategory], () => {
  songTitle.value = songs.value[0] || ''
})

/** 评论：模块一；右侧分析：模块三 */
async function loadForSong() {
  if (!category.value || !subcategory.value || !songTitle.value) return
  try {
    const [cRes, pRes] = await Promise.all([
      fetchGlobalComments(category.value, subcategory.value, songTitle.value),
      fetchPropagationAnalysis({
        category: category.value,
        subcategory: subcategory.value,
        song_title: songTitle.value,
      }),
    ])
    const cData = cRes.data as { comments?: { id: number; text: string; likes?: number }[] }
    allComments.value = cData?.comments || []
    batchIndex.value = 0
    const pData = pRes.data as {
      spread_analysis?: { text?: string; metrics?: unknown }
      anomaly_prediction?: { text?: string }
    }
    spreadText.value =
      pData?.spread_analysis?.text ||
      JSON.stringify(pData?.spread_analysis || pData, null, 2)
    anomalyText.value =
      pData?.anomaly_prediction?.text ||
      JSON.stringify(pData?.anomaly_prediction || {}, null, 2)
  } catch (e: unknown) {
    const err = e as { message?: string }
    allComments.value = []
    spreadText.value = `加载失败：${err.message || '网络错误'}`
    anomalyText.value = spreadText.value
  }
}

watch(songTitle, () => {
  loadForSong()
})

onMounted(async () => {
  try {
    const res = await fetchMusicTaxonomy()
    taxonomy.value = (res.data as Record<string, Record<string, string[]>>) || {}
    // 默认：大类第一个 → 小类第一个 → 歌曲第一个
    category.value = categories.value[0] || ''
    subcategory.value = subNames.value[0] || ''
    songTitle.value = songs.value[0] || ''
  } catch {
    taxonomy.value = {}
  }
  timer = setInterval(() => {
    const totalBatches = Math.max(1, Math.ceil(allComments.value.length / 7))
    batchIndex.value = (batchIndex.value + 1) % totalBatches
  }, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const spherePositions = [
  { x: 50, y: 12 },
  { x: 82, y: 32 },
  { x: 78, y: 68 },
  { x: 50, y: 88 },
  { x: 22, y: 68 },
  { x: 18, y: 32 },
  { x: 50, y: 50 },
]
</script>

<template>
  <div class="page editorial-page global-page">
    <AppNav />
    <div class="layout">
      <section class="left">
        <div class="filters">
          <select v-model="category">
            <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
          </select>
          <select v-model="subcategory">
            <option v-for="s in subNames" :key="s" :value="s">{{ s }}</option>
          </select>
          <select v-model="songTitle">
            <option v-for="song in songs" :key="song" :value="song">{{ song }}</option>
          </select>
        </div>

        <div class="sphere-wrap">
          <div class="sphere-core" />
          <div
            v-for="(c, i) in visibleComments"
            :key="`${batchIndex}-${c.id}-${i}`"
            class="comment-bubble"
            :class="{ center: i === 6 }"
            :style="{ left: `${spherePositions[i]?.x || 50}%`, top: `${spherePositions[i]?.y || 50}%` }"
          >
            {{ c.text }}
          </div>
        </div>
      </section>

      <section class="right">
        <div class="panel">
          <h2>传播数据分析</h2>
          <pre>{{ spreadText }}</pre>
        </div>
        <div class="panel">
          <h2>传播异常分析</h2>
          <pre>{{ anomalyText }}</pre>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
}

.layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 1.25rem;
  min-height: calc(100vh - 56px);
}

.left,
.right {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  min-height: 560px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  padding: 0.85rem;
  background: #fffdf9;
  border: 1px solid #ddd2c4;
}

select {
  padding: 0.45rem 0.6rem;
  border: 1px solid #cfc5b8;
  min-width: 120px;
  background: #fff;
}

.sphere-wrap {
  position: relative;
  flex: 1;
  min-height: 460px;
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  overflow: hidden;
}

.sphere-core {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 220px;
  height: 220px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.55), transparent 45%),
    radial-gradient(circle at 50% 50%, rgba(139, 58, 42, 0.18), rgba(31, 42, 56, 0.35));
}

.comment-bubble {
  position: absolute;
  transform: translate(-50%, -50%);
  max-width: 160px;
  padding: 0.55rem 0.7rem;
  background: rgba(255, 253, 249, 0.95);
  border: 1px solid #e0d3c0;
  border-radius: 12px;
  font-size: 0.78rem;
  line-height: 1.4;
  color: #3d2f24;
  animation: fadeIn 0.45s ease;
}

.comment-bubble.center {
  max-width: 140px;
  background: #8b3a2a;
  color: #fff;
  border-color: #8b3a2a;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.panel {
  flex: 1;
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  padding: 1rem 1.1rem;
  overflow: auto;
}

.panel h2 {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
  color: #3d2f24;
}

.panel pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  color: #5a4a3a;
  line-height: 1.6;
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
