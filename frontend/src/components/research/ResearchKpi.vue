<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  suffix?: string
  note?: string
  accent?: boolean
}>()
</script>

<template>
  <article class="kpi" :class="{ accent }">
    <p class="kpi-label">{{ label }}</p>
    <strong class="kpi-value">
      {{ value }}<small v-if="suffix">{{ suffix }}</small>
    </strong>
    <p v-if="note" class="kpi-note">{{ note }}</p>
  </article>
</template>

<style scoped>
.kpi {
  position: relative;
  min-height: 150px;
  padding: 22px 22px 18px;
  border: 1px solid rgba(159, 198, 181, 0.18);
  border-radius: 13px;
  background:
    linear-gradient(145deg, rgba(13, 49, 44, 0.88), rgba(6, 27, 24, 0.9)),
    #071c19;
  overflow: hidden;
}

.kpi::after {
  content: '';
  position: absolute;
  inset: auto -20% -70% 20%;
  height: 90%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(143, 199, 177, 0.12), transparent 68%);
  pointer-events: none;
}

.kpi.accent {
  border-color: rgba(217, 194, 138, 0.28);
  background:
    linear-gradient(145deg, rgba(53, 50, 35, 0.55), rgba(10, 35, 31, 0.92)),
    #071c19;
}

.kpi-label {
  margin: 0 0 18px;
  color: #a7beb5;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.kpi-value {
  position: relative;
  z-index: 1;
  display: block;
  color: #e8f1ed;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: clamp(38px, 4vw, 52px);
  font-weight: 500;
  line-height: 0.96;
  letter-spacing: 0.01em;
}

.kpi-value small {
  margin-left: 3px;
  color: #d9c28a;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 0.42em;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.kpi-note {
  position: relative;
  z-index: 1;
  margin: 13px 0 0;
  color: #8fa99f;
  font-size: 12px;
  line-height: 1.55;
}
</style>
