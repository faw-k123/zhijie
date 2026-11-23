<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import { fetchProfile, updateProfile } from '@/api/auth'
import {
  fetchFavorites,
  fetchFolderSongs,
  fetchPersonalRecommend,
  fetchLikedSongs,
  deleteFavoriteFolder,
  removeFavoriteSong,
  type FavoriteFolderSummary,
  type RecommendItem,
} from '@/api/personalization'
import { useI18n } from '@/i18n'
import {
  circleOverride,
  loadTestModeConfig,
  musicPersonaOverride,
} from '@/stores/testOverrides'

const router = useRouter()
const { t } = useI18n()
const username = localStorage.getItem('username') || ''
const userId = localStorage.getItem('user_id') || ''

const profile = reactive({
  username,
  nickname: username,
  email: '',
  bio: '',
})

const form = reactive({
  nickname: '',
  email: '',
  bio: '',
  password: '',
})

const profileMsg = ref('')
const profileSaving = ref(false)

const recommend = ref<RecommendItem[]>([])
const recommendLoading = ref(false)
const recommendMsg = ref('')
const recommendMode = ref('')

const folders = ref<FavoriteFolderSummary[]>([])
const likedSongs = ref<{ id: string; title: string; intro?: string; mv_url?: string; cover_url?: string }[]>([])
const showFolderOverlay = ref(false)
const overlayFolderName = ref('')
const overlayFolderId = ref('')
const overlaySongs = ref<{ id: string; title: string; intro?: string; mv_url?: string; cover_url?: string }[]>([])
const overlayLoading = ref(false)

async function loadProfile() {
  try {
    const res = await fetchProfile(username)
    const data = res.data as {
      nickname?: string
      email?: string
      bio?: string
      username?: string
    }
    if (data) {
      profile.username = data.username || username
      profile.nickname = data.nickname || username
      profile.email = data.email || ''
      profile.bio = data.bio || ''
      form.nickname = profile.nickname
      form.email = profile.email
      form.bio = profile.bio
    }
  } catch {
    form.nickname = profile.nickname
  }
}

async function saveProfile() {
  profileMsg.value = ''
  profileSaving.value = true
  try {
    const res = await updateProfile({
      username,
      nickname: form.nickname.trim(),
      email: form.email.trim(),
      bio: form.bio.trim(),
      password: form.password || undefined,
    })
    const data = res.data as { nickname?: string; email?: string; bio?: string }
    if (data) {
      profile.nickname = data.nickname || form.nickname
      profile.email = data.email || form.email
      profile.bio = data.bio || form.bio
    }
    form.password = ''
    profileMsg.value = t('private.saveOk')
  } catch {
    profileMsg.value = t('private.saveFail')
  } finally {
    profileSaving.value = false
  }
}

async function loadRecommend() {
  recommendLoading.value = true
  recommendMsg.value = ''
  recommendMode.value = ''
  try {
    const res = await fetchPersonalRecommend(userId || username, {
      personaOverride: musicPersonaOverride.value,
      circleOverride: circleOverride.value,
    })
    // 接口形如 { success, data: { items, message, recommend_mode } }
    const payload = (res?.data ?? res) as {
      items?: RecommendItem[]
      message?: string
      recommend_mode?: string
    }
    recommend.value = (payload?.items || [])
      .filter((x) => x?.id && x?.title)
      .slice(0, 3)
    recommendMsg.value = payload?.message || ''
    recommendMode.value = payload?.recommend_mode || ''
  } catch {
    recommend.value = []
    recommendMsg.value = '【推荐失败】接口请求异常'
    recommendMode.value = ''
  } finally {
    recommendLoading.value = false
  }
}

// 悬停唱片：旋转 + 播放音频
const recAudio = ref<HTMLAudioElement | null>(null)
let recAudioEl: HTMLAudioElement | null = null

function onRecEnter(item: RecommendItem) {
  if (!item.audio_url) return
  if (!recAudioEl) {
    recAudioEl = new Audio()
    recAudioEl.volume = 0.6
  }
  recAudioEl.src = item.audio_url
  recAudioEl.currentTime = 0
  void recAudioEl.play().catch(() => {})
}

