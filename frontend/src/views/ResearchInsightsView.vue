<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import ResearchState from '@/components/research/ResearchState.vue'
import SampleBadge from '@/components/research/SampleBadge.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import {
  fetchResearchCase,
  fetchResearchCases,
  fetchResearchMusicPotential,
  fetchResearchRegionalMatrix,
  fetchResearchStatistics,
  fetchResearchStatus,
  fetchResearchSuccessFactors,
} from '@/api/research'
import {
  CITY_DIMENSION_GUIDE,
  INDICATOR_GUIDE,
  MUSIC_INDICATOR_GUIDE,
  REGION_FIELD_GUIDE,
} from '@/data/researchFramework'
import type {
  ResearchCaseDetail,
  ResearchCaseList,
  ResearchMusicPotential,
  ResearchRegionalMatrix,
  ResearchStatistics,
  ResearchStatus,
  ResearchSuccessFactors,
} from '@/types/research'

type TabKey = 'mechanism' | 'potential' | 'matrix'

const TABS: Array<{ key: TabKey; index: string; label: string; en: string }> = [
  { key: 'mechanism', index: '01', label: '传播因素与证据', en: 'FACTORS & EVIDENCE' },
  { key: 'potential', index: '02', label: '音乐传播潜力', en: 'POTENTIAL' },
  { key: 'matrix', index: '03', label: '区域传播适配', en: 'REGIONAL FIT' },
]

const route = useRoute()
const router = useRouter()

function normalizeTab(value: unknown): TabKey {
  const raw = Array.isArray(value) ? value[0] : value
  if (raw === 'potential' || raw === 'matrix') return raw
  return 'mechanism'
}

const activeTab = ref<TabKey>(normalizeTab(route.query.tab))
const SAMPLE_SCOPES = [
  { value: 'all', label: '全部扩展案例' },
  { value: 'strict_candidate', label: '严格样本候选（待审批）' },
  { value: 'strict_individual', label: '正式严格样本（已批准）' },
  { value: 'extended_cross_cultural', label: '扩展跨文化传播样本' },
  { value: 'pending_review', label: '待核实案例' },
] as const
type SampleScope = (typeof SAMPLE_SCOPES)[number]['value']
const sampleScope = ref<SampleScope>('all')
const status = ref<ResearchStatus | null>(null)
const statistics = ref<ResearchStatistics | null>(null)
const successFactors = ref<ResearchSuccessFactors | null>(null)
const caseList = ref<ResearchCaseList | null>(null)
const caseDetails = ref<ResearchCaseDetail[]>([])
const music = ref<ResearchMusicPotential | null>(null)
const regional = ref<ResearchRegionalMatrix | null>(null)
const loading = ref(true)
const fatalError = ref('')
const failed = ref<string[]>([])
let requestSeq = 0

const sample = computed(() => statistics.value?.sample ?? status.value?.sample ?? null)
const analysisScope = computed(() => statistics.value?.analysis_scope ?? successFactors.value?.analysis_scope ?? null)
const successAvailable = computed(
  () => successFactors.value?.availability === 'descriptive' && (successFactors.value.rankings?.length ?? 0) > 0,
)
const successExploratory = computed(() => successFactors.value?.availability === 'exploratory')
const rankingThreshold = computed(
  () => successFactors.value?.thresholds.indicator_rank_min ?? successFactors.value?.thresholds.descriptive ?? 20,
)
const gateFactors = computed(() =>
  [...(successFactors.value?.factors ?? [])].sort((a, b) => (a.order ?? 999) - (b.order ?? 999)),
)
const approvalCases = computed(() =>
  caseDetails.value.filter((detail) => detail.case.analysis_sample === 'strict_individual'),
)

const topCountry = computed(() => {
  const rows = statistics.value?.distributions.country ?? []
  return [...rows].sort((a, b) => b.count - a.count)[0] ?? null
})

const topRegion = computed(() => {
  const rows = statistics.value?.distributions.region ?? []
  return [...rows].sort((a, b) => b.count - a.count)[0] ?? null
})

const factorStats = computed(() => {
  const factors = successFactors.value?.factors ?? []
  return {
    total: factors.length,
    descriptive: factors.filter((item) => item.status === 'descriptive').length,
    exploratory: factors.filter((item) => item.status === 'exploratory').length,
    insufficient: factors.filter((item) => item.status === 'insufficient' || item.status === 'empty').length,
    rankable: factors.filter((item) => item.n >= rankingThreshold.value).length,
  }
})

const methodSummary = computed(() => {
  const scope = analysisScope.value
  const cases = scope?.case_count ?? sample.value?.n ?? 0
  const total = cases * 10
  const valid = scope?.valid_score_count ?? statistics.value?.indicator_coverage.reduce((sum, item) => sum + item.valid_count, 0) ?? 0
  return {
    cases,
    total,
    valid,
    missing: Math.max(0, total - valid),
    coverage: total ? Math.round((valid / total) * 1000) / 10 : 0,
    strictApproved: scope?.strict_approved_case_count ?? scope?.owner_approved_count ?? 0,
    bEvidence: statistics.value?.distributions.evidence_grade.find((item) => item.key === 'B')?.count ?? 0,
  }
})
const approvalLabel = (status?: string) => ({
  pending_owner_review: '待负责人审批',
  approved: '负责人已批准',
  rejected: '不批准进入严格样本',
  needs_more_evidence: '需要补充证据',
}[status || ''] || '未设置')
function gateClass(status: string) {
  return `gate-${status}`
}

function hasFailed(label: string) {
  return failed.value.includes(label)
}

function errorText(err: unknown) {
  const e = err as { message?: string }
  return e?.message || '网络请求失败'
}

function switchTab(key: TabKey) {
  activeTab.value = key
  router.replace({
    name: 'research-insights',
    query: { ...route.query, tab: key },
  })
}

watch(
  () => route.query.tab,
  (value) => {
    activeTab.value = normalizeTab(value)
  },
)

async function loadDetails(items: ResearchCaseList['items']) {
  if (!items.length) {
    caseDetails.value = []
    return
  }
  const results = await Promise.allSettled(items.map((item) => fetchResearchCase(item.case_id)))
  const details = results
    .filter((result): result is PromiseFulfilledResult<Awaited<ReturnType<typeof fetchResearchCase>>> => result.status === 'fulfilled')
    .map((result) => result.value.data)
    .filter((item): item is ResearchCaseDetail => Boolean(item))
  caseDetails.value = details
  if (details.length !== items.length) {
    failed.value.push('案例指标')
  }
}

