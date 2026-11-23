<script setup lang="ts">
defineProps<{
  title: string
  kicker?: string
  subtitle?: string
  tone?: 'default' | 'warning' | 'quiet'
}>()
</script>

<template>
  <section class="research-card" :class="tone || 'default'">
    <header class="card-head">
      <div>
        <p v-if="kicker" class="card-kicker">{{ kicker }}</p>
        <h2>{{ title }}</h2>
        <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="card-actions">
        <slot name="actions" />
      </div>
    </header>
    <div class="card-body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.research-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  border: 1px solid rgba(159, 198, 181, 0.19);
  border-radius: 14px;
  background:
    linear-gradient(155deg, rgba(13, 49, 44, 0.78), rgba(6, 27, 24, 0.9)),
    #071c19;
  overflow: hidden;
}

.research-card.warning {
  border-color: rgba(217, 194, 138, 0.26);
}

.research-card.quiet {
  background: rgba(6, 27, 24, 0.62);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 22px 16px;
  border-bottom: 1px solid rgba(159, 198, 181, 0.12);
}

.card-kicker {
  margin: 0 0 8px;
  color: #8fc7b1;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.card-head h2 {
  margin: 0;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 21px;
  font-weight: 500;
  letter-spacing: 0.03em;
}

.card-subtitle {
  max-width: 560px;
  margin: 7px 0 0;
  color: #8fa99f;
  font-size: 12px;
  line-height: 1.65;
}

.card-actions {
  flex-shrink: 0;
}

.card-body {
  flex: 1;
  min-width: 0;
  padding: 20px 22px 22px;
}
</style>
