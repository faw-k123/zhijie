<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import CasePreviewCard from '@/components/research/CasePreviewCard.vue'
import DistributionList from '@/components/research/DistributionList.vue'
import ResearchKpi from '@/components/research/ResearchKpi.vue'
import ResearchState from '@/components/research/ResearchState.vue'
import SampleBadge from '@/components/research/SampleBadge.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import {
  fetchResearchCases,
  fetchResearchStatistics,
  fetchResearchStatus,
  fetchResearchSuccessFactors,
} from '@/api/research'
import type {
  ResearchCaseSummary,
  ResearchCaseList,
  ResearchStatistics,
  ResearchStatus,
  ResearchSuccessFactors,
} from '@/types/research'

const loading = ref(true)
const fatalError = ref('')
const failed = ref<string[]>([])

const status = ref<ResearchStatus | null>(null)
const statistics = ref<ResearchStatistics | null>(null)
const caseList = ref<ResearchCaseList | null>(null)
const successFactors = ref<ResearchSuccessFactors | null>(null)
const countrySuccessFactors = ref<ResearchSuccessFactors | null>(null)
const selectedCountry = ref('')
const countryFactorLoading = ref(false)
const countryFactorError = ref('')
const reportCopyState = ref('')

const sample = computed(() => statistics.value?.sample ?? status.value?.sample ?? null)
const libraryCaseCount = computed(() => status.value?.counts.cases ?? 0)
const countryRows = computed(() => statistics.value?.distributions.country ?? [])
const allCases = computed(() => caseList.value?.items ?? [])
const representativeCases = computed(() => {
  const remaining = [...allCases.value]
  const chosen: ResearchCaseSummary[] = []
  const countries = new Set<string>()
  const instruments = new Set<string>()

  while (remaining.length && chosen.length < 6) {
    remaining.sort((a, b) => {
      const score = (item: ResearchCaseSummary) => {
        const grade = item.review_status === 'A' ? 30 : item.review_status === 'B' ? 20 : 0
        const newCountry = countries.has(item.country) ? 0 : 24
        const newInstruments = item.instrument.filter((name) => !instruments.has(name)).length * 8
        return grade + newCountry + newInstruments + Math.min(item.source_count, 12) + Math.min(item.valid_count, 10)
      }
      return score(b) - score(a) || a.case_id.localeCompare(b.case_id)
    })
    const next = remaining.shift()
    if (!next) break
    chosen.push(next)
    countries.add(next.country)
    next.instrument.forEach((name) => instruments.add(name))
  }
  return chosen
})
const cases = representativeCases
const caseTotal = computed(() => caseList.value?.total ?? 0)
const dataVersion = computed(() => status.value?.version.active_version ?? '—')
const dataUpdatedAt = computed(() => status.value?.version.updated_at ?? '—')
const factorShares = computed(() => {
  const factors = (successFactors.value?.factors ?? []).filter(
    (factor) => factor.mean_score !== null && factor.n > 0,
  )
  const total = factors.reduce((sum, factor) => sum + (factor.mean_score ?? 0), 0)
  if (!total) return []
  return factors
    .map((factor) => ({ ...factor, share: ((factor.mean_score ?? 0) / total) * 100 }))
    .sort((a, b) => b.share - a.share)
})
const countryFactorShares = computed(() => {
  const factors = (countrySuccessFactors.value?.factors ?? []).filter(
    (factor) => factor.mean_score !== null && factor.n > 0,
  )
  const total = factors.reduce((sum, factor) => sum + (factor.mean_score ?? 0), 0)
  if (!total) return []
  return factors
    .map((factor) => ({ ...factor, share: ((factor.mean_score ?? 0) / total) * 100 }))
    .sort((a, b) => b.share - a.share)
})
const countryTopFactors = computed(() => selectedCountry.value ? countryFactorShares.value.slice(0, 3) : [])

function selectionReasons(item: ResearchCaseSummary) {
  const reasons = [
    `${item.country}国别样本`,
    `${item.instrument.join('、') || item.music_type}表演类型`,
    `${item.review_status}级审核`,
  ]
  if (item.source_count > 0) reasons.push(`${item.source_count}条来源可追溯`)
  if (item.era_theme.length) reasons.push(`主题：${item.era_theme.slice(0, 2).join('、')}`)
  return reasons
}

