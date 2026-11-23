<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import { fetchGuessLike, recordListen } from '@/api/personalization'

const songs = ref<{ id: string; title: string; audio_url?: string }[]>([])
const playingId = ref<string | null>(null)
const loading = ref(true)
const audioEl = ref<HTMLAudioElement | null>(null)

/** 对接：POST /api/fun/guess-like/ → 个性化推荐 */
onMounted(async () => {
  const username = localStorage.getItem('username') || 'guest'
  try {
    const res = await fetchGuessLike(username)
    const data = res.data as { songs?: { id: string; title: string; audio_url?: string }[] }
    songs.value = data?.songs || []
  } catch {
    songs.value = []
  } finally {
    loading.value = false
  }
})

async function togglePlay(song: { id: string; title: string; audio_url?: string }) {
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
    recordListen(username, { song_id: song.id, title: song.title, source: 'guess_like' }).catch(
      () => undefined,
    )
  }
}
</script>

<template>
  <div class="page">
    <AppNav />
    <audio ref="audioEl" preload="none" @ended="playingId = null" />
    <div class="bg" />
    <div class="content">
      <div class="float-panel">
        <h1>猜你喜欢</h1>
        <p class="sub">基于你的听歌偏好与人格结果生成</p>
        <p v-if="loading" class="loading">正在获取推荐列表...</p>
        <ul v-else>
          <li v-for="song in songs" :key="song.id">
            <span>{{ song.title }}</span>
            <button type="button" @click="togglePlay(song)">
              {{ playingId === song.id ? '暂停' : '播放' }}
            </button>
          </li>
          <li v-if="!songs.length" class="empty">暂无推荐</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.bg {
  position: absolute;
  inset: 0;
  background: transparent;
}

.content {
  position: relative;
  z-index: 1;
  min-height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.float-panel {
  width: min(480px, 100%);
  background: rgba(255, 253, 249, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
  padding: 1.5rem 1.35rem;
  backdrop-filter: blur(6px);
}

h1 {
  margin: 0;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 1.6rem;
  color: #8b3a2a;
}

.sub,
.loading,
.empty {
  margin: 0.4rem 0 1rem;
  color: #7a6a5a;
  font-size: 0.9rem;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 0.85rem;
  background: rgba(250, 246, 240, 0.9);
  border: 1px solid #e8dccb;
}

button {
  padding: 0.35rem 0.75rem;
  border: none;
  background: #8b3a2a;
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
}
</style>
