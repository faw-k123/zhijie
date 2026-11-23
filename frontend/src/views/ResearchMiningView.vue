<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import SampleBadge from '@/components/research/SampleBadge.vue'
import SectionCard from '@/components/research/SectionCard.vue'
import { fetchResearchMining } from '@/api/research'
import type { ResearchMining, ResearchMiningCorrelation } from '@/types/research'

const loading = ref(true)
const error = ref('')
const data = ref<ResearchMining | null>(null)

const indicatorLabels = computed(() =>
  Object.fromEntries((data.value?.indicators ?? []).map((i) => [i.indicator_id, i.label])),
)
const sourceTotal = computed(() =>
  (data.value?.cases ?? []).reduce((sum, item) => sum + item.source_count, 0),
)
const usableCorrelations = computed(
  () => (data.value?.correlations ?? []).filter((item) => item.status === 'exploratory'),
)
const strongCoverage = computed(
  () => (data.value?.indicators ?? []).filter((item) => item.status === 'exploratory').length,
)

function correlationFor(x: string, y: string): ResearchMiningCorrelation | undefined {
  if (!data.value) return undefined
  return data.value.correlations.find(
    (item) => (item.x === x && item.y === y) || (item.x === y && item.y === x),
  )
}

function cell(x: string, y: string) {
  if (x === y) return { value: '1', n: data.value?.case_count ?? 0, status: 'diagonal' }
  const item = correlationFor(x, y)
  if (!item || item.status === 'insufficient' || item.rho === null) {
    return { value: '—', n: item?.n ?? 0, status: 'insufficient' }
  }
  return { value: item.rho.toFixed(2), n: item.n, status: item.status }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchResearchMining()
    if (!response.data) throw new Error('挖掘接口未返回数据')
    data.value = response.data
  } catch (err) {
    const e = err as { message?: string }
    error.value = e.message || '数据挖掘接口加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page research-page mining-page">
    <AppNav />
    <main class="mining-shell">
      <header class="mining-hero">
        <div>
          <p class="mining-eyebrow">RESEARCH DATA MINING / 数据挖掘</p>
          <h1>研究数据挖掘</h1>
          <p class="mining-desc">
            把当前激活案例转成可追溯的分析数据集：案例画像、指标覆盖、成对相关和音乐库只读连接。
            样本仍小，所有相关分析只作探索性线索，不作因果结论。
          </p>
        </div>
        <div class="hero-badge">
          <SampleBadge :sample="data?.sample || null" />
          <span>数据版本 {{ data?.data_version || 'v1.1' }}</span>
        </div>
      </header>

      <div v-if="loading" class="mining-state">正在读取研究数据仓库...</div>
      <div v-else-if="error" class="mining-state error">
        <p>{{ error }}</p>
        <button type="button" @click="load">重新加载</button>
      </div>

      <template v-else-if="data">
        <div class="metric-grid">
          <div class="metric"><strong>{{ data.case_count }}</strong><span>独立案例</span><small>不是来源数</small></div>
          <div class="metric"><strong>{{ data.valid_score_count }}</strong><span>有效指标值</span><small>共 {{ data.score_count }} 条记录</small></div>
          <div class="metric"><strong>{{ sourceTotal }}</strong><span>来源记录</span><small>案例来源合计</small></div>
          <div class="metric"><strong>{{ data.library.song_count ?? '—' }}</strong><span>音乐库曲目</span><small>{{ data.library.status === 'connected' ? 'SQL Server 只读连接' : '数据库未连接' }}</small></div>
        </div>

        <div class="mining-note">
          <b>分析边界</b>
          <p>{{ data.scope_note }}</p>
          <p>当前 {{ strongCoverage }} 项指标达到探索性展示门槛；任何成对相关都需要看成对 n，不能把 73 条有效值当成 73 个样本。</p>
        </div>

        <SectionCard title="案例数据仓库" kicker="CASE WAREHOUSE" subtitle="当前激活版本的案例；分数为空表示证据不足，不是 0 分。">
          <div class="table-scroll">
            <table class="mining-table">
              <thead>
                <tr><th>案例</th><th>国家/地区</th><th>乐器</th><th>主体类型</th><th>有效/缺失</th><th>均分</th><th>来源</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in data.cases" :key="item.case_id">
                  <td><b>{{ item.case_id }}</b><span>{{ item.performer }}</span></td>
                  <td>{{ item.country }}<small>{{ item.region }}</small></td>
                  <td>{{ item.instrument.join(' / ') || '—' }}</td>
                  <td>{{ item.case_type || '—' }}<small>{{ item.analysis_sample || '—' }}</small></td>
                  <td>{{ item.valid_count }} / {{ item.missing_count }}</td>
                  <td>{{ item.mean_score === null ? '—' : item.mean_score.toFixed(2) }}</td>
                  <td>{{ item.source_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </SectionCard>

        <div class="two-col">
          <SectionCard title="分布概览" kicker="DISTRIBUTIONS" subtitle="只描述当前样本，不代表总体。">
            <div v-for="(rows, key) in data.distributions" :key="key" class="dist-block">
              <p>{{ { country: '国家', instrument: '乐器', case_type: '主体类型', analysis_sample: '分析样本', review_status: '证据等级' }[key] || key }}</p>
              <div v-for="row in rows" :key="row.key" class="dist-row">
                <span>{{ row.key }}</span><i :style="{ width: `${Math.max(8, row.count / data.case_count * 100)}%` }" /><b>{{ row.count }}</b>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="音乐库关联" kicker="MUSIC LIBRARY" subtitle="SQL Server 只读；没有精确曲目匹配时保持 null。">
            <div class="library-card">
              <strong>{{ data.library.song_count ?? '—' }}</strong>
              <span>traditional_song 曲目</span>
              <p>{{ data.library.note }}</p>
              <div class="library-kv"><span>映射案例</span><b>{{ data.library.mapped_count }} / {{ data.library.mapping_count }}</b></div>
              <div class="library-kv"><span>表结构</span><b>{{ data.library.status }}</b></div>
              <div class="library-kv"><span>分析表案例</span><b>{{ data.analysis_db.case_count ?? '—' }}</b></div>
              <div class="library-kv"><span>分析表评分</span><b>{{ data.analysis_db.score_count ?? '—' }}（null {{ data.analysis_db.null_score_count ?? '—' }}）</b></div>
              <div class="library-kv"><span>分析表来源</span><b>{{ data.analysis_db.source_count ?? '—' }}</b></div>
            </div>
          </SectionCard>
        </div>

        <SectionCard title="指标覆盖与门槛" kicker="INDICATOR GATE" subtitle="n 是独立案例数；n<5 不进入相关分析，n<20 不排序。">
          <div class="indicator-grid">
            <article v-for="item in data.indicators" :key="item.indicator_id" class="indicator-card">
              <div><b>{{ item.label }}</b><span>{{ item.n }} / {{ data.case_count }}</span></div>
              <strong>{{ item.mean_score === null ? '—' : item.mean_score.toFixed(2) }}</strong>
              <div class="indicator-track"><i :style="{ width: `${item.coverage_rate * 100}%` }" /></div>
              <small>{{ item.status_label }} · 缺失 {{ item.missing_count }} · 覆盖 {{ (item.coverage_rate * 100).toFixed(0) }}%</small>
            </article>
          </div>
        </SectionCard>

        <SectionCard title="成对 Spearman 相关" kicker="PAIRWISE CORRELATION" subtitle="仅当成对完整案例 n≥5 时计算；探索性，不作因果。">
          <div class="matrix-scroll">
            <table class="corr-table">
              <thead>
                <tr><th></th><th v-for="item in data.indicators" :key="item.indicator_id">{{ item.label.slice(0, 4) }}</th></tr>
              </thead>
              <tbody>
                <tr v-for="row in data.indicators" :key="row.indicator_id">
                  <th>{{ row.label }}</th>
                  <td
                    v-for="col in data.indicators"
                    :key="col.indicator_id"
                    :class="cell(row.indicator_id, col.indicator_id).status"
                    :title="`n=${cell(row.indicator_id, col.indicator_id).n}`"
                  >
                    {{ cell(row.indicator_id, col.indicator_id).value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="matrix-note">
            可用成对相关 {{ usableCorrelations.length }} / {{ data.correlations.length }} 对；空白为 n<5 或无法计算。相关系数不等于因果。
          </p>
        </SectionCard>

        <SectionCard title="数据血缘与边界" kicker="LINEAGE" subtitle="研究数据独立存储，业务库只读关联。">
          <div class="lineage-grid">
            <div><b>研究数据</b><span>research/data/{{ data.data_version }} → 案例/评分/来源</span></div>
            <div><b>分析数据集</b><span>research/analysis/v1.1-case-dataset.csv（v1.1 参考）</span></div>
            <div><b>业务库</b><span>traditional_song 只读；未改表结构</span></div>
            <div><b>映射</b><span>music_id 精确匹配；当前 0 条</span></div>
          </div>
          <p class="lineage-note">不按乐器、国家或活动规模推断音乐与案例关联；没有精确曲目匹配时保持 null。</p>
        </SectionCard>
      </template>
    </main>
  </div>
</template>

<style scoped>
.mining-page { min-height: 100vh; color: #e8f1ed; }
.mining-shell { max-width: 1400px; margin: 0 auto; padding: 42px 36px 70px; }
.mining-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; padding-bottom: 24px; border-bottom: 1px solid rgba(159,198,181,.18); }
.mining-eyebrow { margin: 0 0 10px; color: #8fc7b1; font-size: 10px; letter-spacing: .16em; }
.mining-hero h1 { margin: 0; font-family: 'Songti SC','SimSun',serif; font-size: clamp(38px,4.5vw,54px); font-weight: 500; }
.mining-desc { max-width: 760px; margin: 16px 0 0; color: #9bb7ad; font-size: 12px; line-height: 1.9; }
.hero-badge { display: flex; align-items: flex-end; flex-direction: column; gap: 8px; color: #6f8c81; font-size: 9px; }
.mining-state { padding: 80px 0; color: #9bb7ad; text-align: center; }
.mining-state.error button { margin-top: 12px; padding: 7px 12px; border: 1px solid rgba(217,194,138,.3); background: transparent; color: #d9c28a; }
.metric-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 10px; margin-top: 16px; }
.metric { padding: 14px 16px; border: 1px solid rgba(159,198,181,.14); border-radius: 7px; background: rgba(5,25,22,.34); }
.metric strong { display: block; color: #e8d4a8; font-family: 'Songti SC','SimSun',serif; font-size: 28px; font-weight: 500; }
.metric span { color: #c9d8d1; font-size: 10px; }
.metric small { display: block; margin-top: 4px; color: #6f8c81; font-size: 8px; }
.mining-note { margin: 14px 0 0; padding: 13px 15px; border-left: 2px solid rgba(217,194,138,.45); background: rgba(49,42,27,.22); }
.mining-note b { color: #d9c28a; font-size: 10px; }
.mining-note p { margin: 7px 0 0; color: #9bb7ad; font-size: 10px; line-height: 1.8; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px; }
.table-scroll,.matrix-scroll { overflow-x: auto; }
.mining-table,.corr-table { width: 100%; border-collapse: collapse; font-size: 9px; }
.mining-table th,.mining-table td { padding: 9px 8px; border-bottom: 1px solid rgba(159,198,181,.1); text-align: left; vertical-align: top; }
.mining-table th { color: #6f8c81; font-weight: 400; white-space: nowrap; }
.mining-table td { color: #b6c9c1; }
.mining-table td b { color: #d9c28a; font-family: 'Consolas',monospace; font-size: 8px; }
.mining-table td span,.mining-table td small { display: block; margin-top: 3px; color: #78948a; font-size: 8px; }
.dist-block { margin-top: 10px; }
.dist-block > p { margin: 0 0 6px; color: #8fc7b1; font-size: 9px; }
.dist-row { display: flex; align-items: center; gap: 6px; margin: 5px 0; color: #9bb7ad; font-size: 8px; }
.dist-row span { flex: 0 0 82px; }
.dist-row i { display: block; height: 4px; border-radius: 3px; background: #5ea68c; }
.dist-row b { margin-left: auto; color: #d9c28a; font-weight: 500; }
.library-card { padding: 14px; border: 1px solid rgba(159,198,181,.14); border-radius: 7px; background: rgba(5,25,22,.34); }
.library-card > strong { color: #e8d4a8; font-size: 30px; font-family: 'Songti SC',serif; }
.library-card > span { margin-left: 8px; color: #9bb7ad; font-size: 9px; }
.library-card p { margin: 10px 0 12px; color: #8fa99f; font-size: 9px; line-height: 1.7; }
.library-kv { display: flex; justify-content: space-between; padding-top: 7px; border-top: 1px solid rgba(159,198,181,.1); color: #78948a; font-size: 8px; }
.library-kv b { color: #c9d8d1; font-weight: 500; }
.indicator-grid { display: grid; grid-template-columns: repeat(5,minmax(0,1fr)); gap: 8px; }
.indicator-card { padding: 11px; border: 1px solid rgba(159,198,181,.13); border-radius: 6px; background: rgba(5,25,22,.34); }
.indicator-card > div:first-child { display: flex; justify-content: space-between; gap: 5px; color: #c9d8d1; font-size: 9px; }
.indicator-card > div:first-child span { color: #6f8c81; font-size: 8px; }
.indicator-card > strong { display: block; margin-top: 8px; color: #e8d4a8; font-size: 20px; font-weight: 500; }
.indicator-track { height: 3px; margin-top: 5px; border-radius: 3px; background: rgba(159,198,181,.1); }
.indicator-track i { display: block; height: 100%; background: #5ea68c; }
.indicator-card small { display: block; margin-top: 6px; color: #6f8c81; font-size: 8px; line-height: 1.5; }
.corr-table th,.corr-table td { padding: 7px 5px; border: 1px solid rgba(159,198,181,.08); text-align: center; white-space: nowrap; }
.corr-table thead th,.corr-table tbody th { color: #78948a; font-size: 8px; font-weight: 400; }
.corr-table td { color: #8fa99f; font-family: 'Consolas',monospace; font-size: 8px; }
.corr-table td.exploratory { color: #d9c28a; background: rgba(217,194,138,.07); }
.corr-table td.insufficient { color: #4f6a60; }
.corr-table td.diagonal { color: #8fc7b1; background: rgba(143,199,177,.08); }
.matrix-note,.lineage-note { margin: 10px 0 0; color: #6f8c81; font-size: 9px; line-height: 1.7; }
.lineage-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 8px; }
.lineage-grid > div { padding: 10px; border: 1px solid rgba(159,198,181,.12); border-radius: 5px; }
.lineage-grid b { display: block; color: #8fc7b1; font-size: 9px; font-weight: 500; }
.lineage-grid span { display: block; margin-top: 5px; color: #78948a; font-size: 8px; line-height: 1.6; }
@media (max-width: 1000px) {
  .metric-grid,.indicator-grid,.lineage-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 620px) {
  .mining-shell { padding: 28px 16px 56px; }
  .mining-hero { align-items: flex-start; flex-direction: column; }
  .hero-badge { align-items: flex-start; }
  .metric-grid,.indicator-grid,.lineage-grid { grid-template-columns: 1fr; }
  .mining-table { min-width: 760px; }
  .corr-table { min-width: 700px; }
}
</style>