async function loadInsights() {
  const seq = ++requestSeq
  loading.value = true
  fatalError.value = ''
  failed.value = []
  status.value = null
  statistics.value = null
  successFactors.value = null
  caseList.value = null
  caseDetails.value = []
  music.value = null
  regional.value = null

  const [
    statusResult,
    statisticsResult,
    successResult,
    casesResult,
    musicResult,
    regionalResult,
  ] = await Promise.allSettled([
    fetchResearchStatus(),
    fetchResearchStatistics({ analysis_sample: sampleScope.value }),
    fetchResearchSuccessFactors({ analysis_sample: sampleScope.value }),
    fetchResearchCases({ page: 1, page_size: 50, analysis_sample: sampleScope.value }),
    fetchResearchMusicPotential(),
    fetchResearchRegionalMatrix(),
  ])

  if (statusResult.status === 'fulfilled' && statusResult.value.data) {
    status.value = statusResult.value.data
  } else {
    failed.value.push('研究状态')
  }
  if (statisticsResult.status === 'fulfilled' && statisticsResult.value.data) {
    statistics.value = statisticsResult.value.data
  } else {
    failed.value.push('指标覆盖')
  }
  if (successResult.status === 'fulfilled' && successResult.value.data) {
    successFactors.value = successResult.value.data
  } else {
    failed.value.push('成功机制')
  }
  if (casesResult.status === 'fulfilled' && casesResult.value.data) {
    caseList.value = casesResult.value.data
    await loadDetails(casesResult.value.data.items)
  } else {
    failed.value.push('案例指标')
  }
  if (musicResult.status === 'fulfilled' && musicResult.value.data) {
    music.value = musicResult.value.data
  } else {
    failed.value.push('音乐潜力')
  }
  if (regionalResult.status === 'fulfilled' && regionalResult.value.data) {
    regional.value = regionalResult.value.data
  } else {
    failed.value.push('区域矩阵')
  }

  if (!status.value || !statistics.value) {
    fatalError.value = '研究状态或指标覆盖接口未返回有效数据，无法构建研究洞察。请确认后端与 /api 代理可用。'
  }
  if (seq === requestSeq) loading.value = false
}

function coverageFor(indicatorId: string) {
  return statistics.value?.indicator_coverage.find((item) => item.indicator_id === indicatorId)
}

const totalUnits = computed(() => caseDetails.value.length * 10)
const validUnits = computed(() =>
  caseDetails.value.reduce((sum, detail) => sum + detail.coding.valid_count, 0),
)
const unknownUnits = computed(() =>
  caseDetails.value.reduce((sum, detail) => sum + detail.coding.missing_count, 0),
)
const fullCoverageCount = computed(() =>
  INDICATOR_GUIDE.filter((guide) => coverageFor(guide.id)?.valid_count === caseDetails.value.length).length,
)
const caseComparisons = computed(() =>
  caseDetails.value.map((detail) => ({
    caseId: detail.case.case_id,
    performer: detail.case.performer,
    country: detail.case.country,
    mean: detail.coding.mean_score,
    valid: detail.coding.valid_count,
    missing: detail.coding.missing_count,
    lowCoverage: detail.coding.low_coverage,
  })),
)
const dataObservations = computed(() => [
  {
    label: '指标单元覆盖',
    value: `${validUnits.value} / ${totalUnits.value}`,
    text: `当前 ${caseDetails.value.length} 个案例、10 项指标，共 ${totalUnits.value} 个指标单元；其中 ${unknownUnits.value} 个未知。`,
    cases: caseDetails.value.map((item) => item.case.case_id).join('、'),
  },
  {
    label: '完整覆盖指标',
    value: `${fullCoverageCount.value} / 10`,
    text: '只有全部案例都有有效评分的指标才计入完整覆盖；不完整项明确保留未知。',
    cases: caseDetails.value.map((item) => item.case.case_id).join('、'),
  },
  {
    label: '个案有效指标',
    value: caseComparisons.value.map((item) => item.valid).join(' / '),
    text: '按案例编号顺序展示有效指标数，不代表案例质量或成功程度排名。',
    cases: caseDetails.value.map((item) => item.case.case_id).join('、'),
  },
])

const matrixRows = computed(() =>
  INDICATOR_GUIDE.map((guide) => ({
    ...guide,
    cells: caseDetails.value.map((detail) => {
      const record = detail.coding.indicators.find((item) => item.indicator_id === guide.id)
      return {
        caseId: detail.case.case_id,
        score: record?.score ?? null,
        evidence: record?.evidence ?? null,
        missingReason: record?.missing_reason ?? '评分记录缺失',
        sourceIds: record?.source_ids ?? [],
      }
    }),
  })),
)

const evidenceExcerpts = computed(() => {
  const all = caseDetails.value.flatMap((detail) =>
    detail.coding.indicators
      .filter((indicator) => indicator.score !== null && indicator.score >= 2)
      .map((indicator) => ({
        caseId: detail.case.case_id,
        performer: detail.case.performer,
        label: indicator.label,
        score: indicator.score,
        evidence: indicator.evidence,
        sourceIds: indicator.source_ids,
      })),
  )
  return all.slice(0, 4)
})

const musicIndicators = computed(() =>
  MUSIC_INDICATOR_GUIDE.map((guide) => ({
    ...guide,
    weight: music.value?.weights[guide.id] ?? null,
  })),
)

function formatWeight(weight: number | null) {
  return weight === null ? '—' : `${Math.round(weight * 100)}%`
}

function formatScore(score: number | null | undefined) {
  return score === null || score === undefined ? '—' : score.toFixed(2)
}

function sourceTo(sourceId: string, caseId: string) {
  return {
    name: 'global-case-detail',
    params: { caseId },
    hash: `#source-${sourceId}`,
  }
}

function changeSampleScope() {
  void loadInsights()
}

onMounted(loadInsights)
</script>

