<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import SampleBadge from '@/components/research/SampleBadge.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import { fetchResearchStatus, generateResearchPromoPlan } from '@/api/research'
import type { ResearchPromoPlan, ResearchPromoPlanInput, ResearchStatus } from '@/types/research'

const audiences = ['音乐学院学生', '华裔社群', '青年短视频用户', '世界音乐爱好者', '博物馆与文化机构', '综合']
const ageRanges = ['18-24', '25-34', '35-49', '50+', '全年龄']
const purposes = ['文化交流', '非遗传播', '青年交流', '旅游推广', '教育推广', '商业发布']
const platforms = ['短视频', '社交媒体', '音乐学院 / 艺术节', '博物馆 / 文化机构', '流媒体', '综合']
const formats = ['短视频', '纪录片', '音乐会', '工作坊', '展陈', '图文']
const adaptations = [
  { value: 'yes', label: '允许跨文化改编' },
  { value: 'no', label: '不允许改编' },
  { value: 'undecided', label: '尚未决定' },
]
const budgets = ['低', '中等', '高', '未定']
const durations = ['1个月', '3个月', '6个月', '12个月']
const languages = ['中文', 'English', 'Deutsch', 'Français', '日本語', '한국어', 'Español', 'العربية', '多语种']
const originCities = ['未提供', '北京', '上海', '其他']

const form = reactive<ResearchPromoPlanInput>({
  title: '',
  target_country: '',
  target_city: '',
  target_audience: audiences[0] ?? '',
  age_range: ageRanges[1] ?? '',
  purpose: purposes[0] ?? '',
  platform: platforms[2] ?? '',
  content_format: formats[2] ?? '',
  adaptation_allowed: 'yes',
  budget_range: budgets[1] ?? '',
  duration: durations[1] ?? '',
  language: languages[1] ?? '',
  origin_city: '未提供',
})

const formError = ref('')
const generating = ref(false)
const requestError = ref('')
const plan = ref<ResearchPromoPlan | null>(null)
const researchStatus = ref<ResearchStatus | null>(null)
const resultRef = ref<HTMLElement | null>(null)

const sample = computed(() => plan.value?.sample ?? researchStatus.value?.sample ?? null)
const hasPlan = computed(() => Boolean(plan.value))
const planCounts = computed(
  () => plan.value?.counts ?? { evidence: 0, suggestions: 0, hypotheses: 0, gaps: 0 },
)
const moduleNumber = (index: number) => String(index + 1).padStart(2, '0')

function validate() {
  const required: Array<[keyof ResearchPromoPlanInput, string]> = [
    ['title', '目标音乐'],
    ['target_country', '目标国家/地区'],
    ['target_city', '目标城市'],
    ['target_audience', '目标受众'],
    ['age_range', '年龄范围'],
    ['purpose', '传播目的'],
    ['platform', '主要传播平台'],
    ['content_format', '内容表现形式'],
    ['adaptation_allowed', '是否允许跨文化改编'],
    ['budget_range', '预算范围'],
    ['duration', '活动周期'],
    ['language', '传播语言'],
  ]
  const missing = required.filter(([key]) => !String(form[key] ?? '').trim()).map(([, label]) => label)
  if (missing.length) {
    formError.value = `请填写：${missing.join('、')}`
    return false
  }
  formError.value = ''
  return true
}

