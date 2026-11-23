<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import {
  fetchMusicResource,
  type LyricLine,
  type MusicResourceDetail,
} from '@/api/contentDisplay'
import { fetchSongImagery } from '@/api/imagery'
import {
  createFavoriteFolder,
  fetchFavorites,
  fetchFolderSongs,
  fetchSimilarSongs,
  saveToFavorite,
  deleteFavoriteFolder,
  removeFavoriteSong,
  getFavoriteStatus,
  toggleSongLike,
  getSongLikeStatus,
} from '@/api/personalization'
import { getLocale, useI18n } from '@/i18n'
import { circleOverride, loadTestModeConfig } from '@/stores/testOverrides'

interface FavoriteFolder {
  id: string
  name: string
  songs?: { id: string; title: string; intro?: string; mv_url?: string }[]
}

interface SimilarItem {
  id: string
  title: string
  intro: string
  mv_url: string
}

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const username = localStorage.getItem('username') || ''
const userId = localStorage.getItem('user_id') || ''

const songId = computed(() => String(route.params.id || ''))
const resource = ref<MusicResourceDetail | null>(null)
const loading = ref(false)

const imageryText = ref('')
const imageryLoading = ref(false)
const similar = ref<SimilarItem[]>([])

const liked = ref(false)
const cried = ref(false)
const starred = ref(false)
const shared = ref(false)
const favoritedFolderId = ref('')

const showFavoriteModal = ref(false)
const folders = ref<FavoriteFolder[]>([])
const expandedFolderIds = ref<Set<string>>(new Set())
const selectedFolderId = ref('')
const newFolderName = ref('')
const favoriteSaving = ref(false)
const favoriteMsg = ref('')

const mvEl = ref<HTMLVideoElement | null>(null)
const audioEl = ref<HTMLAudioElement | null>(null)
const lyricsCoreEl = ref<HTMLElement | null>(null)
const audioPlaying = ref(false)
const audioProgress = ref(0)
const audioDuration = ref(0)
const playhead = ref(0)
const mvPausedByUser = ref(false)
const fallbackCover = new URL('@/assets/images/poster/民歌/江南民歌.jpg', import.meta.url).href
const designPreview = import.meta.env.DEV && sessionStorage.getItem('guoyin:design-preview') === '1'
const previewSimilar: SimilarItem[] = [
  { id: 'preview-jiangnan', title: '江南小调', intro: '婉转清丽的水乡声景', mv_url: '' },
  { id: 'preview-yue', title: '越调春声', intro: '细腻绵长的戏曲唱腔', mv_url: '' },
  { id: 'preview-moon', title: '月下清歌', intro: '静谧悠远的古韵旋律', mv_url: '' },
]

const lyricLines = computed<LyricLine[]>(() => {
  const raw = resource.value?.lyrics || []
  if (!raw.length) return [{ time: 0, text: t('display.noLyric') }]
  return raw.map((line, i) => {
    if (typeof line === 'string') return { time: i * 3, text: line }
    return { time: Number(line.time) || 0, text: line.text || '' }
  })
})

const activeLyricIndex = computed(() => {
  const lines = lyricLines.value
  if (!lines.length) return -1
  const t = playhead.value
  let idx = 0
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line && line.time <= t) idx = i
    else break
  }
  return idx
})

watch(activeLyricIndex, async (idx) => {
  await nextTick()
  const root = lyricsCoreEl.value
  if (!root || idx < 0) return
  const el = root.querySelector<HTMLElement>(`[data-lyric-idx="${idx}"]`)
  if (!el) return
  root.scrollTo({ top: Math.max(0, el.offsetTop - root.clientHeight * 0.38), behavior: 'smooth' })
})

let loadSeq = 0

