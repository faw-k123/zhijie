<script setup lang="ts">
import { computed } from 'vue'
import type { ResearchSample } from '@/types/research'

const props = defineProps<{
  sample?: ResearchSample | null
  compact?: boolean
  mode?: 'sample' | 'library' | 'strict-progress'
}>()

const label = computed(() => {
  const sample = props.sample
  if (!sample) return '状态加载中'
  const fraction = `${sample.n}/${sample.target}`
  if (props.mode === 'library') return `案例库收录 ${sample.n} 例`
  if (props.mode === 'strict-progress') return `严格样本建设 · ${fraction}`
  if (sample.status === 'empty') return '暂无案例'
  if (sample.status === 'insufficient') return `证据不足 · ${fraction}`
  if (sample.status === 'exploratory') return `探索性样本 · ${fraction}`
  return `描述性样本 · ${fraction}`
})

const statusClass = computed(() => `sample-${props.sample?.status || 'loading'}`)
</script>

<template>
  <span
    class="sample-badge"
    :class="[statusClass, { compact }]"
    :title="sample?.label || '研究样本状态'"
  >
    <i aria-hidden="true" />
    {{ label }}
  </span>
</template>

<style scoped>
.sample-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 30px;
  padding: 5px 11px;
  border-radius: 999px;
  border: 1px solid rgba(217, 194, 138, 0.36);
  background: rgba(217, 194, 138, 0.1);
  color: #e8d4a8;
  font-size: 12px;
  line-height: 1;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.sample-badge i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 3px rgba(217, 194, 138, 0.12);
}

.sample-insufficient {
  color: #f0bf86;
  border-color: rgba(240, 191, 134, 0.42);
  background: rgba(180, 104, 45, 0.14);
}

.sample-insufficient i {
  box-shadow: 0 0 0 3px rgba(240, 191, 134, 0.13);
}

.sample-exploratory {
  color: #a7d8c3;
  border-color: rgba(143, 199, 177, 0.38);
  background: rgba(94, 166, 140, 0.12);
}

.sample-descriptive {
  color: #a9d9b8;
  border-color: rgba(143, 199, 177, 0.45);
  background: rgba(94, 166, 140, 0.17);
}

.sample-empty,
.sample-loading {
  color: #a7beb5;
  border-color: rgba(159, 198, 181, 0.25);
  background: rgba(159, 198, 181, 0.06);
}

.compact {
  min-height: 24px;
  padding: 3px 8px;
  font-size: 11px;
}
</style>
