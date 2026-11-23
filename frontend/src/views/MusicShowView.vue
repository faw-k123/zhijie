<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import { fetchMusicShowBundle } from '@/api/dataDisplay'
import { getSongLikeStatus, recordListen, toggleSongLike } from '@/api/personalization'
import LiquidBackground from '@/components/LiquidBackground.vue'

type SongItem = { id: string; title: string; audio_url?: string }

const route = useRoute()
const router = useRouter()
const category = computed(() => String(route.params.category || '民歌'))

const intro = ref('')
const coverImageUrl = ref('')
const subMap = ref<Record<string, SongItem[]>>({})
const loading = ref(false)
const morphProgress = ref(0)
const heroImage = computed(() => {
  const images: Record<string, string> = {
    民歌: new URL('@/assets/images/poster/民歌/江南民歌.jpg', import.meta.url).href,
    戏曲: new URL('@/assets/images/poster/戏曲/京剧.jpg', import.meta.url).href,
    说唱: new URL('@/assets/images/poster/说唱/苏州评弹.jpg', import.meta.url).href,
    乐器: new URL('@/assets/images/poster/乐器/古琴.jpg', import.meta.url).href,
  }
  return images[category.value] || coverImageUrl.value || images.民歌
})

const subNames = computed(() => Object.keys(subMap.value))
const selectedSub = ref('')
const playingId = ref<string | null>(null)
const audioEl = ref<HTMLAudioElement | null>(null)
const likedIds = ref<Set<string>>(new Set())
const likeBusyIds = ref<Set<string>>(new Set())
const likeMessage = ref('')

const songs = computed<SongItem[]>(() => {
  if (!selectedSub.value) return []
  return subMap.value[selectedSub.value] || []
})

type NodePos = { name: string; x: number; y: number; vx: number; vy: number }
const nodes = ref<NodePos[]>([])
let animId = 0

type Ripple = { id: number; x: number; y: number; time: number; layer: number }
const ripples = ref<Ripple[]>([])
let rippleId = 0
const bgImageUrl = new URL('@/assets/images/new-bg.png', import.meta.url).href

function initNodes() {
  const names = subNames.value
  nodes.value = names.map((name, i) => {
    const angle = (i / Math.max(names.length, 1)) * Math.PI * 2
    const r = 80 + (i % 3) * 28
    return {
      name,
      x: 220 + Math.cos(angle) * r,
      y: 180 + Math.sin(angle) * r,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
    }
  })
  selectedSub.value = names[0] || ''
}

function tick() {
  const w = 440
  const h = 360
  const r = 42
  for (const n of nodes.value) {
    n.x += n.vx
    n.y += n.vy
    if (n.x < r || n.x > w - r) n.vx *= -1
    if (n.y < r || n.y > h - r) n.vy *= -1
    n.x = Math.min(w - r, Math.max(r, n.x))
    n.y = Math.min(h - r, Math.max(r, n.y))
  }
  for (let i = 0; i < nodes.value.length; i++) {
    for (let j = i + 1; j < nodes.value.length; j++) {
      const a = nodes.value[i]
      const b = nodes.value[j]
      if (!a || !b) continue
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      if (dist < 95) {
        const force = ((95 - dist) / 95) * 0.15
        a.vx -= (dx / dist) * force
        a.vy -= (dy / dist) * force
        b.vx += (dx / dist) * force
        b.vy += (dy / dist) * force
      }
    }
  }
  animId = requestAnimationFrame(tick)
}

function cleanupRipples() {
  ripples.value = ripples.value.filter((r) => Date.now() - r.time < 3500)
  setTimeout(cleanupRipples, 100)
}

function updateMorphProgress() {
  const hero = document.querySelector('.morph-hero')
  if (!hero) return
  const distance = Math.max(hero.clientHeight - window.innerHeight * 0.38, 1)
  morphProgress.value = Math.min(1, Math.max(0, -hero.getBoundingClientRect().top / distance))
}

