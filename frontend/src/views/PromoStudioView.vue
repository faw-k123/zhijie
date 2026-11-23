<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import PromoReportView from './PromoReportView.vue'
import AiMusicView from './AiMusicView.vue'
import VideoBgmView from './VideoBgmView.vue'

type StudioTab = 'copy' | 'music' | 'video'

const route = useRoute()
const router = useRouter()

const tabs: { key: StudioTab; index: string; title: string; description: string }[] = [
  { key: 'copy', index: '01', title: '宣传文案', description: '生成适合目标平台和受众的传播文字' },
  { key: 'music', index: '02', title: 'AI国风音乐', description: '为传播主题生成国风音乐与歌词' },
  { key: 'video', index: '03', title: '视频配乐', description: '分析视频画面并匹配中国传统音乐' },
]

const activeTab = computed<StudioTab>(() => {
  const requested = String(route.query.tab || 'copy')
  return requested === 'music' || requested === 'video' ? requested : 'copy'
})

function selectTab(tab: StudioTab) {
  void router.replace({ name: 'promotion', query: { ...route.query, tab } })
}
</script>

<template>
  <div class="studio-page editorial-page">
    <AppNav />

    <header class="studio-hero">
      <div>
        <span>CONTENT CREATION WORKSPACE</span>
        <h1>宣传内容创作</h1>
        <p>围绕同一个传播任务完成文案、国风音乐和视频配乐，已有旧页面地址会自动进入对应工具。</p>
      </div>
    </header>

    <nav class="studio-tabs" aria-label="宣传创作工具">
      <button
        v-for="item in tabs"
        :key="item.key"
        type="button"
        :class="{ active: activeTab === item.key }"
        @click="selectTab(item.key)"
      >
        <b>{{ item.index }}</b>
        <span><strong>{{ item.title }}</strong><small>{{ item.description }}</small></span>
      </button>
    </nav>

    <main class="studio-content">
      <PromoReportView v-if="activeTab === 'copy'" embedded />
      <AiMusicView v-else-if="activeTab === 'music'" embedded />
      <VideoBgmView v-else embedded />
    </main>
  </div>
</template>

<style scoped>
.studio-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 15% 12%, rgba(117, 177, 153, 0.1), transparent 28%),
    #06231e;
  color: #d8e2dc;
}

.studio-hero {
  max-width: 1280px;
  margin: 0 auto;
  padding: 44px 36px 24px;
  border-bottom: 1px solid rgba(151, 193, 176, 0.18);
}

.studio-hero span {
  color: #8fc7b1;
  font-size: 11px;
  letter-spacing: 0.22em;
}

.studio-hero h1 {
  margin: 8px 0 10px;
  color: #edf3ef;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: clamp(34px, 4vw, 54px);
  font-weight: 500;
}

.studio-hero p {
  max-width: 720px;
  margin: 0;
  color: #9eb1aa;
  line-height: 1.8;
}

.studio-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  max-width: 1280px;
  margin: 22px auto 0;
  padding: 0 36px;
}

.studio-tabs button {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border: 1px solid rgba(151, 193, 176, 0.2);
  background: rgba(7, 42, 35, 0.78);
  color: #a8bab3;
  text-align: left;
  cursor: pointer;
}

.studio-tabs button.active {
  border-color: #8fc7b1;
  background: rgba(23, 70, 58, 0.94);
  color: #eff5f1;
}

.studio-tabs b {
  color: #d9bd7d;
  font-size: 13px;
}

.studio-tabs span {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.studio-tabs strong { font-size: 15px; }
.studio-tabs small { color: #849b92; font-size: 12px; line-height: 1.45; }
.studio-content { max-width: 1280px; margin: 16px auto 0; padding: 0 24px 48px; }

@media (max-width: 760px) {
  .studio-hero { padding: 28px 18px 20px; }
  .studio-tabs { grid-template-columns: 1fr; padding: 0 18px; }
  .studio-content { padding: 0 8px 32px; }
}
</style>
