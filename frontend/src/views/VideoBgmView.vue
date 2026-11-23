<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import AppNav from '@/components/AppNav.vue'
import { analyzeVideo, type VideoAnalysis, type RecommendSong } from '@/api/videoBgm'

withDefaults(defineProps<{ embedded?: boolean }>(), { embedded: false })

const videoFile = ref<File | null>(null)
const videoUrl = ref('')
const videoRef = ref<HTMLVideoElement>()
const loading = ref(false)
const analysis = ref<VideoAnalysis | null>(null)
const recommendations = ref<RecommendSong[]>([])
const reason = ref('')
const errorMsg = ref('')
const currentAudio = ref<HTMLAudioElement | null>(null)
const playingId = ref<number | null>(null)
const dragOver = ref(false)

function loadFile(file: File) {
  if (!file.type.startsWith('video/')) {
    errorMsg.value = '请上传视频文件'
    return
  }
  videoFile.value = file
  videoUrl.value = URL.createObjectURL(file)
  analysis.value = null
  recommendations.value = []
  reason.value = ''
  errorMsg.value = ''
}

function handleUpload(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) loadFile(file)
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) loadFile(file)
}

function captureFrame(): string {
  const video = videoRef.value
  if (!video) return ''
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 360
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.8)
}

async function analyze() {
  if (!videoRef.value) return
  errorMsg.value = ''
  loading.value = true

  try {
    // 等待视频可以播放
    if (videoRef.value.readyState < 2) {
      await new Promise<void>((resolve) => {
        videoRef.value!.addEventListener('loadeddata', () => resolve(), { once: true })
      })
    }
    // 跳到视频中点截取画面
    const dur = videoRef.value.duration
    if (dur && isFinite(dur)) {
      videoRef.value.currentTime = dur / 2
      await new Promise<void>((resolve) => {
        videoRef.value!.addEventListener('seeked', () => resolve(), { once: true })
      })
    }

    const image = captureFrame()
    if (!image) {
      errorMsg.value = '截取视频画面失败'
      loading.value = false
      return
    }

    const res = await analyzeVideo(image)
    if (res.success) {
      analysis.value = res.analysis
      recommendations.value = res.recommendations || []
      reason.value = res.reason
    } else {
      errorMsg.value = '分析失败'
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    errorMsg.value = err.response?.data?.message || '分析失败，请检查后端是否启动'
  } finally {
    loading.value = false
  }
}

function getAssetUrl(path: string): string {
  if (!path) return ''
  try {
    return new URL(`/src/assets/${path}`, import.meta.url).href
  } catch {
    return ''
  }
}

function togglePlay(song: RecommendSong) {
  if (playingId.value === song.id) {
    currentAudio.value?.pause()
    playingId.value = null
    return
  }
  if (currentAudio.value) {
    currentAudio.value.pause()
  }
  const url = getAssetUrl(song.audio_url)
  if (!url) {
    errorMsg.value = '音频文件不存在'
    return
  }
  currentAudio.value = new Audio(url)
  currentAudio.value.play().catch(() => {
    errorMsg.value = '音频播放失败'
  })
  playingId.value = song.id
  currentAudio.value.onended = () => {
    playingId.value = null
  }
}

function download(song: RecommendSong) {
  const url = getAssetUrl(song.audio_url)
  if (!url) return
  const a = document.createElement('a')
  a.href = url
  a.download = `${song.title}.mp3`
  a.click()
}

function reset() {
  if (currentAudio.value) currentAudio.value.pause()
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
  videoFile.value = null
  videoUrl.value = ''
  analysis.value = null
  recommendations.value = []
  reason.value = ''
  errorMsg.value = ''
  playingId.value = null
}

onUnmounted(() => {
  currentAudio.value?.pause()
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
})
</script>

<template>
  <div class="page editorial-page video-page" :class="{ embedded }">
    <AppNav v-if="!embedded" />
    <div class="content">
      <h2 class="title">视频配乐</h2>
      <p class="desc">上传视频，AI 自动分析画面内容，智能推荐最契合的中国传统音乐</p>

      <!-- 上传区 -->
      <div
        v-if="!videoUrl"
        class="upload-zone"
        :class="{ dragOver }"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop="handleDrop"
        @click="(e) => (e.currentTarget as HTMLElement).querySelector('input')?.click()"
      >
        <div class="upload-icon">▶</div>
        <p>点击或拖拽上传视频</p>
        <p class="hint">支持 MP4 / WebM / MOV 格式</p>
        <input type="file" accept="video/*" @change="handleUpload" hidden />
      </div>

      <!-- 视频预览 + 分析 -->
      <div v-else class="preview-section">
        <div class="video-wrapper">
          <video ref="videoRef" :src="videoUrl" controls preload="metadata" />
        </div>
        <div class="actions">
          <button class="btn-primary" @click="analyze" :disabled="loading">
            {{ loading ? 'AI 分析中...' : '开始 AI 分析' }}
          </button>
          <button class="btn-secondary" @click="reset">重新上传</button>
        </div>
      </div>

      <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

      <!-- 分析结果 -->
      <div v-if="analysis" class="result-section">
        <h3 class="section-title">AI 分析结果</h3>
        <div class="analysis-grid">
          <div class="analysis-card">
            <span class="label">场景</span>
            <span class="value">{{ analysis.scene }}</span>
          </div>
          <div class="analysis-card">
            <span class="label">情绪</span>
            <span class="value">{{ analysis.mood }}</span>
          </div>
          <div class="analysis-card">
            <span class="label">人物/服饰</span>
            <span class="value">{{ analysis.character }}</span>
          </div>
          <div class="analysis-card">
            <span class="label">节奏</span>
            <span class="value">{{ analysis.rhythm }}</span>
          </div>
        </div>
      </div>

      <!-- 推荐理由 -->
      <div v-if="reason" class="reason-section">
        <h3 class="section-title">推荐理由</h3>
        <p class="reason-text">{{ reason }}</p>
      </div>

      <!-- 推荐音乐 -->
      <div v-if="recommendations.length" class="music-section">
        <h3 class="section-title">为你推荐的配乐</h3>
        <div class="music-list">
          <div v-for="song in recommendations" :key="song.id" class="music-card">
            <img
              v-if="song.cover_url"
              :src="getAssetUrl(song.cover_url)"
              class="cover"
              :alt="song.title"
              @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')"
            />
            <div class="music-info">
              <span class="music-title">{{ song.title }}</span>
              <span class="music-genre">{{ song.genre }}</span>
            </div>
            <div class="music-actions">
              <button
                class="btn-play"
                @click="togglePlay(song)"
              >
                {{ playingId === song.id ? '⏸' : '▶' }}
              </button>
              <button class="btn-download" @click="download(song)" title="下载配乐">⬇</button>
            </div>
          </div>
        </div>
        <p class="export-hint">
          下载配乐后，可使用剪映、Premiere 等视频剪辑软件将音乐与视频合并导出。
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
}