const selectionReportText = computed(() => {
  const selected = representativeCases.value
  return [
    '海外传播案例选择与可解释性分析报告',
    '',
    '一、样本范围',
    `当前案例库共${libraryCaseCount.value}个已审批案例，全部参与国家覆盖和因素统计。为便于页面展示，从中选取${selected.length}个代表案例进行详细解读。`,
    '',
    '二、选择方法',
    '优先保证国家与乐器/表演类型的差异性，其次考虑审核等级、来源数量和因素编码完整度。选择仅用于展示，不改变全库统计口径。',
    '',
    '三、入选案例与理由',
    ...selected.map((item, index) => `${index + 1}. ${item.performer}（${item.country}）：${selectionReasons(item).join('；')}。`),
    '',
    '四、分析结论',
    `当前样本中较高的传播因素为：${factorShares.value.slice(0, 3).map((item) => item.label).join('、') || '暂无可用因素数据'}。该结果用于描述当前已审批案例，不代表各国总体偏好，也不作因果推断。`,
  ].join('\n')
})

async function copySelectionReport() {
  try {
    await navigator.clipboard.writeText(selectionReportText.value)
    reportCopyState.value = '报告内容已复制'
  } catch {
    reportCopyState.value = '复制失败，请手动选择报告内容'
  }
  window.setTimeout(() => { reportCopyState.value = '' }, 2200)
}

async function loadCountryFactors() {
  if (!selectedCountry.value) {
    countrySuccessFactors.value = null
    countryFactorError.value = ''
    return
  }
  countryFactorLoading.value = true
  countryFactorError.value = ''
  try {
    const response = await fetchResearchSuccessFactors({
      analysis_sample: 'all',
      country: selectedCountry.value,
    })
    if (!response.data) throw new Error('国家因素接口未返回有效数据')
    countrySuccessFactors.value = response.data
  } catch (error) {
    countryFactorError.value = `国家因素加载失败：${errorMessage(error)}`
    countrySuccessFactors.value = null
  } finally {
    countryFactorLoading.value = false
  }
}

function hasFailed(label: string) {
  return failed.value.includes(label)
}

function errorMessage(error: unknown) {
  const err = error as { message?: string }
  return err?.message || '网络请求失败'
}

async function fetchAllApprovedCases() {
  const first = await fetchResearchCases({ page: 1, page_size: 50, analysis_sample: 'all' })
  if (!first.data || !first.data.pagination.has_next) return first

  const remainingPages = Array.from(
    { length: Math.max(0, first.data.pagination.pages - 1) },
    (_, index) => index + 2,
  )
  const remaining = await Promise.all(
    remainingPages.map((page) => fetchResearchCases({ page, page_size: 50, analysis_sample: 'all' })),
  )
  const items = [
    ...first.data.items,
    ...remaining.flatMap((response) => response.data?.items ?? []),
  ]
  return {
    ...first,
    data: {
      ...first.data,
      items,
      result_count: items.length,
      pagination: {
        ...first.data.pagination,
        page: 1,
        page_size: items.length,
        has_next: false,
        has_previous: false,
      },
    },
  }
}

async function loadDashboard() {
  loading.value = true
  fatalError.value = ''
  failed.value = []
  status.value = null
  statistics.value = null
  caseList.value = null
  successFactors.value = null
  countrySuccessFactors.value = null
  selectedCountry.value = ''

  const [
    statusResult,
    statisticsResult,
    casesResult,
    successResult,
  ] = await Promise.allSettled([
    fetchResearchStatus(),
    fetchResearchStatistics({ analysis_sample: 'all' }),
    fetchAllApprovedCases(),
    fetchResearchSuccessFactors({ analysis_sample: 'all' }),
  ])

  if (statusResult.status === 'fulfilled' && statusResult.value.data) {
    status.value = statusResult.value.data
  } else {
    failed.value.push('研究状态')
  }

  if (statisticsResult.status === 'fulfilled' && statisticsResult.value.data) {
    statistics.value = statisticsResult.value.data
  } else {
    failed.value.push('统计分布')
  }

  if (casesResult.status === 'fulfilled' && casesResult.value.data) {
    caseList.value = casesResult.value.data
  } else {
    failed.value.push('代表案例')
  }

  if (successResult.status === 'fulfilled' && successResult.value.data) {
    successFactors.value = successResult.value.data
  } else {
    failed.value.push('成功因素')
  }

  if (!status.value) {
    const firstError =
      statusResult.status === 'rejected'
        ? errorMessage(statusResult.reason)
        : '研究状态接口未返回有效数据'
    fatalError.value = `无法加载研究数据：${firstError}。请确认后端已启动、/api 代理可用。`
  }

  loading.value = false
}