function onRecLeave() {
  if (recAudioEl) {
    recAudioEl.pause()
    recAudioEl.currentTime = 0
  }
}

async function loadFolders() {
  try {
    const res = await fetchFavorites(userId)
    folders.value = res.data?.folders || []
  } catch {
    folders.value = []
  }
}

async function loadLikedSongs() {
  try {
    const res = await fetchLikedSongs(userId)
    likedSongs.value = res.data?.songs || []
  } catch {
    likedSongs.value = []
  }
}

async function openFolder(folder: FavoriteFolderSummary) {
  showFolderOverlay.value = true
  overlayFolderName.value = folder.name
  overlayFolderId.value = folder.id
  overlaySongs.value = []
  overlayLoading.value = true
  try {
    const res = await fetchFolderSongs(userId, folder.id)
    overlayFolderName.value = res.data?.folder_name || folder.name
    overlaySongs.value = res.data?.songs || []
  } catch {
    overlaySongs.value = []
  } finally {
    overlayLoading.value = false
  }
}

async function removeSongFromFolder(songId: string, event: Event) {
  event.stopPropagation()
  try {
    const res = await removeFavoriteSong(userId, overlayFolderId.value, songId)
    if (res.success) {
      overlaySongs.value = overlaySongs.value.filter((s) => s.id !== songId)
    } else {
      alert(res.message || t('private.removeFail'))
    }
  } catch {
    alert(t('private.removeFail'))
  }
}

async function deleteFolder(folder: FavoriteFolderSummary, event: Event) {
  event.stopPropagation()
  if (folder.name === '默认收藏夹') {
    alert(t('private.cantDeleteDefault'))
    return
  }
  if (!confirm(t('private.confirmDeleteFolder', { name: folder.name }))) return
  try {
    const res = await deleteFavoriteFolder(userId, folder.id)
    if (res.success) {
      await loadFolders()
    } else {
      alert(res.message || t('private.deleteFail'))
    }
  } catch {
    alert(t('private.deleteFail'))
  }
}

function goMusic(id: string) {
  router.push({ name: 'music-display', params: { id } })
}

function logout() {
  localStorage.removeItem('username')
  localStorage.removeItem('show_personality_prompt')
  router.replace('/login')
}

watch(musicPersonaOverride, () => {
  void loadRecommend()
})

watch(circleOverride, () => {
  void loadRecommend()
})

onMounted(async () => {
  await loadTestModeConfig()
  // 收藏夹 / 我喜欢的 / 资料先并行快速加载，不被慢推荐阻塞
  void loadProfile()
  void loadFolders()
  void loadLikedSongs()
  void loadRecommend()
})

onUnmounted(() => {
  if (recAudioEl) {
    recAudioEl.pause()
    recAudioEl = null
  }
})
</script>

