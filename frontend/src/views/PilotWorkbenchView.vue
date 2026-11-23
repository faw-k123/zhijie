<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import {
  approvePilotEvidence,
  approvePilotLocalization,
  approvePilotBatch,
  approvePilotConfig,
  approvePilotScore,
  createPilotScoreDraft,
  fetchPilotOverview,
  generatePilotLocalizationSources,
  importPilotRows,
  publishPilotScore,
  revokePublishedPilot,
  revokePilotScore,
  submitPilotConfig,
  submitPilotEvidence,
  submitPilotLocalization,
} from '@/api/research'
import type { PilotBatch, PilotLocalization, PilotOverview, PilotUnit } from '@/types/research'

const overview = ref<PilotOverview | null>(null)
const loading = ref(true)
const error = ref('')
const actionError = ref('')
const actionNotice = ref('')
const selectedCountry = ref('all')
const selectedMusic = ref('all')
const selectedStatus = ref('all')
const selectedVariant = ref('all')
const token = ref(sessionStorage.getItem('pilot-token') || '')
const evidenceMusic = ref('MU001')
const evidenceScore = ref<number | null>(null)
const evidenceSource = ref('')
const evidenceRule = ref('EV-RULE-1')
const pendingConfigVersion = ref('')
const configDraft = reactive({
  min_per_variant: 20, min_per_cell: 40, variant_balance_tolerance: 0.25,
  min_country_total: 120, min_country_cells: 12, min_completion_rate: 70,
  max_missing_ratio: 0.2, cross_country_min_countries: 3, cross_country_min_cells: 12,
})
const batchLabel = ref('六国实测批次')
const importedBatch = ref<PilotBatch | null>(null)
const scoreTitle = ref('六国实测评分草稿')
const busy = ref(false)

const statusLabels: Record<string, string> = {
  not_started: '未开始',
  descriptive_only: '仅描述',
  insufficient_sample: '样本不足',
  variant_imbalance: '版本不平衡',
  incomplete_measurement: '测量不完整',
  awaiting_evidence: '待证据分',
  eligible_for_review: '可评审',
  pending_approval: '待审批',
  approved_candidate: '候选分已审批',
  published: '已发布',
  superseded: '已被替代',
  revoked: '已撤销',
  revoked_published: '已撤销发布',
}

const units = computed(() => overview.value?.units ?? [])
const publishedKeyMap = computed(() => new Map((overview.value?.published?.units ?? []).map((unit) => [`${unit.country}-${unit.music_id}`, unit])))
const displayUnits = computed(() => units.value.map((unit) => {
  const published = publishedKeyMap.value.get(`${unit.country}-${unit.music_id}`)
  return published ? { ...unit, formal_score: published.formal_score, evidence_record_id: published.evidence_record_id ?? unit.evidence_record_id } : unit
}))
const countries = computed(() => [...new Set(units.value.map((unit) => unit.country))])
const musicOptions = computed(() => {
  const seen = new Map<string, string>()
  for (const unit of units.value) seen.set(unit.music_id, unit.title)
  return [...seen.entries()].map(([music_id, title]) => ({ music_id, title }))
})
const filteredUnits = computed(() => displayUnits.value.filter((unit) => {
  if (selectedCountry.value !== 'all' && unit.country !== selectedCountry.value) return false
  if (selectedMusic.value !== 'all' && unit.music_id !== selectedMusic.value) return false
  if (selectedStatus.value !== 'all' && unit.status !== selectedStatus.value) return false
  if (selectedVariant.value === 'original' && unit.n_original === 0) return false
  if (selectedVariant.value === 'adapted' && unit.n_adapted === 0) return false
  return true
}))
const counts = computed(() => overview.value?.status_counts ?? {})
const withData = computed(() => displayUnits.value.filter((unit) => unit.n_total > 0).length)
const eligible = computed(() => units.value.filter((unit) => unit.status === 'eligible_for_review').length)
const pendingScores = computed(() => (overview.value?.scores ?? []).filter((item) => item.status === 'pending_approval').length)
const approvedScores = computed(() => (overview.value?.scores ?? []).filter((item) => item.status === 'approved_candidate').length)
const publishedVersion = computed(() => overview.value?.published?.version || '')
const configApproved = computed(() => overview.value?.config.status === 'approved')
const readyCountries = computed(() => (overview.value?.country_summary ?? []).filter((row) => row.country_ready).length)
const batches = computed(() => overview.value?.batches ?? [])
const evidenceItems = computed(() => overview.value?.evidence ?? [])
const protocolDoc = computed(() => overview.value?.protocol ?? null)
const assignmentCounts = computed(() => overview.value?.assignments ?? {
  total: 0, active: 0, withdrawn: 0, by_country: {}, by_status: {}, by_variant: {}, cells: [], imbalanced_cells: 0,
})
const localizationOverview = computed(() => overview.value?.localizations ?? null)
const localizationItems = computed(() => localizationOverview.value?.items ?? [])
const pendingLocalizations = computed(() => localizationItems.value.filter((item) => item.status !== 'approved').length)

function saveToken() {
  sessionStorage.setItem('pilot-token', token.value)
  actionNotice.value = token.value ? '令牌已保存在当前浏览器会话。' : '令牌已清除。'
}

function requireToken() {
  if (!token.value.trim()) { actionError.value = '请先填写服务端签发的访问令牌'; return false }
  return true
}

function downloadJson(filename: string, value: unknown) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

async function generateLocalizationSources() {
  if (!requireToken() || !protocolDoc.value) return
  busy.value = true
  actionError.value = ''
  try {
    await generatePilotLocalizationSources(protocolDoc.value.protocol_version, token.value)
    actionNotice.value = '六国中文母版已生成；本地语言字段保持空白，等待翻译与母语审校。'
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '生成本地化母版失败'
  } finally { busy.value = false }
}

