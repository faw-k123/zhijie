<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import ResearchState from '@/components/research/ResearchState.vue'
import SampleBadge from '@/components/research/SampleBadge.vue'
import ScoreIndicator from '@/components/research/ScoreIndicator.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import SourceItem from '@/components/research/SourceItem.vue'
import { fetchResearchCase } from '@/api/research'
import type { ResearchCaseDetail, ResearchSimilarCase } from '@/types/research'

const route = useRoute()
const router = useRouter()

const caseId = computed(() => String(route.params.caseId || '').toUpperCase())
const detail = ref<ResearchCaseDetail | null>(null)
const loading = ref(true)
const error = ref('')
const notFound = ref(false)
let requestSeq = 0

const currentCase = computed(() => detail.value?.case ?? null)
const coding = computed(() => detail.value?.coding ?? null)
const sample = computed(() => detail.value?.sample ?? null)
const sources = computed(() => currentCase.value?.sources ?? [])
const missingIndicators = computed(() =>
  (coding.value?.indicators ?? [])
    .filter((indicator) => indicator.score === null)
    .map((indicator) => indicator.label),
)
const similarCases = computed(() => detail.value?.similar_cases ?? [])
const audienceFeedback = computed(() => detail.value?.audience_feedback ?? [])
const acceptanceMechanisms = computed(() =>
  (detail.value?.acceptance_mechanisms ?? []).filter(
    (item) => item.status === 'strong' || item.status === 'partial',
  ),
)

const sampleStatusLabel = computed(() => {
  const value = currentCase.value?.analysis_sample
  if (value === 'strict_individual') return '严格个人样本（已批准）'
  if (value === 'extended_cross_cultural') return '扩展跨文化样本'
  if (value === 'pending_review') return '待核实 · 不纳入严格个人样本'
  return '样本分类未记录'
})

const approvalStatusLabel = computed(() => {
  const value = currentCase.value?.owner_approval_status
  if (value === 'approved') return '审批：已批准'
  if (value === 'needs_more_evidence') return '审批：待补证'
  if (value === 'not_required') return '审批：无需审批'
  return '审批：未记录'
})

const infoRows = computed(() => {
  const item = currentCase.value
  if (!item) return []
  return [
    ['国家 / 区域', `${item.country} / ${item.region}${item.subregion ? ` · ${item.subregion}` : ''}`],
    ['演奏者类型', item.performer_type],
    ['乐器', item.instrument.join(' / ')],
    ['音乐类型', item.music_type],
    ['记录时间', item.event_date_text],
    ['地点', item.venue],
    ['活动', item.event_name],
    ['传播渠道', item.channel.join(' / ')],
    ['目标受众', item.target_audience.join(' / ')],
    ['时代主题', item.era_theme.join(' / ')],
    ['宗教文化背景', item.religion_culture],
  ]
})

const resultBlocks = computed(() => {
  const item = currentCase.value
  if (!item) return []
  return [
    {
      key: 'result',
      label: '传播结果',
      text: item.success_evidence,
      note: '只复述已记录的成功证据，不新增推断',
    },
    {
      key: 'feedback',
      label: '受众反馈',
      text: item.feedback,
      note: '未采集或未知时保持原文，不补写好评',
    },
  ].filter((block) => Boolean(block.text))
})

function errorText(err: unknown) {
  const e = err as { message?: string }
  return e?.message || '网络请求失败'
}

async function loadDetail() {
  const seq = ++requestSeq
  loading.value = true
  error.value = ''
  notFound.value = false
  try {
    const response = await fetchResearchCase(caseId.value)
    if (seq !== requestSeq) return
    if (!response.data) throw new Error('案例详情接口未返回有效数据')
    detail.value = response.data
  } catch (err) {
    if (seq !== requestSeq) return
    detail.value = null
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 404) {
      notFound.value = true
    } else {
      error.value = `案例详情加载失败：${errorText(err)}`
    }
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

function formatScore(score: number | null | undefined) {
  return score === null || score === undefined ? '—' : score.toFixed(2)
}

function similarTo(item: ResearchSimilarCase) {
  return { name: 'global-case-detail', params: { caseId: item.case_id } }
}

function goBack() {
  router.push({ name: 'global-cases' })
}

watch(caseId, () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
  void loadDetail()
})