<template>
  <div class="space-page">
    <AppNav />

    <section class="panel profile-panel">
      <div class="profile-left">
        <div class="avatar">{{ (profile.nickname || username).slice(0, 1) }}</div>
        <button type="button" class="logout-btn" @click="logout">
          {{ t('private.logout') }}
        </button>
        <ul class="info-list">
          <li><span>{{ t('private.username') }}</span>{{ profile.username }}</li>
          <li><span>{{ t('private.nickname') }}</span>{{ profile.nickname || '—' }}</li>
          <li><span>{{ t('private.email') }}</span>{{ profile.email || '—' }}</li>
          <li><span>{{ t('private.bio') }}</span>{{ profile.bio || '—' }}</li>
        </ul>
      </div>
      <div class="profile-right">
        <h3>{{ t('private.editProfile') }}</h3>
        <form class="edit-form" @submit.prevent="saveProfile">
          <label>{{ t('private.nickname') }}<input v-model="form.nickname" type="text" /></label>
          <label>{{ t('private.email') }}<input v-model="form.email" type="email" /></label>
          <label>{{ t('private.bio') }}<textarea v-model="form.bio" rows="2" /></label>
          <label>
            {{ t('private.newPassword') }}
            <input v-model="form.password" type="password" :placeholder="t('private.pwdHint')" />
          </label>
          <div class="edit-actions">
            <p v-if="profileMsg" class="msg">{{ profileMsg }}</p>
            <button type="submit" :disabled="profileSaving">
              {{ profileSaving ? t('private.saving') : t('private.save') }}
            </button>
          </div>
        </form>
      </div>
    </section>

    <section class="panel recommend-panel">
      <h2>{{ t('private.recommend') }}</h2>
      <p v-if="recommendMsg" class="rec-mode-msg" :data-mode="recommendMode">{{ recommendMsg }}</p>
      <div v-if="recommendLoading" class="empty">{{ t('private.loading') }}</div>
      <div v-else-if="recommend.length" class="recommend-grid" aria-label="推荐曲目">
        <article
          v-for="item in recommend"
          :key="item.id"
          class="rec-item"
          role="button"
          tabindex="0"
          :title="item.title"
          @click="goMusic(item.id)"
          @keydown.enter="goMusic(item.id)"
          @mouseenter="onRecEnter(item)"
          @mouseleave="onRecLeave"
        >
          <div class="vinyl">
            <div class="vinyl-disc">
              <div class="vinyl-label">{{ (item.title || '?').slice(0, 1) }}</div>
            </div>
          </div>
          <p class="rec-title">{{ item.title }}</p>
          <p v-if="item.recommend_reason" class="rec-reason">{{ item.recommend_reason }}</p>
        </article>
      </div>
      <p v-else class="empty">{{ t('private.noRecommend') }}</p>
    </section>

    <section class="panel favorites-panel">
      <h2>{{ t('private.favorites') }}</h2>
      <div class="fav-grid">
        <button
          v-for="folder in folders"
          :key="folder.id"
          type="button"
          class="fav-cell"
          @click="openFolder(folder)"
        >
          <div class="fav-icon">
            <img v-if="folder.icon_url" :src="folder.icon_url" alt="" />
            <span v-else>📁</span>
          </div>
          <p>{{ folder.name }}</p>
          <button
            v-if="folder.name !== '默认收藏夹'"
            type="button"
            class="delete-btn"
            @click="deleteFolder(folder, $event)"
            :title="t('private.delete')"
          >
            ✕
          </button>
        </button>
        <p v-if="!folders.length" class="empty full">{{ t('private.noFavorites') }}</p>
      </div>
    </section>

    <section class="panel liked-panel">
      <h2>{{ t('private.liked') }}</h2>
      <div class="liked-grid">
        <article
          v-for="song in likedSongs"
          :key="song.id"
          class="liked-item"
          @click="goMusic(song.id)"
        >
          <div class="liked-thumb">
            <video v-if="song.cover_url?.endsWith('.mp4')" :src="song.cover_url" muted preload="metadata" />
            <img v-else-if="song.cover_url" :src="song.cover_url" :alt="song.title" />
            <video v-else-if="song.mv_url" :src="song.mv_url" muted preload="metadata" />
            <span v-else>{{ song.title.slice(0, 1) }}</span>
          </div>
          <p class="liked-title">{{ song.title }}</p>
        </article>
        <p v-if="!likedSongs.length" class="empty full">{{ t('private.noLiked') }}</p>
      </div>
    </section>

    <div v-if="showFolderOverlay" class="overlay-mask" @click.self="showFolderOverlay = false">
      <div class="overlay-panel">
        <header>
          <h3>{{ overlayFolderName }}</h3>
          <button type="button" @click="showFolderOverlay = false">{{ t('private.close') }}</button>
        </header>
        <div v-if="overlayLoading" class="empty">{{ t('private.loading') }}</div>
        <ul v-else class="overlay-list">
          <li
            v-for="song in overlaySongs"
            :key="song.id"
            @click="goMusic(song.id)"
          >
            <div class="ov-thumb">
              <video v-if="song.cover_url?.endsWith('.mp4')" :src="song.cover_url" muted preload="metadata" />
              <img v-else-if="song.cover_url" :src="song.cover_url" :alt="song.title" />
              <video v-else-if="song.mv_url" :src="song.mv_url" muted preload="metadata" />
              <span v-else>{{ song.title.slice(0, 1) }}</span>
            </div>
            <div class="ov-meta">
              <h4>{{ song.title }}</h4>
              <p>{{ song.intro || t('home.noIntro') }}</p>
            </div>
            <button
              type="button"
              class="ov-remove-btn"
              @click="removeSongFromFolder(song.id, $event)"
              :title="t('private.remove')"
            >
              ✕
            </button>
          </li>
          <li v-if="!overlaySongs.length" class="empty-item">{{ t('private.folderEmpty') }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.space-page {
  min-height: 100vh;
  background: transparent;
  color: #2f2a33;
  padding-bottom: 2.5rem;
}

.panel {
  width: 70%;
  margin: 1.25rem auto 0;
  background: #fbf8f0;
  border-radius: 14px;
  box-shadow: 0 10px 24px rgba(60, 40, 55, 0.12);
  border: 1px solid #e6dee3;
}

.profile-panel {
  height: 200px;
  display: grid;
  grid-template-columns: 2fr 8fr;
  overflow: hidden;
}

.profile-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  padding: 0.75rem;
  border-right: 1px solid #ede5eb;
  background: linear-gradient(160deg, #f6f1f4, #ece5eb);
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #9e2a38, #c98778);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: 700;
  border: 2px solid #d9c28a;
  flex-shrink: 0;
}

.logout-btn {
  border: 1px solid #c9b878;
  background: transparent;
  color: #c77b8a;
  font-size: 0.72rem;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  cursor: pointer;
  line-height: 1.2;
  flex-shrink: 0;
}

.logout-btn:hover {
  background: rgba(208, 63, 76, 0.1);
  border-color: #d03f4c;
  color: #d03f4c;
}

.info-list {
  list-style: none;
  margin: 0;
  padding: 0;
  width: 100%;
  font-size: 0.78rem;
  color: #6a4a55;
}

.info-list li {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 0.2rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-list span {
  color: #a89aa0;
  flex-shrink: 0;
  min-width: 2.4em;
}

.profile-right {
  padding: 0.65rem 1rem 0.75rem;
  overflow: auto;
}

.profile-right h3 {
  margin: 0 0 0.45rem;
  font-size: 0.95rem;
  color: #3a2a33;
}

.edit-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem 0.75rem;
}

.edit-form label {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  font-size: 0.75rem;
  color: #7a6470;
}

.edit-form label:nth-child(3) {
  grid-column: 1 / -1;
}

.edit-form input,
.edit-form textarea {
  border: 1px solid #c9c0c7;
  border-radius: 6px;
  padding: 0.3rem 0.5rem;
  font-size: 0.85rem;
  outline: none;
  resize: none;
  font-family: inherit;
}

.edit-actions {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
}

.edit-actions .msg {
  margin: 0;
  font-size: 0.8rem;
  color: #9e2a38;
}

.edit-actions button {
  border: none;
  background: #9e2a38;
  color: #fff;
  padding: 0.35rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.recommend-panel {
  height: 280px;
  padding: 0.75rem 1rem 0.9rem;
  display: flex;
  flex-direction: column;
}

.recommend-panel h2,
.favorites-panel h2 {
  margin: 0 0 0.65rem;
  font-size: 1.05rem;
  color: #3a2a33;
}

.rec-mode-msg {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  line-height: 1.4;
  color: #6a5560;
  padding: 0.35rem 0.55rem;
  border-radius: 6px;
  background: #f7f1f4;
}

.rec-mode-msg[data-mode='graph'] {
  color: #2f6b4f;
  background: #eaf6ef;
}

.rec-mode-msg[data-mode='random'] {
  color: #8a4b2f;
  background: #f8efe8;
}

.rec-mode-msg[data-mode='mixed'] {
  color: #5a4a8a;
  background: #f0eef8;
}

.rec-mode-msg[data-mode='hybrid'] {
  color: #315f55;
  background: #e9f3ef;
}

.recommend-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: 1fr;
  gap: 0.55rem 0.75rem;
  min-height: 0;
}

.rec-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  cursor: pointer;
  border-radius: 10px;
  transition: transform 0.2s, background 0.2s;
}

