<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pages: number
  total: number
  pageSize: number
}>()

const emit = defineEmits<{
  change: [page: number]
}>()

const pageNumbers = computed(() => {
  if (props.pages <= 1) return [1]
  const start = Math.max(1, Math.min(props.page - 2, props.pages - 4))
  const end = Math.min(props.pages, start + 4)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

function go(page: number) {
  if (page < 1 || page > props.pages || page === props.page) return
  emit('change', page)
}
</script>

<template>
  <nav class="pagination" aria-label="案例分页">
    <span class="page-summary">
      共 {{ total }} 例 · 第 {{ page || 1 }} / {{ Math.max(1, pages) }} 页
    </span>
    <div class="page-controls">
      <button type="button" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
      <button
        v-for="number in pageNumbers"
        :key="number"
        type="button"
        class="page-number"
        :class="{ active: number === page }"
        :aria-current="number === page ? 'page' : undefined"
        @click="go(number)"
      >
        {{ number }}
      </button>
      <button type="button" :disabled="page >= pages" @click="go(page + 1)">下一页</button>
    </div>
  </nav>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding-top: 18px;
}

.page-summary {
  color: #78948a;
  font-size: 11px;
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-controls button {
  min-width: 34px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(159, 198, 181, 0.2);
  border-radius: 4px;
  background: transparent;
  color: #8fa99f;
  font-size: 11px;
  cursor: pointer;
}

.page-controls button:hover:not(:disabled),
.page-controls button.active {
  border-color: rgba(143, 199, 177, 0.46);
  background: rgba(143, 199, 177, 0.1);
  color: #d9c28a;
}

.page-controls button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

@media (max-width: 680px) {
  .pagination {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