onMounted(loadDetail)
</script>

<template>
  <div class="page research-page case-detail-page">
    <AppNav />

    <main class="detail-shell">
      <div v-if="loading" class="detail-skeleton" aria-busy="true">
        <i class="skeleton-line w20" />
        <i class="skeleton-line tall w60" />
        <i class="skeleton-line w40" />
        <div class="skeleton-grid">
          <i class="skeleton-box" />
          <i class="skeleton-box" />
        </div>
      </div>

      <ResearchState
        v-else-if="notFound"
        kind="empty"
        title="案例不存在或未公开"
        :message="`没有找到 ${caseId} 的可展示案例；该案例可能尚未审核或不属于公开列表。`"
        retryable
        retry-label="返回案例库"
        @retry="goBack"
      />

      <ResearchState
        v-else-if="error"
        kind="error"
        title="案例详情加载失败"
        :message="error"
        retryable
        @retry="loadDetail"
      />

      <template v-else-if="detail && currentCase">
        <div class="detail-topline">
          <RouterLink :to="{ name: 'global-cases' }" class="back-link">← 返回案例库</RouterLink>
          <span class="detail-path">CASE LIBRARY / {{ currentCase.case_id }}</span>
          <SampleBadge :sample="sample" compact mode="library" />
        </div>

        <div class="sample-notice" :class="{ 'is-pending': currentCase.analysis_sample === 'pending_review' }">
          <strong>{{ sampleStatusLabel }}</strong>
          <span>{{ approvalStatusLabel }}</span>
          <span>已评分 {{ coding?.valid_count ?? 0 }} 项 · 未知 {{ coding?.missing_count ?? 0 }} 项</span>
          <span v-if="currentCase.analysis_sample === 'pending_review'">待核实案例不参与严格个人样本统计。</span>
        </div>

        <header class="detail-hero">
          <div class="detail-hero-copy">
            <p class="detail-eyebrow">CASE STUDY · {{ currentCase.case_id }}</p>
            <h1>{{ currentCase.performer }}</h1>
            <p class="detail-hero-summary">{{ currentCase.summary }}</p>
            <div class="meta-chips">
              <span>{{ currentCase.country }}</span>
              <span>{{ currentCase.region }}<template v-if="currentCase.subregion"> · {{ currentCase.subregion }}</template></span>
              <span v-for="instrument in currentCase.instrument" :key="instrument">{{ instrument }}</span>
              <span class="grade-chip">证据 {{ currentCase.review_status }}</span>
            </div>
          </div>

          <div class="score-panel">
            <p>已评分指标均值（仅供描述）</p>
            <strong>{{ formatScore(coding?.mean_score) }}<small>/ {{ coding?.score_scale ?? 3 }}</small></strong>
            <div class="score-meta">
              <span>{{ coding?.valid_count ?? 0 }} 项有效</span>
              <span>{{ coding?.missing_count ?? 0 }} 项未知</span>
            </div>
            <p v-if="missingIndicators.length" class="score-note missing-note">
              未知指标：{{ missingIndicators.join('、') }}。没有证据，不按 0 分。
            </p>
            <div class="score-track">
              <i :style="{ width: `${((coding?.mean_score ?? 0) / (coding?.score_scale ?? 3)) * 100}%` }" />
            </div>
            <p class="score-note">均值仅描述已评分指标，不代表证据等级、传播成功率或排名。</p>
          </div>
        </header>

        <div class="detail-grid">
          <div class="main-column">
            <SectionCard
              title="案例摘要与背景"
              kicker="CONTEXT"
              subtitle="只呈现研究记录中的事实，不补写未记录的时间线。"
            >
              <div class="background-block">
                <p class="background-summary">{{ currentCase.summary }}</p>
                <div class="background-row">
                  <span>学习 / 接触动机</span>
                  <p>{{ currentCase.learning_motivation }}</p>
                </div>
                <div class="background-row">
                  <span>改编与呈现</span>
                  <p>{{ currentCase.adaptation }}</p>
                </div>
                <div v-if="currentCase.research_notes" class="background-row muted">
                  <span>研究备注</span>
                  <p>{{ currentCase.research_notes }}</p>
                </div>
              </div>
            </SectionCard>

            <SectionCard
              title="10 项指标评分"
              kicker="CODING RUBRIC"
              subtitle="0—3 分；未知项保持未知，不按 0 分处理。每项评分附证据说明。"
            >
              <template #actions>
                <span class="score-chip">已评分均值 {{ formatScore(coding?.mean_score) }} / 3</span>
              </template>
              <div class="indicator-grid">
                <ScoreIndicator
                  v-for="(indicator, index) in coding?.indicators"
                  :key="indicator.indicator_id"
                  :indicator="indicator"
                  :index="index + 1"
                />
              </div>
            </SectionCard>

            <SectionCard
              title="外国受众反馈证据"
              kicker="AUDIENCE EVIDENCE"
              subtitle="逐条呈现可追溯的海外受众原始反馈、语境与证据限制。"
            >
              <div v-if="audienceFeedback.length" class="feedback-list">
                <article v-for="item in audienceFeedback" :key="item.feedback_id" class="feedback-card">
                  <div class="feedback-head">
                    <span>{{ item.feedback_id }} · {{ item.evidence_type }}</span>
                    <b>证据 {{ item.evidence_grade }}</b>
                  </div>
                  <blockquote v-if="item.excerpt">“{{ item.excerpt }}”</blockquote>
                  <p>{{ item.summary }}</p>
                  <dl>
                    <div><dt>受众语境</dt><dd>{{ item.country_basis }}</dd></div>
                    <div><dt>语言 / 倾向</dt><dd>{{ item.language || '未知' }} / {{ item.valence || '未知' }}</dd></div>
                    <div v-if="item.limitations"><dt>证据限制</dt><dd>{{ item.limitations }}</dd></div>
                  </dl>
                  <a :href="item.source_url" target="_blank" rel="noopener noreferrer">查看原始来源 ↗</a>
                </article>
              </div>
              <ResearchState v-else kind="empty" title="暂无外国受众反馈" message="该案例尚无可公开、可追溯的受众反馈证据。" compact />
            </SectionCard>

            <SectionCard
              title="外国受众为什么接受"
              kicker="ACCEPTANCE MECHANISMS"
              subtitle="依据本案例反馈与来源编码，只展示已见强证据或部分证据的接受机制。"
            >
              <div v-if="acceptanceMechanisms.length" class="mechanism-grid">
                <article
                  v-for="item in acceptanceMechanisms"
                  :key="item.code"
                  class="mechanism-card"
                  :class="item.status"
                >
                  <span>{{ item.code }}</span>
                  <h3>{{ item.label }}</h3>
                  <b>{{ item.status_label }}</b>
                </article>
              </div>
              <p class="mechanism-note">
                编码置信度：{{ detail.acceptance_mechanism_confidence || '未记录' }}。这里说明证据支持的接受路径，不把国籍或宗教直接推断为偏好。
              </p>
            </SectionCard>

            <SectionCard
              title="传播结果摘要"
              kicker="OUTCOME"
              :subtitle="`结果类型：${detail.outcome_label}`"
            >
              <div class="process-grid">
                <article v-for="block in resultBlocks" :key="block.key" class="process-block">
                  <span>{{ block.label }}</span><p>{{ block.text }}</p><small>{{ block.note }}</small>
                </article>
              </div>
            </SectionCard>
          </div>

          <aside class="side-column">
            <SectionCard title="案例信息" kicker="CASE FACTS" tone="quiet">
              <div class="info-list">
                <div v-for="[label, value] in infoRows" :key="label" class="info-row">
                  <span>{{ label }}</span>
                  <b>{{ value || '未知' }}</b>
                </div>
              </div>
            </SectionCard>

            <SectionCard title="来源索引" kicker="SOURCE INDEX" tone="quiet">
              <p class="source-index-lead">
                {{ currentCase.source_count }} 条来源，均可追溯到案例字段。点击编号跳到下方来源卡片。
              </p>
              <div class="source-index">
                <a
                  v-for="source in sources"
                  :key="source.source_id"
                  :href="`#source-${source.source_id}`"
                >
                  <span>{{ source.source_id }}</span>
                  <b>{{ source.publisher }}</b>
                  <small>可靠性 {{ source.reliability }}</small>
                </a>
              </div>
            </SectionCard>
          </aside>
        </div>

        <SectionCard
          title="证据与来源"
          kicker="EVIDENCE & SOURCES"
          subtitle="来源按原始记录列出；外部链接在新窗口打开。"
        >
          <div v-if="sources.length" class="source-list">
            <SourceItem v-for="source in sources" :key="source.source_id" :source="source" />
          </div>
          <ResearchState
            v-else
            kind="empty"
            title="暂无来源记录"
            message="该案例没有可展示的来源，不能作为正式结论依据。"
            compact
          />
        </SectionCard>

        <SectionCard
          title="相似案例"
          kicker="SIMILAR CASES"
          subtitle="由后端规则返回，不是前端自行编造；匹配分只表示规则相似度。"
        >
          <div v-if="similarCases.length" class="similar-grid">
            <RouterLink
              v-for="item in similarCases"
              :key="item.case_id"
              :to="similarTo(item)"
              class="similar-card"
            >
              <div class="similar-top">
                <span>{{ item.case_id }}</span>
                <b>匹配 {{ item.match_score }}</b>
              </div>
              <h3>{{ item.performer }}</h3>
              <p>{{ item.country }} · {{ item.region }} · {{ item.instrument.join(' / ') }}</p>
              <p class="similar-reasons">{{ item.match_reasons.join(' · ') }}</p>
              <div class="similar-foot">
                <span>已评分均值 {{ formatScore(item.mean_score) }} / 3</span>
                <span>证据 {{ item.review_status }}</span>
              </div>
            </RouterLink>
          </div>
          <ResearchState
            v-else
            kind="empty"
            title="暂无相似案例"
            message="后端未返回可展示的相似案例。"
            compact
          />
        </SectionCard>

        <footer class="detail-foot">
          <p>
            本页只展示已审核案例。评分、受众反馈和接受原因均可追溯到来源；未知值不以 0 分或推断补齐。
          </p>
          <button type="button" class="back-button" @click="goBack">返回案例库</button>
        </footer>
      </template>
    </main>
  </div>
