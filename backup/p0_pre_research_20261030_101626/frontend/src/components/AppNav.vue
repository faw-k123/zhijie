<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n, type LocaleCode } from '@/i18n'
import {
  circleOverride,
  culturalCircleOptions,
  loadTestModeConfig,
  musicPersonaOptions,
  musicPersonaOverride,
} from '@/stores/testOverrides'

const router = useRouter()
const route = useRoute()
const { t, locale, setLocale, locales } = useI18n()

const username = ref(localStorage.getItem('username') || '用户')
const showAvatarMenu = ref(false)
const showMusicMenu = ref(false)
const showFunMenu = ref(false)
const showPromoMenu = ref(false)
const showLangMenu = ref(false)
const mobileOpen = ref(false)

onMounted(() => {
  void loadTestModeConfig()
})

const musicCategories = [
  { key: '民歌', label: t('emotion.national') },
  { key: '戏曲', label: t('emotion.opera') },
  { key: '说唱', label: t('emotion.rap') },
  { key: '乐器', label: t('emotion.instrument') },
] as const

const activeKey = computed(() => {
  if (route.name === 'home') return 'home'
  if (route.name === 'emotion') return 'emotion'
  if (route.name === 'imagery') return 'imagery'
  if (route.name === 'music-show') return 'music'
  if (['promo-report', 'video-bgm'].includes(String(route.name))) return 'promo'

  if (['personality-test', 'ai-music'].includes(String(route.name))) return 'fun'
  if (route.name === 'about') return 'about'
  if (route.name === 'private-space') return 'private'
  if (route.name === 'profile') return 'profile'
  return ''
})

const currentLabel = computed(
  () => locales.find((o) => o.code === locale.value)?.label || locale.value,
)

function goHome() {
  router.push({ name: 'home' })
}

function goEmotion() {
  router.push({ name: 'emotion' })
}

function goMusicShow(category: string) {
  router.push({ name: 'music-show', params: { category } })
}

function goPrivateSpace() {
  router.push({ name: 'private-space' })
}

function logout() {
  localStorage.removeItem('username')
  router.push('/login')
}

function onPickLang(code: LocaleCode) {
  setLocale(code)
  localStorage.setItem('app_locale', code)
  showLangMenu.value = false
}
</script>

