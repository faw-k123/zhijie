<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import {
  fetchHomeFeed,
  fetchMusicResource,
  fetchSearchSuggestions,
  type MusicResourceDetail,
  type MusicResourceUrls,
} from '@/api/contentDisplay'
import { useI18n } from '@/i18n'

const router = useRouter()
const { t } = useI18n()

const keyword = ref('')
const searchFocused = ref(false)
const suggestions = ref<string[]>(['国风热歌', '古风 MV', '民乐合奏', '戏曲精选', '新锐国风'])
const showSuggestions = ref(false)

const feed = ref<MusicResourceUrls[]>([])
const details = ref<Record<string, MusicResourceDetail>>({})
const loading = ref(false)
const contentRef = ref<HTMLElement | null>(null)
const videoFailed = ref<Set<string>>(new Set())

async function loadFeed(refresh = false) {
  loading.value = true
  videoFailed.value = new Set()
  try {
    const res = await fetchHomeFeed({
      keyword: keyword.value.trim(),
      refresh,
    })
    const items = (res.data?.items || []).slice(0, 9)
    feed.value = items
    details.value = {}
    await Promise.all(
      items.map(async (item) => {
        try {
          const detailRes = await fetchMusicResource(item.id)
          if (detailRes.data) {
            details.value[item.id] = detailRes.data
          }
        } catch {
          details.value[item.id] = {
            id: item.id,
            title: item.title || `资源 ${item.id}`,
            intro: item.intro || t('home.noIntro'),
            mv_url: item.mv_url || '',
            audio_url: item.audio_url || '',
            lyrics: [],
          }
        }
      }),
    )
  } catch {
    feed.value = []
  } finally {
    loading.value = false
  }
}

async function onRefresh() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
  await nextTick()
  contentRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
  await loadFeed(true)
}

async function onSearchFocus() {
  searchFocused.value = true
  showSuggestions.value = true
  try {
    const res = await fetchSearchSuggestions(keyword.value)
    if (res.data?.suggestions?.length) {
      suggestions.value = res.data.suggestions
    }
  } catch {
  }
}

function onSearchBlur() {
  searchFocused.value = false
  setTimeout(() => {
    showSuggestions.value = false
  }, 180)
}

function applySuggestion(text: string) {
  keyword.value = text
  showSuggestions.value = false
  loadFeed(false)
}

function onHoverCard(videoEl: HTMLVideoElement | null) {
  if (!videoEl) return
  videoEl.muted = true
  videoEl.currentTime = 0
  videoEl.play().catch(() => undefined)
}

function onLeaveCard(videoEl: HTMLVideoElement | null) {
  if (!videoEl) return
  videoEl.pause()
  videoEl.currentTime = 0
}

function onVideoError(id: string) {
  if (!videoFailed.value.has(id)) {
    videoFailed.value = new Set(videoFailed.value).add(id)
  }
}

function hasMv(item: MusicResourceUrls): boolean {
  const url = details.value[item.id]?.mv_url || item.mv_url || ''
  return !!url && !videoFailed.value.has(item.id)
}

function goDisplay(id: string) {
  router.push({ name: 'music-display', params: { id } })
}

onMounted(async () => {
  await loadFeed(false)
})
</script>

