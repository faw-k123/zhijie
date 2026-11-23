<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import { fetchTeacherRevisionOutcomes, validatePilotResponses } from '@/api/research'
import type {
  PilotValidationResult,
  TeacherRevisionCase,
  TeacherRevisionCountry,
  TeacherRevisionOutcome,
} from '@/types/research'

type TabKey = 'cases' | 'mechanisms' | 'music' | 'matrix' | 'execution'

const tabs: Array<{ key: TabKey; label: string; note: string }> = [
  { key: 'cases', label: '严格案例与反馈', note: '10例 / 20条反馈' },
  { key: 'mechanisms', label: '接受机制编码', note: '9项机制' },
  { key: 'music', label: '候选音乐', note: '首批20首' },
  { key: 'matrix', label: '六国适配矩阵', note: '120个试验单元' },
  { key: 'execution', label: '方法与试验执行', note: '准入审计 / 采集模板' },
]

const result = ref<TeacherRevisionOutcome | null>(null)
const activeTab = ref<TabKey>('cases')
const selectedCaseId = ref('')
const selectedCountry = ref('日本')
const musicTier = ref<'all' | 'A' | 'B'>('all')
const loading = ref(true)
const error = ref('')
const pilotValidation = ref<PilotValidationResult | null>(null)
const pilotValidationLoading = ref(false)
const pilotValidationError = ref('')
const pilotFileName = ref('')

const selectedCase = computed<TeacherRevisionCase | null>(() => {
  const cases = result.value?.cases ?? []
  return cases.find((item) => item.case_id === selectedCaseId.value) ?? cases[0] ?? null
})

const selectedCountryRow = computed<TeacherRevisionCountry | null>(() => {
  const rows = result.value?.countries ?? []
  return rows.find((item) => item.country === selectedCountry.value) ?? rows[0] ?? null
})

const filteredMusic = computed(() => {
  const items = result.value?.music.items ?? []
  return musicTier.value === 'all'
    ? items
    : items.filter((item) => item.selection_tier === musicTier.value)
})

const mechanismLabels = computed(() => Object.fromEntries(
  (result.value?.mechanisms ?? []).map((item) => [item.code, item.label]),
))

function statusClass(status: string) {
  return status === 'strong' ? 'strong' : status === 'partial' ? 'partial' : 'muted'
}

function fitLabel(value: string) {
  if (value === 'A') return '优先测试'
  if (value === 'B') return '次优测试'
  if (value === 'C') return '需语境化'
  return value
}