function createRipple(x: number, y: number) {
  for (let i = 0; i < 3; i++) {
    setTimeout(() => {
      ripples.value.push({ id: rippleId++, x, y, time: Date.now(), layer: i })
    }, i * 250)
  }
}

async function loadBundle() {
  loading.value = true
  try {
    const res = await fetchMusicShowBundle(category.value)
    const data = res.data as {
      intro?: string
      cover_image_url?: string
      subcategories?: Record<string, SongItem[]>
    }
    intro.value = data?.intro || ''
    coverImageUrl.value = data?.cover_image_url || ''
    subMap.value = data?.subcategories || {}
    initNodes()
    void loadLikeStatuses()
  } catch {
    intro.value = '加载失败'
    subMap.value = {}
    initNodes()
  } finally {
    loading.value = false
  }
}

watch(category, () => {
  loadBundle()
})

onMounted(() => {
  loadBundle()
  animId = requestAnimationFrame(tick)
  cleanupRipples()
  window.addEventListener('scroll', updateMorphProgress, { passive: true })
  updateMorphProgress()
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('scroll', updateMorphProgress)
})

function selectSub(name: string) {
  selectedSub.value = name
  playingId.value = null
  audioEl.value?.pause()
  void loadLikeStatuses()
}

function goBack() {
  router.push({ name: 'home' })
}

async function togglePlay(song: SongItem) {
  const username = localStorage.getItem('username') || ''
  if (playingId.value === song.id) {
    audioEl.value?.pause()
    playingId.value = null
    return
  }
  playingId.value = song.id
  if (song.audio_url && audioEl.value) {
    audioEl.value.src = song.audio_url
    await audioEl.value.play().catch(() => undefined)
  }
  if (username) {
    recordListen(username, {
      song_id: song.id,
      title: song.title,
      category: category.value,
      subcategory: selectedSub.value,
    }).catch(() => undefined)
  }
}

function currentUserId() {
  return localStorage.getItem('user_id') || localStorage.getItem('username') || ''
}

async function loadLikeStatuses() {
  const userId = currentUserId()
  if (!userId || !songs.value.length) {
    likedIds.value = new Set()
    return
  }
  const results = await Promise.allSettled(
    songs.value.map(async (song) => {
      const res = await getSongLikeStatus(userId, song.id)
      return { id: song.id, liked: Boolean(res.data?.liked) }
    }),
  )
  likedIds.value = new Set(
    results
      .filter((result): result is PromiseFulfilledResult<{ id: string; liked: boolean }> => result.status === 'fulfilled')
      .filter((result) => result.value.liked)
      .map((result) => result.value.id),
  )
}

async function toggleLike(song: SongItem) {
  const userId = currentUserId()
  if (!userId) {
    likeMessage.value = '请先登录后点赞'
    return
  }
  if (likeBusyIds.value.has(song.id)) return
  likeMessage.value = ''
  likeBusyIds.value = new Set(likeBusyIds.value).add(song.id)
  try {
    const res = await toggleSongLike(userId, song.id, 'like')
    if (!res.success) {
      likeMessage.value = res.message || '点赞失败，请稍后重试'
      return
    }
    const next = new Set(likedIds.value)
    if (res.liked) next.add(song.id)
    else next.delete(song.id)
    likedIds.value = next
    likeMessage.value = res.liked ? `《${song.title}》已加入我喜欢的` : `已取消喜欢《${song.title}》`
  } catch {
    likeMessage.value = '点赞失败，请检查网络连接'
  } finally {
    const nextBusy = new Set(likeBusyIds.value)
    nextBusy.delete(song.id)
    likeBusyIds.value = nextBusy
  }
}
</script>

