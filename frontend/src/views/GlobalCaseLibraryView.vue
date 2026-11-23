<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import CaseLibraryRow from '@/components/research/CaseLibraryRow.vue'
import PaginationBar from '@/components/research/PaginationBar.vue'
import ResearchState from '@/components/research/ResearchState.vue'
import SampleBadge from '@/components/research/SampleBadge.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import {
  fetchResearchCases,
  fetchResearchStatistics,
  fetchResearchStatus,
} from '@/api/research'
import type {
  ResearchCaseList,
  ResearchStatistics,
  ResearchStatus,
} from '@/types/research'

const route = useRoute()
const router = useRouter()

function queryString(key: string) {
  const value = route.query[key]
  return typeof value === 'string' ? value : ''
}

const filters = reactive({
  q: queryString('q'),
  country: queryString('country'),
  instrument: queryString('instrument'),
})
const initialPage = Number(route.query.page)
const page = ref(Number.isFinite(initialPage) && initialPage >= 1 ? Math.floor(initialPage) : 1)
const pageSize = 10

const status = ref<ResearchStatus | null>(null)
const statistics = ref<ResearchStatistics | null>(null)
const caseList = ref<ResearchCaseList | null>(null)
const metaError = ref('')
const error = ref('')
const loading = ref(true)
let requestSeq = 0

const sample = computed(() => caseList.value?.sample ?? statistics.value?.sample ?? status.value?.sample ?? null)
const countries = computed(() => statistics.value?.distributions.country ?? [])
const instruments = computed(() => statistics.value?.distributions.instrument ?? [])
const total = computed(() => caseList.value?.total ?? 0)
const pages = computed(() => caseList.value?.pagination.pages ?? 0)
const currentPage = computed(() => caseList.value?.pagination.page ?? page.value)
const hasFilters = computed(
  () => Boolean(filters.q || filters.country || filters.instrument),
)

function errorText(err: unknown) {
  const e = err as { message?: string }
  return e?.message || '网络请求失败'
}

function syncQuery() {
  const query: Record<string, string> = {}
  if (filters.q) query.q = filters.q
  if (filters.country) query.country = filters.country
  if (filters.instrument) query.instrument = filters.instrument
  if (page.value > 1) query.page = String(page.value)
  router.replace({ name: 'global-cases', query })
}

async function loadMeta() {
  const [statusResult, statisticsResult] = await Promise.allSettled([
    fetchResearchStatus(),
    fetchResearchStatistics({ analysis_sample: 'all' }),
  ])
  if (statusResult.status === 'fulfilled' && statusResult.value.data) {
    status.value = statusResult.value.data
  }
  if (statisticsResult.status === 'fulfilled' && statisticsResult.value.data) {
    statistics.value = statisticsResult.value.data
  }
  if (!status.value || !statistics.value) {
    metaError.value = '筛选选项未完整加载；仍可浏览全部案例。'
  } else {
    metaError.value = ''
  }
}