<template>
  <header class="top-nav">
    <button type="button" class="brand-mark" aria-label="返回首页" data-no-auto-translate @click="goHome">
      <span class="brand-name">智解国音</span>
      <span class="brand-note">GUOYIN</span>
    </button>
    <button
      type="button"
      class="menu-toggle"
      :aria-expanded="mobileOpen"
      aria-label="打开主导航"
      @click="mobileOpen = !mobileOpen"
    >
      <span></span><span></span>
    </button>
    <nav class="menu" :class="{ open: mobileOpen }">
      <a
        class="menu-item"
        :class="{ active: activeKey === 'home' }"
        href="javascript:;"
        @click="goHome"
      >
        {{ t('nav.home') }}
      </a>

      <div
        class="menu-item has-sub"
        :class="{ active: activeKey === 'music' }"
        @mouseenter="showMusicMenu = true"
        @mouseleave="showMusicMenu = false"
      >
        {{ t('nav.music') || '音乐展示' }}
        <div v-show="showMusicMenu" class="submenu">
          <a
            v-for="cat in musicCategories"
            :key="cat.key"
            href="javascript:;"
            @click="goMusicShow(cat.key)"
          >
            {{ cat.label }}
          </a>
        </div>
      </div>

      <a
        class="menu-item"
        :class="{ active: activeKey === 'emotion' }"
        href="javascript:;"
        @click="goEmotion"
      >
        {{ t('nav.emotion') }}
      </a>
      <a
        class="menu-item"
        :class="{ active: activeKey === 'imagery' }"
        href="javascript:;"
        @click="router.push({ name: 'imagery' })"
      >
        {{ t('nav.imagery') }}
      </a>
      <div
        class="menu-item has-sub"
        :class="{ active: activeKey === 'promo' }"
        @mouseenter="showPromoMenu = true"
        @mouseleave="showPromoMenu = false"
      >
        {{ t('nav.promo') }}
        <div v-show="showPromoMenu" class="submenu">
          <a href="javascript:;" @click="router.push({ name: 'promo-report' })">{{ t('nav.promoReport') }}</a>
          <a href="javascript:;" @click="router.push({ name: 'video-bgm' })">{{ t('nav.videoBgm') }}</a>
        </div>
      </div>
      <div
        class="menu-item has-sub"
        :class="{ active: activeKey === 'fun' }"
        @mouseenter="showFunMenu = true"
        @mouseleave="showFunMenu = false"
      >
        {{ t('nav.fun') }}
        <div v-show="showFunMenu" class="submenu">
          <a href="javascript:;" @click="router.push({ name: 'personality-test' })">{{ t('nav.personality') }}</a>
          <a href="javascript:;" @click="router.push({ name: 'ai-music' })">{{ t('nav.aiMusic') }}</a>
        </div>
      </div>

      <a
        class="menu-item"
        :class="{ active: activeKey === 'about' }"
        href="javascript:;"
        @click="router.push({ name: 'about' })"
      >
        {{ t('nav.about') }}
      </a>
    </nav>

    <div class="nav-actions">
      <div class="test-overrides" title="个性化推荐偏好">
        <label class="test-field">
          <span>文化圈层</span>
          <select v-model="circleOverride">
            <option
              v-for="opt in culturalCircleOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </label>
        <label class="test-field">
          <span>用户画像</span>
          <select v-model="musicPersonaOverride">
            <option
              v-for="opt in musicPersonaOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </label>
      </div>

      <div
        class="lang-wrap"
        @mouseenter="showLangMenu = true"
        @mouseleave="showLangMenu = false"
      >
        <button type="button" class="lang-btn" :title="t('nav.language')">
          {{ currentLabel }}
        </button>
        <div v-show="showLangMenu" class="submenu lang-menu">
          <a
            v-for="opt in locales"
            :key="opt.code"
            href="javascript:;"
            :class="{ active: opt.code === locale }"
            @click="onPickLang(opt.code)"
          >
            {{ opt.label }}
          </a>
        </div>
      </div>

      <div
        class="avatar-wrap"
        @mouseenter="showAvatarMenu = true"
        @mouseleave="showAvatarMenu = false"
      >
        <div class="avatar" :title="username">{{ username.slice(0, 1) }}</div>
        <div v-show="showAvatarMenu" class="submenu avatar-menu">
          <a href="javascript:;" @click="goPrivateSpace">{{ t('nav.private') || '私人空间' }}</a>
          <a href="javascript:;" @click="logout">{{ t('private.logout') }}</a>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0 1.25rem;
  height: 56px;
  background: var(--gf-navy, #181e38);
  color: var(--gf-cream, #feebc0);
  position: sticky;
  top: 0;
  z-index: 50;
}

.menu {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  flex-wrap: wrap;
  flex: 1;
}

.menu-item {
  position: relative;
  padding: 0.55rem 0.75rem;
  color: inherit;
  text-decoration: none;
  font-size: 0.92rem;
  white-space: nowrap;
  cursor: pointer;
}

.menu-item:hover,
.menu-item.active {
  color: var(--gf-blush, #ec7696);
  font-weight: 500;
}

.has-sub {
  display: inline-block;
}

.submenu {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 140px;
  background: var(--gf-navy, #181e38);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
  border-top: 2px solid var(--gf-blush, #ec7696);
  display: flex;
  flex-direction: column;
  z-index: 60;
}

.submenu a {
  padding: 0.65rem 0.9rem;
  color: var(--gf-cream, #feebc0);
  text-decoration: none;
  font-size: 0.88rem;
}

.submenu a:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--gf-blush, #ec7696);
}

.test-overrides {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-shrink: 0;
  margin-right: 0.35rem;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.test-field {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  color: #d9c28a;
  white-space: nowrap;
}

.test-field select {
  max-width: 200px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid #d9c28a;
  background: #1f2744;
  color: #feebc0;
  font-size: 0.72rem;
  padding: 0 0.35rem;
  cursor: pointer;
}

.test-field select option {
  background: #f4f7f5;
  color: #17372f;
}

.lang-wrap {
  position: relative;
  flex-shrink: 0;
}

.lang-btn {
  min-width: 108px;
  height: 34px;
  border-radius: 999px;
  border: 1px solid #d9c28a;
  background: linear-gradient(135deg, #9e2a38, #8c4356);
  color: #feebc0;
  font-size: 0.82rem;
  cursor: pointer;
  padding: 0 0.85rem;
  white-space: nowrap;
}

.lang-menu {
  right: 0;
  left: auto;
  min-width: 160px;
}

.avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gf-rose, #b45a7e), var(--gf-maroon, #801d3a));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  cursor: pointer;
  border: 2px solid var(--gf-cream, #feebc0);
}

.avatar-menu {
  right: 0;
  left: auto;
}
</style>