async function generatePlan() {
  if (!validate()) return
  generating.value = true
  requestError.value = ''
  plan.value = null
  try {
    const response = await generateResearchPromoPlan({
      ...form,
      origin_city: form.origin_city === '未提供' ? undefined : form.origin_city,
    })
    if (!response.data) throw new Error('方案接口未返回有效数据')
    plan.value = response.data
    await nextTick()
    resultRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (err) {
    const error = err as { message?: string }
    requestError.value = `方案生成失败：${error.message || '网络请求失败'}`
  } finally {
    generating.value = false
  }
}

function resetForm() {
  form.title = ''
  form.target_country = ''
  form.target_city = ''
  form.origin_city = '未提供'
  plan.value = null
  formError.value = ''
  requestError.value = ''
}

onMounted(async () => {
  try {
    const response = await fetchResearchStatus()
    if (response.data) researchStatus.value = response.data
  } catch {
    researchStatus.value = null
  }
})
</script>

<template>
  <div class="page research-page promo-plan-page">
    <AppNav />

    <main class="promo-shell">
      <header class="promo-hero">
        <div>
          <p class="promo-eyebrow">REGIONAL PROPAGATION PLAN / 方案生成</p>
          <h1>区域传播方案</h1>
          <p class="promo-desc">
            根据音乐、目标市场、受众与执行条件，生成 9 个结构化模块。
            方案会把“已有证据、策略建议、待验证假设、证据缺口”分开呈现，方便人工复核。
          </p>
        </div>
        <div class="promo-hero-meta">
          <SampleBadge :sample="sample" />
          <span class="mode-chip">规则模板生成</span>
          <p>不调用大模型；不预设受众偏好或效果提升。</p>
        </div>
      </header>

      <div class="promo-layout">
        <aside class="form-column">
          <div class="form-head">
            <span>INPUTS</span>
            <b>12 项输入</b>
            <small>来源城市为音乐元数据，不替代目标城市</small>
          </div>

          <form class="plan-form" autocomplete="off" @submit.prevent="generatePlan">
            <fieldset>
              <legend>01 音乐信息</legend>
              <label>
                <span>目标音乐 <em>*</em></span>
                <input v-model="form.title" name="research_music_title" autocomplete="off" type="text" maxlength="120" placeholder="如：春江花月夜" />
              </label>
              <label>
                <span>作品来源城市 <small>可选</small></span>
                <select v-model="form.origin_city" name="origin_city">
                  <option v-for="city in originCities" :key="city" :value="city">{{ city }}</option>
                </select>
              </label>
            </fieldset>

            <fieldset>
              <legend>02 目标市场</legend>
              <label>
                <span>目标国家 / 地区 <em>*</em></span>
                <input v-model="form.target_country" name="research_target_country" autocomplete="off" type="text" placeholder="如：德国" />
              </label>
              <label>
                <span>目标城市 <em>*</em></span>
                <input v-model="form.target_city" name="research_target_city" autocomplete="off" type="text" placeholder="如：柏林" />
              </label>
            </fieldset>

            <fieldset>
              <legend>03 受众定位</legend>
              <label>
                <span>目标受众 <em>*</em></span>
                <select v-model="form.target_audience" name="target_audience">
                  <option v-for="audience in audiences" :key="audience" :value="audience">{{ audience }}</option>
                </select>
              </label>
              <label>
                <span>年龄范围 <em>*</em></span>
                <select v-model="form.age_range" name="age_range">
                  <option v-for="range in ageRanges" :key="range" :value="range">{{ range }}</option>
                </select>
              </label>
            </fieldset>

            <fieldset>
              <legend>04 传播目标</legend>
              <label>
                <span>传播目的 <em>*</em></span>
                <select v-model="form.purpose" name="purpose">
                  <option v-for="purpose in purposes" :key="purpose" :value="purpose">{{ purpose }}</option>
                </select>
              </label>
            </fieldset>

            <fieldset>
              <legend>05 渠道与形式</legend>
              <label>
                <span>主要传播平台 <em>*</em></span>
                <select v-model="form.platform" name="platform">
                  <option v-for="platform in platforms" :key="platform" :value="platform">{{ platform }}</option>
                </select>
              </label>
              <label>
                <span>内容表现形式 <em>*</em></span>
                <select v-model="form.content_format" name="content_format">
                  <option v-for="format in formats" :key="format" :value="format">{{ format }}</option>
                </select>
              </label>
            </fieldset>

            <fieldset>
              <legend>06 活动条件</legend>
              <label>
                <span>是否允许跨文化改编 <em>*</em></span>
                <select v-model="form.adaptation_allowed" name="adaptation_allowed">
                  <option v-for="item in adaptations" :key="item.value" :value="item.value">{{ item.label }}</option>
                </select>
              </label>
              <div class="form-row">
                <label>
                  <span>预算范围 <em>*</em></span>
                  <select v-model="form.budget_range" name="budget_range">
                    <option v-for="budget in budgets" :key="budget" :value="budget">{{ budget }}</option>
                  </select>
                </label>
                <label>
                  <span>活动周期 <em>*</em></span>
                  <select v-model="form.duration" name="duration">
                    <option v-for="duration in durations" :key="duration" :value="duration">{{ duration }}</option>
                  </select>
                </label>
              </div>
              <label>
                <span>传播语言 <em>*</em></span>
                <select v-model="form.language" name="language">
                  <option v-for="language in languages" :key="language" :value="language">{{ language }}</option>
                </select>
              </label>
            </fieldset>

            <p v-if="formError" class="form-error">{{ formError }}</p>
            <button type="submit" class="generate-button" :disabled="generating">
              {{ generating ? '生成中...' : '生成结构化方案' }}
            </button>
            <button type="button" class="reset-button" @click="resetForm">清空</button>
          </form>
        </aside>

        <section ref="resultRef" class="result-column" aria-live="polite">
          <div v-if="generating" class="plan-loading">
            <div class="loading-spinner"></div>
            <h2>正在生成 9 个模块</h2>
            <p>正在核对已有证据、标注建议与假设，不调用大模型。</p>
          </div>

          <div v-else-if="requestError" class="plan-error">
            <span>GENERATION ERROR</span>
            <h2>方案生成失败</h2>
            <p>{{ requestError }}</p>
            <button type="button" @click="generatePlan">重新生成</button>
          </div>

          <div v-else-if="!hasPlan" class="plan-empty">
            <div class="empty-mark">09</div>
            <p class="empty-kicker">BEFORE GENERATION</p>
            <h2>填写左侧 12 项输入，生成完整方案</h2>
            <p>
              输出固定 9 个模块，每一块都会区分：
            </p>
            <div class="type-legend">
              <span class="type evidence">已有证据</span>
              <span class="type suggestion">策略建议</span>
              <span class="type hypothesis">待验证假设</span>
              <span class="type gap">证据缺口</span>
            </div>
            <p class="empty-note">
              当前音乐评分与区域策略仍为待补充；生成结果会如实显示证据不足，不会编造受众偏好、文化禁忌或效果提升数字。
            </p>
          </div>

          <template v-else-if="plan">
            <header class="plan-header">
              <div>
                <p class="plan-kicker">GENERATED PLAN / {{ plan.meta.plan_id }}</p>
                <h2>{{ plan.meta.inputs.title }}</h2>
                <p>
                  {{ plan.meta.inputs.target_country }} · {{ plan.meta.inputs.target_city }} ·
                  {{ plan.meta.inputs.target_audience }} · {{ plan.meta.inputs.language }}
                </p>
              </div>
              <div class="plan-header-meta">
                <SampleBadge :sample="plan.sample" compact />
                <span>{{ plan.meta.generation_mode }}</span>
                <small>数据版本 {{ plan.meta.data_version }}</small>
              </div>
            </header>

            <p v-if="planCounts.evidence === 0" class="evidence-boundary">
              本次生成没有直接证据。以下模块只保留策略建议、待验证假设和证据缺口，不构成传播结论。
            </p>

            <div class="plan-counts">
              <div class="count evidence"><strong>{{ planCounts.evidence }}</strong><span>已有证据</span></div>
              <div class="count suggestion"><strong>{{ planCounts.suggestions }}</strong><span>策略建议</span></div>
              <div class="count hypothesis"><strong>{{ planCounts.hypotheses }}</strong><span>待验证假设</span></div>
              <div class="count gap"><strong>{{ planCounts.gaps }}</strong><span>证据缺口</span></div>
            </div>

            <div class="evidence-summary">
              <div>
                <span>音乐研究状态</span>
                <b>{{ plan.evidence_summary.potential.tier }}</b>
                <small>{{ plan.evidence_summary.potential.valid_count }} / 8 项有评分</small>
              </div>
              <div>
                <span>曲目匹配案例</span>
                <b>{{ plan.evidence_summary.case_count }} 个</b>
                <small>{{ plan.evidence_summary.case_scope_label || '按曲名、乐器、类型与机制匹配' }}</small>
              </div>
              <div>
                <span>区域策略</span>
                <b>{{ plan.evidence_summary.regional_count }} 条</b>
                <small>只认 music_ids</small>
              </div>
              <div>
                <span>来源</span>
                <b>{{ plan.evidence_summary.source_count }} 条</b>
                <small>案例/区域策略来源</small>
              </div>
            </div>

            <div class="modules-list">
              <article v-for="(module, index) in plan.modules" :key="module.id" class="plan-module">
                <header class="module-head">
                  <span>{{ moduleNumber(index) }}</span>
                  <h3>{{ module.title }}</h3>
                  <div class="module-counts">
                    <b v-if="module.evidence.length" class="mini evidence">{{ module.evidence.length }} 证据</b>
                    <b v-if="module.suggestions.length" class="mini suggestion">{{ module.suggestions.length }} 建议</b>
                    <b v-if="module.hypotheses.length" class="mini hypothesis">{{ module.hypotheses.length }} 假设</b>
                    <b v-if="module.gaps.length" class="mini gap">{{ module.gaps.length }} 缺口</b>
                  </div>
                </header>

                <div class="module-body">
                  <section class="module-section evidence-section">
                    <p class="section-label">已有证据</p>
                    <div v-if="module.evidence.length" class="item-list">
                      <div v-for="(item, itemIndex) in module.evidence" :key="`${module.id}-e-${itemIndex}`" class="evidence-item">
                        <p>{{ item.text }}</p>
                        <div class="trace-row">
                          <RouterLink
                            v-for="caseId in item.case_ids"
                            :key="caseId"
                            :to="{ name: 'global-case-detail', params: { caseId } }"
                            class="trace-chip"
                          >
                            {{ caseId }}
                          </RouterLink>
                          <span v-for="sourceId in item.source_ids" :key="sourceId" class="trace-chip">{{ sourceId }}</span>
                          <a
                            v-for="source in item.source_links"
                            :key="source.url"
                            :href="source.url"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="trace-chip source-link"
                          >
                            {{ source.publisher || source.title || '查看来源' }} ↗
                          </a>
                        </div>
                      </div>
                    </div>
                    <p v-else class="empty-line">本模块暂无直接证据；保留为证据缺口，不补写结论。</p>
                  </section>

                  <section class="module-section suggestion-section">
                    <p class="section-label">策略建议</p>
                    <div v-if="module.suggestions.length" class="item-list">
                      <div v-for="(item, itemIndex) in module.suggestions" :key="`${module.id}-s-${itemIndex}`">
                        <p>{{ item.text }}</p>
                        <small>依据：{{ item.basis }}</small>
                      </div>
                    </div>
                    <p v-else class="empty-line">本模块暂不生成建议（缺少直接证据）。</p>
                  </section>

                  <section class="module-section hypothesis-section">
                    <p class="section-label">待验证假设</p>
                    <div v-if="module.hypotheses.length" class="item-list">
                      <div v-for="(item, itemIndex) in module.hypotheses" :key="`${module.id}-h-${itemIndex}`">
                        <p>{{ item.text }}</p>
                        <small>验证方式：{{ item.validation }}</small>
                      </div>
                    </div>
                    <p v-else class="empty-line">本模块暂无待验证假设。</p>
                  </section>

                  <section class="module-section gap-section">
                    <p class="section-label">证据缺口</p>
                    <div v-if="module.gaps.length" class="item-list">
                      <div v-for="(item, itemIndex) in module.gaps" :key="`${module.id}-g-${itemIndex}`">
                        <p>{{ item.text }}</p>
                        <small>下一步：{{ item.action }}</small>
                      </div>
                    </div>
                    <p v-else class="empty-line">本模块暂无额外缺口。</p>
                  </section>
                </div>
              </article>
            </div>

            <div class="plan-disclaimer">
              <b>使用说明</b>
              <p>{{ plan.disclaimer }}</p>
            </div>
          </template>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.promo-plan-page {
  min-height: 100vh;
  color: #e8f1ed;
}

.promo-shell {
  position: relative;
  max-width: 1400px;
  margin: 0 auto;
  padding: clamp(30px, 4.5vw, 56px) clamp(20px, 4vw, 44px) 76px;
}

.promo-shell::before {
  content: '';
  position: absolute;
  z-index: -1;
  top: -70px;
  right: 5%;
  width: min(580px, 72vw);
  height: 380px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(71, 139, 116, 0.14), transparent 68%);
  pointer-events: none;
}

