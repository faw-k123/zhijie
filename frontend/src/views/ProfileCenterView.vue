<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import AppNav from '@/components/AppNav.vue'
import { fetchProfile } from '@/api/personalization'

interface Recommendation {
  id: number
  title: string
  genre: string
  audio_url: string
  cover_url: string
}

interface ProfileData {
  has_profile: boolean
  username?: string
  scores?: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }
  tags?: string[]
  description?: string
  update_time?: string
  recommend_directions?: string[]
  recommendations?: Recommendation[]
}

const router = useRouter()
const profile = ref<ProfileData | null>(null)
const loading = ref(true)
const chartRef = ref<HTMLDivElement | null>(null)
const audioEl = ref<HTMLAudioElement | null>(null)
const playingId = ref<number | null>(null)

// 我的标签（基于人格维度生成的兴趣标签）
const interestTags = ref<string[]>([])

onMounted(async () => {
  let user_id = localStorage.getItem('user_id') || ''
  if (!user_id) {
    user_id = '1004'
  }
  try {
    const res = await fetchProfile(user_id)
    profile.value = res.data as ProfileData
    if (profile.value?.has_profile && profile.value.scores) {
      interestTags.value = buildInterestTags(profile.value.scores)
    }
  } catch {
    // 忽略
  } finally {
    loading.value = false
  }
})

watch(() => profile.value?.scores, async (newScores) => {
  if (newScores) {
    await nextTick()
    renderRadar()
  }
})

function buildInterestTags(scores: ProfileData['scores']): string[] {
  if (!scores) return []
  const tags: string[] = []
  if (scores.openness >= 70) tags.push('探索', '创新国风', '民族融合')
  if (scores.conscientiousness >= 70) tags.push('古曲', '文人音乐', '非遗')
  if (scores.extraversion >= 70) tags.push('鼓乐', '舞蹈音乐')
  if (scores.agreeableness >= 70) tags.push('丝竹', '山水意境')
  if (scores.neuroticism >= 70) tags.push('静心', '舒缓')
  if (scores.openness >= 70 && scores.agreeableness >= 70) tags.push('传统文化')
  if (!tags.length) tags.push('均衡', '传统音乐')
  return tags
}

function renderRadar() {
  if (!chartRef.value || !profile.value?.scores) return
  const s = profile.value.scores
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: {},
    radar: {
      indicator: [
        { name: '开放性', max: 100 },
        { name: '责任心', max: 100 },
        { name: '外向性', max: 100 },
        { name: '宜人性', max: 100 },
        { name: '神经质', max: 100 },
      ],
      shape: 'polygon',
      splitNumber: 5,
      axisName: { color: '#5a4a3a', fontSize: 13 },
      splitLine: { lineStyle: { color: '#e0d3c0' } },
      splitArea: { areaStyle: { color: ['#faf6f0', '#f5ede0'] } },
      axisLine: { lineStyle: { color: '#d0c5b5' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [s.openness, s.conscientiousness, s.extraversion, s.agreeableness, s.neuroticism],
            name: '人格画像',
            areaStyle: { color: 'rgba(139, 58, 42, 0.25)' },
            lineStyle: { color: '#8b3a2a', width: 2 },
            itemStyle: { color: '#8b3a2a' },
          },
        ],
      },
    ],
  })
  window.addEventListener('resize', () => chart.resize())
}

function togglePlay(song: Recommendation) {
  if (playingId.value === song.id) {
    audioEl.value?.pause()
    playingId.value = null
    return
  }
  playingId.value = song.id
  if (song.audio_url && audioEl.value) {
    audioEl.value.src = song.audio_url
    audioEl.value.play().catch(() => undefined)
  }
}

function goTest() {
  router.push('/personality-test')
}

function goBack() {
  router.push('/personality-test')
}
</script>

<template>
  <div class="page">
    <AppNav />
    <audio ref="audioEl" preload="none" @ended="playingId = null" />

    <!-- 加载中 -->
    <div v-if="loading" class="center-msg">
      <p>画像加载中...</p>
    </div>

    <!-- 未完成测试 -->
    <div v-else-if="!profile?.has_profile" class="center-msg">
      <div class="empty-card">
        <div class="empty-icon">?</div>
        <h3>尚未生成画像</h3>
        <p>完成人格测试后，这里将展示你的专属画像</p>
        <button type="button" class="primary" @click="goTest">前往人格测试</button>
      </div>
    </div>

    <!-- 画像中心 -->
    <div v-else class="profile-center">
      <!-- 返回栏 -->
      <div class="back-bar">
        <button type="button" class="back-btn" @click="goBack">
          <span class="back-icon">←</span>
          <span>返回人格测试</span>
        </button>
      </div>

      <!-- 顶部：用户信息卡片 -->
      <div class="user-card">
        <div class="avatar">{{ (profile.username || 'U').charAt(0).toUpperCase() }}</div>
        <div class="user-info">
          <h2>{{ profile.username }}</h2>
          <div class="user-tags">
            <span v-for="tag in profile.tags" :key="tag" class="user-tag">{{ tag }}</span>
          </div>
          <p class="update-time" v-if="profile.update_time">更新于 {{ profile.update_time }}</p>
        </div>
      </div>

      <!-- 中间：雷达图 + 我的标签 -->
      <div class="mid-grid">
        <div class="card chart-card">
          <h3>人格画像</h3>
          <div ref="chartRef" class="chart" />
          <div class="scores-list">
            <div class="score-item">
              <span>开放性</span>
              <span class="score-val">{{ profile.scores?.openness }}</span>
            </div>
            <div class="score-item">
              <span>责任心</span>
              <span class="score-val">{{ profile.scores?.conscientiousness }}</span>
            </div>
            <div class="score-item">
              <span>外向性</span>
              <span class="score-val">{{ profile.scores?.extraversion }}</span>
            </div>
            <div class="score-item">
              <span>宜人性</span>
              <span class="score-val">{{ profile.scores?.agreeableness }}</span>
            </div>
            <div class="score-item">
              <span>神经质</span>
              <span class="score-val">{{ profile.scores?.neuroticism }}</span>
            </div>
          </div>
        </div>

        <div class="card tags-card">
          <h3>我的标签</h3>
          <div class="tags-cloud">
            <span v-for="t in interestTags" :key="t" class="interest-tag">✔ {{ t }}</span>
          </div>
          <p class="profile-desc">{{ profile.description }}</p>
        </div>
      </div>

      <!-- 推荐方向 -->
      <div class="card direction-card">
        <h3>推荐方向</h3>
        <div class="directions">
          <span v-for="d in profile.recommend_directions" :key="d" class="direction-item">{{ d }}</span>
        </div>
      </div>

      <!-- 推荐音乐 -->
      <div class="card recommend-card">
        <h3>为你推荐</h3>
        <div class="song-grid">
          <div
            v-for="song in profile.recommendations"
            :key="song.id"
            class="song-card"
            :class="{ playing: playingId === song.id }"
            @click="togglePlay(song)"
          >
            <div class="song-cover">
              <img v-if="song.cover_url" :src="song.cover_url" :alt="song.title" />
              <div v-else class="cover-placeholder">{{ song.genre }}</div>
              <div class="play-icon">{{ playingId === song.id ? '⏸' : '▶' }}</div>
            </div>
            <div class="song-info">
              <p class="song-title">{{ song.title }}</p>
              <p class="song-genre">{{ song.genre }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
}