function csvCell(value: unknown) {
  const text = Array.isArray(value) ? value.join('|') : String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

function downloadCsv(filename: string, headers: string[], rows: unknown[][]) {
  const body = [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n')
  const blob = new Blob([`\uFEFF${body}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function exportAdmissionAudit() {
  if (!result.value) return
  const ruleCodes = result.value.admission_rules.map((item) => item.code)
  downloadCsv(
    '严格案例准入审计_v1.7.csv',
    ['案例编号', '演奏者', '国籍', ...ruleCodes, '准入来源数', '反馈数', '审批状态'],
    result.value.cases.map((item) => [
      item.case_id,
      item.performer,
      item.country,
      ...ruleCodes.map((code) => item.admission_audit.find((audit) => audit.code === code)?.passed ? '通过' : '未通过'),
      item.source_count,
      item.feedback.length,
      item.owner_approval_status,
    ]),
  )
}

function exportPilotPlan() {
  if (!result.value) return
  const musicById = Object.fromEntries(result.value.music.items.map((item) => [item.music_id, item]))
  const rows: unknown[][] = []
  result.value.countries.forEach((country) => {
    Object.entries(country.fits).forEach(([musicId, fit]) => {
      const music = musicById[musicId]
      rows.push([
        country.country,
        country.region,
        musicId,
        music?.title,
        fit,
        music?.selection_tier,
        'original',
        'adapted',
        '',
        country.pilot_design,
        country.success_metrics,
        country.religion_and_cultural_safeguard,
      ])
    })
  })
  downloadCsv(
    '六国曲目试验执行表_v1.7.csv',
    ['国家', '区域', '曲目编号', '曲名', '适配级别', '选曲层级', '版本A', '版本B', '每版本目标样本量', '试验设计', '成功指标', '文化安全要求'],
    rows,
  )
}

function exportResponseTemplate() {
  if (!result.value) return
  downloadCsv(
    '六国受众反馈采集模板_v1.7.csv',
    result.value.pilot.response_fields.map((field) => `${field.key}｜${field.label}`),
    [],
  )
}

function parseCsv(text: string): Array<Record<string, string>> {
  const rows: string[][] = []
  let row: string[] = []
  let cell = ''
  let quoted = false
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    if (char === '"') {
      if (quoted && text[index + 1] === '"') {
        cell += '"'
        index += 1
      } else {
        quoted = !quoted
      }
    } else if (char === ',' && !quoted) {
      row.push(cell)
      cell = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1
      row.push(cell)
      if (row.some((value) => value.trim())) rows.push(row)
      row = []
      cell = ''
    } else {
      cell += char
    }
  }
  row.push(cell)
  if (row.some((value) => value.trim())) rows.push(row)
  if (!rows.length) return []
  const headers = rows[0]!.map((value) => value.replace(/^\uFEFF/, '').split('｜')[0]!.trim())
  return rows.slice(1).map((values) => Object.fromEntries(
    headers.map((header, index) => [header, values[index]?.trim() ?? '']),
  ))
}

async function onPilotFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  pilotFileName.value = file.name
  pilotValidation.value = null
  pilotValidationError.value = ''
  pilotValidationLoading.value = true
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('文件不能超过10MB')
    const rows = parseCsv(await file.text())
    if (!rows.length) throw new Error('CSV没有数据行；请填写反馈后再导入')
    const response = await validatePilotResponses(rows)
    if (!response.success || !response.data) throw new Error(response.message || '校验失败')
    pilotValidation.value = response.data
  } catch (cause) {
    pilotValidationError.value = cause instanceof Error ? cause.message : '反馈文件校验失败'
  } finally {
    pilotValidationLoading.value = false
    input.value = ''
  }
}

function exportValidationErrors() {
  if (!pilotValidation.value?.errors.length) return
  downloadCsv(
    '六国反馈校验错误报告.csv',
    ['CSV行号', '反馈编号', '字段', '错误代码', '说明'],
    pilotValidation.value.errors.map((item) => [item.row_number, item.response_id, item.field, item.code, item.message]),
  )
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchTeacherRevisionOutcomes()
    if (!response.success || !response.data) throw new Error(response.message || '专项研究数据暂不可用')
    result.value = response.data
    selectedCaseId.value = response.data.cases[0]?.case_id ?? ''
    selectedCountry.value = response.data.countries[0]?.country ?? ''
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '专项研究数据加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-shell">
    <AppNav />
    <main class="research-page">
      <section class="hero">
        <div>
          <p class="eyebrow">TEACHER REVISION · APPROVED</p>
          <h1>国际传播专项研究成果</h1>
          <p class="hero-copy">从外国演奏者案例出发，把受众反馈、接受机制、候选音乐与六国试验设计连成一条可追溯的研究链。</p>
        </div>
        <div class="approval-stamp">已审批<br><span>v1.7</span></div>
      </section>

      <div v-if="loading" class="state-card">正在载入专项研究成果…</div>
      <div v-else-if="error" class="state-card error">
        <p>{{ error }}</p>
        <button type="button" @click="load">重新载入</button>
      </div>

      <template v-else-if="result">
        <section class="metric-grid" aria-label="专项研究进度">
          <article><strong>{{ result.counts.strict_cases }}</strong><span>严格案例</span><small>全部通过G1—G6准入</small></article>
          <article><strong>{{ result.counts.feedback }}</strong><span>受众反馈</span><small>{{ result.counts.coding_eligible_feedback }}条可进入机制编码</small></article>
          <article><strong>{{ result.counts.music_candidates }}</strong><span>候选音乐</span><small>已选曲，评分待实测</small></article>
          <article><strong>{{ result.counts.countries }}</strong><span>目标国家</span><small>{{ result.counts.matrix_cells }}个国家×曲目单元</small></article>
        </section>

        <aside class="scope-note"><b>研究边界</b><span>{{ result.scope_note }}</span></aside>

        <nav class="tab-list" aria-label="专项成果模块">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <span>{{ tab.label }}</span><small>{{ tab.note }}</small>
          </button>
        </nav>

        <section v-if="activeTab === 'cases'" class="content-panel cases-layout">
          <aside class="case-list">
            <button
              v-for="item in result.cases"
              :key="item.case_id"
              type="button"
              :class="{ active: selectedCase?.case_id === item.case_id }"
              @click="selectedCaseId = item.case_id"
            >
              <span class="case-id">{{ item.case_id }}</span>
              <b>{{ item.performer }}</b>
              <small>{{ item.country }} · {{ item.instrument.join('、') }}</small>
            </button>
          </aside>

          <article v-if="selectedCase" class="case-detail">
            <header class="detail-head">
              <div>
                <p>{{ selectedCase.country }} / {{ selectedCase.region }}</p>
                <h2>{{ selectedCase.performer }}</h2>
                <span>{{ selectedCase.instrument.join('、') }}</span>
              </div>
              <div class="outcome-badge">{{ selectedCase.outcome_label }}</div>
            </header>
            <p class="case-summary">{{ selectedCase.summary }}</p>

            <h3>外国受众反馈证据</h3>
            <div class="feedback-grid">
              <article v-for="feedback in selectedCase.feedback" :key="feedback.feedback_id" class="feedback-card">
                <div class="feedback-meta">
                  <span>{{ feedback.feedback_id }}</span>
                  <span>证据 {{ feedback.evidence_grade }}</span>
                  <span :class="feedback.coding_eligible ? 'eligible' : 'limited'">
                    {{ feedback.coding_eligible ? '可编码' : '限制作参考' }}
                  </span>
                </div>
                <blockquote v-if="feedback.excerpt">“{{ feedback.excerpt }}”</blockquote>
                <p>{{ feedback.summary }}</p>
                <small><b>受众依据：</b>{{ feedback.country_basis }}</small>
                <small><b>局限：</b>{{ feedback.limitations }}</small>
                <a :href="feedback.source_url" target="_blank" rel="noopener noreferrer">查看原始来源 ↗</a>
              </article>
            </div>

            <h3>本例接受机制</h3>
            <div class="mechanism-chips">
              <span v-for="mechanism in selectedCase.mechanisms" :key="mechanism.code" :class="statusClass(mechanism.status)">
                {{ mechanism.code }} {{ mechanism.label }} · {{ mechanism.status_label }}
              </span>
            </div>
            <h3>严格案例准入审计</h3>
            <div class="audit-strip">
              <span v-for="audit in selectedCase.admission_audit" :key="audit.code" :title="audit.evidence">
                <b>{{ audit.code }}</b>{{ audit.passed ? '通过' : '未通过' }}
              </span>
            </div>
            <details class="limits">
              <summary>查看证据局限</summary>
              <ul><li v-for="item in selectedCase.evidence_limitations" :key="item">{{ item }}</li></ul>
            </details>
            <RouterLink class="detail-link" :to="{ name: 'global-case-detail', params: { caseId: selectedCase.case_id } }">进入完整案例档案 →</RouterLink>
          </article>
        </section>

        <section v-else-if="activeTab === 'mechanisms'" class="content-panel">
          <header class="section-head">
            <div><p>ACCEPTANCE MECHANISM CODING</p><h2>外国受众为什么接受</h2></div>
            <span>探索性编码 · n={{ result.counts.strict_cases }}</span>
          </header>
          <div class="mechanism-table">
            <article v-for="item in result.mechanisms" :key="item.code">
              <div class="mechanism-title"><span>{{ item.code }}</span><b>{{ item.label }}</b></div>
              <div class="stacked-bar" :aria-label="`${item.label}证据分布`">
                <i class="strong" :style="{ width: `${item.strong / item.total * 100}%` }"></i>
                <i class="partial" :style="{ width: `${item.partial / item.total * 100}%` }"></i>
                <i class="muted" :style="{ width: `${item.not_evidenced / item.total * 100}%` }"></i>
              </div>
              <div class="mechanism-counts"><span>强 {{ item.strong }}</span><span>部分 {{ item.partial }}</span><span>未见 {{ item.not_evidenced }}</span></div>
            </article>
          </div>
          <p class="interpretation">读法：这些计数回答“10个严格案例中，哪些机制获得证据支持”，不能换算成外国受众总体接受率。后续六国测试将用统一量表继续验证。</p>
          <h3 class="matrix-title">案例 × 接受机制对照</h3>
          <div class="matrix-wrap mechanism-matrix">
            <table>
              <thead><tr><th>案例</th><th v-for="mechanism in result.mechanisms" :key="mechanism.code" :title="mechanism.label">{{ mechanism.code }}</th></tr></thead>
              <tbody>
                <tr v-for="item in result.cases" :key="item.case_id">
                  <th><small>{{ item.case_id }}</small>{{ item.performer }}</th>
                  <td v-for="mechanism in item.mechanisms" :key="mechanism.code" :title="`${mechanism.label}：${mechanism.status_label}`">
                    <span class="evidence-dot" :class="statusClass(mechanism.status)">{{ mechanism.status === 'strong' ? '强' : mechanism.status === 'partial' ? '部' : '—' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-else-if="activeTab === 'music'" class="content-panel">
          <header class="section-head">
            <div><p>MUSIC CANDIDATE POOL</p><h2>第一批20首候选音乐</h2></div>
            <label class="tier-filter">筛选
              <select v-model="musicTier"><option value="all">全部</option><option value="A">A：优先验证</option><option value="B">B：补充验证</option></select>
            </label>
          </header>
          <div class="music-grid">
            <article v-for="music in filteredMusic" :key="music.music_id" class="music-card">
              <div class="music-top"><span class="tier">{{ music.selection_tier }}</span><span>{{ music.music_id }}</span><em>{{ music.score_status_label }}</em></div>
              <h3>{{ music.title }}</h3>
              <p class="music-type">{{ music.instrument_or_form }} · {{ music.era_theme }}</p>
              <p>{{ music.selection_reason }}</p>
              <div class="mini-tags"><span v-for="code in music.primary_mechanisms" :key="code">{{ code }} {{ mechanismLabels[code] }}</span></div>
              <dl>
                <div><dt>国际形式</dt><dd>{{ music.international_format }}</dd></div>
                <div><dt>主要风险</dt><dd>{{ music.main_risk }}</dd></div>
                <div><dt>首轮验证</dt><dd>{{ music.first_validation }}</dd></div>
              </dl>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'matrix'" class="content-panel matrix-panel">
          <header class="section-head">
            <div><p>SIX-COUNTRY PILOT MATRIX</p><h2>六国区域适配矩阵</h2></div>
            <span>A优先 · B次优 · C需语境化</span>
          </header>
          <div class="country-tabs">
            <button v-for="country in result.countries" :key="country.country" type="button" :class="{ active: selectedCountry === country.country }" @click="selectedCountry = country.country">{{ country.country }}</button>
          </div>
          <article v-if="selectedCountryRow" class="country-brief">
            <div><span>目标受众</span><p>{{ selectedCountryRow.audience }}</p></div>
            <div><span>主题框架</span><p>{{ selectedCountryRow.theme_frame }}</p></div>
            <div><span>内容适配</span><p>{{ selectedCountryRow.adaptation_design }}</p></div>
            <div><span>语言与中介</span><p>{{ selectedCountryRow.language_and_mediation }}</p></div>
            <div><span>宗教文化保障</span><p>{{ selectedCountryRow.religion_and_cultural_safeguard }}</p></div>
            <div><span>试验与指标</span><p>{{ selectedCountryRow.pilot_design }}；{{ selectedCountryRow.success_metrics }}</p></div>
          </article>
          <div class="matrix-wrap">
            <table>
              <thead><tr><th>曲目</th><th>选曲层级</th><th v-for="country in result.countries" :key="country.country">{{ country.country }}</th></tr></thead>
              <tbody>
                <tr v-for="row in result.matrix" :key="row.music_id">
                  <th><small>{{ row.music_id }}</small>{{ row.title }}</th>
                  <td>{{ row.selection_tier }}</td>
                  <td v-for="country in result.countries" :key="country.country">
                    <span class="fit" :class="`fit-${row.countries[country.country] ?? '待核验'}`" :title="fitLabel(row.countries[country.country] ?? '待核验')">{{ row.countries[country.country] ?? '待核验' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-else class="content-panel execution-panel">
          <header class="section-head">
            <div><p>METHOD & PILOT EXECUTION</p><h2>方法审计与六国试验执行</h2></div>
            <span>{{ result.pilot.status_label }}</span>
          </header>

          <div class="execution-status">
            <div><strong>{{ result.pilot.completed_cells }}</strong><span>已完成试验单元</span></div>
            <div><strong>{{ result.pilot.planned_cells }}</strong><span>计划试验单元</span></div>
            <p>当前只完成方案设计，尚未录入真实六国测试结果。完成采集和质量核验后，才允许计算8项音乐评分。</p>
          </div>

          <h3>G1—G6严格案例准入规则</h3>
          <div class="rule-grid">
            <article v-for="rule in result.admission_rules" :key="rule.code">
              <span>{{ rule.code }}</span><h4>{{ rule.label }}</h4><p>{{ rule.requirement }}</p>
            </article>
          </div>

          <h3>试验执行原则</h3>
          <ol class="principle-list"><li v-for="item in result.pilot.design_principles" :key="item">{{ item }}</li></ol>

          <div class="download-grid">
            <article>
              <h4>严格案例准入审计表</h4>
              <p>导出10例的G1—G6结果、准入来源数、反馈数和审批状态。</p>
              <button type="button" @click="exportAdmissionAudit">下载CSV</button>
            </article>
            <article>
              <h4>六国曲目试验执行表</h4>
              <p>导出120个国家×曲目单元，含A/B/C等级、版本设计和文化安全要求。</p>
              <button type="button" @click="exportPilotPlan">下载CSV</button>
            </article>
            <article>
              <h4>受众反馈采集模板</h4>
              <p>导出统一字段空表，供六国测试录入；模板不预填任何结果。</p>
              <button type="button" @click="exportResponseTemplate">下载CSV</button>
            </article>
          </div>

          <section class="import-panel">
            <div class="import-head">
              <div><span>DATA RETURN</span><h3>导入反馈CSV并做质量校验</h3><p>校验在进入正式评分前完成；程序不会在此步骤写入研究版本。</p></div>
              <label class="upload-button" for="pilot-response-file">选择CSV文件</label>
              <input id="pilot-response-file" type="file" accept=".csv,text/csv" @change="onPilotFile">
            </div>
            <p v-if="pilotValidationLoading" class="validation-message">正在校验 {{ pilotFileName }}…</p>
            <p v-else-if="pilotValidationError" class="validation-message error">{{ pilotValidationError }}</p>
            <template v-else-if="pilotValidation">
              <div class="validation-summary">
                <article><strong>{{ pilotValidation.summary.total_rows }}</strong><span>导入行数</span></article>
                <article><strong>{{ pilotValidation.summary.eligible_rows }}</strong><span>可纳入行数</span></article>
                <article><strong>{{ pilotValidation.summary.invalid_rows }}</strong><span>无效行数</span></article>
                <article><strong>{{ pilotValidation.summary.balanced_cells }}</strong><span>双版本完整单元</span></article>
              </div>
              <p class="validation-scope">{{ pilotValidation.scope_note }}</p>
              <div class="metric-preview">
                <article v-for="metric in pilotValidation.descriptive_metrics" :key="metric.key">
                  <span>{{ metric.label }}</span><strong>{{ metric.mean_1_5 ?? '—' }}</strong><small>n={{ metric.n }} / 5分描述均值</small>
                </article>
              </div>
              <div v-if="pilotValidation.errors.length" class="error-report">
                <div><h4>发现 {{ pilotValidation.summary.error_count }} 项错误</h4><button type="button" @click="exportValidationErrors">下载错误报告</button></div>
                <div class="matrix-wrap">
                  <table>
                    <thead><tr><th>行</th><th>反馈编号</th><th>字段</th><th>问题</th></tr></thead>
                    <tbody><tr v-for="item in pilotValidation.errors.slice(0, 50)" :key="`${item.row_number}-${item.field}-${item.code}`"><td>{{ item.row_number }}</td><td>{{ item.response_id ?? '—' }}</td><td>{{ item.field_label }}</td><td>{{ item.message }}</td></tr></tbody>
                  </table>
                </div>
                <small v-if="pilotValidation.errors.length > 50">页面仅显示前50项，完整内容请下载错误报告。</small>
              </div>
              <div v-else class="validation-success">格式、同意、编号和量表范围校验全部通过；仍需达到研究负责人确定的每版本样本量后，才能进入正式聚合。</div>
            </template>
          </section>

          <h3>统一采集字段</h3>
          <div class="field-table">
            <div class="field-row field-head"><span>字段</span><span>含义</span><span>必填</span><span>填写规则</span></div>
            <div v-for="field in result.pilot.response_fields" :key="field.key" class="field-row">
              <code>{{ field.key }}</code><b>{{ field.label }}</b><span>{{ field.required ? '是' : '否' }}</span><p>{{ field.rule }}</p>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page-shell{min-height:100vh;background:#f6f1e7;color:#22263b}.research-page{width:min(1440px,calc(100% - 40px));margin:0 auto;padding:34px 0 70px}.hero{display:flex;justify-content:space-between;gap:32px;align-items:center;padding:38px 42px;background:linear-gradient(120deg,#18203b,#2a3558);color:#fff3d6;border-radius:24px;box-shadow:0 18px 50px #18203b26}.eyebrow,.section-head p{margin:0 0 10px;color:#d6ad63;font-size:12px;letter-spacing:.18em}.hero h1{margin:0;font-family:serif;font-size:clamp(30px,4vw,52px)}.hero-copy{max-width:760px;margin:16px 0 0;color:#e5dfd2;line-height:1.8}.approval-stamp{flex:0 0 auto;width:104px;height:104px;border:2px solid #d6ad63;border-radius:50%;display:grid;place-content:center;text-align:center;font-family:serif;font-size:22px;transform:rotate(-7deg)}.approval-stamp span{font-size:14px;letter-spacing:.16em}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:22px 0}.metric-grid article{padding:22px;background:#fff;border:1px solid #e6dcc9;border-radius:16px}.metric-grid strong{display:block;color:#8f302c;font:700 34px/1 serif}.metric-grid span{display:block;margin:5px 0;font-weight:700}.metric-grid small{color:#77746e}.scope-note{display:flex;gap:18px;padding:15px 20px;background:#fff9e9;border-left:4px solid #c8923b;border-radius:8px;line-height:1.65}.scope-note b{white-space:nowrap}.scope-note span{color:#5f5b55}.tab-list{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:24px 0 16px}.tab-list button{padding:16px;border:1px solid #d8cfbf;background:#fff;border-radius:13px;text-align:left;color:#30354a;cursor:pointer}.tab-list button span,.tab-list button small{display:block}.tab-list button span{font-weight:700}.tab-list button small{margin-top:5px;color:#8a857c}.tab-list button.active{background:#8f302c;border-color:#8f302c;color:white}.tab-list button.active small{color:#f3d6c2}.content-panel{padding:26px;background:#fff;border:1px solid #e4dac9;border-radius:18px;box-shadow:0 8px 24px #3026190a}.cases-layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:26px}.case-list{display:flex;flex-direction:column;gap:8px;max-height:760px;overflow:auto;padding-right:4px}.case-list button{display:flex;flex-direction:column;gap:5px;padding:14px;border:1px solid #e6dfd2;border-radius:10px;background:#faf8f3;text-align:left;cursor:pointer}.case-list button.active{border-color:#8f302c;background:#fff5ed}.case-list small{color:#76716a}.case-id{color:#a76d38;font-size:11px;letter-spacing:.08em}.detail-head{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;border-bottom:1px solid #eee5d8;padding-bottom:18px}.detail-head p{margin:0;color:#9a6b37;font-size:12px}.detail-head h2{margin:5px 0;font-family:serif;font-size:30px}.detail-head span{color:#666}.outcome-badge{padding:9px 13px;border-radius:999px;background:#e8f2e8;color:#315b3a;font-weight:700;white-space:nowrap}.case-summary{line-height:1.8;color:#555b68}.case-detail h3{margin:24px 0 12px;font-size:17px}.feedback-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.feedback-card{padding:17px;border:1px solid #e8dfd1;border-radius:12px;background:#fcfbf8}.feedback-meta{display:flex;flex-wrap:wrap;gap:7px}.feedback-meta span{padding:3px 7px;background:#eee9df;border-radius:5px;font-size:11px}.feedback-meta .eligible{background:#e3f1e5;color:#28613a}.feedback-meta .limited{background:#f5ead7;color:#895b1d}.feedback-card blockquote{margin:15px 0;padding-left:13px;border-left:3px solid #d4a34e;color:#34394b;font-family:serif;line-height:1.65}.feedback-card p{line-height:1.7}.feedback-card small{display:block;margin-top:8px;color:#6f6b65;line-height:1.55}.feedback-card a,.detail-link{display:inline-block;margin-top:12px;color:#8f302c;text-decoration:none;font-weight:700}.mechanism-chips,.mini-tags{display:flex;flex-wrap:wrap;gap:7px}.mechanism-chips span,.mini-tags span{padding:7px 9px;border-radius:7px;font-size:12px}.strong{background:#527c5d!important;color:white}.partial{background:#d29a43!important;color:white}.muted{background:#dbd7d0!important;color:#666}.limits{margin-top:18px;color:#6c6862}.limits summary{cursor:pointer;font-weight:700}.limits li{margin:7px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:22px}.section-head h2{margin:0;font-family:serif;font-size:30px}.section-head>span{padding:7px 10px;background:#f2ede4;border-radius:7px;color:#676158;font-size:12px}.mechanism-table{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.mechanism-table article{padding:17px;border:1px solid #e6dfd3;border-radius:12px}.mechanism-title{display:flex;gap:9px;align-items:center}.mechanism-title span{color:#a36b32}.stacked-bar{display:flex;height:12px;margin:15px 0 9px;overflow:hidden;border-radius:999px;background:#eee}.stacked-bar i{display:block;height:100%}.mechanism-counts{display:flex;justify-content:space-between;color:#6f6b65;font-size:12px}.interpretation{margin:20px 0 0;padding:15px;background:#f8f4ec;border-radius:9px;color:#64605a;line-height:1.7}.tier-filter{display:flex;align-items:center;gap:8px}.tier-filter select{padding:8px 10px;border:1px solid #d5cec2;border-radius:7px;background:white}.music-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.music-card{padding:18px;border:1px solid #e5ddd0;border-radius:13px}.music-top{display:flex;align-items:center;gap:8px;color:#8b857c;font-size:11px}.music-top .tier{display:grid;place-items:center;width:25px;height:25px;border-radius:50%;background:#8f302c;color:#fff;font-weight:800}.music-top em{margin-left:auto;padding:4px 7px;border-radius:5px;background:#fff0d8;color:#875923;font-style:normal}.music-card h3{margin:15px 0 5px;font:700 24px serif}.music-card>p{line-height:1.65;color:#555a64}.music-card .music-type{color:#9b6b34;font-size:12px}.mini-tags span{background:#eee9df;color:#59554f}.music-card dl{margin:15px 0 0;padding-top:12px;border-top:1px solid #eee7db}.music-card dl div{display:grid;grid-template-columns:65px 1fr;gap:7px;margin:8px 0;font-size:12px;line-height:1.55}.music-card dt{color:#918a80}.music-card dd{margin:0}.country-tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}.country-tabs button{padding:8px 18px;border:1px solid #d8d0c3;border-radius:999px;background:white;cursor:pointer}.country-tabs button.active{background:#24304d;border-color:#24304d;color:white}.country-brief{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#ddd3c3;border:1px solid #ddd3c3;border-radius:12px;overflow:hidden;margin-bottom:22px}.country-brief div{padding:15px;background:#fbf9f4}.country-brief span{color:#9a6a36;font-size:11px}.country-brief p{margin:6px 0 0;font-size:13px;line-height:1.6}.matrix-wrap{overflow:auto;border:1px solid #e0d8cb;border-radius:12px}.matrix-wrap table{width:100%;min-width:900px;border-collapse:collapse}.matrix-wrap th,.matrix-wrap td{padding:11px 12px;border-bottom:1px solid #ebe4d8;text-align:center}.matrix-wrap thead th{position:sticky;top:0;background:#252f4b;color:white;font-size:12px}.matrix-wrap tbody th{text-align:left;background:#fbf8f3;white-space:nowrap}.matrix-wrap tbody th small{display:block;color:#a4743b;font-weight:400}.fit{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;font-weight:800}.fit-A{background:#dcebdd;color:#315e3b}.fit-B{background:#fae8c8;color:#89591b}.fit-C{background:#ece7df;color:#6d665f}.state-card{margin-top:22px;padding:50px;text-align:center;background:white;border-radius:16px}.state-card.error{color:#8f302c}.state-card button{padding:8px 15px;border:0;border-radius:7px;background:#8f302c;color:#fff;cursor:pointer}
.audit-strip{display:grid;grid-template-columns:repeat(6,1fr);gap:7px}.audit-strip span{padding:10px;background:#e7f1e7;border:1px solid #c9dfcc;border-radius:8px;color:#315e3a;text-align:center;font-size:12px}.audit-strip b{display:block;margin-bottom:3px}.matrix-title{margin:26px 0 12px}.mechanism-matrix{max-height:520px}.evidence-dot{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;font-size:11px}.execution-status{display:grid;grid-template-columns:160px 160px 1fr;gap:12px;align-items:stretch;margin-bottom:28px}.execution-status>div,.execution-status>p{margin:0;padding:18px;background:#f7f2e9;border-radius:11px}.execution-status strong{display:block;color:#8f302c;font:700 30px serif}.execution-status span{font-size:12px;color:#716b63}.execution-status p{line-height:1.7;color:#5e5a55}.execution-panel>h3{margin:28px 0 13px;font-size:18px}.rule-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}.rule-grid article{position:relative;padding:16px 16px 16px 54px;border:1px solid #e3dacd;border-radius:11px}.rule-grid span{position:absolute;left:14px;top:15px;display:grid;place-items:center;width:31px;height:31px;border-radius:50%;background:#26304c;color:white;font-weight:800}.rule-grid h4{margin:0 0 6px}.rule-grid p{margin:0;color:#68635d;font-size:12px;line-height:1.6}.principle-list{padding:18px 18px 18px 42px;background:#fbf7ef;border-radius:11px}.principle-list li{margin:9px 0;line-height:1.65}.download-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:22px}.download-grid article{padding:18px;border:1px solid #ded5c7;border-radius:12px}.download-grid h4{margin:0}.download-grid p{min-height:46px;color:#6e6861;font-size:13px;line-height:1.6}.download-grid button{padding:9px 15px;border:0;border-radius:7px;background:#8f302c;color:#fff;font-weight:700;cursor:pointer}.field-table{border:1px solid #e0d7c9;border-radius:11px;overflow:hidden}.field-row{display:grid;grid-template-columns:1.1fr 1fr 65px 2fr;align-items:center;border-bottom:1px solid #ebe3d7}.field-row:last-child{border-bottom:0}.field-row>*{margin:0;padding:11px 13px}.field-row code{color:#8f302c;overflow-wrap:anywhere}.field-row p{color:#66615b;font-size:12px;line-height:1.5}.field-head{background:#26304c;color:white;font-size:12px;font-weight:700}
.import-panel{margin-top:24px;padding:22px;border:1px solid #d9cfbf;border-radius:14px;background:#faf8f3}.import-head{display:flex;align-items:center;justify-content:space-between;gap:18px}.import-head span{color:#a06c35;font-size:11px;letter-spacing:.14em}.import-head h3{margin:5px 0}.import-head p{margin:0;color:#6a655e;font-size:13px}.import-head input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}.upload-button{flex:0 0 auto;padding:10px 16px;border-radius:8px;background:#26304c;color:white;font-weight:700;cursor:pointer}.validation-message{margin:18px 0 0;padding:13px;background:#eee9df;border-radius:8px}.validation-message.error{background:#fae3e0;color:#8a312b}.validation-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:18px}.validation-summary article{padding:14px;background:white;border:1px solid #e1d8ca;border-radius:9px}.validation-summary strong{display:block;color:#8f302c;font:700 27px serif}.validation-summary span{font-size:12px}.validation-scope{padding:12px 14px;background:#fff4dc;border-radius:8px;color:#735c36;font-size:12px;line-height:1.6}.metric-preview{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.metric-preview article{padding:12px;background:white;border-radius:8px;text-align:center}.metric-preview span,.metric-preview small{display:block;color:#77716a;font-size:11px}.metric-preview strong{display:block;margin:5px;color:#315d3b;font:700 24px serif}.error-report{margin-top:18px}.error-report>div:first-child{display:flex;align-items:center;justify-content:space-between}.error-report h4{margin:0 0 10px}.error-report button{padding:7px 11px;border:1px solid #8f302c;border-radius:6px;background:white;color:#8f302c;cursor:pointer}.error-report table{min-width:700px}.validation-success{margin-top:18px;padding:15px;border-radius:8px;background:#e4f0e5;color:#315d3b;line-height:1.6}
@media(max-width:1000px){.metric-grid,.tab-list{grid-template-columns:repeat(2,1fr)}.cases-layout{grid-template-columns:1fr}.case-list{display:grid;grid-template-columns:repeat(2,1fr);max-height:none}.mechanism-table,.music-grid,.country-brief,.rule-grid,.download-grid{grid-template-columns:repeat(2,1fr)}.execution-status{grid-template-columns:repeat(2,1fr)}.execution-status p{grid-column:1/-1}.metric-preview{grid-template-columns:repeat(3,1fr)}}
@media(max-width:640px){.research-page{width:min(100% - 22px,1440px);padding-top:18px}.hero{padding:25px}.approval-stamp{display:none}.metric-grid,.tab-list,.feedback-grid,.mechanism-table,.music-grid,.country-brief,.case-list,.rule-grid,.download-grid,.execution-status,.validation-summary,.metric-preview{grid-template-columns:1fr}.tab-list{display:flex;overflow:auto}.tab-list button{min-width:170px}.content-panel{padding:16px}.detail-head,.section-head,.import-head{align-items:flex-start;flex-direction:column}.scope-note{flex-direction:column;gap:5px}.audit-strip{grid-template-columns:repeat(3,1fr)}.field-table{overflow:auto}.field-row{min-width:720px}}
</style>