.promo-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 30px;
  padding-bottom: 26px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.18);
}

.promo-eyebrow,
.plan-kicker {
  margin: 0 0 12px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.18em;
}

.promo-hero h1 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(42px, 5vw, 58px);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.04em;
}

.promo-desc {
  max-width: 760px;
  margin: 18px 0 0;
  color: #9bb7ad;
  font-size: 13px;
  line-height: 1.9;
}

.promo-hero-meta {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 8px;
  flex: 0 0 280px;
}

.mode-chip {
  padding: 3px 8px;
  border: 1px solid rgba(143, 199, 177, 0.3);
  border-radius: 999px;
  color: #8fc7b1;
  font-size: 9px;
}

.promo-hero-meta p {
  margin: 0;
  color: #6f8c81;
  font-size: 9px;
  text-align: right;
}

.promo-layout {
  display: grid;
  grid-template-columns: 380px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
  margin-top: 22px;
}

.form-column {
  position: sticky;
  top: 96px;
  border: 1px solid rgba(159, 198, 181, 0.18);
  border-radius: 12px;
  background: rgba(8, 33, 30, 0.78);
  overflow: hidden;
}

.form-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 16px 17px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.12);
}

.form-head > span {
  color: #8fc7b1;
  font-size: 9px;
  letter-spacing: 0.15em;
}

