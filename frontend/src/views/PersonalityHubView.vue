<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import CulturalCircleTest from './PersonalityTestView.vue'
import GuofengPersonaTest from './GuofengPersonaTestView.vue'

type TabKey = 'cultural-circle' | 'guofeng-persona'

const route = useRoute()
const router = useRouter()

const initialTab = route.query.tab === 'guofeng-persona' ? 'guofeng-persona' : 'cultural-circle'
const activeTab = ref<TabKey>(initialTab)
const returnTo = computed(() => {
  const value = String(route.query.returnTo || '')
  return value.startsWith('/') && !value.startsWith('//') ? value : ''
})

const tabs: { key: TabKey; label: string }[] = [
  { key: 'cultural-circle', label: '文化圈层匹配' },
  { key: 'guofeng-persona', label: '国风人设测试' },
]

watch(activeTab, (tab) => {
  void router.replace({ query: { ...route.query, tab } })
})

function returnToPreviousPage() {
  if (returnTo.value) void router.push(returnTo.value)
  else void router.push({ name: 'home' })
}
</script>

<template>
  <div class="hub-page">
    <AppNav />

    <div v-if="returnTo" class="return-notice">
      <span>完成测试后，系统会使用真实结果计算文化圈层和用户画像。</span>
      <button type="button" @click="returnToPreviousPage">返回原页面</button>
    </div>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <CulturalCircleTest v-if="activeTab === 'cultural-circle'" />
    <GuofengPersonaTest v-else />
  </div>
</template>

<style scoped>
.hub-page {
  min-height: 100vh;
  background: #e8e0d4;
}

.tab-bar {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  padding: 1.25rem 1.5rem 0;
}

.return-notice {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  max-width: 1000px;
  margin: 1rem auto 0;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(139, 58, 42, 0.22);
  background: rgba(255, 253, 249, 0.74);
  color: #5a4a3a;
  font-size: 0.88rem;
}

.return-notice button {
  padding: 0.45rem 0.8rem;
  border: 1px solid #8b3a2a;
  background: transparent;
  color: #8b3a2a;
  cursor: pointer;
  white-space: nowrap;
}

.tab-btn {
  padding: 0.6rem 1.4rem;
  border: 1px solid #cfc5b8;
  background: rgba(255, 253, 249, 0.6);
  color: #5a4a3a;
  font-size: 0.92rem;
  cursor: pointer;
  transition: all 0.15s;
}

.tab-btn:hover {
  border-color: #c4a87a;
}

.tab-btn.active {
  border-color: #8b3a2a;
  background: #8b3a2a;
  color: #fff;
}
</style>