<template>
  <div class="page research-page insights-page">
    <AppNav />

    <main class="insights-shell">
      <header class="insights-hero">
        <div>
          <p class="insights-eyebrow">RESEARCH INSIGHTS / 研究分析</p>
          <h1>研究洞察</h1>
          <p class="insights-desc">
            把已有案例组织成可追溯的研究分析：指标覆盖、个案对比、证据缺口与待补充规则。
            当前样本不足，页面不生成成功因素排行，也不把框架当成研究结论。
          </p>
        </div>
        <div class="hero-meta">
          <SampleBadge :sample="sample" />
          <p>{{ sample?.label || '研究样本状态待加载' }}</p>
          <small>数据版本 {{ status?.version.active_version || '—' }}</small>
        </div>
      </header>

      <section class="finding-panel">
        <div class="finding-head">
          <p class="finding-kicker">WHAT THIS PAGE ANSWERS</p>
          <h2>本期研究结论</h2>
          <p>
            本页研究的是：当前正式案例库能支持哪些描述性判断、哪些证据不足，以及为什么部分结论仍只属于探索性观察。
          </p>
        </div>
        <div class="finding-grid">
          <article>
            <strong>{{ methodSummary.cases }}</strong>
            <span>个案例</span>
            <small>严格已批准 {{ methodSummary.strictApproved }} 例；其余为扩展或待核实</small>
          </article>
          <article>
            <strong>{{ methodSummary.valid }} / {{ methodSummary.total }}</strong>
            <span>条有效评分</span>
            <small>覆盖率 {{ methodSummary.coverage }}%；{{ methodSummary.missing }} 条未知，不填 0</small>
          </article>
          <article>
            <strong>{{ topCountry?.key || '—' }}</strong>
            <span>{{ topCountry?.count ?? 0 }} / {{ methodSummary.cases }} 例</span>
            <small>案例国家集中度最高；不代表全球传播分布</small>
          </article>
          <article>
            <strong>{{ factorStats.rankable }} / {{ factorStats.total || 10 }}</strong>
            <span>项指标可做描述性排序</span>
            <small>达到 n≥{{ rankingThreshold }} 才允许排序</small>
          </article>
        </div>
        <div class="finding-boundary">
          <p><b>已经能回答：</b>案例结构、国家/区域分布、十项指标的覆盖与缺失、个案证据摘录、严格/扩展样本构成。</p>
          <p><b>目前不能回答：</b>成功因素 TOP 排名、因果结论、国家受众偏好、302 首曲目的完整传播潜力排名。指标达到排序门槛的只有 {{ factorStats.rankable }} 项；描述性 {{ factorStats.descriptive }} 项，探索性 {{ factorStats.exploratory }} 项，不足 {{ factorStats.insufficient }} 项。</p>
        </div>
      </section>

      <div class="scope-selector">
        <label>
          <span>分析样本</span>
          <select v-model="sampleScope" @change="changeSampleScope">
            <option v-for="scope in SAMPLE_SCOPES" :key="scope.value" :value="scope.value">
              {{ scope.label }}
            </option>
          </select>
        </label>
        <div v-if="analysisScope" class="scope-summary">
          <b>{{ analysisScope.label }}</b>
          <span>{{ analysisScope.case_count }} 个案例 · {{ analysisScope.valid_score_count }} 条有效评分</span>
          <span v-if="sampleScope === 'strict_candidate' || sampleScope === 'strict_individual'">
            候选 {{ analysisScope.strict_candidate_count ?? 0 }} ·
            已批准 {{ analysisScope.owner_approved_count ?? 0 }} ·
            待审批 {{ analysisScope.pending_owner_review_count ?? 0 }} ·
            需补证 {{ analysisScope.needs_more_evidence_count ?? 0 }} ·
            不批准 {{ analysisScope.rejected_count ?? 0 }}
          </span>
        </div>
        <p>切换样本会重新加载统计、成功因素和案例矩阵；不同样本范围不混合解释。</p>
      </div>

      <nav class="insight-tabs" aria-label="研究洞察分区">
        <button
          v-for="tab in TABS"
          :key="tab.key"
          type="button"
          class="insight-tab"
          :class="{ active: activeTab === tab.key }"
          :aria-current="activeTab === tab.key ? 'page' : undefined"
          @click="switchTab(tab.key)"
        >
          <span class="tab-index">{{ tab.index }}</span>
          <span>
            <b>{{ tab.label }}</b>
            <small>{{ tab.en }}</small>
          </span>
        </button>
      </nav>

      <div v-if="loading" class="insights-skeleton" aria-busy="true">
        <i class="skeleton-line w30" />
        <i class="skeleton-line tall w60" />
        <div class="skeleton-grid">
          <i class="skeleton-box" />
          <i class="skeleton-box" />
          <i class="skeleton-box" />
        </div>
      </div>

      <ResearchState
        v-else-if="fatalError"
        kind="error"
        title="研究洞察加载失败"
        :message="fatalError"
        retryable
        @retry="loadInsights"
      />

      <template v-else>
        <div v-if="failed.length" class="partial-alert" role="status">
          <span>部分模块未加载：{{ failed.join('、') }}。其余内容仍来自真实接口。</span>
          <button type="button" @click="loadInsights">重新加载</button>
        </div>

        <section v-show="activeTab === 'mechanism'" class="tab-panel">
          <header class="panel-head">
            <div>
              <p class="panel-kicker">01 / FACTORS & EVIDENCE</p>
              <h2>传播因素与证据</h2>
              <p>当前只能做指标覆盖、个案对比与证据摘录；不做成功因素 TOP 排行，不做国家或区域偏好推断。</p>
            </div>
            <div class="panel-status">
              <span class="status-chip" :class="successAvailable ? 'ready' : 'warning'">
                {{ successAvailable ? '描述性可排序' : successExploratory ? '探索性展示' : '证据不足' }}
              </span>
              <small>样本 {{ sample?.n ?? 0 }} / {{ sample?.target ?? 40 }}</small>
            </div>
          </header>

          <div class="rule-callout">
            <b>阅读规则</b>
            <p>
              10 项指标均为 0—3 分编码；未知项保持 <code>null</code>，不按 0 分。
              当前国家/区域样本仍很少，无法比较国家偏好；当前样本不具备统计推断条件。
            </p>
            <p class="api-gate">
              后端门禁：{{ successFactors?.reason || '统计层未返回可用的成功因素排行。' }}
            </p>
          </div>

          <SectionCard
            v-if="successFactors"
            title="指标级统计门禁"
            kicker="INDICATOR GATE"
            subtitle="n=0 暂无数据；n=1—4 不参与排行；n=5—19 探索性展示；n≥20 允许描述性排序。"
          >
            <template #actions>
              <span class="gate-count">
                {{ successFactors.gate_counts?.insufficient ?? 0 }} 项证据不足 · {{ successFactors.gate_counts?.exploratory ?? 0 }} 项探索性
              </span>
            </template>
            <div class="gate-grid">
              <article
                v-for="(item, index) in gateFactors"
                :key="item.indicator_id"
                class="gate-card"
                :class="gateClass(item.status)"
              >
                <div class="gate-top">
                  <span>{{ String(item.order ?? index + 1).padStart(2, '0') }}</span>
                  <h4>{{ item.label }}</h4>
                  <b>{{ item.status_label }}</b>
                </div>
                <div class="gate-metrics">
                  <span>有效 <strong>{{ item.n }}</strong></span>
                  <span>缺失 <strong>{{ item.missing_count }}</strong></span>
                  <span>均值 <strong>{{ item.mean_score === null ? '—' : item.mean_score.toFixed(2) }}</strong></span>
                </div>
                <p>{{ item.gate_note }}</p>
              </article>
            </div>
          </SectionCard>

          <SectionCard
            v-if="approvalCases.length"
            title="严格样本审批记录"
            kicker="OWNER APPROVAL"
            subtitle="严格样本候选不等于正式批准；只有 approved 才进入正式严格样本统计。"
          >
            <div class="approval-grid">
              <article
                v-for="detail in approvalCases"
                :key="detail.case.case_id"
                class="approval-card"
                :class="`approval-${detail.case.owner_approval_status || 'pending_owner_review'}`"
              >
                <div class="approval-top">
                  <span>{{ detail.case.case_id }}</span>
                  <b>{{ approvalLabel(detail.case.owner_approval_status) }}</b>
                </div>
                <h4>{{ detail.case.performer }}</h4>
                <p>{{ detail.case.owner_approval_note || '暂无审批意见' }}</p>
                <div class="approval-foot">
                  <span>审批人：{{ detail.case.owner_approval_by || '未指定' }}</span>
                  <span>审批时间：{{ detail.case.owner_approval_at || '未审批' }}</span>
                </div>
                <div class="trace-row">
                  <span
                    v-for="sourceId in detail.case.owner_approval_source_ids || []"
                    :key="sourceId"
                    class="trace-chip"
                  >{{ sourceId }}</span>
                </div>
              </article>
            </div>
          </SectionCard>

          <div class="observation-grid">
            <article v-for="item in dataObservations" :key="item.label" class="observation">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <p>{{ item.text }}</p>
              <small>案例：{{ item.cases || '暂无' }}</small>
            </article>
          </div>

          <SectionCard
            title="10 项指标解释与覆盖"
            kicker="INDICATOR FRAMEWORK"
            subtitle="指标定义来自《指标编码手册 v1.0》；覆盖数来自 P2 统计接口。"
          >
            <div class="guide-grid">
              <article v-for="(guide, index) in INDICATOR_GUIDE" :key="guide.id" class="guide-card">
                <div class="guide-top">
                  <span>{{ String(index + 1).padStart(2, '0') }}</span>
                  <h3>{{ guide.label }}</h3>
                  <b>
                    {{ coverageFor(guide.id)?.valid_count ?? 0 }} / {{ caseDetails.length }} 有评分
                  </b>
                </div>
                <p>{{ guide.description }}</p>
                <small>{{ guide.anchor }}</small>
                <div class="guide-track">
                  <i
                    :style="{
                      width: `${((coverageFor(guide.id)?.valid_count ?? 0) / Math.max(1, caseDetails.length)) * 100}%`,
                    }"
                  />
                </div>
              </article>
            </div>
          </SectionCard>

          <SectionCard
            title="指标 × 案例矩阵"
            kicker="CASE-BY-CASE MATRIX"
            subtitle="按案例编号排列，不是按得分排序；未知项显示“未知”。"
          >
            <div v-if="caseDetails.length" class="matrix-scroll">
              <table class="matrix-table">
                <thead>
                  <tr>
                    <th scope="col">指标</th>
                    <th v-for="detail in caseDetails" :key="detail.case.case_id" scope="col">
                      <span>{{ detail.case.case_id }}</span>
                      <small>{{ detail.case.country }} · {{ detail.case.instrument.join(' / ') }}</small>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in matrixRows" :key="row.id">
                    <th scope="row">{{ row.label }}</th>
                    <td
                      v-for="cell in row.cells"
                      :key="`${row.id}-${cell.caseId}`"
                      :class="{ unknown: cell.score === null }"
                      :title="cell.score === null ? cell.missingReason : cell.evidence || ''"
                    >
                      {{ cell.score === null ? '未知' : cell.score }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <ResearchState
              v-else
              kind="error"
              title="案例指标未加载"
              message="无法构建指标 × 案例矩阵。"
              retryable
              compact
              @retry="loadInsights"
            />
            <p class="matrix-note">
              单元格只显示编码分，不显示成功因素排名。悬停可查看对应证据或缺失原因；完整证据见案例详情。
            </p>
          </SectionCard>

          <SectionCard
            title="个案对比"
            kicker="CASE COMPARISON"
            subtitle="仅做单案例事实比较；不是国家偏好、不是效果排名、不是因果结论。"
          >
            <div class="case-compare-grid">
              <article v-for="item in caseComparisons" :key="item.caseId" class="compare-card">
                <div class="compare-top">
                  <span>{{ item.caseId }}</span>
                  <b>{{ item.missing }} 项未知</b>
                </div>
                <h3>{{ item.performer }}</h3>
                <p>{{ item.country }} · {{ item.valid }} 项有效 / 10 项</p>
                <div class="compare-score">
                  <strong>{{ formatScore(item.mean) }}</strong>
                  <span>/ 3 编码均分</span>
                </div>
                <div class="compare-track">
                  <i :style="{ width: `${((item.mean ?? 0) / 3) * 100}%` }" />
                </div>
                <RouterLink
                  :to="{ name: 'global-case-detail', params: { caseId: item.caseId } }"
                  class="compare-link"
                >
                  查看完整证据 →
                </RouterLink>
              </article>
            </div>
          </SectionCard>

          <SectionCard
            title="证据摘录"
            kicker="EVIDENCE EXCERPTS"
            subtitle="仅抽取已有评分与原文的指标，按案例顺序展示，不构成排行。"
          >
            <div v-if="evidenceExcerpts.length" class="excerpt-grid">
              <article v-for="item in evidenceExcerpts" :key="`${item.caseId}-${item.label}`" class="excerpt-card">
                <div class="excerpt-top">
                  <span>{{ item.caseId }}</span>
                  <b>{{ item.label }}</b>
                  <strong>{{ item.score }}/3</strong>
                </div>
                <p>{{ item.evidence }}</p>
                <div class="excerpt-sources">
                  <RouterLink
                    v-for="sourceId in item.sourceIds"
                    :key="sourceId"
                    :to="sourceTo(sourceId, item.caseId)"
                    class="source-chip"
                  >
                    {{ sourceId }}
                  </RouterLink>
                  <span v-if="!item.sourceIds.length">无来源</span>
                </div>
              </article>
            </div>
            <ResearchState
              v-else
              kind="empty"
              title="暂无可摘录证据"
              message="当前案例没有可展示的评分证据。"
              compact
            />
          </SectionCard>

          <div class="limits-callout">
            <b>当前不能得出的结论</b>
            <ul>
              <li>当前整体样本 {{ sample?.n ?? 0 }} 例；只有单个指标有效评分达到 {{ rankingThreshold }} 例，才允许描述性排序。</li>
              <li>不能比较国家或区域接受偏好：样本分布严重不均，且多数国家案例很少。</li>
              <li>不能做因果推断：案例为非随机样本，且现有案例均为 B 级证据。</li>
              <li>不能把编码均分等同于传播效果或文化理解。</li>
            </ul>
          </div>
        </section>

        <section v-show="activeTab === 'potential'" class="tab-panel">
          <header class="panel-head">
            <div>
              <p class="panel-kicker">02 / POTENTIAL</p>
              <h2>音乐传播潜力</h2>
              <p>8 项加权指标与分级规则；当前数据待补充，不生成曲目评分和排名。</p>
            </div>
            <div class="panel-status">
              <span class="status-chip pending">{{ music?.status_label || '待补充' }}</span>
              <small>{{ music?.music_sample.n ?? 0 }} / {{ music?.music_sample.target ?? 20 }} 已评分</small>
            </div>
          </header>

          <div class="pending-banner">
            <div>
              <span>PENDING / 待补充</span>
              <h3>{{ music?.note || '音乐潜力评分尚未完成。' }}</h3>
            </div>
            <div class="pending-counter">
              <strong>{{ music?.music_sample.n ?? 0 }}</strong>
              <span>/ {{ music?.music_sample.target ?? 20 }} 首已评分</span>
            </div>
          </div>

          <div class="weight-grid">
            <article v-for="(item, index) in musicIndicators" :key="item.id" class="weight-card">
              <div class="weight-top">
                <span>{{ String(index + 1).padStart(2, '0') }}</span>
                <b>{{ formatWeight(item.weight) }}</b>
              </div>
              <h3>{{ item.label }}</h3>
              <p>{{ item.description }}</p>
              <small>当前：待评分</small>
            </article>
          </div>

          <div class="two-col">
            <SectionCard
              title="评分与分级规则"
              kicker="SCORING RULES"
              subtitle="权重来自 API；总分 = Σ（分项 × 权重）。"
              tone="quiet"
            >
              <div class="formula">
                总分 = 8 项评分 × 对应权重
              </div>
              <div class="tier-list">
                <div v-for="tier in music?.tiers || []" :key="`${tier.min}-${tier.max}`">
                  <span>{{ tier.min }}—{{ tier.max }}</span>
                  <b>{{ tier.label }}</b>
                </div>
              </div>
              <p class="rule-note">
                任一评分缺失时，不重新归一化权重、不生成总分；不使用 0 分补齐。
              </p>
            </SectionCard>

            <SectionCard
              title="候选音乐状态"
              kicker="CANDIDATE STATUS"
              subtitle="当前没有已完成评分的候选曲目。"
              tone="quiet"
            >
              <ResearchState
                kind="pending"
                title="候选曲目评分待补充"
                :message="music?.note || '尚未完成候选音乐评分。'"
                compact
              />
              <div class="pending-facts">
                <div><b>0</b><span>已评分曲目</span></div>
                <div><b>{{ music?.music_sample.target ?? 20 }}</b><span>候选目标</span></div>
                <div><b>0</b><span>可排名曲目</span></div>
              </div>
            </SectionCard>
          </div>

          <div class="limits-callout">
            <b>当前不能展示</b>
            <ul>
              <li>不生成 20 首曲目的分数、综合排名或推荐顺序。</li>
              <li>不使用 0 分补齐缺失指标。</li>
              <li>不把“待补充”包装成“暂无传播潜力”。</li>
            </ul>
          </div>
        </section>

        <section v-show="activeTab === 'matrix'" class="tab-panel">
          <header class="panel-head">
            <div>
              <p class="panel-kicker">03 / REGIONAL FIT</p>
              <h2>区域传播适配</h2>
              <p>6 个既定研究区域、受众与主题枚举；当前没有已审核矩阵行。区域矩阵独立于案例样本，不随上方筛选变化。</p>
            </div>
            <div class="panel-status">
              <span class="status-chip pending">{{ regional?.status_label || '待补充' }}</span>
              <small>{{ regional?.rows.length ?? 0 }} 条已审核策略</small>
            </div>
          </header>

          <div v-if="regional?.scope_note" class="matrix-scope-note">
            {{ regional.scope_note }}
          </div>

          <div class="pending-banner">
            <div>
              <span>PENDING / 研究范围</span>
              <h3>{{ regional?.note || '区域矩阵尚未完成研究与审核。' }}</h3>
            </div>
            <div class="pending-counter">
              <strong>{{ regional?.regions.length ?? 0 }}</strong>
              <span>个研究区域 · {{ regional?.rows.length ?? 0 }} 条策略</span>
            </div>
          </div>

          <div class="region-scope">
            <div class="scope-label">
              <span>6 个区域 = 研究范围，不是 6 个已验证策略</span>
              <small>当前 rows = {{ regional?.rows.length ?? 0 }}</small>
            </div>
            <div class="region-grid">
              <article v-for="region in regional?.regions || []" :key="region">
                <span>REGION</span>
                <h3>{{ region }}</h3>
                <p>目标国家、受众、语言、宗教习俗与适配理由待研究补充。</p>
                <small>当前状态：待补充</small>
              </article>
            </div>
          </div>

          <div class="two-col">
            <SectionCard
              title="矩阵字段框架"
              kicker="FIELD FRAMEWORK"
              subtitle="字段说明是研究框架，不是对某个文化的判断。"
              tone="quiet"
            >
              <div class="field-list">
                <div v-for="field in REGION_FIELD_GUIDE" :key="field.key">
                  <b>{{ field.label }}</b>
                  <span>{{ field.description }}</span>
                  <em>待补</em>
                </div>
              </div>
            </SectionCard>

            <SectionCard
              title="受众与主题枚举"
              kicker="AUDIENCE & THEME"
              subtitle="来自 P2 区域矩阵接口的定义范围，当前没有对应策略。"
              tone="quiet"
            >
              <p class="enum-title">受众</p>
              <div class="enum-chips">
                <span v-for="audience in regional?.audiences || []" :key="audience">{{ audience }}</span>
              </div>
              <p class="enum-title">时代主题</p>
              <div class="enum-chips">
                <span v-for="theme in regional?.themes || []" :key="theme">{{ theme }}</span>
              </div>
              <p class="rule-note">
                这里只列研究框架中的可选受众和主题，不表示已经完成适配或已验证接受度。
              </p>
            </SectionCard>
          </div>

          <SectionCard
            title="北京 / 上海：作品来源城市维度"
            kicker="ORIGIN CITY"
            subtitle="城市是作品来源维度，不替代目标国家；当前字段待补来源。"
          >
            <div class="city-grid">
              <article v-for="city in CITY_DIMENSION_GUIDE" :key="city.city" class="city-card">
                <span>{{ city.city }}</span>
                <h3>{{ city.label }}</h3>
                <p>{{ city.description }}</p>
                <div class="city-fields">
                  <span>文化锚点：待补</span>
                  <span>可用场景：待补</span>
                  <span>城市叙事：待补</span>
                  <span>来源：待补</span>
                </div>
              </article>
            </div>
          </SectionCard>

          <div class="limits-callout">
            <b>当前不能展示</b>
            <ul>
              <li>不生成“某音乐适合某区域”的适配关系：rows = 0。</li>
              <li>不凭印象写宗教、习俗或文化禁忌：必须有来源。</li>
              <li>不把 6 个研究区域当成 6 个实证策略。</li>
              <li>不把北京/上海的城市叙事替代目标国家分析。</li>
            </ul>
          </div>
        </section>

        <footer class="insights-foot">
          <p>
            研究洞察只消费 P2 的只读 API；指标定义来自《指标编码手册 v1.0》，不写入案例结论。
            当前样本 {{ sample?.n ?? 0 }} / {{ sample?.target ?? 40 }}，状态 {{ sample?.status || 'unknown' }}。
          </p>
          <p>null 保持未知；无证据不补写；排行和区域适配必须等待后端返回可用数据。</p>
        </footer>
      </template>
    </main>
  </div>
</template>

<style scoped>
.insights-page {
  min-height: 100vh;
  color: #e8f1ed;
}

.insights-shell {
  position: relative;
  max-width: 1360px;
  margin: 0 auto;
  padding: clamp(30px, 4.8vw, 58px) clamp(20px, 4vw, 44px) 76px;
}

.insights-shell::before {
  content: '';
  position: absolute;
  z-index: -1;
  top: -70px;
  right: 5%;
  width: min(600px, 72vw);
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(71, 139, 116, 0.14), transparent 68%);
  pointer-events: none;
}

