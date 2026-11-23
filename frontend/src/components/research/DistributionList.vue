<script setup lang="ts">
import { computed } from 'vue'
import type { ResearchDistributionItem } from '@/types/research'

const props = withDefaults(defineProps<{
  items: ResearchDistributionItem[]
  emptyText?: string
  countLabel?: string
  showBar?: boolean
}>(), {
  emptyText: '暂无分布数据',
  countLabel: '案例',
  showBar: true,
})

const maxCount = computed(() => Math.max(1, ...props.items.map((item) => item.count)))
</script>

<template>
  <div v-if="items.length" class="distribution-list">
    <div v-for="item in items" :key="item.key" class="distribution-row">
      <span class="distribution-label">{{ item.key }}</span>
      <span v-if="showBar" class="distribution-track" aria-hidden="true">
        <i :style="{ width: `${(item.count / maxCount) * 100}%` }" />
      </span>
      <strong class="distribution-count">{{ item.count }}</strong>
    </div>
    <p class="distribution-note">仅统计已纳入案例的{{ countLabel }}，不代表偏好或传播效果排名。</p>
  </div>
  <p v-else class="distribution-empty">{{ emptyText }}</p>
</template>

<style scoped>
.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.distribution-row {
  display: grid;
  grid-template-columns: minmax(96px, 0.8fr) minmax(80px, 1.4fr) 32px;
  align-items: center;
  gap: 12px;
  min-height: 42px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.1);
}

.distribution-row:last-of-type {
  border-bottom: 0;
}

.distribution-label {
  color: #c9d8d1;
  font-size: 13px;
}

.distribution-track {
  display: block;
  height: 5px;
  border-radius: 999px;
  background: rgba(159, 198, 181, 0.1);
  overflow: hidden;
}

.distribution-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5ea68c, #8fc7b1);
}

.distribution-count {
  color: #e8d4a8;
  font-size: 15px;
  font-weight: 500;
  text-align: right;
}

.distribution-note {
  margin: 15px 0 0;
  color: #78948a;
  font-size: 11px;
  line-height: 1.65;
}

.distribution-empty {
  margin: 0;
  padding: 28px 0;
  color: #8fa99f;
  font-size: 13px;
  text-align: center;
}
</style>