.rec-item:hover {
  transform: translateY(-3px);
  background: #f4eff2;
}

.rec-item:hover .vinyl-disc {
  animation: vinyl-spin 2.2s linear infinite;
}

@keyframes vinyl-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.vinyl {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vinyl-disc {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, #2f2a33 0 28%, transparent 29%),
    repeating-radial-gradient(circle at center, #1a1a1a 0 2px, #333 3px 4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  will-change: transform;
}

.vinyl-label {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #c9b878, #9e2a38);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.rec-title {
  margin: 0;
  font-size: 0.8rem;
  color: #3a2a33;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.rec-reason {
  margin: 0;
  max-width: 100%;
  color: #78666f;
  font-size: 0.68rem;
  line-height: 1.35;
  text-align: center;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.favorites-panel {
  padding: 0.9rem 1rem 1.2rem;
}

.fav-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.85rem;
}

.fav-cell {
  border: 1px solid #ede5eb;
  background: #fff;
  border-radius: 12px;
  padding: 1rem 0.75rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
}

.fav-cell:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(60, 40, 55, 0.12);
}

.fav-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #f0ebef;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-size: 1.4rem;
}

.fav-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.fav-cell p {
  margin: 0;
  font-size: 0.88rem;
  color: #3a2a33;
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border: none;
  background: rgba(208, 63, 76, 0.7);
  color: #fff;
  border-radius: 50%;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.fav-cell:hover .delete-btn {
  opacity: 1;
}

.liked-panel {
  padding: 0.9rem 1rem 1.2rem;
}

.liked-panel h2 {
  margin: 0 0 0.65rem;
  font-size: 1.05rem;
  color: #3a2a33;
}

.liked-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.85rem;
}