.insights-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 30px;
  padding-bottom: 26px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.18);
}

.insights-eyebrow,
.panel-kicker {
  margin: 0 0 12px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.18em;
}

.insights-hero h1 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(42px, 5vw, 58px);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.04em;
}

.insights-desc {
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

.insight-tabs {
  position: sticky;
  top: 76px;
  z-index: 30;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin: 20px 0 22px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 9px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
  backdrop-filter: blur(16px);
}

.insight-tab {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 62px;
  padding: 11px 15px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: rgba(7, 28, 25, 0.92);
  color: #8fa99f;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.insight-tab:hover,
.insight-tab.active {
  background: rgba(19, 58, 51, 0.92);
  border-bottom-color: #8fc7b1;
}

.tab-index {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 10px;
}

.insight-tab.active .tab-index {
  color: #d9c28a;
}

.insight-tab b {
  display: block;
  color: #c9d8d1;
  font-size: 13px;
  font-weight: 500;
}

.insight-tab.active b {
  color: #e8f1ed;
}

.insight-tab small {
  display: block;
  margin-top: 3px;
  color: #6f8c81;
  font-size: 8px;
  letter-spacing: 0.12em;
}

.tab-panel {
  animation: tab-in 0.22s ease both;
}

.panel-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.panel-kicker {
  margin-bottom: 8px;
}

.panel-head h2 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 26px;
  font-weight: 500;
}

.panel-head p {
  max-width: 760px;
  margin: 9px 0 0;
  color: #8fa99f;
  font-size: 12px;
  line-height: 1.75;
}

.panel-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.panel-status small {
  color: #6f8c81;
  font-size: 9px;
}

.status-chip,
.pending-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 10px;
}