.form-head b {
  color: #d9c28a;
  font-size: 10px;
  font-weight: 500;
}

.form-head small {
  margin-left: auto;
  color: #6f8c81;
  font-size: 8px;
  text-align: right;
}

.plan-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
}

fieldset {
  min-width: 0;
  margin: 0;
  padding: 0 0 13px;
  border: 0;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

fieldset:last-of-type {
  border-bottom: 0;
  padding-bottom: 0;
}

legend {
  margin-bottom: 9px;
  padding: 0;
  color: #8fc7b1;
  font-size: 9px;
  letter-spacing: 0.08em;
}

label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 8px;
}

label > span {
  color: #9bb7ad;
  font-size: 9px;
}

label em {
  color: #e2a276;
  font-style: normal;
}

label small {
  color: #6f8c81;
  font-size: 8px;
}

input,
select {
  width: 100%;
  height: 36px;
  padding: 0 9px;
  border: 1px solid rgba(159, 198, 181, 0.2);
  border-radius: 4px;
  background: rgba(3, 20, 18, 0.58);
  color: #e8f1ed;
  font-size: 11px;
  outline: none;
}

input::placeholder {
  color: #5f7b71;
}

input:focus,
select:focus {
  border-color: rgba(143, 199, 177, 0.5);
}

select option {
  background: #0b2823;
  color: #e8f1ed;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.form-error {
  margin: 0;
  color: #e2a276;
  font-size: 10px;
  line-height: 1.6;
}