function exportLocalization(item: PilotLocalization) {
  if (!item.source_zh) return
  downloadJson(`${item.localization_version || item.country}-translation-template.json`, {
    protocol_version: item.protocol_version,
    country: item.country,
    language: item.language,
    localization_version: item.localization_version,
    source_zh: item.source_zh,
    translations: item.translations,
    instructions: '仅填写translations；不得把机器草稿标记为母语审校完成。',
  })
}

async function onLocalizationFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !requireToken()) return
  busy.value = true
  actionError.value = ''
  try {
    const payload = JSON.parse(await file.text()) as {
      protocol_version?: string
      country?: string
      translations?: Record<string, unknown>
    }
    if (!payload.protocol_version || !payload.country || !payload.translations) {
      throw new Error('JSON必须包含protocol_version、country和translations')
    }
    await submitPilotLocalization(payload.protocol_version, payload.country, payload.translations, token.value)
    actionNotice.value = `${payload.country}本地化材料已提交母语审校。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '本地化材料导入失败'
  } finally {
    busy.value = false
    input.value = ''
  }
}

async function approveLocalization(item: PilotLocalization) {
  if (!requireToken()) return
  busy.value = true
  actionError.value = ''
  try {
    await approvePilotLocalization(item.protocol_version, item.country, token.value)
    actionNotice.value = `${item.country}本地化材料已通过母语审校。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '本地化审批失败'
  } finally { busy.value = false }
}

function statusLabel(status: string) {
  return statusLabels[status] || status
}

function statusClass(status: string) {
  if (status === 'eligible_for_review') return 'ok'
  if (status === 'awaiting_evidence' || status === 'descriptive_only') return 'warn'
  if (status === 'insufficient_sample' || status === 'variant_imbalance' || status === 'incomplete_measurement') return 'bad'
  return 'muted'
}

function unitLabel(unit: PilotUnit) {
  return `${unit.country} / ${unit.music_id} ${unit.title}`
}

function formatScore(value: number | null) {
  return value === null ? '—' : value.toFixed(2)
}

function csvCell(value: unknown) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`
}

function exportUnits() {
  const header = ['国家', '曲目ID', '曲目', '原版n', '适配版n', '有效n', '状态', '正式评分', '证据分', '说明']
  const rows = filteredUnits.value.map((unit) => [
    unit.country, unit.music_id, unit.title, unit.n_original, unit.n_adapted, unit.n_total,
    statusLabel(unit.status), formatScore(unit.formal_score), unit.evidence_score ?? '', unit.status_reason,
  ])
  const body = [header, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n')
  const blob = new Blob([`\uFEFF${body}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '六国实测单元.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function exportReport() {
  if (!overview.value) return
  const lines = [
    '# 六国实测阶段报告',
    '',
    `生成时间：${new Date().toISOString()}`,
    `计划单元：${overview.value.sample.cells}`,
    `已有反馈单元：${withData.value}`,
    `可评审单元：${eligible.value}`,
    `待审批评分：${pendingScores.value}`,
    `门槛状态：${configApproved.value ? '已审批' : '建议值，未审批'}`,
    '',
    '## 门槛',
    `- 每版本最低有效样本：${overview.value.config.min_per_variant}`,
    `- 版本差异上限：${Math.round(overview.value.config.variant_balance_tolerance * 100)}%`,
    `- 完整观看率下限：${overview.value.config.min_completion_rate}%`,
    `- 国家最低有效样本：${overview.value.config.min_country_total}`,
    `- 国家最低覆盖单元：${overview.value.config.min_country_cells}`,
    '',
    '## 计算口径',
    `- 正式分：${overview.value.formula.score}`,
    `- 既有传播证据：${overview.value.formula.existing_evidence}`,
    '- 跨国汇总：国家内先聚合，再对国家等权。',
    '',
    '## 单元明细',
    '| 国家 | 曲目 | 原版n | 适配版n | 状态 | 正式分 | 开放回答 | 风险 |',
    '|---|---|---:|---:|---|---:|---:|---:|',
    ...filteredUnits.value.map((unit) => `| ${unit.country} | ${unit.music_id} ${unit.title} | ${unit.n_original} | ${unit.n_adapted} | ${statusLabel(unit.status)} | ${formatScore(unit.formal_score)} | ${unit.open_responses.length} | ${unit.cultural_risk_flags.length} |`),
    '',
    '## 解释边界',
    '本报告不把样本不足单元补 0；正式排名须门槛配置、批次、评分均审批，且八项完整。',
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '六国实测阶段报告.md'
  link.click()
  URL.revokeObjectURL(url)
}

function parseCsv(text: string): Array<Record<string, string>> {
  const rows: string[][] = []
  let row: string[] = []
  let cell = ''
  let quoted = false
  const source = text.replace(/^\uFEFF/, '')
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i]
    if (char === '"') {
      if (quoted && source[i + 1] === '"') { cell += '"'; i += 1 } else { quoted = !quoted }
    } else if (char === ',' && !quoted) {
      row.push(cell); cell = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && source[i + 1] === '\n') i += 1
      row.push(cell); cell = ''
      if (row.some((item) => item.trim() !== '')) rows.push(row)
      row = []
    } else {
      cell += char
    }
  }
  if (cell !== '' || row.length) { row.push(cell); if (row.some((item) => item.trim() !== '')) rows.push(row) }
  if (!rows.length) return []
  const headers = (rows[0] ?? []).map((item) => item.trim())
  return rows.slice(1).map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])))
}