.status-chip.warning {
  border: 1px solid rgba(240, 191, 134, 0.35);
  background: rgba(180, 104, 45, 0.12);
  color: #f0bf86;
}

.status-chip.ready {
  border: 1px solid rgba(143, 199, 177, 0.38);
  background: rgba(94, 166, 140, 0.12);
  color: #a7d8c3;
}

.status-chip.pending {
  border: 1px solid rgba(217, 194, 138, 0.32);
  background: rgba(217, 194, 138, 0.08);
  color: #d9c28a;
}

.rule-callout,
.limits-callout {
  padding: 15px 17px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.44);
}

.rule-callout b,
.limits-callout b {
  color: #8fc7b1;
  font-size: 11px;
  font-weight: 500;
}

.rule-callout p,
.api-gate {
  margin: 7px 0 0;
  color: #9bb7ad;
  font-size: 11px;
  line-height: 1.8;
}

.api-gate {
  color: #b99767 !important;
}

.rule-callout code {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
}

.observation-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 18px;
}

.observation {
  display: flex;
  flex-direction: column;
  min-height: 150px;
  padding: 16px 17px;
  border: 1px solid rgba(217, 194, 138, 0.18);
  border-radius: 8px;
  background: rgba(38, 37, 27, 0.35);
}

.observation > span {
  color: #8fa99f;
  font-size: 10px;
}