onMounted(loadDashboard)
</script>

<template>
  <div class="page research-page global-page">
    <AppNav />

    <main class="dashboard">
      <div v-if="loading" class="skeleton" aria-busy="true" aria-label="正在加载研究数据">
        <div class="skeleton-hero">
          <i class="skeleton-line w40" />
          <i class="skeleton-line w58 tall" />
          <i class="skeleton-line w48" />
        </div>
        <div class="skeleton-kpis">
          <i v-for="n in 4" :key="n" class="skeleton-box" />
        </div>
        <div class="skeleton-panels">
          <i class="skeleton-box wide" />
          <i class="skeleton-box" />
        </div>
      </div>

      <ResearchState
        v-else-if="fatalError"
        kind="error"
        title="研究数据加载失败"
        :message="fatalError"
        retryable
        @retry="loadDashboard"
      />

      <template v-else>
        <header class="dashboard-hero">
          <div class="dashboard-hero-copy">
            <p class="dashboard-eyebrow">GLOBAL PROPAGATION DASHBOARD</p>
            <h1>全球传播效果<span>分析</span></h1>
            <p class="dashboard-hero-desc">
              以已核验的外国演奏案例为证据，展示案例涉及国家及传播影响因素的样本内占比。
              所有结果均可回到具体案例、评分和来源核验。
            </p>
          </div>
          <div class="dashboard-hero-side">
            <SampleBadge :sample="sample" mode="library" />
            <p class="dashboard-hero-side-text">
              {{ libraryCaseCount }}个已审批案例全部参与国家覆盖与因素分析
            </p>
            <p class="dashboard-hero-version">
              数据版本 {{ dataVersion }} · 更新 {{ dataUpdatedAt }}
            </p>
          </div>
        </header>

        <div v-if="failed.length" class="partial-alert" role="status">
          <span>部分模块未加载：{{ failed.join('、') }}。其余模块仍展示真实数据。</span>
          <button type="button" @click="loadDashboard">重新加载</button>
        </div>

        <section class="kpi-grid case-count-only" aria-label="案例总数">
          <ResearchKpi
            label="案例总数"
            :value="libraryCaseCount"
            suffix=" 例"
            note="全部案例均已审批并参与分析"
            accent
          />
        </section>

        <SectionCard
          id="case-selection-report"
          title="案例选择与可解释性分析报告"
          kicker="EXPLAINABLE CASE REPORT"
          :subtitle="`从${libraryCaseCount}个已审批案例中选取${representativeCases.length}个代表案例进行展示；全部案例仍参与总体分析。`"
          class="selection-report-card"
        >
          <template #actions>
            <button type="button" class="report-copy-button" @click="copySelectionReport">复制报告内容</button>
          </template>
          <p v-if="reportCopyState" class="report-copy-state">{{ reportCopyState }}</p>

          <div class="selection-method">
            <div>
              <span>01</span>
              <p><b>国家多样性</b>优先补足不同国家的展示，避免案例过度集中在单一地区。</p>
            </div>
            <div>
              <span>02</span>
              <p><b>乐器与形式差异</b>兼顾不同乐器、乐种和表演形式，便于比较共性机制。</p>
            </div>
            <div>
              <span>03</span>
              <p><b>证据可追溯</b>优先审核等级较高、来源记录和因素编码较完整的案例。</p>
            </div>
          </div>

          <div v-if="representativeCases.length" class="selection-case-list">
            <RouterLink
              v-for="(item, index) in representativeCases"
              :key="`selected-${item.case_id}`"
              :to="{ name: 'global-case-detail', params: { caseId: item.case_id } }"
              class="selection-case-row"
            >
              <span class="selection-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <b>{{ item.performer }}</b>
                <small>{{ item.country }} · {{ item.instrument.join(' / ') || item.music_type }}</small>
              </div>
              <p>{{ selectionReasons(item).join('；') }}</p>
              <em>查看证据 →</em>
            </RouterLink>
          </div>
          <ResearchState
            v-else
            kind="empty"
            title="暂无可选案例"
            message="当前案例库没有可用的已审批案例。"
            compact
          />
          <p class="selection-boundary">
            <b>结论边界：</b>代表案例用于展示选择逻辑与证据链，不代表传播效果排名；国家占比和因素占比仍按全部{{ libraryCaseCount }}个案例计算。
          </p>
        </SectionCard>

        <div class="dashboard-grid">
          <SectionCard
            title="案例涉及国家"
            kicker="CASE DISTRIBUTION"
            subtitle="统计当前案例库中全部已审核传播案例，显示涉及国家、案例数与样本占比。"
          >
            <template #actions>
              <span class="card-count">{{ countryRows.length }} 个国家</span>
            </template>
            <ResearchState
              v-if="hasFailed('统计分布')"
              kind="error"
              title="分布数据加载失败"
              message="国家与区域分布暂不可用。"
              retryable
              compact
              @retry="loadDashboard"
            />
            <div v-else class="distribution-layout">
              <DistributionList
                :items="countryRows"
                empty-text="当前没有可展示的国家分布"
              />
            </div>
          </SectionCard>

          <SectionCard
            title="传播影响因素占比"
            kicker="SUCCESS MECHANISMS"
            :subtitle="`按全部${libraryCaseCount}个已审批案例的10项指标平均分归一化，显示各因素在当前编码结果中的相对占比。`"
          >
            <template #actions>
              <span class="availability-chip ready">可用</span>
            </template>

            <ResearchState
              v-if="hasFailed('成功因素')"
              kind="error"
              title="成功因素加载失败"
              message="全部案例的传播影响因素暂不可用。"
              retryable
              compact
              @retry="loadDashboard"
            />

            <div v-else-if="factorShares.length" class="factor-list">
              <div
                v-for="(factor, index) in factorShares"
                :key="factor.indicator_id"
                class="factor-row"
              >
                <span class="factor-rank">{{ String(index + 1).padStart(2, '0') }}</span>
                <div class="factor-main">
                  <div class="factor-label">
                    <span>{{ factor.label }}</span>
                    <b>{{ factor.share.toFixed(1) }}%</b>
                  </div>
                  <div class="factor-track">
                    <i :style="{ width: `${factor.share}%` }" />
                  </div>
                  <small>平均分 {{ factor.mean_score?.toFixed(2) }} / {{ factor.score_scale }} · 有效案例 n={{ factor.n }}</small>
                </div>
              </div>
              <p class="factor-coverage-note">
                基于{{ libraryCaseCount }}个已审批案例的描述性编码，不代表因果贡献率或各国总体偏好。
              </p>
            </div>
            <div v-else class="unavailable">
              <h3>暂无可计算的因素评分</h3>
              <p>{{ successFactors?.reason || '当前案例尚未形成有效因素评分。' }}</p>
            </div>
          </SectionCard>
        </div>

        <SectionCard
          title="按国家查看前三项影响因素"
          kicker="COUNTRY TOP FACTORS"
          :subtitle="selectedCountry ? `${selectedCountry}案例中平均编码较高的前三项因素。` : '选择国家后，展示该国排名靠前的三个传播影响因素。'"
          class="country-factor-card"
        >
          <template #actions>
            <select
              v-model="selectedCountry"
              class="country-factor-select"
              aria-label="选择国家"
              @change="loadCountryFactors"
            >
              <option value="">选择国家</option>
              <option v-for="country in countryRows" :key="country.key" :value="country.key">
                {{ country.key }}（{{ country.count }}例）
              </option>
            </select>
          </template>

          <ResearchState
            v-if="countryFactorError"
            kind="error"
            title="国家因素加载失败"
            :message="countryFactorError"
            retryable
            compact
            @retry="loadCountryFactors"
          />
          <ResearchState
            v-else-if="!selectedCountry"
            kind="empty"
            title="请选择国家"
            message="选择一个国家后，这里只展示该国排名最高的三个传播影响因素。"
            compact
          />
          <ResearchState
            v-else-if="countryFactorLoading"
            kind="pending"
            title="正在计算国家因素"
            :message="`正在汇总${selectedCountry}案例的因素编码。`"
            compact
          />
          <div v-else-if="countryTopFactors.length" class="factor-list country-top-list">
            <div
              v-for="(factor, index) in countryTopFactors"
              :key="factor.indicator_id"
              class="factor-row"
            >
              <span class="factor-rank">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="factor-main">
                <div class="factor-label">
                  <span>{{ factor.label }}</span>
                  <b>{{ factor.share.toFixed(1) }}%</b>
                </div>
                <div class="factor-track"><i :style="{ width: `${factor.share}%` }" /></div>
                <small>平均分 {{ factor.mean_score?.toFixed(2) }} / {{ factor.score_scale }} · 有效案例 n={{ factor.n }}</small>
              </div>
            </div>
            <p class="factor-coverage-note">
              基于{{ selectedCountry }}的{{ countrySuccessFactors?.analysis_scope.case_count ?? 0 }}个已审批案例；排名是案例内描述性结果，不代表该国总体偏好。
            </p>
          </div>
          <div v-else class="unavailable">
            <h3>暂无可计算的因素评分</h3>
            <p>{{ countrySuccessFactors?.reason || `${selectedCountry}案例尚未形成有效因素评分。` }}</p>
          </div>
        </SectionCard>

        <SectionCard
          title="代表性案例"
          kicker="REPRESENTATIVE CASES"
          subtitle="根据国家多样性、表演形式差异与证据完整度选出的展示案例。"
        >
          <template #actions>
            <span class="card-count">展示 {{ cases.length }} / 全库 {{ caseTotal }} 例</span>
          </template>
          <ResearchState
            v-if="hasFailed('代表案例')"
            kind="error"
            title="案例数据加载失败"
            message="代表性案例暂不可用。"
            retryable
            compact
            @retry="loadDashboard"
          />
          <ResearchState
            v-else-if="cases.length === 0"
            kind="empty"
            title="暂无已纳入案例"
            message="案例库尚未导入可展示数据。"
            compact
          />
          <div v-else class="case-grid">
            <CasePreviewCard v-for="item in cases" :key="item.case_id" :item="item" />
          </div>
          <p class="case-footnote">点击案例可查看摘要背景、10项因素评分、来源索引、外国受众反馈证据与接受原因。</p>
        </SectionCard>

        <footer class="method">
          <p>
            <b>阅读口径：</b>
            案例库共 {{ libraryCaseCount }} 例，本页已将全部案例纳入国家覆盖和因素统计。
            国家占比与因素占比均是当前案例库的描述性结果，不代表各国总体偏好，也不作因果推断。
          </p>
          <p>数据版本 {{ dataVersion }} · 更新时间 {{ dataUpdatedAt }}；未知评分不按 0 分计入。</p>
        </footer>
      </template>
    </main>
  </div>