.page.embedded { min-height: auto; }

.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem 3rem;
}

.title {
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 1.6rem;
  color: #8b3a2a;
  letter-spacing: 0.05em;
  margin: 0 0 0.3rem;
}

.desc {
  color: #6a5a4a;
  font-size: 0.92rem;
  margin: 0 0 1.8rem;
}

/* 上传区 */
.upload-zone {
  border: 2px dashed #c4a87a;
  border-radius: 8px;
  padding: 4rem 2rem;
  text-align: center;
  cursor: pointer;
  background: #fffdf9;
  transition: border-color 0.2s, background 0.2s;
}

.upload-zone:hover,
.upload-zone.dragover {
  border-color: #8b3a2a;
  background: #faf5ee;
}

.upload-icon {
  font-size: 3rem;
  color: #c4a87a;
  margin-bottom: 1rem;
}

.upload-zone p {
  color: #5a4a3a;
  margin: 0.3rem 0;
}

.upload-zone .hint {
  font-size: 0.82rem;
  color: #9a8a7a;
}

/* 视频预览 */
.preview-section {
  background: #fffdf9;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #ddd2c4;
}

.video-wrapper {
  border-radius: 6px;
  overflow: hidden;
  background: #000;
}

.video-wrapper video {
  width: 100%;
  display: block;
  max-height: 450px;
}

.actions {
  display: flex;
  gap: 0.8rem;
  margin-top: 1rem;
}

.btn-primary {
  padding: 0.65rem 1.8rem;
  border: none;
  border-radius: 4px;
  background: #8b3a2a;
  color: #fff;
  font-size: 0.95rem;
  cursor: pointer;
  letter-spacing: 0.05em;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.65rem 1.2rem;
  border: 1px solid #c4a87a;
  border-radius: 4px;
  background: transparent;
  color: #8b3a2a;
  font-size: 0.95rem;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #faf5ee;
}

.error {
  color: #c0392b;
  margin: 1rem 0;
  padding: 0.8rem;
  background: #fdf0ee;
  border-radius: 4px;
  font-size: 0.9rem;
}

/* 结果区 */
.result-section,
.reason-section,
.music-section {
  margin-top: 1.8rem;
}

.section-title {
  font-size: 1.1rem;
  color: #8b3a2a;
  margin: 0 0 0.8rem;
  padding-bottom: 0.4rem;
  border-bottom: 2px solid #e8dcc8;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.8rem;
}

.analysis-card {
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.analysis-card .label {
  font-size: 0.8rem;
  color: #9a8a7a;
}

.analysis-card .value {
  font-size: 1.05rem;
  color: #4a3a2a;
  font-weight: 600;
}

.reason-text {
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  border-radius: 6px;
  padding: 1.2rem;
  color: #4a3a2a;
  line-height: 1.7;
  font-size: 0.95rem;
}

/* 音乐列表 */
.music-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.music-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  border-radius: 6px;
  padding: 0.8rem 1rem;
}

.cover {
  width: 50px;
  height: 50px;
  border-radius: 4px;
  object-fit: cover;
  flex-shrink: 0;
  background: #e8dcc8;
}

.music-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.music-title {
  font-size: 1rem;
  color: #4a3a2a;
  font-weight: 600;
}

.music-genre {
  font-size: 0.82rem;
  color: #9a8a7a;
}

.music-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-play,
.btn-download {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-play {
  background: #8b3a2a;
  color: #fff;
}

.btn-play:hover {
  background: #a04a3a;
}

.btn-download {
  background: #e8dcc8;
  color: #8b3a2a;
}

.btn-download:hover {
  background: #d8ccb8;
}

.export-hint {
  margin-top: 1rem;
  font-size: 0.85rem;
  color: #9a8a7a;
  text-align: center;
  padding: 0.6rem;
  background: #faf5ee;
  border-radius: 4px;
}
</style>