</template>

<style scoped>
.case-detail-page {
  min-height: 100vh;
  color: #e8f1ed;
}

.detail-shell {
  position: relative;
  max-width: 1320px;
  margin: 0 auto;
  padding: clamp(24px, 4vw, 48px) clamp(20px, 4vw, 44px) 76px;
}

.detail-shell::before {
  content: '';
  position: absolute;
  z-index: -1;
  top: -80px;
  right: 5%;
  width: min(620px, 72vw);
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(71, 139, 116, 0.14), transparent 68%);
  pointer-events: none;
}

.detail-topline {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.back-link {
  color: #8fc7b1;
  font-size: 11px;
  text-decoration: none;
}

.back-link:hover {
  color: #d9c28a;
}

.detail-path {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 9px;
  letter-spacing: 0.08em;
}

.detail-topline :deep(.sample-badge) {
  margin-left: auto;
}

.detail-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  padding-bottom: 28px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.18);
}

.detail-hero-copy {
  min-width: 0;
}

.detail-eyebrow {
  margin: 0 0 12px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.18em;
}

.detail-hero-copy h1 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(32px, 4.2vw, 48px);
  font-weight: 500;
  line-height: 1.18;
  letter-spacing: 0.02em;
}

.detail-hero-summary {
  max-width: 760px;
  margin: 17px 0 0;
  color: #b6c9c1;
  font-size: 13px;
  line-height: 1.85;
}