</template>

<style scoped>
.global-page {
  min-height: 100vh;
  color: #e8f1ed;
}

.dashboard {
  position: relative;
  max-width: 1380px;
  margin: 0 auto;
  padding: clamp(32px, 5vw, 64px) clamp(20px, 4vw, 48px) 76px;
}

.selection-report-card {
  margin-bottom: 24px;
  scroll-margin-top: 96px;
}

.report-copy-button {
  padding: 8px 13px;
  border: 1px solid rgba(217, 194, 138, 0.38);
  border-radius: 5px;
  background: rgba(217, 194, 138, 0.08);
  color: #e8d4a8;
  cursor: pointer;
}

.report-copy-state {
  margin: 0 0 14px;
  color: #8fc7b1;
  font-size: 12px;
}

.selection-method {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.selection-method > div {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  padding: 15px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 7px;
  background: rgba(5, 25, 22, 0.34);
}

.selection-method span,
.selection-index {
  color: #d9c28a;
  font-family: Consolas, monospace;
  font-size: 12px;
}

.selection-method p {
  margin: 0;
  color: #a9beb5;
  font-size: 12px;
  line-height: 1.7;
}

.selection-method b { display: block; margin-bottom: 4px; color: #e8f1ed; }

.selection-case-list {
  border-top: 1px solid rgba(159, 198, 181, 0.14);
}

.selection-case-row {
  display: grid;
  grid-template-columns: 38px minmax(150px, .75fr) minmax(260px, 1.5fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px 4px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.12);
  color: inherit;
  text-decoration: none;
}

.selection-case-row:hover { background: rgba(143, 199, 177, 0.035); }
.selection-case-row b,
.selection-case-row small { display: block; }
.selection-case-row b { color: #e8f1ed; font-size: 14px; }
.selection-case-row small { margin-top: 4px; color: #78948a; font-size: 11px; }
.selection-case-row p { margin: 0; color: #a9beb5; font-size: 12px; line-height: 1.6; }
.selection-case-row em { color: #8fc7b1; font-size: 11px; font-style: normal; white-space: nowrap; }

.selection-boundary {
  margin: 18px 0 0;
  padding: 12px 14px;
  border-left: 2px solid rgba(217, 194, 138, 0.48);
  background: rgba(49, 42, 27, 0.24);
  color: #9db2aa;
  font-size: 12px;
  line-height: 1.7;
}

.selection-boundary b { color: #e8d4a8; }

.dashboard::before {
  content: '';
  position: absolute;
  z-index: -1;
  top: -80px;
  right: 4%;
  width: min(620px, 70vw);
  height: 440px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(71, 139, 116, 0.15), transparent 68%);
  pointer-events: none;
}

.dashboard-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 36px;
  padding-bottom: 30px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.18);
}

.dashboard-eyebrow {
  margin: 0 0 14px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.2em;
}

.dashboard-hero-copy h1 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(40px, 5vw, 62px);
  font-weight: 500;
  line-height: 1.02;
  letter-spacing: 0.04em;
}

.dashboard-hero-copy h1 span {
  color: #8fc7b1;
}

.dashboard-hero-desc {
  max-width: 760px;
  margin: 20px 0 0;
  color: #9bb7ad;
  font-size: 13px;
  line-height: 1.9;
}

.dashboard-hero-side {
  flex: 0 0 min(320px, 34%);
  padding-bottom: 4px;
}

.dashboard-hero-side-text {
  margin: 12px 0 0;
  color: #c3d5cb;
  font-size: 12px;
  line-height: 1.6;
}

.dashboard-hero-version {
  margin: 8px 0 0;
  color: #6f8c81;
  font-family: 'Consolas', 'SFMono-Regular', monospace;
  font-size: 10px;
  letter-spacing: 0.04em;
}

.partial-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 22px;
  padding: 11px 14px;
  border: 1px solid rgba(226, 162, 118, 0.28);
  border-radius: 8px;
  background: rgba(126, 75, 42, 0.14);
  color: #d8b392;
  font-size: 12px;
  line-height: 1.6;
}

.partial-alert button {
  flex-shrink: 0;
  padding: 6px 10px;
  border: 1px solid rgba(217, 194, 138, 0.3);
  border-radius: 4px;
  background: transparent;
  color: #e8d4a8;
  font-size: 11px;
  cursor: pointer;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 26px;
}

.case-count-only {
  grid-template-columns: minmax(260px, 380px);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(340px, 0.9fr);
  gap: 18px;
  margin-top: 18px;
}

.status-pending-grid {
  display: grid;
  grid-template-columns: minmax(260px, 0.95fr) repeat(2, minmax(260px, 1fr));
  gap: 18px;
  margin-top: 18px;
}

.card-count,
.availability-chip,
.pending-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  white-space: nowrap;
}

.card-count {
  border: 1px solid rgba(159, 198, 181, 0.2);
  color: #8fa99f;
}

.availability-chip {
  border: 1px solid rgba(217, 194, 138, 0.34);
  background: rgba(217, 194, 138, 0.08);
  color: #d9c28a;
}

.availability-chip.ready {
  border-color: rgba(143, 199, 177, 0.38);
  background: rgba(94, 166, 140, 0.12);
  color: #a7d8c3;
}

.country-factor-card {
  margin-top: 18px;
}

.country-factor-select {
  min-width: 150px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(143, 199, 177, 0.34);
  border-radius: 5px;
  background: rgba(3, 20, 18, 0.72);
  color: #d8e6df;
  font-size: 11px;
  outline: none;
}

.country-factor-select:focus {
  border-color: rgba(143, 199, 177, 0.68);
}

.country-factor-select option {
  background: #0b2823;
}

.country-top-list {
  max-width: 900px;
}

.pending-chip {
  border: 1px solid rgba(217, 194, 138, 0.32);
  background: rgba(217, 194, 138, 0.08);
  color: #d9c28a;
}

.distribution-layout {
  display: block;
}

.region-side {
  padding-left: 22px;
  border-left: 1px solid rgba(159, 198, 181, 0.12);
}

.mini-title {
  margin: 0 0 12px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.region-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.region-chips span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 8px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 4px;
  color: #adc1b8;
  font-size: 11px;
}

.region-chips b {
  color: #d9c28a;
  font-weight: 500;
}

.region-empty {
  margin: 0;
  color: #78948a;
  font-size: 12px;
}

.coverage {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid rgba(159, 198, 181, 0.12);
}

.coverage-head,
.gap-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  color: #9bb7ad;
  font-size: 11px;
}

