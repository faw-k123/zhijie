<script setup lang="ts">
withDefaults(defineProps<{
  kind?: 'loading' | 'error' | 'empty' | 'pending'
  title: string
  message?: string
  retryable?: boolean
  retryLabel?: string
  compact?: boolean
}>(), {
  kind: 'empty',
  message: '',
  retryable: false,
  retryLabel: '重新加载',
  compact: false,
})

defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="research-state" :class="[`state-${kind}`, { compact }]">
    <span v-if="kind === 'loading'" class="state-spinner" aria-hidden="true" />
    <span v-else class="state-mark" aria-hidden="true">{{ kind === 'error' ? '!' : kind === 'pending' ? '·' : '—' }}</span>
    <div>
      <h3>{{ title }}</h3>
      <p v-if="message">{{ message }}</p>
      <button v-if="retryable" type="button" class="state-retry" @click="$emit('retry')">
        {{ retryLabel }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.research-state {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-height: 150px;
  padding: 28px 6px;
}

.research-state.compact {
  min-height: 0;
  padding: 10px 0;
}

.state-mark,
.state-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  margin-top: 2px;
  border: 1px solid rgba(159, 198, 181, 0.3);
  border-radius: 50%;
  color: #8fc7b1;
  font-size: 17px;
  line-height: 1;
}

.state-error .state-mark {
  color: #e2a276;
  border-color: rgba(226, 162, 118, 0.45);
}

.state-pending .state-mark {
  color: #d9c28a;
  border-color: rgba(217, 194, 138, 0.42);
}

.state-spinner {
  border-color: rgba(143, 199, 177, 0.2);
  border-top-color: #8fc7b1;
  animation: spin 0.9s linear infinite;
}

.research-state h3 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 18px;
  font-weight: 500;
}

.research-state p {
  max-width: 680px;
  margin: 8px 0 0;
  color: #8fa99f;
  font-size: 12px;
  line-height: 1.75;
}

.state-retry {
  margin-top: 16px;
  padding: 8px 14px;
  border: 1px solid rgba(143, 199, 177, 0.4);
  border-radius: 5px;
  background: rgba(143, 199, 177, 0.08);
  color: #cfe3da;
  font-size: 12px;
  cursor: pointer;
}

.state-retry:hover {
  background: rgba(143, 199, 177, 0.14);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .state-spinner { animation: none; }
}
</style>
