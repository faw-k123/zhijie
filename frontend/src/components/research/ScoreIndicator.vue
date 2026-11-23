<script setup lang="ts">
import { computed } from 'vue'
import type { ResearchCodingIndicator } from '@/types/research'

const props = defineProps<{
  indicator: ResearchCodingIndicator
  index: number
}>()

const hasScore = computed(() => props.indicator.score !== null)
const percent = computed(() => {
  if (!hasScore.value || props.indicator.score === null) return 0
  return (props.indicator.score / 3) * 100
})

function sourceHref(sourceId: string) {
  return `#source-${sourceId}`
}

const approvalLabel = computed(() => {
  const value = props.indicator.approval_status
  if (value === 'approved') return '已批准'
  if (value === 'approved_revoked') return '已批准撤回'
  if (value === 'not_applicable') return '不适用'
  if (value === 'pending') return '待审批'
  return '未记录'
})

const scoreStatusLabel = computed(() => {
  const value = props.indicator.score_status
  if (value === 'approved') return '评分已生效'
  if (value === 'revoked_approved') return '评分已撤回'
  if (value === 'null') return '未知'
  if (value) return value
  return '未记录'
})
</script>

<template>
  <article class="indicator" :class="{ unknown: !hasScore, partial: hasScore && indicator.score !== null && indicator.score < 2 }">
    <div class="indicator-head">
      <span class="indicator-index">{{ String(index).padStart(2, '0') }}</span>
      <h3>{{ indicator.label }}</h3>
      <strong v-if="hasScore">{{ indicator.score }}<small>/3</small></strong>
      <strong v-else class="unknown-score">未知</strong>
    </div>

    <div class="indicator-track" aria-hidden="true">
      <i :style="{ width: `${percent}%` }" />
    </div>

    <p class="indicator-evidence">
      {{ indicator.evidence || (hasScore ? '未记录证据说明。' : '该指标暂无可用证据。') }}
    </p>

    <div class="indicator-gov">
      <span class="gov-chip" :class="`gov-${indicator.approval_status || 'missing'}`">{{ approvalLabel }}</span>
      <span class="gov-chip subtle">{{ scoreStatusLabel }}</span>
      <span v-if="indicator.approver || indicator.approval_date" class="gov-meta">
        {{ indicator.approver || '未记录' }}<template v-if="indicator.approval_date"> · {{ indicator.approval_date }}</template>
      </span>
    </div>

    <div class="indicator-foot">
      <template v-if="indicator.source_ids.length">
        <span class="source-label">来源</span>
        <a
          v-for="sourceId in indicator.source_ids"
          :key="sourceId"
          :href="sourceHref(sourceId)"
          class="source-chip"
        >
          {{ sourceId }}
        </a>
      </template>
      <span v-else class="source-empty">无来源</span>
      <span v-if="!hasScore && indicator.missing_reason" class="missing-reason">
        {{ indicator.missing_reason }}
      </span>
    </div>
  </article>
</template>

<style scoped>
.indicator {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 17px 18px;
  border: 1px solid rgba(159, 198, 181, 0.15);
  border-radius: 9px;
  background: rgba(5, 25, 22, 0.44);
}

.indicator.unknown {
  border-style: dashed;
  border-color: rgba(217, 194, 138, 0.24);
}

.indicator.partial {
  border-color: rgba(226, 162, 118, 0.22);
}

.indicator-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.indicator-index {
  color: #6f8c81;
  font-family: 'Consolas', monospace;
  font-size: 9px;
}

.indicator-head h3 {
  flex: 1;
  margin: 0;
  color: #d7e4dd;
  font-size: 12px;
  font-weight: 500;
}

.indicator-head strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 22px;
  font-weight: 500;
  line-height: 1;
}

.indicator-head strong small {
  color: #78948a;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 9px;
}

.indicator-head .unknown-score {
  color: #b99767;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.indicator-track {
  height: 3px;
  margin-top: 12px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.indicator-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.indicator.unknown .indicator-track i {
  background: transparent;
}

.indicator.partial .indicator-track i {
  background: #b99767;
}

.indicator-evidence {
  margin: 12px 0 0;
  color: #9bb7ad;
  font-size: 11px;
  line-height: 1.75;
}

.indicator-foot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
  padding-top: 13px;
}

.source-label,
.indicator-gov {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin: 9px 0 2px;
}

.gov-chip {
  padding: 3px 7px;
  border: 1px solid rgba(159, 198, 181, 0.2);
  border-radius: 999px;
  color: #9bb7ad;
  font-size: 8px;
  line-height: 1.2;
}

.gov-chip.subtle {
  border-color: rgba(159, 198, 181, 0.1);
  color: #78948a;
}

.gov-approved {
  border-color: rgba(143, 199, 177, 0.35);
  color: #8fc7b1;
}

.gov-approved_revoked {
  border-color: rgba(226, 162, 118, 0.35);
  color: #d7a17a;
}

.gov-pending {
  border-color: rgba(217, 194, 138, 0.3);
  color: #d9c28a;
}

.gov-not_applicable {
  color: #6f8c81;
}

.gov-meta {
  color: #6f8c81;
  font-size: 8px;
}

.source-empty {
  color: #6f8c81;
  font-size: 9px;
}

.source-chip {
  padding: 2px 5px;
  border: 1px solid rgba(143, 199, 177, 0.19);
  border-radius: 3px;
  color: #8fc7b1;
  font-family: 'Consolas', monospace;
  font-size: 8px;
  text-decoration: none;
}

.source-chip:hover {
  border-color: rgba(217, 194, 138, 0.4);
  color: #d9c28a;
}

.missing-reason {
  width: 100%;
  color: #b99767;
  font-size: 9px;
  line-height: 1.6;
}
</style>