.coverage-head b,
.gap-line b {
  color: #e8d4a8;
  font-weight: 500;
}

.coverage-track,
.gap-track {
  height: 4px;
  margin-top: 9px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.coverage-track i,
.gap-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.coverage-note,
.gap-note {
  margin: 9px 0 0;
  color: #6f8c81;
  font-size: 10px;
}

.unavailable {
  padding: 2px 0 0;
}

.unavailable-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.unavailable-chip {
  padding: 4px 8px;
  border: 1px solid rgba(226, 162, 118, 0.34);
  border-radius: 999px;
  background: rgba(126, 75, 42, 0.12);
  color: #e2a276;
  font-size: 10px;
}

.unavailable-threshold {
  color: #78948a;
  font-size: 10px;
}

.unavailable h3 {
  margin: 18px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 20px;
  font-weight: 500;
  line-height: 1.55;
}

.unavailable p {
  margin: 10px 0 0;
  color: #8fa99f;
  font-size: 12px;
  line-height: 1.8;
}

.gap-line {
  margin-top: 24px;
}

.factor-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.country-share-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 14px;
}

.country-share-grid span {
  padding: 6px 9px;
  border: 1px solid rgba(143, 199, 177, 0.12);
  background: rgba(143, 199, 177, 0.05);
  color: #9fb8ae;
  font-size: 11px;
}