async function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  actionError.value = ''
  actionNotice.value = ''
  busy.value = true
  try {
    const rows = parseCsv(await file.text())
    if (!rows.length) throw new Error('CSV 没有数据行')
    const imported = await importPilotRows(rows, batchLabel.value, token.value)
    if (!imported) throw new Error('导入接口未返回批次')
    importedBatch.value = imported
    actionNotice.value = `已导入 ${imported.batch_id}：${imported.rows_clean} 条清洗记录，${imported.rows_rejected} 条隔离。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '导入失败'
  } finally {
    busy.value = false
    input.value = ''
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const next = await fetchPilotOverview()
    if (!next) throw new Error('六国测试数据为空')
    overview.value = next
    Object.assign(configDraft, {
      min_per_variant: next.config.min_per_variant, min_per_cell: next.config.min_per_cell,
      variant_balance_tolerance: next.config.variant_balance_tolerance,
      min_country_total: next.config.min_country_total, min_country_cells: next.config.min_country_cells,
      min_completion_rate: next.config.min_completion_rate, max_missing_ratio: next.config.max_missing_ratio,
      cross_country_min_countries: next.config.cross_country_min_countries,
      cross_country_min_cells: next.config.cross_country_min_cells,
    })
  } catch (err) {
    error.value = (err as { message?: string }).message || '六国测试数据加载失败'
  } finally {
    loading.value = false
  }
}

async function approveBatch(batch: PilotBatch) {
  if (!requireToken()) return
  if (!window.confirm(`确认审批批次 ${batch.batch_id}？审批后该批次可进入聚合，但不能撤销到未审批状态。`)) return
  busy.value = true
  try {
    await approvePilotBatch(batch.batch_id, token.value)
    actionNotice.value = `批次 ${batch.batch_id} 已审批。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '批次审批失败'
  } finally { busy.value = false }
}

async function approveThresholds() {
  if (!requireToken()) return
  if (!window.confirm('确认审批当前建议门槛？审批后配置版本不可修改，修改必须新建版本。')) return
  busy.value = true
  try {
    await approvePilotConfig(pendingConfigVersion.value || undefined, token.value)
    actionNotice.value = '门槛配置已审批；发布评分前仍需评分审批。'
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '门槛审批失败'
  } finally { busy.value = false }
}

async function submitThresholds() {
  if (!requireToken()) return
  busy.value = true
  actionError.value = ''
  try {
    const cfg = await submitPilotConfig({ ...configDraft }, token.value)
    if (!cfg) throw new Error('配置接口未返回版本')
    pendingConfigVersion.value = cfg.config_version
    actionNotice.value = `已创建待审批门槛版本 ${cfg.config_version}；审批前不生效。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '门槛提交失败'
  } finally { busy.value = false }
}

async function draftScore() {
  if (!requireToken()) return
  busy.value = true
  actionError.value = ''
  try {
    await createPilotScoreDraft(scoreTitle.value, token.value)
    actionNotice.value = '已生成待审批评分草稿；未写入正式数据。'
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '评分草稿生成失败'
  } finally { busy.value = false }
}

async function approveScore(scoreId: string) {
  if (!requireToken()) return
  if (!window.confirm(`确认审批候选评分 ${scoreId}？审批后仍是候选分，不等于正式发布。`)) return
  busy.value = true
  try {
    await approvePilotScore(scoreId, token.value)
    actionNotice.value = `评分 ${scoreId} 已审批为候选分；尚未正式发布。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '评分审批失败'
  } finally { busy.value = false }
}

async function revokeScore(scoreId: string) {
  if (!requireToken()) return
  const reason = window.prompt('撤销原因（必填）')
  if (!reason?.trim()) return
  if (!window.confirm('确认撤销候选评分？该操作会保留审计记录。')) return
  busy.value = true
  try {
    await revokePilotScore(scoreId, reason, token.value)
    actionNotice.value = `评分 ${scoreId} 已撤销。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '评分撤销失败'
  } finally { busy.value = false }
}

async function submitEvidenceScore() {
  if (!requireToken()) return
  if (evidenceScore.value === null) { actionError.value = '请填写 0—100 证据分'; return }
  busy.value = true
  actionError.value = ''
  try {
    await submitPilotEvidence({
      music_id: evidenceMusic.value,
      score_0_100: evidenceScore.value,
      source: evidenceSource.value,
      rule_version: evidenceRule.value,
    }, token.value)
    actionNotice.value = '证据分已提交，状态为待审批；未审批前不会进入正式评分。'
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '证据分提交失败'
  } finally { busy.value = false }
}

async function approveEvidence(evidenceId: string) {
  if (!requireToken()) return
  if (!window.confirm(`确认审批证据分 ${evidenceId}？审批后可作为八项之一参与评分。`)) return
  busy.value = true
  try {
    await approvePilotEvidence(evidenceId, token.value)
    actionNotice.value = `证据分 ${evidenceId} 已审批。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '证据分审批失败'
  } finally { busy.value = false }
}

async function publishScore(scoreId: string) {
  if (!requireToken()) return
  if (!window.confirm(`确认发布评分 ${scoreId}？发布后成为当前正式版本，旧版本会被 superseded。`)) return
  busy.value = true
  try {
    await publishPilotScore(scoreId, token.value)
    actionNotice.value = '评分已发布为当前正式版本。'
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '评分发布失败'
  } finally { busy.value = false }
}