<template>
  <div class="page">
    <AppNav />
    <audio ref="audioEl" preload="none" @ended="playingId = null" />

    <section
      class="hero morph-hero"
      :style="{ '--morph-progress': morphProgress, '--hero-image': `url(${heroImage})` }"
    >
      <div class="hero-bg">
        <div class="hero-bg-image" />
      </div>
      <div class="morph-stage">
        <button type="button" class="morph-back back-button" @click="goBack">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 18l-6-6 6-6" /></svg>
          <span>返回</span>
        </button>
        <div class="morph-orbit orbit-one" />
        <div class="morph-orbit orbit-two" />
        <div class="morph-circle">
          <span class="morph-circle-label">{{ category }}</span>
          <span class="morph-circle-index">GUOYIN / 0{{ Math.max(1, ['民歌', '戏曲', '说唱', '乐器'].indexOf(category) + 1) }}</span>
        </div>
        <div class="morph-copy">
          <p>{{ loading ? '正在展开声景…' : intro }}</p>
          <span>向下滚动，进入 {{ category }} 的声音地图</span>
        </div>
      </div>
    </section>

    <section class="body">
      <div class="graph-area">
        <h2>小类图谱</h2>
        <div class="canvas">
          <LiquidBackground 
            :image-url="bgImageUrl"
            :metalness="0.05"
            :roughness="0.8"
            :displacement-scale="1.5"
            :enable-chromatic-aberration="false"
          />
          <button
            v-for="n in nodes"
            :key="n.name"
            type="button"
            class="node"
            :class="{ active: selectedSub === n.name }"
            :style="{ left: `${n.x}px`, top: `${n.y}px` }"
            @click="selectSub(n.name)"
          >
            {{ n.name }}
          </button>
          <div
            v-for="r in ripples"
            :key="r.id"
            class="ripple"
            :class="`ripple-${r.layer}`"
            :style="{ left: `${r.x}px`, top: `${r.y}px`, animationDelay: `${(Date.now() - r.time) / 1000}s` }"
          />
        </div>
      </div>

      <div class="song-area">
        <h2>{{ selectedSub || '请选择小类' }} · 曲目列表</h2>
        <p v-if="likeMessage" class="like-message" aria-live="polite">{{ likeMessage }}</p>
        <ul class="song-list">
          <li v-for="(song, index) in songs" :key="song.id">
            <span class="song-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="song-title">{{ song.title }}</span>
            <button
              type="button"
              class="like-btn"
              :class="{ liked: likedIds.has(song.id) }"
              :aria-pressed="likedIds.has(song.id)"
              :aria-label="likedIds.has(song.id) ? `取消喜欢${song.title}` : `喜欢${song.title}`"
              :title="likedIds.has(song.id) ? '取消喜欢' : '加入我喜欢的'"
              :disabled="likeBusyIds.has(song.id)"
              @click="toggleLike(song)"
            >
              <span aria-hidden="true">{{ likedIds.has(song.id) ? '♥' : '♡' }}</span>
            </button>
            <button type="button" class="play-btn" @click="togglePlay(song)">
              {{ playingId === song.id ? '暂停' : '播放' }}
            </button>
          </li>
          <li v-if="songs.length === 0" class="empty">暂无曲目</li>
        </ul>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
}

