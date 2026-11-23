<script setup lang="ts">
import { ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import { generateAiMusic, getAiMusicStatus, generateAiLyrics } from '@/api/personalization'
import { useI18n } from '@/i18n'

withDefaults(defineProps<{ embedded?: boolean }>(), { embedded: false })

const { t } = useI18n()

const mode = ref<'instrumental' | 'lyrics'>('instrumental')
const title = ref('')
const style = ref('古风')
const mood = ref('')
const theme = ref('')
const keywords = ref('')
const prompt = ref('')
const lyrics = ref('')
const vocalGender = ref('')
const result = ref('')
const audioUrl = ref('')
const loading = ref(false)
const lyricsLoading = ref(false)
const polling = ref(false)
const taskId = ref('')

let pollInterval: number | null = null

const styleOptions = [
  { label: '古风', value: '古风' },
  { label: '民乐', value: '民乐' },
  { label: '戏曲风', value: '戏曲风' },
  { label: '融合流行', value: '融合流行' },
  { label: '仙侠风', value: '仙侠风' },
  { label: '江南小调', value: '江南小调' },
  { label: '宫廷雅乐', value: '宫廷雅乐' },
]

const moodOptions = [
  { label: '宁静', value: '宁静' },
  { label: '激昂', value: '激昂' },
  { label: '欢快', value: '欢快' },
  { label: '忧伤', value: '忧伤' },
  { label: '悠远', value: '悠远' },
  { label: '豪迈', value: '豪迈' },
  { label: '温婉', value: '温婉' },
  { label: '空灵', value: '空灵' },
]

const themeOptions = [
  { label: '山水意境', value: '山水意境' },
  { label: '江湖豪情', value: '江湖豪情' },
  { label: '爱情相思', value: '爱情相思' },
  { label: '思乡之情', value: '思乡之情' },
  { label: '边塞风光', value: '边塞风光' },
  { label: '诗词歌赋', value: '诗词歌赋' },
  { label: '神话传说', value: '神话传说' },
  { label: '田园牧歌', value: '田园牧歌' },
]

const keywordTags = [
  '古筝', '琵琶', '二胡', '笛子', '古琴', '箫', '鼓', '编钟',
  '明月', '清风', '流水', '青山', '白云', '夕阳', '烟雨', '霜雪',
  '剑', '酒', '江湖', '侠客', '红颜', '相思', '离别', '重逢',
]

function toggleKeyword(tag: string) {
  const keywordsList = keywords.value.split(',').map(k => k.trim()).filter(k => k)
  const index = keywordsList.indexOf(tag)
  if (index > -1) {
    keywordsList.splice(index, 1)
  } else {
    keywordsList.push(tag)
  }
  keywords.value = keywordsList.join(', ')
}

async function handleGenerateLyrics() {
  const username = localStorage.getItem('username') || 'guest'
  if (!style.value || !mood.value) {
    result.value = t('ai.selectFirst')
    return
  }
  
  lyricsLoading.value = true
  result.value = ''
  
  try {
    const res = await generateAiLyrics(username, {
      style: style.value,
      mood: mood.value,
      theme: theme.value,
      keywords: keywords.value,
    })
    const data = res.data as { success?: boolean; message?: string; lyrics?: string }
    
    if (data?.success && data?.lyrics) {
      lyrics.value = data.lyrics
      result.value = t('ai.lyricsSuccess')
    } else {
      result.value = data?.message || t('ai.lyricsFail')
    }
  } catch (e: unknown) {
    const err = e as { message?: string }
    result.value = t('ai.generateFail', { error: err.message || 'network error' })
  } finally {
    lyricsLoading.value = false
  }
}

async function handleGenerate() {
  const username = localStorage.getItem('username') || 'guest'
  loading.value = true
  polling.value = false
  result.value = ''
  audioUrl.value = ''
  taskId.value = ''

  try {
    const res = await generateAiMusic(username, {
      mode: mode.value,
      style: style.value,
      mood: mood.value,
      theme: theme.value,
      keywords: keywords.value,
      prompt: prompt.value,
      lyrics: lyrics.value,
      title: title.value || t('ai.untitled'),
      vocal_gender: vocalGender.value,
    })
    const data = res.data as { message?: string; audio_url?: string; title?: string; success?: boolean; task_id?: string; status?: string }

    if (data?.task_id) {
      taskId.value = data.task_id
      result.value = data.message || t('ai.submitted')
      startPolling()
    } else if (data?.audio_url) {
      result.value = data.message || t('ai.success')
      audioUrl.value = data.audio_url
      if (data?.title) {
        title.value = data.title
      }
    } else {
      result.value = data?.message || t('ai.fail')
    }
  } catch (e: unknown) {
    const err = e as { message?: string }
    result.value = t('ai.generateFail', { error: err.message || 'network error' })
  } finally {
    loading.value = false
  }
}

function startPolling() {
  if (!taskId.value) return

  polling.value = true
  let attempts = 0
  const maxAttempts = 120

  pollInterval = window.setInterval(async () => {
    attempts++
    if (attempts >= maxAttempts) {
      stopPolling()
      result.value = t('ai.timeout')
      return
    }

    try {
      const res = await getAiMusicStatus(taskId.value)
      const data = res.data as { message?: string; audio_url?: string; status?: string; success?: boolean; title?: string }

      if (data?.audio_url) {
        stopPolling()
        result.value = data.message || t('ai.success')
        audioUrl.value = data.audio_url
        if (data?.title) {
          title.value = data.title
        }
      } else if (data?.status === 'failed') {
        stopPolling()
        result.value = data.message || t('ai.fail')
      } else if (data?.status === 'complete') {
        stopPolling()
        result.value = t('ai.noAudio')
      } else {
        result.value = data?.message || t('ai.polling')
      }
    } catch (e: unknown) {
      result.value = t('ai.pollFail', { error: (e as { message?: string }).message || 'network error' })
    }
  }, 3000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  polling.value = false
}

const examplePrompts = [
  { name: '山水意境', value: '一首宁静的古筝曲，描绘山水意境，悠扬舒缓，中国传统乐器' },
  { name: '武侠豪情', value: '激昂的武侠风格音乐，大鼓与笛子合奏，气势磅礴，江湖气息浓厚' },
  { name: '江南小调', value: '江南水乡风格，琵琶与二胡演奏，婉转细腻，富有诗意' },
  { name: '宫廷雅乐', value: '古典宫廷音乐，编钟与古琴，庄重典雅，皇家气派' },
]

function usePrompt(promptText: string) {
  prompt.value = promptText
}
</script>

<template>
  <div class="page ai-music-page" :class="{ embedded }">
    <AppNav v-if="!embedded" />
    <div class="box">
      <h1>{{ t('ai.title') }}</h1>
      <p class="desc">{{ t('ai.desc') }}</p>

      <div class="mode-tabs">
        <button type="button" :class="['tab-btn', { active: mode === 'instrumental' }]" @click="mode = 'instrumental'">{{ t('ai.instrumentalMode') }}</button>
        <button type="button" :class="['tab-btn', { active: mode === 'lyrics' }]" @click="mode = 'lyrics'">{{ t('ai.lyricsMode') }}</button>
      </div>

      <label>
        {{ t('ai.titleLabel') }}
        <input v-model="title" type="text" :placeholder="t('ai.titlePlaceholder')" />
      </label>

      <label>
        {{ t('ai.styleLabel') }}
        <select v-model="style">
          <option v-for="opt in styleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </label>

      <label>
        {{ t('ai.moodLabel') }}
        <select v-model="mood">
          <option value="">{{ t('ai.selectMood') }}</option>
          <option v-for="opt in moodOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </label>

      <label>
        {{ t('ai.themeLabel') }}
        <select v-model="theme">
          <option value="">{{ t('ai.selectTheme') }}</option>
          <option v-for="opt in themeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </label>

      <label>
        {{ t('ai.keywordsLabel') }}
        <div class="keyword-container">
          <input v-model="keywords" type="text" :placeholder="t('ai.keywordsPlaceholder')" />
          <div class="keyword-tags">
            <button
              type="button"
              v-for="tag in keywordTags"
              :key="tag"
              :class="['keyword-tag', { active: keywords.includes(tag) }]"
              @click="toggleKeyword(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>
      </label>

      <label v-if="mode === 'instrumental'">
        {{ t('ai.promptLabel') }}
        <textarea v-model="prompt" rows="4" :placeholder="t('ai.promptPlaceholder')" />
      </label>

      <div v-if="mode === 'instrumental'" class="examples">
        <p class="examples-title">{{ t('ai.examplesTitle') }}</p>
        <div class="example-list">
          <button type="button" v-for="example in examplePrompts" :key="example.name" @click="usePrompt(example.value)" class="example-btn">
            {{ example.name }}
          </button>
        </div>
      </div>

      <div v-if="mode === 'lyrics'" class="lyrics-section">
        <div class="lyrics-header">
          <label class="lyrics-label">{{ t('ai.lyricsLabel') }}</label>
          <button type="button" :disabled="lyricsLoading || !style || !mood" @click="handleGenerateLyrics" class="generate-lyrics-btn">
            {{ lyricsLoading ? t('ai.generating') : t('ai.generateLyrics') }}
          </button>
        </div>
        <textarea v-model="lyrics" rows="8" :placeholder="t('ai.lyricsPlaceholder')" />
        <p class="lyrics-hint">{{ t('ai.lyricsHint') }}</p>
      </div>

      <label v-if="mode === 'lyrics'">
        {{ t('ai.genderLabel') }}
        <select v-model="vocalGender">
          <option value="">{{ t('ai.genderAuto') }}</option>
          <option value="f">{{ t('ai.genderFemale') }}</option>
          <option value="m">{{ t('ai.genderMale') }}</option>
        </select>
      </label>

      <button type="button" :disabled="loading || polling || (!prompt && mode === 'instrumental') || (!lyrics && mode === 'lyrics')" @click="handleGenerate" class="generate-btn">
        {{ loading ? t('ai.submitting') : (polling ? t('ai.generating') : t('ai.generateMusic')) }}
      </button>

      <div v-if="polling" class="polling-container">
        <div class="spinner"></div>
        <span class="polling-text">{{ result || t('ai.polling') }}</span>
      </div>

      <div v-if="result && !polling" :class="['result-box', { success: audioUrl || (mode === 'lyrics' && lyrics && !audioUrl), error: !audioUrl && !lyrics && result }]">
        <pre>{{ result }}</pre>
      </div>

      <div v-if="audioUrl" class="audio-container">
        <h3>{{ t('ai.resultTitle', { title: title || t('ai.untitled') }) }}</h3>
        <audio :src="audioUrl" controls class="audio-player" />
        <a :href="audioUrl" target="_blank" download class="download-btn">{{ t('ai.downloadAudio') }}</a>
      </div>

      <div v-if="taskId" class="task-info">
        <p>{{ t('ai.taskId', { id: taskId }) }}</p>
        <button type="button" @click="startPolling" :disabled="polling">{{ t('ai.retry') }}</button>
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

.box {
  max-width: 600px;
  margin: 2rem auto;
  padding: 1.5rem;
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

h1 {
  margin: 0;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  color: #3d2f24;
  font-size: 1.5rem;
}

.desc {
  margin: 0;
  color: #7a6a5a;
  font-size: 0.9rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.88rem;
  color: #5a4a3a;
}

input,
select,
textarea {
  padding: 0.55rem 0.7rem;
  border: 1px solid #cfc5b8;
  font: inherit;
  border-radius: 4px;
  background: #fff;
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: #8b3a2a;
}

button {
  padding: 0.6rem 1.2rem;
  border: none;
  background: #8b3a2a;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  font-size: 1rem;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #a54a3a;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.mode-tabs {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.tab-btn {
  padding: 0.6rem 1.2rem;
  background: #e8e0d8;
  color: #5a4a3a;
  font-size: 0.95rem;
  font-weight: 500;
}

.tab-btn.active {
  background: #8b3a2a;
  color: #fff;
}

.keyword-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.keyword-tag {
  padding: 0.3rem 0.7rem;
  background: #f5f0ea;
  color: #5a4a3a;
  font-size: 0.82rem;
  border: 1px solid #cfc5b8;
  border-radius: 20px;
  transition: all 0.2s;
}

.keyword-tag:hover {
  background: #e8e0d8;
  border-color: #8b3a2a;
}

.keyword-tag.active {
  background: #8b3a2a;
  color: #fff;
  border-color: #8b3a2a;
}

.examples {
  margin-top: 0.5rem;
}

.examples-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.88rem;
  color: #5a4a3a;
}

.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.example-btn {
  padding: 0.4rem 0.8rem;
  background: #f5f0ea;
  color: #5a4a3a;
  font-size: 0.85rem;
  border: 1px solid #cfc5b8;
}

.example-btn:hover {
  background: #e8e0d8;
  border-color: #8b3a2a;
}

.lyrics-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.lyrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.lyrics-label {
  margin: 0;
  font-size: 0.88rem;
  color: #5a4a3a;
}

.generate-lyrics-btn {
  align-self: flex-end;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  font-size: 0.9rem;
  padding: 0.5rem 1rem;
}

.generate-lyrics-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
}

.lyrics-hint {
  margin: 0;
  font-size: 0.82rem;
  color: #8b7a6a;
  font-style: italic;
}

.generate-btn {
  align-self: flex-start;
  margin-top: 0.5rem;
  padding: 0.7rem 1.5rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.polling-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #cfc5b8;
  border-top-color: #8b3a2a;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.polling-text {
  font-size: 0.9rem;
  color: #7a6a5a;
}

.result-box {
  margin-top: 0.5rem;
  padding: 0.85rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.result-box.success {
  background: #f0f8f0;
  border: 1px solid #b8d8b8;
}

.result-box.error {
  background: #fdf0f0;
  border: 1px solid #d8b8b8;
}

.result-box pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
}

.audio-container {
  margin-top: 1rem;
  padding: 1rem;
  background: #faf6f0;
  border-radius: 8px;
  border: 1px solid #ddd2c4;
}

.audio-container h3 {
  margin: 0 0 0.75rem 0;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  color: #3d2f24;
}

.audio-player {
  width: 100%;
  margin-bottom: 0.75rem;
}

.download-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #8b3a2a;
  color: #fff;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.download-btn:hover {
  background: #a54a3a;
}

.task-info {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: #f5f0ea;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #5a4a3a;
}

.task-info p {
  margin: 0 0 0.5rem 0;
}
</style>