.center-msg {
  min-height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-card {
  text-align: center;
  padding: 2rem;
}

.empty-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 1rem;
  border-radius: 50%;
  background: rgba(139, 58, 42, 0.1);
  color: #8b3a2a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

.empty-card h3 {
  margin: 0 0 0.5rem;
  color: #5a4a3a;
}

.empty-card p {
  color: #8a7a6a;
  margin: 0 0 1.25rem;
}

/* 画像中心 */
.profile-center {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* 返回栏 */
.back-bar {
  margin-bottom: 1rem;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.9rem;
  background: rgba(255, 253, 249, 0.95);
  border: 1px solid #ddd2c4;
  color: #5a4a3a;
  cursor: pointer;
  font-size: 0.88rem;
  transition: all 0.15s;
}

.back-btn:hover {
  border-color: #8b3a2a;
  color: #8b3a2a;
}

.back-icon {
  font-size: 1.1rem;
  font-weight: 700;
}

/* 顶部用户卡片 */
.user-card {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: rgba(255, 253, 249, 0.95);
  border: 1px solid #ddd2c4;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b3a2a, #c47a4a);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info h2 {
  margin: 0 0 0.4rem;
  font-size: 1.3rem;
  color: #2f2a26;
}

.user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
}

.user-tag {
  padding: 0.25rem 0.7rem;
  background: rgba(139, 58, 42, 0.1);
  border: 1px solid rgba(139, 58, 42, 0.3);
  color: #8b3a2a;
  font-size: 0.82rem;
}

.update-time {
  margin: 0;
  font-size: 0.78rem;
  color: #8a7a6a;
}

/* 中间网格 */
.mid-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .mid-grid {
    grid-template-columns: 1fr;
  }
}

.card {
  background: rgba(255, 253, 249, 0.95);
  border: 1px solid #ddd2c4;
  padding: 1.5rem;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
}

h3 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
  color: #8b3a2a;
}

/* 雷达图 */
.chart {
  width: 100%;
  height: 300px;
}

/* 分数条 */
.scores-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.score-item {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0.6rem;
  background: #faf6f0;
  border: 1px solid #ede0d0;
}

.score-val {
  font-weight: 700;
  color: #8b3a2a;
}

/* 我的标签 */
.tags-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.interest-tag {
  padding: 0.3rem 0.75rem;
  background: #f5ede0;
  border: 1px solid #e0d3c0;
  color: #5a4a3a;
  font-size: 0.82rem;
}

.profile-desc {
  margin: 0;
  line-height: 1.7;
  color: #3d2f24;
  font-size: 0.9rem;
}

/* 推荐方向 */
.direction-card {
  margin-bottom: 1.5rem;
}

.directions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.direction-item {
  padding: 0.45rem 1rem;
  background: linear-gradient(135deg, rgba(139, 58, 42, 0.08), rgba(196, 122, 74, 0.08));
  border: 1px solid rgba(139, 58, 42, 0.2);
  color: #8b3a2a;
  font-size: 0.9rem;
  font-weight: 500;
}

/* 推荐音乐 */
.song-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}

.song-card {
  cursor: pointer;
  border: 1px solid #e8dccb;
  background: #faf6f0;
  overflow: hidden;
  transition: all 0.2s;
}

.song-card:hover {
  border-color: #c4a87a;
  transform: translateY(-2px);
}

.song-card.playing {
  border-color: #8b3a2a;
}

.song-cover {
  position: relative;
  aspect-ratio: 1;
  background: #e8dccb;
}

.song-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8a7a6a;
  font-size: 0.9rem;
}

.play-icon {
  position: absolute;
  bottom: 0.4rem;
  right: 0.4rem;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(139, 58, 42, 0.9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.song-info {
  padding: 0.5rem;
}

.song-title {
  margin: 0;
  font-size: 0.88rem;
  color: #2f2a26;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-genre {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: #8a7a6a;
}

/* 按钮 */
.primary {
  padding: 0.55rem 1.2rem;
  background: #8b3a2a;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
}
</style>