.observation strong {
  margin-top: 10px;
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 30px;
  font-weight: 500;
  line-height: 1;
}

.observation p {
  margin: 10px 0 0;
  color: #9bb7ad;
  font-size: 11px;
  line-height: 1.7;
}

.observation small {
  margin-top: auto;
  padding-top: 12px;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.5;
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.guide-card {
  padding: 14px 16px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.38);
}

.guide-top {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.guide-top > span {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.guide-top h3 {
  flex: 1;
  margin: 0;
  color: #d7e4dd;
  font-size: 12px;
  font-weight: 500;
}

.guide-top b {
  color: #d9c28a;
  font-size: 9px;
  font-weight: 500;
}

.guide-card p {
  margin: 9px 0 0;
  color: #9bb7ad;
  font-size: 10px;
  line-height: 1.7;
}

.guide-card small {
  display: block;
  margin-top: 7px;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.5;
}

.guide-track {
  height: 3px;
  margin-top: 10px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.guide-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.matrix-scroll {
  overflow-x: auto;
  padding-bottom: 4px;
}

.matrix-table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
}

.matrix-table th,
.matrix-table td {
  padding: 11px 12px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
  text-align: center;
}

.matrix-table thead th {
  color: #78948a;
  font-size: 9px;
  font-weight: 500;
  text-align: center;
}

.matrix-table thead th:first-child,
.matrix-table tbody th {
  text-align: left;
}

.matrix-table thead th span {
  display: block;
  color: #8fc7b1;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.matrix-table thead th small {
  display: block;
  max-width: 160px;
  margin: 4px auto 0;
  overflow: hidden;
  color: #6f8c81;
  font-size: 8px;
  font-weight: 400;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.matrix-table tbody th {
  color: #c9d8d1;
  font-size: 11px;
  font-weight: 400;
}

.matrix-table td {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 19px;
}

.matrix-table td.unknown {
  color: #b99767;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 10px;
}

.matrix-note {
  margin: 13px 0 0;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.7;
}

.case-compare-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.compare-card {
  display: flex;
  flex-direction: column;
  padding: 16px 17px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.38);
}

.compare-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.compare-top span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.compare-top b {
  color: #78948a;
  font-size: 8px;
  font-weight: 500;
}

.compare-card h3 {
  display: -webkit-box;
  margin: 9px 0 0;
  overflow: hidden;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.45;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.compare-card p {
  margin: 6px 0 0;
  color: #8fa99f;
  font-size: 9px;
}

.compare-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 14px;
}

.compare-score strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 28px;
  font-weight: 500;
  line-height: 1;
}

.compare-score span {
  color: #78948a;
  font-size: 9px;
}

.compare-track {
  height: 3px;
  margin-top: 9px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.compare-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.compare-link {
  margin-top: 14px;
  color: #8fc7b1;
  font-size: 9px;
  text-decoration: none;
}

.compare-link:hover {
  color: #d9c28a;
}

.excerpt-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.excerpt-card {
  padding: 15px 16px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.38);
}

.excerpt-top {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.excerpt-top span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.excerpt-top b {
  flex: 1;
  color: #c9d8d1;
  font-size: 11px;
  font-weight: 500;
}

.excerpt-top strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 18px;
  font-weight: 500;
}

.excerpt-card p {
  margin: 10px 0 0;
  color: #9bb7ad;
  font-size: 10px;
  line-height: 1.75;
}

.excerpt-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 11px;
}