async function loadResource() {
  if (!songId.value) return
  const seq = ++loadSeq
  loading.value = true
  liked.value = false
  cried.value = false
  starred.value = false
  shared.value = false
  audioPlaying.value = false
  audioProgress.value = 0
  playhead.value = 0
  mvPausedByUser.value = false
  try {
    const res = await fetchMusicResource(songId.value)
    if (seq !== loadSeq) return
    resource.value = res.data || null
    if (designPreview && resource.value && !resource.value.lyrics?.length) {
      resource.value = {
        ...resource.value,
        lyrics: [
          { time: 0, text: '山水入梦，风从江南来' }, { time: 4, text: '一叶轻舟载着旧时光' },
          { time: 8, text: '烟雨落在青石巷' }, { time: 12, text: '远山低，月色长' },
          { time: 16, text: '听见故乡在歌唱' }, { time: 20, text: '水袖轻扬，回声荡漾' },
          { time: 24, text: '把思念写进一阕新腔' }, { time: 28, text: '不问归期，不问风霜' },
        ],
      }
    }
    await nextTick()
    if (seq !== loadSeq) return
    if (mvEl.value && !mvPausedByUser.value) {
      try {
        await mvEl.value.play()
      } catch {
      }
    }
    if (audioEl.value) {
      audioEl.value.pause()
      audioEl.value.src = resource.value?.audio_url || ''
    }
  } catch {
    if (seq !== loadSeq) return
    resource.value = {
      id: songId.value,
      title: `歌曲 ${songId.value}`,
      intro: '资源加载失败或暂无数据',
      mv_url: '',
      audio_url: '',
      lyrics: designPreview ? [
        { time: 0, text: '山水入梦，风从江南来' },
        { time: 4, text: '一叶轻舟载着旧时光' },
        { time: 8, text: '烟雨落在青石巷' },
        { time: 12, text: '远山低，月色长' },
        { time: 16, text: '听见故乡在歌唱' },
        { time: 20, text: '水袖轻扬，回声荡漾' },
        { time: 24, text: '把思念写进一阕新腔' },
        { time: 28, text: '不问归期，不问风霜' },
      ] : [],
    }
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

async function loadFavoriteStatus() {
  if (!songId.value || !userId) return
  try {
    const res = await getFavoriteStatus(userId, songId.value)
    starred.value = res.data?.favorited || false
    favoritedFolderId.value = res.data?.folder_id || ''
  } catch {
    starred.value = false
    favoritedFolderId.value = ''
  }
}

async function loadImagery() {
  if (!songId.value) return
  imageryLoading.value = true
  try {
    // 只从后端缓冲池取文案：未命中则服务端申请解析并写入后再返回
    const res = await fetchSongImagery(songId.value, getLocale(), {
      userId: localStorage.getItem('user_id') || '',
      sceneTags: resource.value?.scene_tags || [],
      thingTags: resource.value?.thing_tags || [],
      emotionTags: resource.value?.emotion_tags || [],
      circleOverride: circleOverride.value,
    })
    imageryText.value = res.data?.text || t('display.imageryEmpty')
  } catch {
    imageryText.value = t('display.imageryFail')
  } finally {
    imageryLoading.value = false
  }
}

async function loadSimilar() {
  if (!songId.value) return
  try {
    const res = await fetchSimilarSongs(username, songId.value)
    const items = (res.data?.items || []).slice(0, 10) as SimilarItem[]
    similar.value = items.length ? items : designPreview ? previewSimilar : []
  } catch {
    similar.value = designPreview ? previewSimilar : []
  }
}

async function onLike() {
  try {
    console.log('onLike called, userId:', userId, 'songId:', songId.value, 'current liked:', liked.value)
    const res = await toggleSongLike(userId, songId.value, 'like')
    console.log('toggleSongLike response:', res)
    if (res.success && res.liked !== undefined) {
      liked.value = res.liked
    } else {
      liked.value = !liked.value
    }
    if (liked.value) cried.value = false
  } catch (e) {
    console.error('onLike error:', e)
    liked.value = !liked.value
    if (liked.value) cried.value = false
  }
}

async function onCry() {
  try {
    const res = await toggleSongLike(userId, songId.value, 'dislike')
    if (res.success && res.liked !== undefined) {
      cried.value = !res.liked
    } else {
      cried.value = !cried.value
    }
    if (cried.value) liked.value = false
  } catch {
    cried.value = !cried.value
    if (cried.value) liked.value = false
  }
}

async function loadLikeStatus() {
  if (!songId.value || !userId) {
    console.log('loadLikeStatus skipped: songId or userId empty, songId:', songId.value, 'userId:', userId)
    return
  }
  try {
    const res = await getSongLikeStatus(userId, songId.value)
    console.log('loadLikeStatus response:', res)
    liked.value = res.data?.liked || false
    cried.value = res.data?.disliked || false
    console.log('loadLikeStatus set: liked=', liked.value, 'cried=', cried.value)
  } catch (e) {
    console.error('loadLikeStatus error:', e)
    liked.value = false
    cried.value = false
  }
}

async function toggleFavorite() {
  if (starred.value && favoritedFolderId.value) {
    try {
      const res = await removeFavoriteSong(userId, favoritedFolderId.value, songId.value)
      if (res.success) {
        starred.value = false
        favoritedFolderId.value = ''
        favoriteMsg.value = t('display.favRemoved')
      } else {
        favoriteMsg.value = res.message || t('display.deleteFail')
      }
    } catch {
      favoriteMsg.value = t('display.deleteFail')
    }
  } else {
    openFavoriteModal()
  }
}

async function openFavoriteModal() {
  showFavoriteModal.value = true
  favoriteMsg.value = ''
  selectedFolderId.value = ''
  expandedFolderIds.value = new Set()
  try {
    const res = await fetchFavorites(userId)
    folders.value = (res.data?.folders || []).map((f) => ({
      id: f.id,
      name: f.name,
      songs: f.songs || [],
    }))
  } catch {
    folders.value = []
    favoriteMsg.value = t('display.favLoadFail')
  }
}

async function toggleFolderExpand(id: string) {
  const next = new Set(expandedFolderIds.value)
  if (next.has(id)) {
    next.delete(id)
    expandedFolderIds.value = next
    return
  }
  next.add(id)
  expandedFolderIds.value = next
  const folder = folders.value.find((f) => f.id === id)
  if (!folder || (folder.songs && folder.songs.length)) return
  try {
    const res = await fetchFolderSongs(userId, id)
    folder.songs = (res.data?.songs || []).map((s) => ({ id: s.id, title: s.title }))
  } catch {
  }
}

async function onCreateFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  try {
    await createFavoriteFolder(userId, name)
    newFolderName.value = ''
    const res = await fetchFavorites(userId)
    folders.value = res.data?.folders || []
  } catch {
    favoriteMsg.value = t('display.folderCreateFail')
  }
}

async function onDeleteFolder(folderId: string, folderName: string, event: Event) {
  event.stopPropagation()
  if (folderName === '默认收藏夹') {
    alert(t('display.cantDeleteDefault'))
    return
  }
  if (!confirm(t('display.confirmDeleteFolder', { name: folderName }))) return
  try {
    const res = await deleteFavoriteFolder(userId, folderId)
    if (res.success) {
      const resFolders = await fetchFavorites(userId)
      folders.value = resFolders.data?.folders || []
      if (selectedFolderId.value === folderId) {
        selectedFolderId.value = ''
      }
    } else {
      favoriteMsg.value = res.message || t('display.deleteFail')
    }
  } catch {
    favoriteMsg.value = t('display.deleteFail')
  }
}

async function onRemoveSong(folderId: string, songIdStr: string, event: Event) {
  event.stopPropagation()
  try {
    const res = await removeFavoriteSong(userId, folderId, songIdStr)
    if (res.success) {
      const folder = folders.value.find((f) => f.id === folderId)
      if (folder && folder.songs) {
        folder.songs = folder.songs.filter((s) => s.id !== songIdStr)
      }
      if (songIdStr === songId.value) {
        starred.value = false
      }
    } else {
      alert(res.message || t('display.removeFail'))
    }
  } catch {
    alert(t('display.removeFail'))
  }
}

async function confirmFavorite() {
  if (!selectedFolderId.value) {
    favoriteMsg.value = t('display.pickFolder')
    return
  }
  favoriteSaving.value = true
  favoriteMsg.value = ''
  try {
    const res = await saveToFavorite(userId, songId.value, selectedFolderId.value)
    if (res.success) {
      starred.value = true
      favoriteMsg.value = t('display.favOk')
      setTimeout(() => {
        showFavoriteModal.value = false
      }, 600)
    } else {
      favoriteMsg.value = res.message || t('display.favFail')
    }
  } catch {
    favoriteMsg.value = t('display.favFail')
  } finally {
    favoriteSaving.value = false
  }
}

function onShare() {
  shared.value = !shared.value
}

function goSimilar(id: string) {
  router.push({ name: 'music-display', params: { id } })
}

function toggleAudio() {
  const el = audioEl.value
  if (!el || !resource.value?.audio_url) return
  if (audioPlaying.value) {
    el.pause()
    audioPlaying.value = false
  } else {
    el.play().catch(() => undefined)
    audioPlaying.value = true
  }
}

function onAudioTimeUpdate() {
  const el = audioEl.value
  if (!el) return
  audioProgress.value = el.currentTime
  audioDuration.value = el.duration || 0
  if (audioPlaying.value || !el.paused) {
    playhead.value = el.currentTime
  }
}

function onMvTimeUpdate() {
  const el = mvEl.value
  if (!el) return
  if (!audioPlaying.value) {
    playhead.value = el.currentTime
  }
}

function onMvPause() {
  mvPausedByUser.value = true
}

function onMvPlay() {
  mvPausedByUser.value = false
}

function seekAudio(e: Event) {
  const el = audioEl.value
  const input = e.target as HTMLInputElement
  if (!el) return
  el.currentTime = Number(input.value)
  audioProgress.value = el.currentTime
  playhead.value = el.currentTime
}

function formatTime(sec: number) {
  if (!sec || Number.isNaN(sec)) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

async function bootstrapPage() {
  await loadResource()
  await Promise.all([loadImagery(), loadSimilar(), loadLikeStatus(), loadFavoriteStatus()])
}

watch(songId, async (id, prev) => {
  if (!prev || id === prev) return
  await bootstrapPage()
})

// 测试模式下切换文化圈层 → 换缓冲分片，重新从缓冲池取/申请
watch(circleOverride, async () => {
  if (!songId.value) return
  await loadImagery()
})

onMounted(async () => {
  await loadTestModeConfig()
  await bootstrapPage()
})

onUnmounted(() => {
  loadSeq += 1
  mvEl.value?.pause()
  audioEl.value?.pause()
})
</script>

<template>
  <div class="display-page">
    <AppNav />
    <audio
      ref="audioEl"
      preload="metadata"
      @timeupdate="onAudioTimeUpdate"
      @ended="audioPlaying = false"
      @loadedmetadata="onAudioTimeUpdate"
    />

    <div v-if="loading" class="loading-bar">{{ t('display.loading') }}</div>

    <main class="layout">
      <section class="left">
        <div class="left-grid">
          <div class="zone title-zone">
            <h1>{{ resource?.title || '—' }}</h1>
            <div class="intro">{{ resource?.intro || t('display.noIntro') }}</div>
          </div>

          <div class="zone mv-zone">
            <video
              v-if="resource?.mv_url"
              :key="resource.id"
              ref="mvEl"
              class="mv"
              :src="resource.mv_url"
              controls
              playsinline
              @timeupdate="onMvTimeUpdate"
              @pause="onMvPause"
              @play="onMvPlay"
            />
            <div v-else class="mv-placeholder">{{ t('display.mvPlaceholder') }}</div>
          </div>

          <div class="zone actions-zone">
            <button
              type="button"
              class="icon-btn like"
              :class="{ active: liked }"
              :title="t('display.like')"
              @click="onLike"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M12 21s-6.7-4.35-9.33-7.4C.8 11.4 1.1 7.8 3.6 6.1 5.5 4.8 8 5.1 9.5 6.7L12 9.4l2.5-2.7c1.5-1.6 4-1.9 5.9-.6 2.5 1.7 2.8 5.3.93 7.5C18.7 16.65 12 21 12 21z"
                />
              </svg>
            </button>
            <button
              type="button"
              class="icon-btn cry"
              :class="{ active: cried }"
              :title="t('display.dislike')"
              @click="onCry"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.6" />
                <circle cx="9" cy="10" r="1" />
                <circle cx="15" cy="10" r="1" />
                <path d="M8.5 16c1.2-1.2 2.3-1.8 3.5-1.8S14.3 14.8 15.5 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                <path d="M8.2 12.2c0 1.2-.5 2.3-1.2 2.8M15.8 12.2c0 1.2.5 2.3 1.2 2.8" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
              </svg>
            </button>
            <button
              type="button"
              class="icon-btn star"
              :class="{ active: starred }"
              :title="starred ? t('display.unfavorite') : t('display.favorite')"
              @click="toggleFavorite"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M12 3.6l2.4 4.9 5.4.8-3.9 3.8.9 5.4L12 15.9 7.2 18.5l.9-5.4L4.2 9.3l5.4-.8L12 3.6z"
                  :fill="starred ? 'currentColor' : 'none'"
                  :stroke="starred ? 'none' : 'currentColor'"
                  :stroke-width="starred ? '0' : '1.5'"
                />
              </svg>
            </button>
            <button
              type="button"
              class="icon-btn share"
              :class="{ active: shared }"
              :title="t('display.share')"
              @click="onShare"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="18" cy="5" r="2.4" />
                <circle cx="6" cy="12" r="2.4" />
                <circle cx="18" cy="19" r="2.4" />
                <path d="M8.2 11.1l7.5-4.2M8.2 12.9l7.5 4.2" fill="none" stroke="currentColor" stroke-width="1.6" />
              </svg>
            </button>
          </div>

          <div class="zone lyrics-zone">
            <div class="lyrics-body">
              <div class="lyrics-cover">
                <img :src="resource?.cover_url || fallbackCover" :alt="resource?.title || '歌曲封面'" />
                <div class="lyrics-cover-meta">
                  <strong>{{ resource?.title || '正在播放' }}</strong>
                  <span>国风声景 · lyrics</span>
                </div>
              </div>
              <div ref="lyricsCoreEl" class="lyrics-core">
                <p
                  v-for="(line, i) in lyricLines"
                  :key="`${line.time}-${i}`"
                  class="lyric-line"
                  :class="{ active: i === activeLyricIndex }"
                  :data-lyric-idx="i"
                  :style="{ '--lyric-index': i - activeLyricIndex }"
                >
                  {{ line.text }}
                </p>
              </div>
            </div>
            <div class="audio-bar">
              <button type="button" class="audio-play" @click="toggleAudio">
                {{ audioPlaying ? '❚❚' : '▶' }}
              </button>
              <span class="audio-title">{{ resource?.title || t('display.audio') }}</span>
              <input
                type="range"
                min="0"
                :max="audioDuration || 0"
                step="0.1"
                :value="audioProgress"
                :disabled="!resource?.audio_url"
                @input="seekAudio"
              />
              <em>{{ formatTime(audioProgress) }}</em>
            </div>
          </div>
        </div>
      </section>

      <aside class="right">
        <div class="right-top">
          <div class="terminal-tools" aria-hidden="true"><span class="terminal-dot red"></span><span class="terminal-dot yellow"></span><span class="terminal-dot green"></span></div>
          <h2>{{ t('display.imagery') }}</h2>
          <div class="imagery-body">
            <p v-if="imageryLoading">{{ t('display.imageryLoading') }}</p>
            <p v-else class="imagery-text">{{ imageryText }}</p>
          </div>
        </div>
        <div class="right-bottom">
          <h2>{{ t('display.similar') }}</h2>
          <div class="similar-glass-list">
            <li
              v-for="item in similar"
              :key="item.id"
              class="similar-glass"
              :data-text="item.title"
              @click="goSimilar(item.id)"
            >
              <div class="sim-thumb">
                <video v-if="item.mv_url" :src="item.mv_url" muted preload="metadata" />
                <span v-else>{{ item.title.slice(0, 1) }}</span>
              </div>
              <div class="sim-meta">
                <h3>{{ item.title }}</h3>
                <p>{{ item.intro || t('display.noIntro') }}</p>
              </div>
            </li>
            <li v-if="!similar.length" class="sim-empty">{{ t('display.noRecommend') }}</li>
          </div>
        </div>
      </aside>
    </main>

    <div v-if="showFavoriteModal" class="modal-mask" @click.self="showFavoriteModal = false">
      <div class="fav-modal">
        <h3>{{ t('display.favTitle') }}</h3>
        <ul class="folder-list">
          <li v-for="folder in folders" :key="folder.id" class="folder-item">
            <div class="folder-row">
              <label class="radio-label">
                <input
                  v-model="selectedFolderId"
                  type="radio"
                  name="fav-folder"
                  :value="folder.id"
                />
                <span>{{ folder.name }}</span>
              </label>
              <div class="folder-actions">
                <button type="button" class="expand-btn" @click="toggleFolderExpand(folder.id)">
                  {{ expandedFolderIds.has(folder.id) ? '▲' : '▼' }}
                </button>
                <button
                  v-if="folder.name !== '默认收藏夹'"
                  type="button"
                  class="delete-folder-btn"
                  @click="onDeleteFolder(folder.id, folder.name, $event)"
                  :title="t('display.delete')"
                >
                  ✕
                </button>
              </div>
            </div>
            <ul v-show="expandedFolderIds.has(folder.id)" class="song-list">
              <li v-for="s in folder.songs" :key="s.id" class="song-item">
                <span>{{ s.title }}</span>
                <button
                  type="button"
                  class="remove-song-btn"
                  @click="onRemoveSong(folder.id, s.id, $event)"
                  :title="t('display.remove')"
                >
                  ✕
                </button>
              </li>
              <li v-if="!folder.songs?.length" class="dim">{{ t('display.emptyFolder') }}</li>
            </ul>
          </li>
          <li class="folder-item new-folder">
            <input v-model="newFolderName" type="text" :placeholder="t('display.newFolder')" />
            <button type="button" @click="onCreateFolder">{{ t('display.addFolder') }}</button>
          </li>
        </ul>
        <p v-if="favoriteMsg" class="fav-msg">{{ favoriteMsg }}</p>
        <div class="fav-actions">
          <button type="button" class="cancel" @click="showFavoriteModal = false">
            {{ t('display.cancel') }}
          </button>
          <button type="button" class="confirm" :disabled="favoriteSaving" @click="confirmFavorite">
            {{ favoriteSaving ? t('display.submitting') : t('display.confirm') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.display-page {
  min-height: 100vh;
  background: transparent;
  color: var(--color-text);
}

.loading-bar {
  text-align: center;
  padding: 0.5rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.layout {
  display: grid;
  grid-template-columns: 7fr 3fr;
  gap: 1rem;
  padding: 1rem 1.25rem;
  min-height: calc(100vh - 56px);
}

.left-grid {
  display: grid;
  grid-template-rows: 1.5fr 4fr 0.5fr 4fr;
  gap: 0.75rem;
  min-height: 720px;
  height: calc(100vh - 56px - 2rem);
}

.zone {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.title-zone {
  padding: 0.85rem 1rem;
  overflow-y: auto;
}

.title-zone h1 {
  margin: 0 0 0.5rem;
  font-size: 1.35rem;
  color: var(--color-brown);
}

.intro {
  font-size: 0.92rem;
  line-height: 1.65;
  color: var(--color-brown-warm);
  white-space: pre-wrap;
}

.mv-zone {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a222c;
}

.mv {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.mv-placeholder {
  color: #c9c0c7;
  font-size: 1rem;
}

.actions-zone {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 5px;
  padding: 0 0.75rem;
  background: var(--color-cream);
}

.icon-btn {
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  color: var(--color-brown);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s, border-color 0.2s, fill 0.2s;
}

.icon-btn svg {
  width: 20px;
  height: 20px;
  display: block;
}

.icon-btn.like svg path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
}

.icon-btn.like.active {
  color: #d03f4c;
  border-color: #d03f4c;
  background: transparent;
}

.icon-btn.like.active svg path {
  fill: #d03f4c;
  stroke: #d03f4c;
}

.icon-btn.cry.active {
  background: #efe2b2;
  border-color: #d9c28a;
  color: #6a4a55;
}

.icon-btn.star svg path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
}

.icon-btn.star.active {
  background: #efe2b2;
  border-color: #d9c28a;
  color: #6a4a55;
}

.icon-btn.star.active svg path {
  fill: #efe2b2;
  stroke: #c9b878;
}

.icon-btn.share svg circle {
  fill: currentColor;
}

.icon-btn.share.active {
  background: #4c8dae;
  border-color: #3a6b8c;
  color: #fff;
}

.lyrics-zone {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--color-primary-soft);
}

.lyrics-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 30% 40% 30%;
  position: relative;
  background: var(--color-primary-soft);
}

.lyrics-body { grid-template-columns: 34% 66%; align-items: stretch; overflow:hidden; }
.lyrics-cover { position:relative; min-width:0; display:flex; flex-direction:column; justify-content:center; padding:1.5rem; background:linear-gradient(145deg,rgba(11,48,43,.96),rgba(23,35,38,.95)); overflow:hidden; }
.lyrics-cover::after { content:''; position:absolute; inset:0; background:linear-gradient(135deg,rgba(217,193,139,.2),transparent 42%,rgba(0,0,0,.28)); pointer-events:none; }
.lyrics-cover img { width:100%; aspect-ratio:1; object-fit:cover; border-radius:10px; filter:saturate(.78) contrast(1.05); box-shadow:0 18px 38px rgba(0,0,0,.34); }
.lyrics-cover-meta { position:relative; z-index:1; display:flex; flex-direction:column; gap:5px; padding:14px 3px 0; color:#edf0e7; }
.lyrics-cover-meta strong { font:500 1.15rem 'Songti SC','SimSun',serif; }
.lyrics-cover-meta span { color:#a9c2b6; font-size:.72rem; letter-spacing:.12em; }

.lyrics-side {
  position: relative;
  pointer-events: none;
  z-index: 2;
}

.lyrics-side.left-fade {
  background: linear-gradient(
    90deg,
    var(--color-primary-soft) 0%,
    rgba(231, 241, 229, 0.92) 40%,
    transparent 100%
  );
}

.lyrics-side.right-fade {
  background: linear-gradient(
    270deg,
    var(--color-primary-soft) 0%,
    rgba(231, 241, 229, 0.92) 40%,
    transparent 100%
  );
}

.lyrics-core {
  height: 100%;
  overflow-y: auto;
  padding: 1rem 0.35rem 0.5rem;
  text-align: center;
  background: transparent;
  scroll-behavior: smooth;
}

.lyrics-core { position:relative; padding:2.5rem 1rem 4rem; background:linear-gradient(90deg,rgba(11,35,34,.14),rgba(7,23,27,.72)); mask-image:linear-gradient(to bottom,transparent 0%,#000 15%,#000 78%,transparent 100%); }

.lyric-line {
  margin: 0 0 0.75rem;
  color: var(--color-text-muted);
  font-size: 18px;
  line-height: 1.7;
  letter-spacing: 0.03em;
  transition: color 0.35s ease, transform 0.35s ease, text-shadow 0.35s ease, font-weight 0.35s ease;
}

.lyric-line.active {
  color: var(--color-emphasis);
  font-weight: 700;
  transform: scale(1.06);
  text-shadow: 0 0 12px rgba(208, 63, 76, 0.18);
}

.lyrics-core { perspective:900px; overflow-x:hidden; overflow-y:auto; padding:5rem 1.4rem 8rem; }
.lyric-line { position:relative; width:100%; transform:translateX(calc(var(--lyric-index) * -7px)) rotate(calc(var(--lyric-index) * 1.8deg)); transform-origin:center center; opacity:calc(1 - min(.62, abs(var(--lyric-index)) * .055)); filter:blur(calc(min(2px, abs(var(--lyric-index)) * .16))); transition:color .35s ease, transform .45s ease, opacity .45s ease, filter .45s ease, text-shadow .35s ease; }
.lyric-line:nth-child(even) { letter-spacing:.055em; }
.lyric-line.active { transform:translateX(0) rotate(0deg) scale(1.1); opacity:1; filter:none; color:#efe5c7; text-shadow:0 0 18px rgba(210,191,132,.28); }

.audio-bar {
  height: 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0 0.5rem;
  background: rgba(140, 67, 86, 0.92);
  border-top: 1px solid var(--color-primary-deep);
  color: var(--color-surface);
  width: 50%;
  margin: 0 auto;
  box-sizing: border-box;
}

.audio-play {
  border: none;
  background: transparent;
  color: var(--color-wood);
  width: 18px;
  height: 18px;
  padding: 0;
  font-size: 0.65rem;
  cursor: pointer;
  flex-shrink: 0;
  line-height: 1;
}

.audio-title {
  font-size: 0.65rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 28%;
  flex-shrink: 0;
}

.audio-bar input[type='range'] {
  flex: 1;
  height: 3px;
  min-width: 0;
  margin: 0;
}

.audio-bar em {
  font-style: normal;
  font-size: 0.6rem;
  color: #c9c0c7;
  flex-shrink: 0;
}

.right {
  display: grid;
  grid-template-rows: 7fr 3fr;
  gap: 0.75rem;
  min-height: 720px;
  height: calc(100vh - 56px - 2rem);
}

.right-top,
.right-bottom {
  background: #fbf8f0;
  border: 1px solid #d8cdd4;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-top h2,
.right-bottom h2 {
  margin: 0;
  padding: 0.7rem 0.9rem;
  font-size: 1rem;
  border-bottom: 1px solid #ede5eb;
  color: #3a2a33;
}

.right-top { position:relative; background:#f7f5ee; border-color:#d5cec0; }
.terminal-tools { display:flex; align-items:center; gap:6px; height:32px; padding:0 12px; background:#e8e4d9; border-bottom:1px solid #d5cec0; }
.terminal-dot { width:10px; height:10px; border-radius:50%; display:block; }
.terminal-dot.red { background:#ff605c; }.terminal-dot.yellow { background:#ffbd44; }.terminal-dot.green { background:#00ca4e; }
.right-top .imagery-body { background:#f8fbfe; margin:0 12px 12px; border-radius:0 0 7px 7px; box-shadow:inset 0 0 0 1px rgba(54,65,64,.08); }

.imagery-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.9rem;
}

.imagery-text {
  margin: 0;
  line-height: 1.75;
  white-space: pre-wrap;
  font-size: 0.92rem;
  color: #6a4a55;
}

.similar-list {
  list-style: none;
  margin: 0;
  padding: 0.4rem;
  overflow-y: auto;
  flex: 1;
}

.similar-list li {
  display: grid;
  grid-template-columns: 4fr 6fr;
  gap: 0.55rem;
  padding: 0.45rem;
  cursor: pointer;
  border-bottom: 1px solid #ede5eb;
}

.similar-list li:hover {
  background: #f4eff2;
}

.similar-glass-list { position:relative; display:flex; justify-content:center; align-items:center; min-height:220px; padding:1rem; }
.right-bottom { background:linear-gradient(145deg,#243d3b,#122727); border-color:#47605b; }
.right-bottom h2 { color:#f1eadb; border-color:rgba(220,225,211,.15); }
.similar-glass { position:relative; display:flex; flex-direction:column; align-items:center; justify-content:center; width:150px; height:178px; margin:0 -28px; padding:1rem; border:1px solid rgba(255,255,255,.24); border-radius:10px; background:linear-gradient(145deg,rgba(255,255,255,.34),rgba(115,151,146,.12)); box-shadow:0 20px 28px rgba(13,39,37,.22); backdrop-filter:blur(12px); transform:rotate(var(--recommend-rotate,0deg)); transition:.35s ease; cursor:pointer; z-index:1; overflow:hidden; }
.similar-glass:nth-child(1) { --recommend-rotate:-10deg; }.similar-glass:nth-child(2) { --recommend-rotate:2deg; z-index:2; }.similar-glass:nth-child(3) { --recommend-rotate:10deg; z-index:1; }
.similar-glass-list:hover .similar-glass { margin:0 7px; transform:rotate(0deg) translateY(-4px); }
.similar-glass .sim-thumb { width:82px; aspect-ratio:1; border-radius:8px; margin-bottom:10px; box-shadow:0 8px 16px rgba(0,0,0,.22); }
.similar-glass .sim-meta { width:100%; text-align:center; }.similar-glass .sim-meta h3 { color:#eff2e8; font-size:.86rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }.similar-glass .sim-meta p { display:none; }
.similar-glass::after { content:attr(data-text); position:absolute; left:0; right:0; bottom:0; padding:7px; text-align:center; color:#dce9dc; font-size:.68rem; background:rgba(255,255,255,.08); }

.sim-thumb {
  aspect-ratio: 16 / 10;
  background: linear-gradient(145deg, #c9d2d8, #a8b5bc);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: #3a2a33;
  font-weight: 700;
}

.sim-thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sim-meta h3 {
  margin: 0 0 0.25rem;
  font-size: 0.88rem;
}

.sim-meta p {
  margin: 0;
  font-size: 0.75rem;
  color: #8a7a82;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sim-empty {
  display: block !important;
  text-align: center;
  color: #9a8a92;
  padding: 1rem !important;
  cursor: default !important;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 32, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.fav-modal {
  width: min(420px, 92vw);
  max-height: 80vh;
  overflow: auto;
  background: #fbf8f0;
  border: 1px solid #d8cdd4;
  padding: 1.25rem;
}

.fav-modal h3 {
  margin: 0 0 1rem;
  color: #3a2a33;
}

.folder-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.folder-item {
  border-bottom: 1px solid #ede5eb;
  padding: 0.55rem 0;
}

.folder-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.folder-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.expand-btn {
  border: 1px solid #c9c0c7;
  background: #fff;
  width: 32px;
  height: 28px;
  cursor: pointer;
}

.delete-folder-btn {
  border: none;
  background: rgba(208, 63, 76, 0.7);
  color: #fff;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-folder-btn:hover {
  background: #d03f4c;
}

.song-list {
  list-style: none;
  margin: 0.4rem 0 0 1.6rem;
  padding: 0;
  font-size: 0.88rem;
  color: #6a4a55;
}

.song-list .dim {
  color: #a89aa0;
}

.new-folder {
  display: flex;
  gap: 0.5rem;
  padding-top: 0.85rem;
  border-bottom: none;
}

.new-folder input {
  flex: 1;
  padding: 0.45rem 0.6rem;
  border: 1px solid #c9c0c7;
}

.new-folder button {
  border: none;
  background: #1f2a38;
  color: #fff;
  padding: 0.45rem 0.75rem;
  cursor: pointer;
  white-space: nowrap;
}

.fav-msg {
  margin: 0.75rem 0 0;
  font-size: 0.88rem;
  color: #9e2a38;
}

.fav-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1rem;
}

.fav-actions .cancel {
  border: 1px solid #c9c0c7;
  background: #fff;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.fav-actions .confirm {
  border: none;
  background: #9e2a38;
  color: #fff;
  padding: 0.5rem 1.1rem;
  cursor: pointer;
}

@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .left-grid,
  .right {
    height: auto;
    min-height: 0;
  }

  .left-grid {
    grid-template-rows: auto 240px auto 280px;
  }

  .right {
    grid-template-rows: 280px 240px;
  }

  .audio-bar {
    width: 92%;
  }
}
</style>