.generate-button,
.reset-button {
  height: 38px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.generate-button {
  border: 1px solid #8fc7b1;
  background: #8fc7b1;
  color: #071c19;
  font-weight: 600;
}

.generate-button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.reset-button {
  border: 1px solid rgba(159, 198, 181, 0.18);
  background: transparent;
  color: #78948a;
}

.result-column {
  min-width: 0;
  scroll-margin-top: 96px;
}

.plan-empty,
.plan-loading,
.plan-error {
  display: flex;
  align-items: center;
  min-height: 520px;
  padding: 44px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 12px;
  background: rgba(8, 33, 30, 0.58);
}

.plan-empty,
.plan-loading {
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

.empty-mark {
  display: grid;
  width: 64px;
  height: 64px;
  margin-bottom: 18px;
  place-items: center;
  border: 1px solid rgba(217, 194, 138, 0.32);
  border-radius: 50%;
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 15px;
}

.empty-kicker {
  margin: 0;
  color: #6f8c81;
  font-size: 9px;
  letter-spacing: 0.16em;
}

.plan-empty h2,
.plan-loading h2,
.plan-error h2 {
  margin: 12px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 24px;
  font-weight: 500;
}

.plan-empty > p,
.plan-loading p,
.plan-error p {
  max-width: 620px;
  margin: 12px 0 0;
  color: #8fa99f;
  font-size: 11px;
  line-height: 1.8;
}

.type-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 7px;
  margin-top: 20px;
}

.type {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 9px;
}

.type.evidence,
.mini.evidence {
  color: #9ed2b5;
  border: 1px solid rgba(143, 199, 177, 0.32);
  background: rgba(94, 166, 140, 0.1);
}

.type.suggestion,
.mini.suggestion {
  color: #d9c28a;
  border: 1px solid rgba(217, 194, 138, 0.3);
  background: rgba(217, 194, 138, 0.08);
}

.type.hypothesis,
.mini.hypothesis {
  color: #d8b392;
  border: 1px solid rgba(226, 162, 118, 0.3);
  background: rgba(126, 75, 42, 0.1);
}

.type.gap,
.mini.gap {
  color: #b9a484;
  border: 1px solid rgba(185, 164, 132, 0.25);
  background: rgba(111, 92, 58, 0.1);
}

.empty-note {
  margin-top: 20px !important;
  color: #6f8c81 !important;
}

.plan-error {
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
}

.plan-error > span {
  color: #e2a276;
  font-size: 9px;
  letter-spacing: 0.14em;
}

.plan-error button {
  margin-top: 18px;
  padding: 8px 14px;
  border: 1px solid rgba(217, 194, 138, 0.3);
  border-radius: 4px;
  background: transparent;
  color: #e8d4a8;
  font-size: 10px;
  cursor: pointer;
}

.plan-loading {
  gap: 4px;
}

.plan-loading .loading-spinner {
  width: 34px;
  height: 34px;
  margin-bottom: 12px;
}

.plan-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 20px;
  border: 1px solid rgba(159, 198, 181, 0.18);
  border-radius: 10px;
  background: rgba(8, 33, 30, 0.7);
}

