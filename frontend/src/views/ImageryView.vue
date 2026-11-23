<script setup lang="ts">
import AppNav from '@/components/AppNav.vue'
</script>

<template>
  <div class="page">
    <AppNav />
    <div class="layout">
      <section class="placeholder">
        <h2>国风意象译析</h2>
        <p>该模块正在开发中，敬请期待。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
  display: flex;
  flex-direction: column;
}

.layout {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 56px);
  padding: 1rem;
}

.placeholder {
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  padding: 3rem 4rem;
  text-align: center;
}

h2 {
  margin: 0 0 1rem;
  color: #8b3a2a;
  letter-spacing: 0.05em;
}

p {
  color: #5a4a3a;
  font-size: 0.95rem;
}
</style>