async function loadCases() {
  const seq = ++requestSeq
  loading.value = true
  error.value = ''
  try {
    const response = await fetchResearchCases({
      q: filters.q.trim() || undefined,
      country: filters.country || undefined,
      instrument: filters.instrument || undefined,
      analysis_sample: 'all',
      page: page.value,
      page_size: pageSize,
    })
    if (seq !== requestSeq) return
    if (!response.data) throw new Error('案例接口未返回有效数据')
    if (response.data.pagination.pages > 0 && page.value > response.data.pagination.pages) {
      page.value = response.data.pagination.pages
      syncQuery()
      await loadCases()
      return
    }
    caseList.value = response.data
    page.value = response.data.pagination.page
  } catch (err) {
    if (seq !== requestSeq) return
    error.value = `案例列表加载失败：${errorText(err)}`
    caseList.value = null
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

async function applyFilters(resetPage = true) {
  if (resetPage) page.value = 1
  syncQuery()
  await loadCases()
}

async function resetFilters() {
  filters.q = ''
  filters.country = ''
  filters.instrument = ''
  page.value = 1
  await applyFilters(false)
}

async function changePage(nextPage: number) {
  page.value = nextPage
  syncQuery()
  await loadCases()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  loading.value = true
  await Promise.all([loadMeta(), loadCases()])
})
</script>

<template>
  <div class="page research-page case-page">
    <AppNav />

    <main class="case-dashboard">
      <header class="case-hero">
        <div>
          <p class="case-eyebrow">CASE LIBRARY / 研究证据</p>
          <h1>案例库</h1>
          <p class="case-desc">
            检索全部{{ sample?.n ?? 0 }}个已审批海外传播案例。点开可查看摘要背景、因素评分、案例信息、
            来源索引、外国受众反馈证据与接受原因。
          </p>
        </div>
        <div class="hero-meta">
          <SampleBadge :sample="sample" mode="library" />
          <p>展示全部已审批海外传播案例</p>
          <small>数据版本 {{ status?.version.active_version || '—' }}</small>
        </div>
      </header>

      <section class="mini-stats" aria-label="案例库概况">
        <div>
          <strong>{{ caseList?.analysis_scope.case_count ?? 0 }}</strong>
          <span>已审批案例</span>
        </div>
        <div>
          <strong>{{ countries.length }}</strong>
          <span>覆盖国家</span>
        </div>
        <div>
          <strong>{{ instruments.length }}</strong>
          <span>涉及乐器</span>
        </div>
      </section>

      <SectionCard
        title="检索与筛选"
        kicker="SEARCH & FILTER"
        subtitle="筛选由后端执行；只返回已审核且允许展示的案例。"
        tone="quiet"
      >
        <form class="filter-bar" @submit.prevent="applyFilters(true)">
          <label class="search-field">
            <span>关键词</span>
            <input
              v-model="filters.q"
              type="search"
              maxlength="100"
              placeholder="搜索演奏者、曲目、国家、乐器……"
            />
          </label>
          <label>
            <span>国家</span>
            <select v-model="filters.country" @change="applyFilters(true)">
              <option value="">全部国家</option>
              <option v-for="item in countries" :key="item.key" :value="item.key">
                {{ item.key }}（{{ item.count }}）
              </option>
            </select>
          </label>
          <label>
            <span>乐器</span>
            <select v-model="filters.instrument" @change="applyFilters(true)">
              <option value="">全部乐器</option>
              <option v-for="item in instruments" :key="item.key" :value="item.key">
                {{ item.key }}（{{ item.count }}）
              </option>
            </select>
          </label>
          <div class="filter-actions">
            <button type="submit" class="search-submit">搜索</button>
            <button v-if="hasFilters" type="button" class="reset-button" @click="resetFilters">
              重置
            </button>
          </div>
        </form>
        <p class="filter-note">
          本页检索全部{{ sample?.n ?? 0 }}个已审批案例；未审核记录不会混入结果。
        </p>
      </SectionCard>

      <div v-if="metaError" class="partial-alert" role="status">
        {{ metaError }}
        <button type="button" @click="loadMeta">重试筛选选项</button>
      </div>

      <section class="result-section" aria-live="polite">
        <div class="result-head">
          <div>
            <p class="result-kicker">MATCHED CASES</p>
            <h2>案例列表</h2>
          </div>
          <span class="result-count">共 {{ total }} 例</span>
        </div>

        <div v-if="loading" class="case-skeletons" aria-busy="true">
          <div v-for="n in 3" :key="n" class="case-skeleton">
            <i class="skeleton-cover" />
            <div>
              <i class="skeleton-line w30" />
              <i class="skeleton-line w70" />
              <i class="skeleton-line w55" />
            </div>
          </div>
        </div>

        <ResearchState
          v-else-if="error"
          kind="error"
          title="案例列表加载失败"
          :message="error"
          retryable
          @retry="loadCases"
        />

        <ResearchState
          v-else-if="total === 0"
          kind="empty"
          title="没有符合条件的案例"
          :message="hasFilters ? '可以清空筛选条件，查看全部已审核案例。' : '案例库尚未导入可展示数据。'"
          :retryable="hasFilters"
          retry-label="清空筛选"
          @retry="resetFilters"
        />

        <div v-else class="case-list">
          <CaseLibraryRow v-for="item in caseList?.items" :key="item.case_id" :item="item" />
        </div>

        <PaginationBar
          v-if="!loading && !error && total > 0"
          :page="currentPage"
          :pages="pages"
          :total="total"
          :page-size="pageSize"
          @change="changePage"
        />
      </section>

      <footer class="case-foot">
        <p>
          编码均分是案例有效指标的描述性均分（0—3），不等同于证据等级或传播成功率。
        </p>
        <p>案例详情可查看 10 项指标、逐项证据、来源链接与后端返回的相似案例。</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.case-page {
  min-height: 100vh;
  color: #e8f1ed;
}

.case-dashboard {
  position: relative;
  max-width: 1320px;
  margin: 0 auto;
  padding: clamp(32px, 5vw, 60px) clamp(20px, 4vw, 44px) 76px;
}

.case-dashboard::before {
  content: '';
  position: absolute;
  z-index: -1;
  top: -60px;
  right: 8%;
  width: min(560px, 70vw);
  height: 360px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(71, 139, 116, 0.14), transparent 68%);
  pointer-events: none;
}

.case-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 30px;
  padding-bottom: 26px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.18);
}

.case-eyebrow,
.result-kicker {
  margin: 0 0 12px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.18em;
}