.plan-kicker {
  margin-bottom: 8px;
  color: #6f8c81;
  letter-spacing: 0.08em;
}

.plan-header h2 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 28px;
  font-weight: 500;
}

.plan-header p {
  margin: 8px 0 0;
  color: #8fa99f;
  font-size: 10px;
}

.plan-header-meta {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 5px;
  color: #6f8c81;
  font-size: 9px;
}

.plan-counts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-top: 12px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 7px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.plan-counts > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px 14px;
  background: rgba(7, 28, 25, 0.88);
}

.plan-counts strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 25px;
  font-weight: 500;
  line-height: 1;
}

.plan-counts span {
  color: #78948a;
  font-size: 9px;
}

.plan-counts .evidence strong { color: #9ed2b5; }
.plan-counts .suggestion strong { color: #d9c28a; }
.plan-counts .hypothesis strong { color: #d8b392; }
.plan-counts .gap strong { color: #b9a484; }

.evidence-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin-top: 12px;
}

.evidence-summary > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid rgba(159, 198, 181, 0.13);
  border-radius: 6px;
  background: rgba(5, 25, 22, 0.34);
}

.evidence-summary span,
.evidence-summary small {
  color: #6f8c81;
  font-size: 8px;
}

.evidence-summary b {
  color: #c9d8d1;
  font-size: 12px;
  font-weight: 500;
}

.modules-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.plan-module {
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 9px;
  background: rgba(8, 33, 30, 0.58);
  overflow: hidden;
}

.module-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 16px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.module-head > span {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.module-head h3 {
  flex: 1;
  margin: 0;
  color: #d7e4dd;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 18px;
  font-weight: 500;
}

.module-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.mini {
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 8px;
  font-weight: 500;
}

.module-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: rgba(159, 198, 181, 0.1);
}

.module-section {
  min-width: 0;
  padding: 14px 16px;
  background: rgba(7, 28, 25, 0.9);
}

.section-label {
  margin: 0 0 9px;
  color: #6f8c81;
  font-size: 8px;
  letter-spacing: 0.1em;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item-list p {
  margin: 0;
  color: #b6c9c1;
  font-size: 10px;
  line-height: 1.75;
}

.item-list small {
  display: block;
  margin-top: 4px;
  color: #6f8c81;
  font-size: 8px;
  line-height: 1.6;
}

.evidence-item {
  padding-left: 9px;
  border-left: 2px solid rgba(143, 199, 177, 0.35);
}

.trace-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.trace-chip {
  padding: 2px 5px;
  border: 1px solid rgba(143, 199, 177, 0.2);
  border-radius: 3px;
  color: #8fc7b1;
  font-family: 'Consolas', monospace;
  font-size: 7px;
  text-decoration: none;
}

.empty-line {
  margin: 0;
  color: #5f7b71;
  font-size: 9px;
  line-height: 1.7;
}

.plan-disclaimer {
  margin-top: 14px;
  padding: 15px 17px;
  border: 1px solid rgba(217, 194, 138, 0.22);
  border-radius: 7px;
  background: rgba(49, 42, 27, 0.28);
}

.plan-disclaimer b {
  color: #d9c28a;
  font-size: 10px;
  font-weight: 500;
}

.plan-disclaimer p {
  margin: 7px 0 0;
  color: #9bb7ad;
  font-size: 9px;
  line-height: 1.75;
}

@media (max-width: 1180px) {
  .promo-layout {
    grid-template-columns: 340px minmax(0, 1fr);
  }

  .module-body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .promo-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .promo-hero-meta {
    align-items: flex-start;
    flex-basis: auto;
  }

  .promo-hero-meta p {
    text-align: left;
  }

  .promo-layout {
    grid-template-columns: 1fr;
  }

  .form-column {
    position: static;
  }

  .plan-form {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0 12px;
  }

  .plan-form fieldset {
    min-width: 0;
  }

  .generate-button,
  .reset-button,
  .form-error {
    grid-column: 1 / -1;
  }
}

@media (max-width: 620px) {
  .promo-shell {
    padding: 28px 16px 56px;
  }

  .promo-hero h1 {
    font-size: 40px;
  }

  .plan-form {
    display: flex;
  }

  .plan-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .plan-header-meta {
    align-items: flex-start;
  }

  .plan-counts,
  .evidence-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .module-head {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .module-counts {
    width: 100%;
  }

  .plan-empty,
  .plan-loading,
  .plan-error {
    min-height: 420px;
    padding: 26px 20px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .plan-loading .loading-spinner {
    animation: none;
  }
}

.evidence-boundary {
  margin: 12px 0 0;
  padding: 10px 12px;
  border-left: 2px solid rgba(217, 194, 138, 0.55);
  background: rgba(217, 194, 138, 0.07);
  color: #d8c393;
  font-size: 11px;
  line-height: 1.6;
}

</style>
