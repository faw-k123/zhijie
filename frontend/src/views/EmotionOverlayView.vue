<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchEmotionSubcategories } from '@/api/dataDisplay'

const router = useRouter()
const tabs = ['民歌', '戏曲', '说唱', '乐器'] as const
const activeTab = ref<(typeof tabs)[number]>('民歌')
const keyword = ref('')
const loading = ref(false)
const items = ref<{ id: string; name: string; thumb_url?: string }[]>([])

const list = computed(() => {
  const q = keyword.value.trim()
  if (!q) return items.value
  return items.value.filter((i) => i.name.includes(q))
})

/** 对接：GET /api/emotion/subcategories/ → 关系数据库小类列表 */
async function loadSubcategories(category: string) {
  loading.value = true
  try {
    const res = await fetchEmotionSubcategories(category)
    const data = res.data as { subcategories?: { id: string; name: string; thumb_url?: string }[] }
    items.value = data?.subcategories || []
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

watch(activeTab, (c) => {
  loadSubcategories(c)
})

function closeOverlay() {
  router.push({ name: 'home' })
}

/** 网格项是小类：进入详情页再拉歌曲与资源 */
function openItem(subcategory: string) {
  router.push({
    name: 'music-detail',
    params: { category: activeTab.value, subcategory },
  })
}

onMounted(() => {
  const savedCategory = router.currentRoute.value.query.category as string
  if (savedCategory && tabs.includes(savedCategory as typeof tabs[number])) {
    activeTab.value = savedCategory as typeof tabs[number]
  }
  loadSubcategories(activeTab.value)
})
</script>

<template>
  <div class="overlay-page">
    <div class="backdrop" @click="closeOverlay" />

    <div class="notebook">
      <aside class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab"
          type="button"
          class="tab"
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </aside>

      <section class="panel">
        <button class="close" type="button" @click="closeOverlay">×</button>
        <div class="search-row">
          <input v-model="keyword" type="search" :placeholder="`搜索${activeTab}小类...`" />
        </div>
        <div class="grid">
          <p v-if="loading" class="empty">加载小类中...</p>
          <button
            v-for="item in list"
            :key="item.id"
            type="button"
            class="card"
            @click="openItem(item.name)"
          >
            <div class="thumb">{{ item.name.slice(0, 1) }}</div>
            <h3>{{ item.name }}</h3>
            <p>小类 · 点击查看歌曲</p>
          </button>
          <p v-if="!loading && list.length === 0" class="empty">暂无匹配内容</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.overlay-page {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.backdrop {
  position: absolute;
  inset: 0;
  background: transparent;
}

.notebook {
  position: relative;
  z-index: 1;
  display: flex;
  width: min(960px, 100%);
  height: min(620px, 88vh);
  filter: drop-shadow(0 18px 40px rgba(0, 0, 0, 0.35));
}

.tabs {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 0.55rem;
  padding-top: 2.5rem;
  width: 88px;
  flex-shrink: 0;
}

.tab {
  border: none;
  background: linear-gradient(160deg, var(--gf-pink-light, #f0a1a8) 0%, var(--gf-border, #f0d9c0) 100%);
  color: var(--gf-text, #411c35);
  padding: 0.85rem 0.4rem;
  border-radius: 10px 0 0 10px;
  cursor: pointer;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 0.95rem;
  box-shadow: inset -2px 0 0 rgba(0, 0, 0, 0.06);
  transform: translateX(6px);
  transition:
    transform 0.15s ease,
    background 0.15s ease,
    color 0.15s ease;
}

.tab.active {
  background: #fff8ec;
  transform: translateX(0);
  font-weight: 700;
  color: var(--gf-maroon, #801d3a);
}

.panel {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 248, 236, 0.9);
  border-radius: 0 8px 8px 0;
  border: 1px solid rgba(240, 217, 192, 0.7);
  border-left: 3px solid var(--gf-maroon, #801d3a);
  overflow: hidden;
}

.close {
  position: absolute;
  top: 8px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  color: var(--gf-text-muted, #8b7480);
  cursor: pointer;
  z-index: 2;
  transition: color 0.15s ease;
}

.close:hover {
  color: var(--gf-maroon, #801d3a);
}

.search-row {
  flex: 2;
  display: flex;
  align-items: center;
  padding: 1.4rem 1.4rem 0.6rem;
}

.search-row input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--gf-border, #f0d9c0);
  background: #fff;
  color: var(--gf-text, #411c35);
  outline: none;
  font-size: 1rem;
}

.search-row input:focus {
  border-color: var(--gf-blue-deep, #29509b);
}

.grid {
  flex: 8;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.9rem;
  padding: 0.8rem 1.4rem 1.4rem;
  overflow: auto;
  align-content: start;
}

.card {
  position: relative;
  border: 1px solid rgba(240, 217, 192, 0.7);
  background: rgba(255, 248, 236, 0.95);
  padding: 0.9rem;
  text-align: left;
  cursor: pointer;
  min-height: 140px;
  transition:
    border-color 0.15s ease,
    transform 0.15s ease,
    box-shadow 0.15s ease;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('@/assets/images/bg_detail.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.15;
  pointer-events: none;
}

.card:hover {
  border-color: var(--gf-maroon, #801d3a);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(128, 29, 58, 0.12);
}

.thumb {
  width: 42px;
  height: 42px;
  border-radius: 4px;
  background: linear-gradient(135deg, var(--gf-rose, #b45a7e), var(--gf-maroon, #801d3a));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-bottom: 0.6rem;
}

.card h3 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  color: var(--gf-text, #411c35);
}

.card p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--gf-text-muted, #8b7480);
}

.empty {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--gf-text-muted, #8b7480);
}

@media (max-width: 700px) {
  .notebook {
    flex-direction: column;
    height: auto;
    max-height: 90vh;
  }

  .tabs {
    flex-direction: row;
    width: 100%;
    padding: 0.6rem 0.6rem 0;
    gap: 0.35rem;
  }

  .tab {
    flex: 1;
    border-radius: 8px 8px 0 0;
    transform: none;
  }

  .panel {
    border-radius: 0 0 8px 8px;
    border-left: 1px solid var(--gf-border, #f0d9c0);
    border-top: 3px solid var(--gf-maroon, #801d3a);
    min-height: 420px;
  }

  .grid {
    grid-template-columns: 1fr;
  }

}
</style>