.case-hero h1 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(42px, 5vw, 58px);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.04em;
}

.case-desc {
  max-width: 760px;
  margin: 18px 0 0;
  color: #9bb7ad;
  font-size: 13px;
  line-height: 1.9;
}

.hero-meta {
  flex: 0 0 min(300px, 34%);
}

.hero-meta p {
  margin: 10px 0 0;
  color: #c3d5cb;
  font-size: 12px;
  line-height: 1.6;
}

.hero-meta small {
  display: block;
  margin-top: 7px;
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 10px;
}

.mini-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin: 22px 0;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 10px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.mini-stats > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  background: rgba(8, 33, 30, 0.9);
}

.mini-stats strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 28px;
  font-weight: 500;
  line-height: 1;
}

.mini-stats span {
  color: #78948a;
  font-size: 10px;
}

.filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1.7fr) repeat(2, minmax(120px, 0.75fr)) auto;
  gap: 12px;
  align-items: end;
}

.filter-bar label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.filter-bar label > span {
  color: #8fa99f;
  font-size: 10px;
  letter-spacing: 0.04em;
}

.filter-bar input,
.filter-bar select {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 1px solid rgba(159, 198, 181, 0.2);
  border-radius: 5px;
  background: rgba(3, 20, 18, 0.55);
  color: #e8f1ed;
  font-size: 12px;
  outline: none;
}

.filter-bar input::placeholder {
  color: #6f8c81;
}

.filter-bar input:focus,
.filter-bar select:focus {
  border-color: rgba(143, 199, 177, 0.52);
}

.filter-bar option {
  background: #0b2823;
  color: #e8f1ed;
}

.filter-actions {
  display: flex;
  gap: 7px;
}

.search-submit,
.reset-button {
  height: 38px;
  padding: 0 16px;
  border-radius: 5px;
  font-size: 12px;
  cursor: pointer;
}

.search-submit {
  border: 1px solid #8fc7b1;
  background: #8fc7b1;
  color: #071c19;
}

.reset-button {
  border: 1px solid rgba(159, 198, 181, 0.22);
  background: transparent;
  color: #9bb7ad;
}

.filter-note {
  margin: 13px 0 0;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.7;
}

.partial-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  padding: 10px 13px;
  border: 1px solid rgba(226, 162, 118, 0.28);
  border-radius: 7px;
  background: rgba(126, 75, 42, 0.12);
  color: #d8b392;
  font-size: 11px;
  line-height: 1.6;
}

.partial-alert button {
  flex-shrink: 0;
  padding: 5px 9px;
  border: 1px solid rgba(217, 194, 138, 0.28);
  border-radius: 4px;
  background: transparent;
  color: #e8d4a8;
  font-size: 10px;
  cursor: pointer;
}

.result-section {
  margin-top: 24px;
}

.result-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 13px;
}

.result-kicker {
  margin-bottom: 7px;
}

.result-head h2 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 26px;
  font-weight: 500;
}

.result-count {
  color: #8fa99f;
  font-size: 11px;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-skeletons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-skeleton {
  display: flex;
  gap: 20px;
  padding: 18px;
  border: 1px solid rgba(159, 198, 181, 0.13);
  border-radius: 12px;
}

.skeleton-cover,
.skeleton-line {
  display: block;
  border-radius: 6px;
  background: linear-gradient(100deg, rgba(159, 198, 181, 0.05), rgba(159, 198, 181, 0.11), rgba(159, 198, 181, 0.05));
  background-size: 220% 100%;
  animation: shimmer 1.6s ease-in-out infinite;
}

.skeleton-cover {
  width: 100px;
  height: 100px;
  flex: 0 0 auto;
}

.case-skeleton > div {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 11px;
  padding-top: 8px;
}

.skeleton-line {
  height: 11px;
}

.w30 { width: 30%; }
.w55 { width: 55%; }
.w70 { width: 70%; }

.case-foot {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid rgba(159, 198, 181, 0.13);
}

.case-foot p {
  margin: 0 0 5px;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.8;
}

@keyframes shimmer {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}

@media (max-width: 1100px) {
  .filter-bar {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .search-field {
    grid-column: 1 / -1;
  }

  .filter-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 800px) {
  .case-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-meta {
    flex-basis: auto;
    width: 100%;
  }

  .mini-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }

  .search-field,
  .filter-actions {
    grid-column: auto;
  }
}

@media (max-width: 520px) {
  .case-dashboard {
    padding: 28px 16px 56px;
  }

  .case-hero h1 {
    font-size: 40px;
  }

  .mini-stats {
    margin: 18px 0;
  }

  .result-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 7px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-cover,
  .skeleton-line {
    animation: none;
  }
}
</style>