async function revokePublished() {
  if (!requireToken() || !publishedVersion.value) return
  const reason = window.prompt('撤销当前正式版本的原因（必填）')
  if (!reason?.trim()) return
  if (!window.confirm('确认撤销当前正式版本？排名会立即关闭，且不会自动恢复旧版本。')) return
  busy.value = true
  try {
    await revokePublishedPilot(publishedVersion.value, reason, token.value)
    actionNotice.value = `正式版本 ${publishedVersion.value} 已撤销；排名关闭。`
    await load()
  } catch (err) {
    actionError.value = (err as { message?: string }).message || '正式版本撤销失败'
  } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div class="page research-page pilot-page">
    <AppNav />
    <main class="pilot-shell">
      <header class="pilot-hero">
        <div>
          <p class="eyebrow">SIX-COUNTRY PILOT / 国际传播专项</p>
          <h1>六国实测工作台</h1>
          <p class="desc">
            120 个国家×曲目单元。原版与适配版分开统计；样本不足、缺测量项或缺证据分时，不生成评分，不补 0。
          </p>
        </div>
        <div class="hero-actions">
          <RouterLink class="text-link" to="/teacher-revision-outcomes?designPreview=1">查看专项成果</RouterLink>
          <button type="button" class="ghost" :disabled="busy" @click="load">刷新</button>
        </div>
      </header>

      <div v-if="loading" class="pilot-empty">加载六国测试数据…</div>
      <div v-else-if="error" class="pilot-empty error">{{ error }}</div>

      <template v-else-if="overview">
        <section class="metric-grid">
          <article><strong>120</strong><span>计划单元</span><small>{{ withData }} 个已有反馈</small></article>
          <article><strong>{{ eligible }}</strong><span>可评审单元</span><small>达到全部门槛且八项完整</small></article>
          <article><strong>{{ pendingScores }}</strong><span>待审批评分</span><small>{{ approvedScores }} 个候选评分已审批</small></article>
          <article><strong>{{ readyCountries }}</strong><span>国家样本达标</span><small>最低 {{ overview.config.min_country_cells }} 单元 / {{ overview.config.min_country_total }} 份</small></article>
        </section>

        <aside class="gate" :class="{ approved: configApproved }">
          <div>
            <b>{{ configApproved ? '门槛配置已审批' : '门槛配置为建议值，尚未审批' }}</b>
            <span>
              每版本至少 {{ overview.config.min_per_variant }} 份；版本差异不超过
              {{ Math.round(overview.config.variant_balance_tolerance * 100) }}%；
              完整观看率至少 {{ overview.config.min_completion_rate }}%。
            </span>
          </div>
          <button v-if="!configApproved" type="button" class="ghost" :disabled="busy" @click="approveThresholds">
            审批{{ pendingConfigVersion ? '待审版本' : '建议门槛' }}
          </button>
          <code v-else>{{ overview.config.approved_by }} · {{ overview.config.approved_at }}</code>
        </aside>
        <details class="config-editor">
          <summary>修改门槛并提交新版本（已审批配置不可直接改）</summary>
          <div class="config-grid">
            <label>每版本最低样本<input v-model.number="configDraft.min_per_variant" type="number" min="1" /></label>
            <label>每单元最低合计<input v-model.number="configDraft.min_per_cell" type="number" min="2" /></label>
            <label>版本差异上限<input v-model.number="configDraft.variant_balance_tolerance" type="number" min="0" max="1" step="0.01" /></label>
            <label>国家最低样本<input v-model.number="configDraft.min_country_total" type="number" min="1" /></label>
            <label>国家最低单元<input v-model.number="configDraft.min_country_cells" type="number" min="1" max="120" /></label>
            <label>完整观看率<input v-model.number="configDraft.min_completion_rate" type="number" min="0" max="100" /></label>
            <label>最大缺失率<input v-model.number="configDraft.max_missing_ratio" type="number" min="0" max="1" step="0.01" /></label>
            <label>跨国最低国家<input v-model.number="configDraft.cross_country_min_countries" type="number" min="1" max="6" /></label>
            <label>跨国最低单元<input v-model.number="configDraft.cross_country_min_cells" type="number" min="1" max="120" /></label>
          </div>
          <div class="config-actions">
            <span>当前版本：{{ pendingConfigVersion || overview.config.config_version }} · {{ configApproved ? '已审批' : (pendingConfigVersion ? '待审批' : '建议值') }}</span>
            <button type="button" :disabled="busy" @click="submitThresholds">提交新门槛版本</button>
          </div>
        </details>

        <section class="token-panel">
          <label>服务端签发的访问令牌
            <input v-model="token" type="password" placeholder="Bearer token；不填写只能查看" />
          </label>
          <button type="button" class="ghost" @click="saveToken">保存到当前会话</button>
          <span class="hint">身份与角色由服务端认证；页面不发送 approver/operator 姓名。</span>
        </section>

        <section class="protocol-strip">
          <div>
            <p class="kicker">PROTOCOL / RECRUITMENT</p>
            <b>{{ protocolDoc ? `${protocolDoc.protocol_version} · ${protocolDoc.status}` : '尚未创建协议候选稿' }}</b>
            <span v-if="protocolDoc">SHA {{ protocolDoc.sha256.slice(0, 16) }}… · 待母语审校 {{ pendingLocalizations }}/6</span>
            <span v-else>先由 operator 创建协议，approver 审批冻结后才能分配。</span>
          </div>
          <div class="assignment-stat">
            <strong>{{ assignmentCounts.active }}</strong>
            <span>有效分配</span>
            <small>总 {{ assignmentCounts.total }} / 退出 {{ assignmentCounts.withdrawn }}</small>
          </div>
        </section>

        <section class="panel localization-panel">
          <header class="panel-head">
            <div>
              <p class="kicker">LOCALIZATION GATE</p>
              <h2>六国本地化与母语审校</h2>
              <p>{{ localizationOverview?.note || '先生成中文母版，再由翻译者填写本地语言材料并由另一名审校者审批。' }}</p>
            </div>
            <div class="head-actions">
              <button type="button" class="ghost" :disabled="busy || !protocolDoc || protocolDoc.status !== 'frozen'" @click="generateLocalizationSources">生成中文母版</button>
              <label class="file-button compact">导入翻译JSON<input type="file" accept="application/json,.json" :disabled="busy" @change="onLocalizationFile"></label>
            </div>
          </header>
          <div class="localization-gate" :class="{ ready: localizationOverview?.recruitment_ready }">
            <b>{{ localizationOverview?.recruitment_ready ? '六国材料均已审校，可进入正式招募' : `正式招募未开放：仍有 ${pendingLocalizations} 国材料未审批` }}</b>
            <span>翻译者与母语审校者必须为不同的服务端身份；机器翻译草稿不得直接标记为已审校。</span>
          </div>
          <div class="localization-grid">
            <article v-for="item in localizationItems" :key="item.country">
              <div><b>{{ item.country }}</b><span>{{ item.language }} · {{ item.localization_version || '未创建' }}</span></div>
              <span class="status" :class="item.status === 'approved' ? 'ok' : item.status === 'pending_native_review' ? 'warn' : 'muted'">{{ item.status }}</span>
              <small v-if="item.translator">翻译：{{ item.translator }}</small>
              <small v-if="item.reviewer">审校：{{ item.reviewer }}</small>
              <div class="localization-actions">
                <button v-if="item.source_zh" type="button" class="ghost" @click="exportLocalization(item)">下载模板</button>
                <button v-if="item.status === 'pending_native_review'" type="button" class="ghost" :disabled="busy" @click="approveLocalization(item)">审批审校</button>
              </div>
            </article>
          </div>
        </section>

        <section class="panel assignment-monitor">
          <header class="panel-head">
            <div><p class="kicker">RECRUITMENT MONITOR</p><h2>招募与分配监控</h2><p>按国家监控分配数量、执行状态和原版/适配版平衡；退出记录不计入有效配额。</p></div>
            <span class="status" :class="assignmentCounts.imbalanced_cells ? 'bad' : 'ok'">不平衡单元 {{ assignmentCounts.imbalanced_cells }}</span>
          </header>
          <div class="country-assignment-grid">
            <article v-for="country in ['日本','泰国','英国','美国','阿联酋','巴西']" :key="country">
              <b>{{ country }}</b><strong>{{ assignmentCounts.by_country[country] ?? 0 }}</strong><span>有效分配</span>
            </article>
          </div>
          <div class="assignment-breakdown">
            <span>原版 {{ assignmentCounts.by_variant.original ?? 0 }}</span>
            <span>适配版 {{ assignmentCounts.by_variant.adapted ?? 0 }}</span>
            <span>已开始 {{ assignmentCounts.by_status.started ?? 0 }}</span>
            <span>已播放 {{ assignmentCounts.by_status.played ?? 0 }}</span>
            <span>已完成 {{ assignmentCounts.by_status.completed ?? 0 }}</span>
            <span>已提交 {{ assignmentCounts.by_status.submitted ?? 0 }}</span>
            <span>已退出 {{ assignmentCounts.withdrawn }}</span>
          </div>
        </section>

        <section class="panel">
          <header class="panel-head">
            <div>
              <p class="kicker">UNIT STATUS</p>
              <h2>国家×曲目单元</h2>
              <p>这里的“可评审”不等于正式评分；正式评分仍需批次审批、评分审批和完整八项。</p>
            </div>
            <div class="head-actions"><button type="button" class="ghost" @click="exportReport">导出报告</button><button type="button" class="ghost" @click="exportUnits">导出当前视图 CSV</button></div>
          </header>
          <div class="filters">
            <label>国家
              <select v-model="selectedCountry">
                <option value="all">全部</option>
                <option v-for="country in countries" :key="country" :value="country">{{ country }}</option>
              </select>
            </label>
            <label>曲目
              <select v-model="selectedMusic">
                <option value="all">全部</option>
                <option v-for="item in musicOptions" :key="item.music_id" :value="item.music_id">{{ item.music_id }} {{ item.title }}</option>
              </select>
            </label>
            <label>版本
              <select v-model="selectedVariant">
                <option value="all">全部版本</option>
                <option value="original">仅原版</option>
                <option value="adapted">仅适配版</option>
              </select>
            </label>
            <label>状态
              <select v-model="selectedStatus">
                <option value="all">全部</option>
                <option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option>
              </select>
            </label>
            <span class="filter-count">{{ filteredUnits.length }} / 120 单元</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>国家</th><th>曲目</th><th>原版 n</th><th>适配版 n</th><th>状态</th>
                  <th>{{ publishedVersion ? '正式分' : '候选分（未发布）' }}</th><th>证据分</th><th>开放回答 / 风险</th><th>说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="unit in filteredUnits" :key="`${unit.country}-${unit.music_id}`">
                  <td>{{ unit.country }}</td>
                  <td><b>{{ unit.music_id }}</b> {{ unit.title }}</td>
                  <td>{{ unit.n_original }}</td>
                  <td>{{ unit.n_adapted }}</td>
                  <td><span class="status" :class="statusClass(unit.status)">{{ statusLabel(unit.status) }}</span></td>
                  <td>{{ formatScore(unit.formal_score) }}</td>
                  <td>{{ unit.evidence_score ?? '—' }}</td>
                  <td class="open-cell">
                    <details v-if="unit.open_responses.length || unit.cultural_risk_flags.length">
                      <summary>{{ unit.open_responses.length }} 回答 / {{ unit.cultural_risk_flags.length }} 风险</summary>
                      <p v-for="(answer, index) in unit.open_responses.slice(0, 3)" :key="`a-${index}`">{{ answer }}</p>
                      <p v-for="(risk, index) in unit.cultural_risk_flags.slice(0, 2)" :key="`r-${index}`" class="risk">风险：{{ risk }}</p>
                    </details>
                    <span v-else class="hint">—</span>
                  </td>
                  <td class="reason">{{ unit.status_reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="two-col">
          <article class="panel">
            <header class="panel-head">
              <div><p class="kicker">IMPORT</p><h2>反馈导入</h2><p>CSV 只进入候选批次；去标识化后分 raw / clean / rejected 三层保存。</p></div>
            </header>
            <div class="form-row">
              <label>批次标签<input v-model="batchLabel" /></label>
            </div>
            <label class="file-button">
              选择反馈 CSV
              <input type="file" accept=".csv,text/csv" :disabled="busy" @change="onFile" />
            </label>
            <p class="hint">必填字段含同意、国家、MU001—MU020、原版/适配版、完整观看率、七项量表与辅助量表。</p>
            <div v-if="importedBatch" class="batch-result">
              <b>{{ importedBatch.batch_id }}</b>
              <span>清洗 {{ importedBatch.rows_clean }} / 隔离 {{ importedBatch.rows_rejected }} / 错误 {{ importedBatch.error_count }}</span>
              <span>状态：{{ importedBatch.approval_status }}</span>
            </div>
          </article>

          <article class="panel">
            <header class="panel-head">
              <div><p class="kicker">APPROVAL</p><h2>批次与评分审批</h2><p>审批只写候选记录，不写 v1.7 正式版本。</p></div>
            </header>
            <p class="hint">审批身份从访问令牌读取；请求体中的姓名不会改变实际操作人。</p>
            <div class="batch-list">
              <div v-for="batch in batches" :key="batch.batch_id" class="batch-row">
                <div><b>{{ batch.batch_id }}</b><span>{{ batch.rows_clean }} clean / {{ batch.rows_rejected }} rejected</span></div>
                <span v-if="batch.approval_status === 'approved'" class="status ok">已审批</span>
                <button v-else type="button" class="ghost" :disabled="busy" @click="approveBatch(batch)">审批批次</button>
              </div>
              <p v-if="!batches.length" class="hint">还没有导入批次。</p>
            </div>
            <div class="score-action">
              <label>评分草稿标题<input v-model="scoreTitle" /></label>
              <button type="button" :disabled="busy || !batches.some((item) => item.approval_status === 'approved')" @click="draftScore">
                生成待审批评分
              </button>
            </div>
            <div class="score-list">
              <div v-for="score in overview.scores" :key="score.score_id" class="score-row">
                <div><b>{{ score.score_id }}</b><span>{{ score.title }} · {{ score.status }}</span></div>
                <div class="score-buttons">
                  <button v-if="score.status === 'pending_approval'" type="button" class="ghost" :disabled="busy" @click="approveScore(score.score_id)">审批候选</button>
                  <button v-if="score.status === 'approved_candidate'" type="button" class="ghost" :disabled="busy" @click="publishScore(score.score_id)">发布正式版本</button>
                  <button v-if="score.status === 'pending_approval' || score.status === 'approved_candidate'" type="button" class="ghost" :disabled="busy" @click="revokeScore(score.score_id)">撤销候选</button>
                </div>
              </div>
              <p v-if="!overview.scores.length" class="hint">还没有评分草稿。</p>
            </div>
          </article>
        </section>

        <section class="panel">
          <header class="panel-head">
            <div><p class="kicker">EVIDENCE SCORE / 0—100</p><h2>既有传播证据分</h2><p>独立录入、独立审批；不使用受众量表替代，未审批不会进入正式评分。</p></div>
          </header>
          <div class="evidence-form">
            <label>曲目<input v-model="evidenceMusic" placeholder="MU001" /></label>
            <label>证据分 0—100<input v-model.number="evidenceScore" type="number" min="0" max="100" step="0.1" /></label>
            <label>来源<input v-model="evidenceSource" placeholder="官方页/档案/数据库" /></label>
            <label>评分规则版本<input v-model="evidenceRule" /></label>
            <button type="button" :disabled="busy" @click="submitEvidenceScore">提交证据分</button>
          </div>
          <div class="evidence-list">
            <div v-for="item in evidenceItems" :key="item.evidence_id" class="evidence-row">
              <div><b>{{ item.music_id }} · {{ item.score_0_100 }}</b><span>{{ item.source }} · {{ item.rule_version }} · {{ item.status }}</span></div>
              <button v-if="item.status === 'pending_approval'" type="button" class="ghost" :disabled="busy" @click="approveEvidence(item.evidence_id)">审批证据</button>
              <span v-else class="hint">{{ item.approved_by || item.entered_by }}</span>
            </div>
            <p v-if="!evidenceItems.length" class="hint">还没有证据分记录。正式评分会保持 null。</p>
          </div>
        </section>

        <section class="panel formula">
          <header class="panel-head">
            <div><p class="kicker">FORMULA</p><h2>计算口径</h2></div>
          </header>
          <p><b>候选/正式分公式：</b>{{ overview.formula.score }}</p>
          <p><b>既有传播证据：</b>{{ overview.formula.existing_evidence }}</p>
          <p><b>跨国汇总：</b>国家内先聚合，再对国家等权；样本量大的国家不会因 n 更大而支配结果。</p>
          <p><b>发布状态：</b>{{ publishedVersion ? `当前正式版本 ${publishedVersion}` : '尚未发布正式版本；表格分数仅为候选分。' }}</p>
          <button v-if="publishedVersion" type="button" class="ghost" :disabled="busy" @click="revokePublished">撤销当前正式版本</button>
          <p class="hint">{{ overview.scope_note }}</p>
        </section>

        <p v-if="actionError" class="action-message error">{{ actionError }}</p>
        <p v-if="actionNotice" class="action-message">{{ actionNotice }}</p>
      </template>
    </main>
  </div>
</template>

<style scoped>
.pilot-page { --pilot-bg: #101b18; --pilot-panel: #172822; --pilot-line: rgba(159, 198, 181, 0.18); --pilot-ink: #e8f1ed; --pilot-muted: #8da79b; background: var(--pilot-bg); color: var(--pilot-ink); min-height: 100vh; }
.pilot-shell { width: min(1440px, calc(100% - 48px)); margin: 0 auto; padding: 36px 0 70px; }
.pilot-hero { display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; margin-bottom: 24px; }
.eyebrow, .kicker { margin: 0 0 8px; color: #8fc7b1; font-size: 10px; letter-spacing: .16em; }
.pilot-hero h1 { margin: 0; font-size: clamp(28px, 4vw, 46px); letter-spacing: -.03em; }
.desc { max-width: 760px; margin: 10px 0 0; color: var(--pilot-muted); line-height: 1.8; font-size: 12px; }
.hero-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.text-link { color: #a9d9b8; font-size: 11px; text-decoration: none; }
button, select, input { font: inherit; }
button, .ghost { border: 1px solid var(--pilot-line); background: rgba(143, 199, 177, .07); color: var(--pilot-ink); border-radius: 7px; padding: 7px 10px; cursor: pointer; font-size: 11px; }
button:disabled { opacity: .45; cursor: not-allowed; }
.ghost { background: transparent; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
.metric-grid article { padding: 16px; border: 1px solid var(--pilot-line); background: var(--pilot-panel); border-radius: 10px; }
.metric-grid strong { display: block; font-size: 28px; color: #a9d9b8; }
.metric-grid span { display: block; margin-top: 4px; font-size: 12px; }
.metric-grid small { display: block; margin-top: 5px; color: var(--pilot-muted); font-size: 10px; line-height: 1.5; }
.gate { display: flex; justify-content: space-between; gap: 16px; align-items: center; border: 1px solid rgba(217, 194, 138, .32); background: rgba(217, 194, 138, .07); padding: 13px 16px; border-radius: 9px; margin-bottom: 14px; }
.gate.approved { border-color: rgba(143, 199, 177, .32); background: rgba(143, 199, 177, .07); }
.gate b, .gate span { display: block; font-size: 11px; }
.gate span { color: var(--pilot-muted); margin-top: 4px; line-height: 1.6; }
.gate code { color: #a9d9b8; font-size: 10px; }
.panel { border: 1px solid var(--pilot-line); background: var(--pilot-panel); border-radius: 10px; padding: 17px; margin-bottom: 14px; }
.panel-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 12px; }
.panel-head h2 { margin: 0; font-size: 17px; }
.panel-head p:not(.kicker) { margin: 5px 0 0; color: var(--pilot-muted); font-size: 11px; line-height: 1.6; }
.filters { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 10px; }
.filters label, .form-row label, .score-action label, .panel > label { display: grid; gap: 4px; color: var(--pilot-muted); font-size: 10px; }
select, input { border: 1px solid var(--pilot-line); border-radius: 6px; padding: 7px 8px; background: #0d1815; color: var(--pilot-ink); min-width: 130px; }
.filter-count { margin-left: auto; color: var(--pilot-muted); font-size: 10px; }
.table-wrap { max-height: 460px; overflow: auto; border-top: 1px solid var(--pilot-line); }
table { width: 100%; border-collapse: collapse; font-size: 11px; }
th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid rgba(159, 198, 181, .08); vertical-align: top; }
th { position: sticky; top: 0; background: #13231e; color: var(--pilot-muted); font-weight: 500; }
td b { color: #a9d9b8; }
.reason { color: var(--pilot-muted); max-width: 250px; line-height: 1.5; }
.status { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; white-space: nowrap; }
.status.ok { background: rgba(143, 199, 177, .16); color: #a9d9b8; }
.status.warn { background: rgba(217, 194, 138, .14); color: #d8c393; }
.status.bad { background: rgba(224, 123, 123, .14); color: #e59c9c; }
.status.muted { background: rgba(141, 167, 155, .1); color: var(--pilot-muted); }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.file-button { display: inline-block; margin-top: 8px; padding: 8px 12px; border: 1px dashed var(--pilot-line); border-radius: 7px; color: #a9d9b8; font-size: 11px; cursor: pointer; }
.file-button input { display: none; }
.hint { color: var(--pilot-muted); font-size: 10px; line-height: 1.7; }
.batch-result, .batch-row, .score-row { display: flex; justify-content: space-between; gap: 8px; align-items: center; border-top: 1px solid rgba(159, 198, 181, .1); padding-top: 9px; margin-top: 9px; font-size: 10px; }
.batch-result { flex-wrap: wrap; color: var(--pilot-muted); }
.batch-result b, .batch-row b, .score-row b { color: #d8e6df; }
.batch-row div, .score-row div { display: grid; gap: 3px; }
.batch-row span, .score-row span { color: var(--pilot-muted); }
.batch-list { margin-bottom: 12px; }
.score-action { border-top: 1px solid var(--pilot-line); padding-top: 12px; display: flex; gap: 10px; align-items: flex-end; }
.score-action label { flex: 1; }
.score-buttons { display: flex; gap: 5px; }
.formula p { margin: 7px 0; color: var(--pilot-muted); font-size: 11px; line-height: 1.7; }
.formula b { color: var(--pilot-ink); }
.pilot-empty { padding: 50px 20px; border: 1px solid var(--pilot-line); color: var(--pilot-muted); text-align: center; }
.pilot-empty.error, .action-message.error { color: #e59c9c; }
.action-message { margin: 12px 0 0; font-size: 11px; }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } .two-col { grid-template-columns: 1fr; } .pilot-hero { align-items: flex-start; flex-direction: column; } }
@media (max-width: 560px) { .pilot-shell { width: min(100% - 24px, 1440px); padding-top: 20px; } .metric-grid, .form-row { grid-template-columns: 1fr; } .panel-head { flex-direction: column; } }

.head-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.open-cell { min-width: 125px; }
.open-cell details summary { cursor: pointer; color: #a9d9b8; font-size: 10px; }
.open-cell p { margin: 4px 0; color: var(--pilot-muted); font-size: 10px; line-height: 1.5; }
.open-cell p.risk { color: #d8c393; }


.token-panel { display:flex; gap:10px; align-items:flex-end; flex-wrap:wrap; border:1px solid var(--pilot-line); background:var(--pilot-panel); border-radius:9px; padding:12px 15px; margin-bottom:14px; }
.token-panel label { flex:1; min-width:260px; display:grid; gap:4px; color:var(--pilot-muted); font-size:10px; }
.evidence-form { display:grid; grid-template-columns: 90px 130px 1.4fr 130px auto; gap:8px; align-items:end; }
.evidence-form label { display:grid; gap:4px; color:var(--pilot-muted); font-size:10px; }
.evidence-list { margin-top:10px; }
.evidence-row { display:flex; justify-content:space-between; gap:10px; align-items:center; border-top:1px solid rgba(159,198,181,.1); padding-top:8px; margin-top:8px; font-size:10px; }
.evidence-row div { display:grid; gap:3px; }
.evidence-row span { color:var(--pilot-muted); }
@media (max-width: 900px) { .evidence-form { grid-template-columns: 1fr 1fr; } }


.config-editor { border:1px solid var(--pilot-line); background:var(--pilot-panel); border-radius:9px; padding:10px 14px; margin-bottom:14px; }
.config-editor summary { cursor:pointer; color:var(--pilot-muted); font-size:11px; }
.config-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:10px; }
.config-grid label { display:grid; gap:3px; color:var(--pilot-muted); font-size:10px; }
.config-actions { display:flex; justify-content:space-between; gap:10px; align-items:center; margin-top:10px; font-size:10px; color:var(--pilot-muted); }
@media (max-width:900px) { .config-grid { grid-template-columns:repeat(2,1fr); } }


.protocol-strip { display:flex; justify-content:space-between; gap:16px; align-items:center; border:1px solid var(--pilot-line); background:var(--pilot-panel); border-radius:9px; padding:12px 16px; margin-bottom:14px; }
.protocol-strip b, .protocol-strip span { display:block; font-size:11px; }
.protocol-strip span { color:var(--pilot-muted); margin-top:3px; }
.assignment-stat { text-align:right; }
.assignment-stat strong { color:#a9d9b8; font-size:22px; }
.assignment-stat small { display:block; color:var(--pilot-muted); font-size:10px; margin-top:3px; }
@media (max-width:560px) { .protocol-strip { flex-direction:column; align-items:flex-start; } .assignment-stat { text-align:left; } }

.localization-panel { margin-bottom:14px; }
.file-button.compact { margin:0; border-style:solid; }
.localization-gate { display:grid; gap:4px; padding:10px 12px; margin-bottom:10px; border:1px solid rgba(217,194,138,.32); border-radius:7px; background:rgba(217,194,138,.07); }
.localization-gate.ready { border-color:rgba(143,199,177,.32); background:rgba(143,199,177,.07); }
.localization-gate b { font-size:11px; }
.localization-gate span { color:var(--pilot-muted); font-size:10px; line-height:1.5; }
.localization-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.localization-grid article { display:grid; gap:7px; padding:11px; border:1px solid var(--pilot-line); border-radius:8px; background:#11201b; }
.localization-grid article>div:first-child { display:grid; gap:2px; }
.localization-grid article b { font-size:12px; }
.localization-grid article span,.localization-grid article small { color:var(--pilot-muted); font-size:9px; }
.localization-actions { display:flex; gap:5px; margin-top:auto; }
@media (max-width:900px) { .localization-grid { grid-template-columns:repeat(2,1fr); } }
@media (max-width:560px) { .localization-grid { grid-template-columns:1fr; } }
.country-assignment-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:7px; }
.country-assignment-grid article { padding:10px; border:1px solid var(--pilot-line); border-radius:7px; background:#11201b; }
.country-assignment-grid b,.country-assignment-grid span { display:block; color:var(--pilot-muted); font-size:9px; }
.country-assignment-grid strong { display:block; margin:4px 0; color:#a9d9b8; font-size:20px; }
.assignment-breakdown { display:flex; flex-wrap:wrap; gap:7px; margin-top:10px; }
.assignment-breakdown span { padding:4px 7px; border-radius:5px; background:rgba(143,199,177,.07); color:var(--pilot-muted); font-size:9px; }
@media (max-width:900px) { .country-assignment-grid { grid-template-columns:repeat(3,1fr); } }
@media (max-width:560px) { .country-assignment-grid { grid-template-columns:repeat(2,1fr); } }

</style>