.source-chip {
  padding: 2px 5px;
  border: 1px solid rgba(143, 199, 177, 0.18);
  border-radius: 3px;
  color: #8fc7b1;
  font-family: 'Consolas', monospace;
  font-size: 8px;
  text-decoration: none;
}

.source-chip:hover {
  color: #d9c28a;
  border-color: rgba(217, 194, 138, 0.36);
}

.limits-callout {
  margin-top: 18px;
  border-color: rgba(217, 194, 138, 0.2);
  background: rgba(49, 42, 27, 0.3);
}

.limits-callout ul {
  margin: 9px 0 0;
  padding-left: 18px;
}

.limits-callout li {
  margin: 5px 0;
  color: #9bb7ad;
  font-size: 10px;
  line-height: 1.7;
}

.status-chip {
  white-space: nowrap;
}

.pending-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 20px;
  border: 1px solid rgba(217, 194, 138, 0.25);
  border-radius: 9px;
  background: rgba(49, 42, 27, 0.34);
}

.pending-banner > div:first-child > span {
  color: #b99767;
  font-size: 9px;
  letter-spacing: 0.1em;
}

.pending-banner h3 {
  margin: 8px 0 0;
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}

.pending-counter {
  display: flex;
  align-items: baseline;
  gap: 7px;
  flex-shrink: 0;
}

.pending-counter strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 32px;
  font-weight: 500;
}

.pending-counter span {
  color: #8fa99f;
  font-size: 9px;
}

.weight-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin: 16px 0;
}

.weight-card {
  padding: 15px 16px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.38);
}

.weight-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.weight-top span {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.weight-top b {
  color: #d9c28a;
  font-size: 13px;
  font-weight: 500;
}

.weight-card h3 {
  margin: 10px 0 0;
  color: #d7e4dd;
  font-size: 12px;
  font-weight: 500;
}

.weight-card p {
  margin: 8px 0 0;
  color: #8fa99f;
  font-size: 10px;
  line-height: 1.65;
}

.weight-card small {
  display: block;
  margin-top: 12px;
  color: #b99767;
  font-size: 9px;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.formula {
  padding: 14px;
  border: 1px dashed rgba(217, 194, 138, 0.28);
  border-radius: 5px;
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 12px;
  text-align: center;
}

.tier-list {
  display: flex;
  flex-direction: column;
  margin-top: 12px;
}

.tier-list > div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.tier-list span {
  color: #78948a;
  font-size: 9px;
}

.tier-list b {
  color: #c9d8d1;
  font-size: 10px;
  font-weight: 500;
}

.rule-note {
  margin: 12px 0 0;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.7;
}

.pending-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin-top: 18px;
  border: 1px solid rgba(159, 198, 181, 0.12);
  border-radius: 6px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.pending-facts > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px;
  background: rgba(7, 28, 25, 0.8);
}

.pending-facts b {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 22px;
  font-weight: 500;
}

.pending-facts span {
  color: #6f8c81;
  font-size: 8px;
}

.region-scope {
  margin-top: 16px;
}

.scope-label {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 2px;
  border-top: 1px solid rgba(159, 198, 181, 0.14);
  border-bottom: 1px solid rgba(159, 198, 181, 0.14);
}

.scope-label span {
  color: #d9c28a;
  font-size: 10px;
}

.scope-label small {
  color: #78948a;
  font-size: 9px;
}

.region-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
  margin-top: 12px;
}

.region-grid article {
  padding: 14px 15px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 7px;
  background: rgba(5, 25, 22, 0.35);
}

.region-grid span {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 8px;
}

.region-grid h3 {
  margin: 7px 0 0;
  color: #d7e4dd;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 16px;
  font-weight: 500;
}

.region-grid p {
  margin: 7px 0 0;
  color: #8fa99f;
  font-size: 9px;
  line-height: 1.65;
}

.region-grid small {
  display: block;
  margin-top: 10px;
  color: #b99767;
  font-size: 8px;
}

.field-list {
  display: flex;
  flex-direction: column;
}

.field-list > div {
  display: grid;
  grid-template-columns: 128px minmax(0, 1fr) 32px;
  gap: 9px;
  align-items: baseline;
  padding: 8px 0;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.field-list b {
  color: #c9d8d1;
  font-size: 9px;
  font-weight: 500;
}

.field-list span {
  color: #78948a;
  font-size: 9px;
  line-height: 1.55;
}

.field-list em {
  color: #b99767;
  font-size: 8px;
  font-style: normal;
  text-align: right;
}

.enum-title {
  margin: 10px 0 7px;
  color: #8fc7b1;
  font-size: 9px;
  letter-spacing: 0.06em;
}

.enum-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.enum-chips span {
  padding: 4px 6px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 3px;
  color: #8fa99f;
  font-size: 8px;
}

.city-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.city-card {
  padding: 17px 18px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.38);
}

.city-card > span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.city-card h3 {
  margin: 8px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 18px;
  font-weight: 500;
}

.city-card p {
  margin: 8px 0 0;
  color: #9bb7ad;
  font-size: 10px;
  line-height: 1.7;
}

.city-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 12px;
}

.city-fields span {
  padding: 3px 6px;
  border: 1px dashed rgba(217, 194, 138, 0.22);
  border-radius: 3px;
  color: #b99767;
  font-size: 8px;
}

.insights-foot {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid rgba(159, 198, 181, 0.13);
}

.insights-foot p {
  margin: 0 0 5px;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.8;
}

.partial-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
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

.insights-skeleton {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 18px;
}

.skeleton-line,
.skeleton-box {
  display: block;
  border-radius: 7px;
  background: linear-gradient(100deg, rgba(159, 198, 181, 0.05), rgba(159, 198, 181, 0.11), rgba(159, 198, 181, 0.05));
  background-size: 220% 100%;
  animation: shimmer 1.6s ease-in-out infinite;
}

.skeleton-line {
  height: 12px;
}

.skeleton-line.tall {
  height: 58px;
}

.w30 { width: 30%; }
.w60 { width: 60%; }

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.skeleton-box {
  height: 220px;
}

@keyframes shimmer {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}

