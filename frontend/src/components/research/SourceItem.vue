<script setup lang="ts">
import type { ResearchSource } from '@/types/research'

defineProps<{
  source: ResearchSource
}>()

function safeHost(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
</script>

<template>
  <article :id="`source-${source.source_id}`" class="source-item">
    <div class="source-head">
      <span class="source-id">{{ source.source_id }}</span>
      <span class="source-type">{{ source.source_type }}</span>
      <span class="source-reliability">可靠性 {{ source.reliability }}</span>
      <span v-if="source.is_primary" class="source-primary">主要来源</span>
    </div>

    <h3>{{ source.title }}</h3>
    <p class="source-publisher">{{ source.publisher }}</p>
    <p class="source-support">{{ source.supports }}</p>

    <div class="source-foot">
      <span>发布 {{ source.published_at || '未标注' }}</span>
      <span>访问 {{ source.accessed_at }}</span>
      <a
        v-if="source.url"
        :href="source.url"
        target="_blank"
        rel="noopener noreferrer"
        class="source-link"
        :title="source.url"
      >
        打开来源 · {{ safeHost(source.url) }} ↗
      </a>
      <span v-else-if="source.citation" class="source-citation">{{ source.citation }}</span>
      <span v-if="source.notes" class="source-notes">{{ source.notes }}</span>
    </div>
  </article>
</template>

<style scoped>
.source-item {
  padding: 17px 18px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 9px;
  background: rgba(5, 25, 22, 0.4);
  scroll-margin-top: 110px;
}

.source-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
}

.source-id {
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
  letter-spacing: 0.05em;
}

.source-type,
.source-reliability,
.source-primary {
  padding: 2px 6px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 3px;
  color: #78948a;
  font-size: 8px;
}

.source-primary {
  border-color: rgba(217, 194, 138, 0.24);
  color: #b99767;
}

.source-item h3 {
  margin: 11px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 17px;
  font-weight: 500;
  line-height: 1.5;
}

.source-publisher {
  margin: 5px 0 0;
  color: #8fc7b1;
  font-size: 10px;
}

.source-support {
  margin: 9px 0 0;
  color: #9bb7ad;
  font-size: 11px;
  line-height: 1.7;
}

.source-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  color: #6f8c81;
  font-size: 9px;
}

.source-link {
  color: #8fc7b1;
  text-decoration: none;
}

.source-link:hover {
  color: #d9c28a;
}

.source-notes,
.source-citation {
  color: #b99767;
}
</style>