.hero {
  position: relative;
  min-height: 380px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.hero-bg-image {
  position: absolute;
  inset: 0;
  background-image: url('@/assets/images/hero.png');
  background-size: cover;
  background-position: center;
}

.morph-hero {
  min-height: min(820px, calc(100dvh - 76px));
  height: 770px;
  isolation: isolate;
}

.morph-hero .hero-bg-image {
  background-image: var(--hero-image);
}

.morph-stage {
  position: relative;
  z-index: 2;
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  padding: 5rem 1.5rem 8rem;
  background: linear-gradient(180deg, rgba(3, 18, 17, .35), rgba(3, 18, 17, .72));
}

.morph-circle {
  position: relative;
  display: grid;
  place-items: center;
  width: clamp(180px, 23vw, 300px);
  aspect-ratio: 1;
  border: 1px solid rgba(238, 231, 207, .74);
  border-radius: 50%;
  background: rgba(13, 34, 33, .52);
  box-shadow: 0 0 0 14px rgba(230, 220, 192, .08), 0 24px 70px rgba(0, 0, 0, .4), inset 0 0 50px rgba(226, 212, 169, .12);
  backdrop-filter: blur(5px);
  transform: scale(calc(1 + var(--morph-progress) * 2.25)) translateY(calc(var(--morph-progress) * 82px));
  transition: transform .12s linear;
}

.morph-circle::before,
.morph-circle::after {
  content: '';
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(228, 215, 173, .34);
  border-radius: 50%;
}

.morph-circle::after { inset: -28px; border-color: rgba(222, 213, 184, .18); }

.morph-circle-label {
  position: relative;
  z-index: 1;
  color: #f3eedc;
  font: 500 clamp(2.1rem, 5vw, 4.8rem) / 1 'Songti SC', 'SimSun', serif;
  letter-spacing: .12em;
  text-shadow: 0 4px 24px rgba(0, 0, 0, .55);
}

.morph-circle-index {
  position: absolute;
  bottom: 24%;
  color: rgba(236, 225, 194, .72);
  font: 10px/1 sans-serif;
  letter-spacing: .18em;
}

.morph-copy {
  position: absolute;
  bottom: 7.5rem;
  width: min(780px, 90vw);
  text-align: center;
  color: #ecf0e9;
  transform: translateY(calc(var(--morph-progress) * 92px));
  opacity: calc(1 - var(--morph-progress) * .75);
  transition: transform .12s linear, opacity .12s linear;
}

.morph-copy p { margin: 0 auto 14px; font-size: clamp(1rem, 1.6vw, 1.25rem); line-height: 1.9; text-shadow: 0 2px 18px rgba(0, 0, 0, .8); }
.morph-copy span { color: rgba(235, 222, 184, .82); font-size: .75rem; letter-spacing: .14em; }
.morph-orbit { position: absolute; border: 1px solid rgba(233, 221, 186, .24); border-radius: 50%; pointer-events: none; }
.orbit-one { width: min(58vw, 680px); aspect-ratio: 1; transform: rotateX(66deg) rotateZ(18deg) scale(calc(1 + var(--morph-progress) * .35)); }
.orbit-two { width: min(42vw, 500px); aspect-ratio: 1; transform: rotateY(66deg) rotateZ(-24deg) scale(calc(1 + var(--morph-progress) * .5)); border-color: rgba(145, 198, 178, .2); }

.hero-content {
  position: relative;
  z-index: 1;
  padding: 2.5rem 3rem;
  color: #181E38;
  max-width: 800px;
}

.hero-content h1 {
  margin: 0 0 0.75rem;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 2rem;
  letter-spacing: 0.08em;
}

.hero-content p {
  margin: 0;
  line-height: 1.75;
  font-size: 1rem;
  opacity: 0.95;
}

.body {
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: 1.35rem;
  padding: 3rem clamp(1.25rem, 4vw, 4rem) 5rem;
  min-height: 420px;
}

.graph-area,
.song-area {
  backdrop-filter: blur(14px);
  border: 1px solid rgba(211, 190, 154, 0.22);
  padding: 1.35rem;
  border-radius: 8px;
  box-shadow: 0 22px 54px rgba(0, 0, 0, 0.2);
}

.graph-area {
  background: linear-gradient(145deg, rgba(27, 45, 47, 0.92), rgba(10, 27, 28, 0.94));
}

.song-area {
  background: linear-gradient(145deg, rgba(195, 199, 194, 0.96), rgba(158, 169, 167, 0.94));
}

h2 {
  margin: 0 0 0.8rem;
  font-size: 1.05rem;
  color: #4a3b35;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
}

.song-area h2 {
  color: #172521;
  font-size: 1.18rem;
}

.canvas {
  position: relative;
  height: 360px;
  overflow: hidden;
  border: 1px solid rgba(180, 190, 210, 0.4);
  border-radius: 6px;
}

.node {
  position: absolute;
  width: 84px;
  height: 84px;
  margin-left: -42px;
  margin-top: -42px;
  border-radius: 50%;
  border: 2px solid rgba(80, 100, 140, 0.4);
  background: rgba(255, 253, 248, 0.9);
  color: #3a4a6a;
  font-size: 0.78rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(80, 100, 140, 0.15);
  transition: all 0.3s ease;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
}

.node:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(80, 100, 140, 0.25);
}