.meta-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 17px;
}

.meta-chips span {
  padding: 4px 8px;
  border: 1px solid rgba(159, 198, 181, 0.19);
  border-radius: 4px;
  color: #9bb7ad;
  font-size: 10px;
}

.meta-chips .grade-chip {
  border-color: rgba(217, 194, 138, 0.32);
  color: #d9c28a;
}

.sample-notice {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  align-items: center;
  margin: 12px 0 18px;
  padding: 10px 14px;
  border: 1px solid rgba(143, 199, 177, 0.25);
  border-radius: 10px;
  background: rgba(94, 166, 140, 0.08);
  color: #a9d9b8;
  font-size: 11px;
  line-height: 1.5;
}

.sample-notice strong { color: #d8eadf; }

.sample-notice.is-pending {
  border-color: rgba(217, 194, 138, 0.35);
  background: rgba(217, 194, 138, 0.08);
  color: #e8d4a8;
}

.sample-notice.is-pending strong { color: #f0d89f; }

.score-panel {
  flex: 0 0 min(250px, 26%);
  padding: 18px 20px;
  border: 1px solid rgba(217, 194, 138, 0.24);
  border-radius: 10px;
  background: rgba(40, 41, 29, 0.38);
}

.score-panel > p:first-child {
  margin: 0;
  color: #8fa99f;
  font-size: 10px;
  letter-spacing: 0.06em;
}

.score-panel strong {
  display: block;
  margin-top: 10px;
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 48px;
  font-weight: 500;
  line-height: 0.95;
}

.score-panel strong small {
  margin-left: 4px;
  color: #8fa99f;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
}

.score-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
  color: #78948a;
  font-size: 9px;
}

.score-track {
  height: 4px;
  margin-top: 9px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.score-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.score-note {
  margin: 12px 0 0;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.6;
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 310px;
  gap: 18px;
  align-items: start;
  margin-top: 22px;
}

.main-column,
.side-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.side-column {
  position: sticky;
  top: 96px;
}

.background-block {
  display: flex;
  flex-direction: column;
  gap: 17px;
}

.background-summary {
  margin: 0;
  color: #d7e4dd;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 19px;
  line-height: 1.75;
}

.background-row {
  display: grid;
  grid-template-columns: 116px minmax(0, 1fr);
  gap: 16px;
  padding-top: 15px;
  border-top: 1px solid rgba(159, 198, 181, 0.11);
}

.background-row > span {
  color: #8fc7b1;
  font-size: 10px;
}

.background-row p {
  margin: 0;
  color: #b6c9c1;
  font-size: 12px;
  line-height: 1.8;
}

.background-row.muted p {
  color: #8fa99f;
}

.score-chip {
  padding: 4px 8px;
  border: 1px solid rgba(217, 194, 138, 0.3);
  border-radius: 999px;
  color: #d9c28a;
  font-size: 10px;
}

.indicator-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.feedback-list {
  display: grid;
  gap: 12px;
}

.feedback-card {
  padding: 18px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  background: rgba(10, 30, 24, 0.34);
}

.feedback-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #8fc7b1;
  font-size: 12px;
}

.feedback-head b { color: #e8d4a8; font-weight: 500; }
.feedback-card blockquote { margin: 14px 0 8px; color: #f0e5cc; font-size: 17px; line-height: 1.7; }
.feedback-card > p { margin: 0 0 12px; color: #c7d7d0; line-height: 1.75; }
.feedback-card dl { margin: 0; display: grid; gap: 6px; }
.feedback-card dl div { display: grid; grid-template-columns: 78px 1fr; gap: 10px; }
.feedback-card dt { color: #77958a; font-size: 12px; }
.feedback-card dd { margin: 0; color: #aabfb6; font-size: 12px; line-height: 1.6; }
.feedback-card a { display: inline-block; margin-top: 12px; color: #8fc7b1; font-size: 12px; }

.mechanism-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.mechanism-card {
  padding: 15px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  background: rgba(10, 30, 24, 0.3);
}

.mechanism-card.strong { border-color: rgba(143, 199, 177, 0.35); }
.mechanism-card > span { color: #78948a; font-size: 11px; }
.mechanism-card h3 { margin: 8px 0; color: #dce8e2; font-size: 14px; }
.mechanism-card b { color: #e8d4a8; font-size: 11px; font-weight: 500; }
.mechanism-note { margin: 14px 0 0; color: #78948a; font-size: 11px; line-height: 1.7; }

.process-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.process-block {
  padding: 16px 17px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.38);
}

.process-block > span {
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.06em;
}

.process-block p {
  margin: 9px 0 0;
  color: #b6c9c1;
  font-size: 12px;
  line-height: 1.75;
}

.process-block small {
  display: block;
  margin-top: 10px;
  color: #6f8c81;
  font-size: 9px;
  line-height: 1.55;
}

.info-list {
  display: flex;
  flex-direction: column;
}

.info-row {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.info-row:last-child {
  border-bottom: 0;
}

.info-row span {
  color: #78948a;
  font-size: 9px;
}

.info-row b {
  color: #c9d8d1;
  font-size: 10px;
  font-weight: 500;
  line-height: 1.6;
  text-align: right;
}

.source-index-lead {
  margin: 0 0 12px;
  color: #8fa99f;
  font-size: 10px;
  line-height: 1.65;
}

.source-index {
  display: flex;
  flex-direction: column;
}

.source-index a {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 3px 8px;
  padding: 8px 0;
  border-top: 1px solid rgba(159, 198, 181, 0.1);
  text-decoration: none;
}

.source-index a span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.source-index a b {
  color: #9bb7ad;
  font-size: 9px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-index a small {
  grid-column: 1 / -1;
  color: #6f8c81;
  font-size: 8px;
}

.source-index a:hover b {
  color: #d9c28a;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.similar-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.similar-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 15px 16px;
  border: 1px solid rgba(159, 198, 181, 0.15);
  border-radius: 8px;
  background: rgba(5, 25, 22, 0.4);
  text-decoration: none;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.similar-card:hover {
  border-color: rgba(143, 199, 177, 0.34);
  transform: translateY(-2px);
}

.similar-top,
.similar-foot {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.similar-top span {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.similar-top b {
  color: #8fc7b1;
  font-size: 9px;
  font-weight: 500;
}

.similar-card h3 {
  margin: 10px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 17px;
  font-weight: 500;
  line-height: 1.4;
}

.similar-card p {
  margin: 6px 0 0;
  color: #8fa99f;
  font-size: 10px;
  line-height: 1.6;
}

.similar-card .similar-reasons {
  color: #78948a;
  font-size: 9px;
}

.similar-foot {
  margin-top: 13px;
  padding-top: 10px;
  border-top: 1px solid rgba(159, 198, 181, 0.1);
  color: #6f8c81;
  font-size: 9px;
}

.detail-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid rgba(159, 198, 181, 0.13);
}

.detail-foot p {
  margin: 0;
  color: #6f8c81;
  font-size: 10px;
  line-height: 1.8;
}

.back-button {
  flex-shrink: 0;
  padding: 8px 14px;
  border: 1px solid rgba(159, 198, 181, 0.24);
  border-radius: 4px;
  background: transparent;
  color: #9bb7ad;
  font-size: 10px;
  cursor: pointer;
}

.detail-skeleton {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 24px;
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
  height: 64px;
}

.w20 { width: 20%; }
.w40 { width: 40%; }
.w60 { width: 60%; }

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.skeleton-box {
  height: 340px;
}

@keyframes shimmer {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}

@media (max-width: 1100px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    position: static;
  }

  .indicator-grid,
  .process-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 800px) {
  .detail-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .score-panel {
    flex-basis: auto;
    width: 100%;
  }

  .indicator-grid,
  .process-grid,
  .similar-grid {
    grid-template-columns: 1fr;
  }

  .background-row {
    grid-template-columns: 1fr;
    gap: 7px;
  }

  .detail-foot {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 700px) {
  .mechanism-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 520px) {
  .detail-shell {
    padding: 22px 16px 56px;
  }

  .detail-topline {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .detail-path {
    order: 3;
    width: 100%;
  }

  .detail-topline :deep(.sample-badge) {
    margin-left: 0;
  }

  .detail-hero-copy h1 {
    font-size: 30px;
  }

  .score-panel strong {
    font-size: 42px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-line,
  .skeleton-box {
    animation: none;
  }
}

.missing-note {
  margin-top: 8px;
  color: #d7b98a;
}

</style>