@keyframes tab-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1100px) {
  .observation-grid,
  .case-compare-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .weight-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .region-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .guide-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 800px) {
  .insights-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-meta {
    flex-basis: auto;
    width: 100%;
  }

  .panel-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .panel-status {
    align-items: flex-start;
  }

  .two-col,
  .excerpt-grid,
  .city-grid {
    grid-template-columns: 1fr;
  }

  .pending-banner {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 560px) {
  .insights-shell {
    padding: 28px 16px 56px;
  }

  .insights-hero h1 {
    font-size: 40px;
  }

  .insight-tabs {
    top: 76px;
    grid-template-columns: 1fr;
  }

  .insight-tab {
    min-height: 54px;
  }

  .matrix-scroll {
    overflow-x: visible;
  }

  .matrix-table {
    min-width: 0;
    table-layout: fixed;
  }

  .matrix-table th,
  .matrix-table td {
    padding: 8px 3px;
  }

  .matrix-table thead th:first-child,
  .matrix-table tbody th {
    width: 42%;
  }

  .matrix-table thead th:not(:first-child) {
    width: 19.3%;
  }

  .matrix-table thead th small {
    display: none;
  }

  .matrix-table tbody th {
    font-size: 10px;
    line-height: 1.35;
  }

  .matrix-table td {
    font-size: 16px;
  }

  .matrix-table td.unknown {
    font-size: 9px;
  }

  .observation-grid,
  .case-compare-grid,
  .weight-grid,
  .region-grid {
    grid-template-columns: 1fr;
  }

  .scope-label {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .field-list > div {
    grid-template-columns: 100px minmax(0, 1fr) 26px;
  }

  .pending-facts {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tab-panel,
  .skeleton-line,
  .skeleton-box {
    animation: none;
  }
}

.gate-count {
  color: #d9c28a;
  font-size: 9px;
}

.gate-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.gate-card {
  padding: 12px 13px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 6px;
  background: rgba(5, 25, 22, 0.34);
}

.gate-top {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.gate-top > span {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 8px;
}

.gate-top h4 {
  flex: 1;
  margin: 0;
  color: #c9d8d1;
  font-size: 11px;
  font-weight: 500;
}

.gate-top b {
  padding: 2px 6px;
  border: 1px solid rgba(159, 198, 181, 0.18);
  border-radius: 999px;
  color: #8fa99f;
  font-size: 8px;
  font-weight: 500;
  white-space: nowrap;
}

.gate-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 9px;
  color: #78948a;
  font-size: 8px;
}

.gate-metrics strong {
  color: #c9d8d1;
  font-weight: 500;
}

.gate-card p {
  margin: 8px 0 0;
  color: #6f8c81;
  font-size: 8px;
  line-height: 1.65;
}

.gate-insufficient .gate-top b {
  color: #d8b392;
  border-color: rgba(226, 162, 118, 0.28);
}

.gate-exploratory .gate-top b {
  color: #d9c28a;
  border-color: rgba(217, 194, 138, 0.3);
}

.gate-descriptive .gate-top b {
  color: #9ed2b5;
  border-color: rgba(143, 199, 177, 0.3);
}

.gate-empty .gate-top b {
  color: #6f8c81;
}

@media (max-width: 620px) {
  .gate-grid {
    grid-template-columns: 1fr;
  }
}


.scope-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin: 18px 0 0;
  padding: 10px 12px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 6px;
  background: rgba(5, 25, 22, 0.34);
}

.scope-selector label {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #78948a;
  font-size: 9px;
}

.scope-selector select {
  height: 30px;
  padding: 0 8px;
  border: 1px solid rgba(159, 198, 181, 0.22);
  border-radius: 4px;
  background: #0b2823;
  color: #d7e4dd;
  font-size: 10px;
}

.scope-summary {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.scope-summary b {
  color: #d9c28a;
  font-size: 10px;
  font-weight: 500;
}

.scope-summary span {
  color: #8fa99f;
  font-size: 9px;
}

.scope-selector > p {
  flex: 1 1 100%;
  margin: 0;
  color: #6f8c81;
  font-size: 8px;
  line-height: 1.5;
}

@media (max-width: 620px) {
  .scope-selector {
    align-items: flex-start;
    flex-direction: column;
    gap: 7px;
  }

  .scope-selector select {
    max-width: 240px;
  }
}


.matrix-scope-note {
  margin: 0 0 10px;
  padding: 10px 12px;
  border-left: 2px solid rgba(217, 194, 138, 0.45);
  background: rgba(49, 42, 27, 0.25);
  color: #b9a484;
  font-size: 9px;
  line-height: 1.7;
}


.approval-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}

.approval-card {
  padding: 13px 14px;
  border: 1px solid rgba(226, 162, 118, 0.25);
  border-radius: 7px;
  background: rgba(49, 42, 27, 0.24);
}

.approval-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.approval-top > span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 8px;
}

.approval-top b {
  color: #d8b392;
  font-size: 8px;
  font-weight: 500;
  text-align: right;
}

.approval-card h4 {
  margin: 8px 0 0;
  color: #d7e4dd;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 14px;
  font-weight: 500;
}

.approval-card p {
  margin: 7px 0 0;
  color: #8fa99f;
  font-size: 9px;
  line-height: 1.6;
}

.approval-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  color: #6f8c81;
  font-size: 8px;
}

.approval-approved {
  border-color: rgba(143, 199, 177, 0.32);
}

.approval-approved .approval-top b {
  color: #9ed2b5;
}

.approval-rejected {
  border-color: rgba(216, 102, 104, 0.3);
}

.approval-needs_more_evidence {
  border-color: rgba(217, 194, 138, 0.35);
}

@media (max-width: 900px) {
  .approval-grid {
    grid-template-columns: 1fr;
  }
}


.finding-panel {
  margin: 0 0 18px;
  padding: 20px 22px;
  border: 1px solid rgba(159, 198, 181, 0.2);
  border-radius: 14px;
  background: rgba(23, 40, 35, 0.72);
}
.finding-head h2 { margin: 4px 0 8px; color: #e8f1ed; }
.finding-head > p:last-child { max-width: 900px; margin: 0; color: #9fb8ae; font-size: 12px; line-height: 1.7; }
.finding-kicker { margin: 0; color: #8fc7b1; font-size: 9px; letter-spacing: 0.16em; }
.finding-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 16px 0 14px; }
.finding-grid article { padding: 12px; border: 1px solid rgba(159, 198, 181, 0.12); border-radius: 9px; background: rgba(8, 19, 16, 0.35); }
.finding-grid strong { display: block; color: #a9d9b8; font-size: 21px; line-height: 1.1; }
.finding-grid span { display: block; margin-top: 5px; color: #d8e6df; font-size: 11px; }
.finding-grid small { display: block; margin-top: 5px; color: #7f9b8f; font-size: 10px; line-height: 1.5; }
.finding-boundary { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; border-top: 1px solid rgba(159, 198, 181, 0.12); padding-top: 12px; }
.finding-boundary p { margin: 0; color: #9fb8ae; font-size: 11px; line-height: 1.7; }
.finding-boundary b { color: #d8e6df; }
@media (max-width: 820px) {
  .finding-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .finding-boundary { grid-template-columns: 1fr; }
}

</style>