.node.active {
  border-color: #5a7abc;
  background: rgba(90, 122, 188, 0.9);
  color: #fff;
}

.ripple {
  position: absolute;
  width: 40px;
  height: 40px;
  margin-left: -20px;
  margin-top: -20px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(90, 122, 188, 0.5) 0%, rgba(90, 122, 188, 0.2) 40%, rgba(90, 122, 188, 0.05) 70%, transparent 100%);
  animation: inkRipple 2.5s ease-out forwards;
  pointer-events: none;
}

@keyframes inkRipple {
  0% {
    transform: scale(0.3);
    opacity: 0.9;
  }
  30% {
    opacity: 0.6;
  }
  100% {
    transform: scale(10);
    opacity: 0;
  }
}

.song-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  max-height: 360px;
  overflow: auto;
}

.song-list li {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.75rem;
  min-height: 64px;
  padding: 0.85rem 0.9rem;
  background-color: #e8e5dc;
  background-image: linear-gradient(100deg, rgba(255,255,255,.55), rgba(225,218,203,.45)), url('@/assets/images/底纹.jpg');
  background-size: cover;
  background-blend-mode: screen, luminosity;
  border: 1px solid rgba(72, 72, 64, 0.16);
  border-left: 3px solid transparent;
  border-radius: 5px;
  box-shadow: 0 5px 16px rgba(33, 43, 40, 0.08);
  transition: transform 0.24s ease, background-color 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
}

.song-list li:hover {
  transform: translateX(5px);
  background-color: #d8c6a7;
  border-left-color: #8d3c32;
  box-shadow: 0 10px 24px rgba(33, 43, 40, 0.16);
}

.song-index {
  color: #7f776b;
  font: 600 0.7rem/1 sans-serif;
  letter-spacing: .08em;
}

.song-title {
  flex: 1;
  color: #111714;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 1rem;
  font-weight: 600;
}

.like-message {
  margin: -0.25rem 0 0.75rem;
  min-height: 1.1rem;
  color: #315e50;
  font-size: 0.76rem;
}

.like-btn {
  display: grid;
  place-items: center;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid rgba(38, 63, 59, 0.22);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.58);
  color: #435c55;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: transform .2s ease, color .2s ease, background .2s ease, box-shadow .2s ease;
}

.like-btn:hover,
.like-btn.liked {
  color: #9d3543;
  background: #fff6f2;
  box-shadow: 0 5px 14px rgba(107, 45, 52, .16);
}

.like-btn.liked { transform: scale(1.04); }
.like-btn:disabled { cursor: wait; opacity: .55; }

.play-btn {
  flex-shrink: 0;
  padding: 0.35rem 0.75rem;
  border: none;
  background: #263f3b;
  color: #f2e8d5;
  cursor: pointer;
  font-size: 0.85rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.play-btn:hover {
  background: #8d3c32;
}

.empty {
  justify-content: center !important;
  color: #8a7a6a;
}

@media (max-width: 900px) {
  .morph-hero { height: 680px; min-height: 680px; }
  .morph-copy { bottom: 5rem; }
  .body {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .morph-circle, .morph-copy, .morph-orbit { transition: none; }
}
</style>