.country-share-grid b { margin-left: 5px; color: #e8d4a8; font-weight: 500; }

.factor-row {
  display: flex;
  gap: 12px;
}

.factor-rank {
  padding-top: 2px;
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 10px;
}

.factor-main {
  flex: 1;
}

.factor-label {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #c9d8d1;
  font-size: 12px;
}

.factor-label b {
  color: #e8d4a8;
  font-weight: 500;
}

.factor-track {
  height: 5px;
  margin-top: 7px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.factor-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.factor-main small {
  display: block;
  margin-top: 5px;
  color: #6f8c81;
  font-size: 10px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.status-list > div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.status-list > div:last-child {
  border-bottom: 0;
}

.status-list span {
  color: #78948a;
  font-size: 11px;
}

.status-list b {
  color: #c9d8d1;
  font-size: 11px;
  font-weight: 500;
  text-align: right;
}

.status-foot {
  margin: 16px 0 0;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.7;
}

.pending-body h3 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.55;
}

.pending-body p {
  margin: 10px 0 0;
  color: #8fa99f;
  font-size: 11px;
  line-height: 1.75;
}

.pending-muted {
  color: #78948a !important;
}

.pending-stats {
  display: flex;
  gap: 30px;
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid rgba(159, 198, 181, 0.1);
}

.pending-stats > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pending-stats b {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 24px;
  font-weight: 500;
}

.pending-stats span {
  color: #78948a;
  font-size: 10px;
}

.case-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.case-footnote {
  margin: 18px 0 0;
  color: #6f8c81;
  font-size: 10px;
}

.method {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(159, 198, 181, 0.14);
}

.method p {
  margin: 0;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.8;
}

.method b {
  color: #9bb7ad;
  font-weight: 500;
}

.method code {
  color: #a7beb5;
  font-size: 10px;
}

.skeleton {
  display: flex;
  flex-direction: column;
  gap: 26px;
  padding-top: 26px;
}

.skeleton-hero {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 28px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.12);
}

.skeleton-line,
.skeleton-box {
  display: block;
  border-radius: 8px;
  background: linear-gradient(100deg, rgba(159, 198, 181, 0.06), rgba(159, 198, 181, 0.12), rgba(159, 198, 181, 0.06));
  background-size: 220% 100%;
  animation: shimmer 1.6s ease-in-out infinite;
}

.skeleton-line {
  height: 12px;
}

.skeleton-line.tall {
  height: 48px;
}

.w40 { width: 40%; }
.w48 { width: 48%; }
.w58 { width: 58%; }

.skeleton-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.skeleton-kpis .skeleton-box {
  height: 150px;
}

.skeleton-panels {
  display: grid;
  grid-template-columns: 1.35fr 0.9fr;
  gap: 18px;
}

.skeleton-panels .skeleton-box {
  height: 340px;
}

.skeleton-panels .wide {
  min-width: 0;
}

@keyframes shimmer {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}

@media (max-width: 1180px) {
  .selection-method { grid-template-columns: 1fr; }
  .selection-case-row { grid-template-columns: 34px minmax(150px, .8fr) minmax(220px, 1.4fr); }
  .selection-case-row em { display: none; }

  .dashboard-grid,
  .skeleton-panels {
    grid-template-columns: 1fr;
  }

  .status-pending-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .status-pending-grid > :first-child {
    grid-column: 1 / -1;
  }

  .case-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .dashboard-hero {
    align-items: flex-start;
    flex-direction: column;
    gap: 22px;
  }

  .dashboard-hero-side {
    flex-basis: auto;
    width: 100%;
  }

  .kpi-grid,
  .skeleton-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .distribution-layout {
    grid-template-columns: 1fr;
  }

  .region-side {
    padding-top: 18px;
    padding-left: 0;
    border-top: 1px solid rgba(159, 198, 181, 0.12);
    border-left: 0;
  }

  .coverage {
    margin-top: 20px;
  }
}

@media (max-width: 680px) {
  .dashboard {
    padding: 28px 16px 56px;
  }

  .kpi-grid,
  .skeleton-kpis,
  .status-pending-grid,
  .case-grid {
    grid-template-columns: 1fr;
  }

  .status-pending-grid > :first-child {
    grid-column: auto;
  }

  .partial-alert {
    align-items: flex-start;
    flex-direction: column;
  }

  .dashboard-hero-copy h1 {
    font-size: 38px;
  }

  .dashboard-grid {
    gap: 14px;
  }

  .case-grid {
    gap: 12px;
  }

  .selection-case-row {
    grid-template-columns: 30px 1fr;
  }

  .selection-case-row p { grid-column: 2; }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-line,
  .skeleton-box {
    animation: none;
  }
}

.availability-chip.exploratory {
  color: #d9c28a;
  border-color: rgba(217, 194, 138, 0.35);
  background: rgba(217, 194, 138, 0.1);
}

.unavailable-chip.exploratory {
  color: #d9c28a;
  border-color: rgba(217, 194, 138, 0.32);
}


.factor-coverage {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 9px;
  background: rgba(8, 19, 16, 0.28);
}
.factor-coverage-title { margin: 0 0 8px; color: #d8e6df; font-size: 12px; }
.factor-coverage-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.factor-coverage-grid span { padding: 4px 7px; border-radius: 6px; background: rgba(143, 199, 177, 0.08); color: #9fb8ae; font-size: 10px; }
.factor-coverage-grid b { color: #a9d9b8; font-weight: 600; }
.factor-coverage-note { margin: 8px 0 0; color: #7f9b8f; font-size: 10px; line-height: 1.6; }

</style>