.liked-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  border: 1px solid #ede5eb;
  background: #fff;
  border-radius: 12px;
  padding: 0.85rem 0.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.liked-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(60, 40, 55, 0.12);
}

.liked-thumb {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(145deg, #c9d2d8, #a8b5bc);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-weight: 700;
  color: #3a2a33;
}

.liked-thumb video,
.liked-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.liked-title {
  margin: 0;
  font-size: 0.85rem;
  color: #3a2a33;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.empty {
  text-align: center;
  color: #9a8a92;
  font-size: 0.9rem;
  padding: 1rem;
}

.empty.full {
  grid-column: 1 / -1;
}

.overlay-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 32, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.overlay-panel {
  width: min(520px, 92vw);
  max-height: 70vh;
  background: #fbf8f0;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.overlay-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid #ede5eb;
}

.overlay-panel h3 {
  margin: 0;
  font-size: 1rem;
}

.overlay-panel header button {
  border: 1px solid #c9c0c7;
  background: #fff;
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
}

.overlay-list {
  list-style: none;
  margin: 0;
  padding: 0.5rem;
  overflow-y: auto;
}

.overlay-list li {
  display: grid;
  grid-template-columns: 3fr 7fr 1fr;
  gap: 0.75rem;
  padding: 0.55rem;
  border-bottom: 1px solid #ede5eb;
  cursor: pointer;
  border-radius: 8px;
}

.overlay-list li:hover {
  background: #f4eff2;
}

.ov-thumb {
  aspect-ratio: 16 / 10;
  background: linear-gradient(145deg, #c9d2d8, #a8b5bc);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #3a2a33;
}

.ov-thumb video,
.ov-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ov-meta h4 {
  margin: 0 0 0.3rem;
  font-size: 0.92rem;
}

.ov-meta p {
  margin: 0;
  font-size: 0.8rem;
  color: #8a7a82;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ov-remove-btn {
  border: none;
  background: rgba(208, 63, 76, 0.7);
  color: #fff;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.overlay-list li:hover .ov-remove-btn {
  opacity: 1;
}

.ov-remove-btn:hover {
  background: #d03f4c;
}

.empty-item {
  display: block !important;
  text-align: center;
  color: #9a8a92;
  cursor: default !important;
  padding: 1.5rem !important;
}

@media (max-width: 900px) {
  .panel {
    width: 92%;
  }

  .profile-panel {
    height: auto;
    grid-template-columns: 1fr;
  }

  .recommend-panel {
    height: auto;
  }

  .fav-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
