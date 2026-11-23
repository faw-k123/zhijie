<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import erhuImage from '@/assets/images/poster/乐器/二胡.jpg'
import guzhengImage from '@/assets/images/poster/乐器/古筝.jpg'
import type { ResearchCaseSummary } from '@/types/research'

const props = defineProps<{
  item: ResearchCaseSummary
}>()

const instrumentImages: Record<string, string> = {
  二胡: erhuImage,
  古筝: guzhengImage,
}

const cover = computed(() => {
  if (props.item.cover_url) return props.item.cover_url
  const first = props.item.instrument[0] ?? ''
  return instrumentImages[first] || ''
})

const detailTo = computed(() => ({
  name: 'global-case-detail',
  params: { caseId: props.item.case_id },
}))

function formatScore(score: number | null) {
  return score === null ? '—' : score.toFixed(2)
}

function tags(item: ResearchCaseSummary) {
  return [...item.era_theme, ...item.cultural_hooks].slice(0, 4)
}
</script>

<template>
  <article class="case-row">
    <RouterLink :to="detailTo" class="case-cover" :aria-label="`查看 ${item.case_id} 详情`">
      <img v-if="cover" :src="cover" :alt="`${item.instrument.join('、')} 乐器图`" loading="lazy" />
      <span v-else class="cover-fallback">{{ item.instrument[0]?.slice(0, 1) || '乐' }}</span>
      <span class="cover-id">{{ item.case_id }}</span>
    </RouterLink>

    <div class="case-main">
      <div class="case-top">
        <span class="case-country">{{ item.country }}</span>
        <span class="case-sep">/</span>
        <span>{{ item.region }}<template v-if="item.subregion"> · {{ item.subregion }}</template></span>
        <span class="case-grade">证据 {{ item.review_status }}</span>
      </div>

      <h2>
        <RouterLink :to="detailTo">{{ item.performer }}</RouterLink>
      </h2>

      <p class="case-meta">
        {{ item.instrument.join(' / ') }} · {{ item.music_type }} · {{ item.event_date_text }}
      </p>
      <p class="case-summary">{{ item.summary }}</p>

      <div class="case-tags">
        <span v-for="tag in tags(item)" :key="tag">{{ tag }}</span>
      </div>
    </div>

    <div class="case-score">
      <strong>{{ formatScore(item.mean_score) }}</strong>
      <span>/ {{ item.score_scale }} 已评分均值</span>
      <small>{{ item.valid_count }} 项有效 · {{ item.missing_count }} 项未知</small>
    </div>

    <div class="case-side">
      <span class="source-count">{{ item.source_count }} 条来源</span>
      <RouterLink :to="detailTo" class="detail-link">查看详情 →</RouterLink>
    </div>
  </article>
</template>

<style scoped>
.case-row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr) 122px 108px;
  gap: 20px;
  align-items: center;
  padding: 18px;
  border: 1px solid rgba(159, 198, 181, 0.17);
  border-radius: 12px;
  background:
    linear-gradient(145deg, rgba(13, 49, 44, 0.72), rgba(6, 27, 24, 0.86)),
    #071c19;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.case-row:hover {
  border-color: rgba(143, 199, 177, 0.34);
  transform: translateY(-2px);
}

.case-cover {
  position: relative;
  display: block;
  width: 112px;
  height: 112px;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(145deg, #153f38, #091f1c);
}

.case-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: saturate(0.72) contrast(1.06) brightness(0.82);
}

.cover-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  color: #8fc7b1;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 34px;
}

.cover-id {
  position: absolute;
  left: 7px;
  bottom: 7px;
  padding: 3px 6px;
  border-radius: 3px;
  background: rgba(3, 22, 19, 0.8);
  color: #d9c28a;
  font-family: 'Consolas', monospace;
  font-size: 9px;
  letter-spacing: 0.06em;
}

.case-main {
  min-width: 0;
}

.case-top {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  color: #78948a;
  font-size: 10px;
}

.case-country {
  color: #8fc7b1;
}

.case-sep {
  color: #4f6a60;
}

.case-grade {
  margin-left: 4px;
  padding: 3px 7px;
  border: 1px solid rgba(217, 194, 138, 0.3);
  border-radius: 999px;
  color: #d9c28a;
}

.case-main h2 {
  margin: 8px 0 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 21px;
  font-weight: 500;
  line-height: 1.4;
}

.case-main h2 a {
  color: inherit;
  text-decoration: none;
}

.case-main h2 a:hover {
  color: #d9c28a;
}

.case-meta {
  margin: 7px 0 0;
  color: #8fa99f;
  font-size: 10px;
  line-height: 1.6;
}

.case-summary {
  display: -webkit-box;
  margin: 9px 0 0;
  overflow: hidden;
  color: #b6c9c1;
  font-size: 12px;
  line-height: 1.7;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.case-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 10px;
}

.case-tags span {
  padding: 3px 6px;
  border: 1px solid rgba(159, 198, 181, 0.14);
  border-radius: 3px;
  color: #78948a;
  font-size: 9px;
}

.case-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  padding-left: 16px;
  border-left: 1px solid rgba(159, 198, 181, 0.12);
}

.case-score strong {
  color: #e8d4a8;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 30px;
  font-weight: 500;
  line-height: 1;
}

.case-score span {
  color: #8fa99f;
  font-size: 9px;
}

.case-score small {
  color: #6f8c81;
  font-size: 9px;
  text-align: right;
}

.case-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.source-count {
  color: #78948a;
  font-size: 10px;
}

.detail-link {
  color: #8fc7b1;
  font-size: 11px;
  text-decoration: none;
  white-space: nowrap;
}

.detail-link:hover {
  color: #d9c28a;
}

@media (max-width: 1080px) {
  .case-row {
    grid-template-columns: 96px minmax(0, 1fr) 110px;
  }

  .case-cover {
    width: 96px;
    height: 96px;
  }

  .case-side {
    grid-column: 2 / -1;
    align-items: flex-start;
    flex-direction: row;
    justify-content: space-between;
    padding-top: 10px;
    border-top: 1px solid rgba(159, 198, 181, 0.1);
  }
}

@media (max-width: 680px) {
  .case-row {
    grid-template-columns: 72px minmax(0, 1fr);
    gap: 12px;
    padding: 14px;
  }

  .case-cover {
    width: 72px;
    height: 72px;
  }

  .case-main h2 {
    font-size: 17px;
  }

  .case-score {
    grid-column: 1 / -1;
    align-items: flex-start;
    flex-direction: row;
    gap: 8px;
    padding: 10px 0 0;
    border-top: 1px solid rgba(159, 198, 181, 0.1);
    border-left: 0;
  }

  .case-score strong {
    font-size: 24px;
  }

  .case-score span,
  .case-score small {
    align-self: center;
  }

  .case-side {
    grid-column: 1 / -1;
  }
}
</style>
