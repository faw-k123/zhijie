<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { ResearchCaseSummary } from '@/types/research'

defineProps<{
  item: ResearchCaseSummary
}>()

function formatScore(score: number | null) {
  return score === null ? '—' : score.toFixed(2)
}

function primaryTags(item: ResearchCaseSummary) {
  return [...item.era_theme, ...item.cultural_hooks].slice(0, 3)
}
</script>

<template>
  <article class="case-preview">
    <div class="case-top">
      <span class="case-id">{{ item.case_id }}</span>
      <span class="case-grade">证据 {{ item.review_status }}</span>
    </div>

    <h3>{{ item.performer }}</h3>
    <p class="case-meta">
      {{ item.country }} · {{ item.region }}<span v-if="item.subregion"> / {{ item.subregion }}</span>
    </p>
    <p class="case-instrument">{{ item.instrument.join(' / ') }}</p>
    <p class="case-summary">{{ item.summary }}</p>

    <div class="case-tags">
      <span v-for="tag in primaryTags(item)" :key="tag">{{ tag }}</span>
    </div>

    <div class="case-bottom">
      <div class="case-score">
        <strong>{{ formatScore(item.mean_score) }}</strong>
        <span>/ {{ item.score_scale }} 已评分均值</span>
      </div>
      <div class="case-sources">{{ item.source_count }} 条来源</div>
    </div>

    <RouterLink
      :to="{ name: 'global-case-detail', params: { caseId: item.case_id } }"
      class="case-detail"
    >
      查看案例详情 →
    </RouterLink>
  </article>
</template>

<style scoped>
.case-preview {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 340px;
  padding: 18px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 10px;
  background:
    linear-gradient(160deg, rgba(16, 58, 52, 0.58), rgba(5, 25, 22, 0.66)),
    #071c19;
}

.case-top,
.case-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.case-id {
  color: #8fc7b1;
  font-family: 'Consolas', 'SFMono-Regular', monospace;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.case-grade {
  padding: 3px 8px;
  border: 1px solid rgba(217, 194, 138, 0.3);
  border-radius: 999px;
  color: #d9c28a;
  font-size: 10px;
}

.case-preview h3 {
  margin: 16px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 20px;
  font-weight: 500;
  line-height: 1.4;
}

.case-meta {
  margin: 7px 0 0;
  color: #8fa99f;
  font-size: 11px;
}

.case-instrument {
  margin: 8px 0 0;
  color: #d9c28a;
  font-size: 12px;
  letter-spacing: 0.04em;
}

.case-summary {
  display: -webkit-box;
  margin: 14px 0 0;
  overflow: hidden;
  color: #b6c9c1;
  font-size: 12px;
  line-height: 1.75;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.case-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 15px 0 0;
}

.case-tags span {
  padding: 4px 7px;
  border: 1px solid rgba(159, 198, 181, 0.16);
  border-radius: 4px;
  color: #8fa99f;
  font-size: 10px;
}

.case-bottom {
  margin-top: auto;
  padding-top: 18px;
}

.case-score strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 24px;
  font-weight: 500;
}

.case-score span,
.case-sources {
  color: #78948a;
  font-size: 10px;
}

.case-detail {
  display: block;
  width: 100%;
  margin-top: 13px;
  padding: 8px 10px;
  border: 1px solid rgba(159, 198, 181, 0.22);
  border-radius: 4px;
  background: rgba(143, 199, 177, 0.04);
  color: #8fc7b1;
  font-size: 11px;
  text-align: center;
  text-decoration: none;
  transition: border-color 0.2s ease, color 0.2s ease;
}

.case-detail:hover {
  border-color: rgba(217, 194, 138, 0.38);
  color: #d9c28a;
}
</style>