<template>
  <div class="home-page">
    <AppNav />

    <section class="search-wrap">
      <div class="search-box" :class="{ focused: searchFocused }">
        <input
          v-model="keyword"
          type="text"
          :placeholder="t('home.searchPlaceholder')"
          @focus="onSearchFocus"
          @blur="onSearchBlur"
          @keyup.enter="loadFeed(false)"
        />
        <button type="button" class="search-btn" @mousedown.prevent="loadFeed(false)">
          {{ t('home.search') }}
        </button>
        <ul v-show="showSuggestions" class="suggestions">
          <li
            v-for="s in suggestions"
            :key="s"
            @mousedown.prevent="applySuggestion(s)"
          >
            {{ s }}
          </li>
        </ul>
      </div>
    </section>

    <section class="content-section">
      <div class="content-inner">
        <div class="content-head">
          <h2>{{ t('home.content') }}</h2>
          <button type="button" class="refresh-btn" :disabled="loading" @click="onRefresh">
            {{ loading ? t('home.refreshing') : t('home.refresh') }}
          </button>
        </div>

        <div ref="contentRef" class="content-grid-wrap">
          <div v-if="loading && !feed.length" class="empty">{{ t('home.loading') }}</div>
          <div v-else-if="!feed.length" class="empty">{{ t('home.empty') }}</div>
          <div v-else class="content-grid">
            <article
              v-for="item in feed"
              :key="item.id"
              class="card"
              @click="goDisplay(item.id)"
              @mouseenter="onHoverCard(($event.currentTarget as HTMLElement).querySelector('video'))"
              @mouseleave="onLeaveCard(($event.currentTarget as HTMLElement).querySelector('video'))"
            >
              <div class="thumb">
                <video
                  v-if="hasMv(item)"
                  :src="details[item.id]?.mv_url || item.mv_url"
                  muted
                  playsinline
                  preload="metadata"
                  @error="onVideoError(item.id)"
                />
                <div v-else class="thumb-placeholder">
                  <span>{{ (details[item.id]?.title || item.title || '?').slice(0, 1) }}</span>
                  <p>{{ t('home.mvPlaceholder') }}</p>
                </div>
              </div>
              <div class="card-meta">
                <h3>{{ details[item.id]?.title || item.title }}</h3>
                <p>{{ details[item.id]?.intro || item.intro || t('home.noIntro') }}</p>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  color: #2f2a33;
}

.search-wrap {
  display: flex;
  justify-content: center;
  padding: 1.5rem 1rem 0.5rem;
}

.search-box {
  position: relative;
  width: 50%;
  min-width: 260px;
  display: flex;
  background: #fbf8f0;
  border: 1px solid #c9c0c7;
  border-radius: 8px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box.focused {
  border-color: #9e2a38;
  box-shadow: 0 4px 16px rgba(158, 42, 56, 0.12);
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  background: transparent;
  border-radius: 8px 0 0 8px;
}

.search-btn {
  border: none;
  background: #9e2a38;
  color: #fff;
  padding: 0 1.2rem;
  cursor: pointer;
  border-radius: 0 8px 8px 0;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin: 0;
  padding: 0.35rem 0;
  list-style: none;
  background: #fbf8f0;
  border: 1px solid #d8cdd4;
  border-top: none;
  border-radius: 0 0 8px 8px;
  z-index: 20;
  max-height: 220px;
  overflow: auto;
}

.suggestions li {
  padding: 0.55rem 1rem;
  cursor: pointer;
  color: #6a4a55;
  font-size: 0.92rem;
}

.suggestions li:hover {
  background: #f0ebef;
}

.content-section {
  flex: 1;
  padding: 1rem 0 2.5rem;
  position: relative;
}

.content-inner {
  width: 70%;
  margin: 0 auto;
}

.content-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.content-head h2 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: #3a2a33;
}

.refresh-btn {
  position: sticky;
  top: 70px;
  z-index: 10;
  border: 1px solid #9e2a38;
  background: #fbf8f0;
  color: #9e2a38;
  padding: 0.45rem 1rem;
  cursor: pointer;
  border-radius: 8px;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.content-grid-wrap {
  max-height: calc(3 * 180px + 2 * 1rem);
  overflow-y: auto;
  padding: 0.35rem 0.35rem 0.75rem;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.card {
  background: #fbf8f0;
  border: 1px solid #e6dee3;
  border-radius: 12px;
  cursor: pointer;
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(60, 40, 55, 0.1);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 28px rgba(60, 40, 55, 0.2);
}

.thumb {
  aspect-ratio: 16 / 9;
  background: #c9d2d8;
  overflow: hidden;
  position: relative;
}

.thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  color: #6a4a55;
  background: linear-gradient(145deg, #c9d2d8, #a8b5bc);
}

.thumb-placeholder span {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  font-weight: 700;
}

.thumb-placeholder p {
  margin: 0;
  font-size: 0.8rem;
}

.card-meta {
  padding: 0.7rem 0.85rem 0.9rem;
}

.card-meta h3 {
  margin: 0 0 0.35rem;
  font-size: 0.98rem;
  color: #2f2a33;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta p {
  margin: 0;
  font-size: 0.82rem;
  color: #8a7a82;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #9a8a92;
}

@media (max-width: 900px) {
  .content-inner {
    width: 90%;
  }

  .content-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .search-box {
    width: 80%;
  }
}

@media (max-width: 560px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .search-box {
    width: 100%;
  }
}
</style>