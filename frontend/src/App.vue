<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterView, useRouter } from 'vue-router'

const router = useRouter()
const routeLoading = ref(true)
let loadingTimer: number | undefined

router.beforeEach(() => {
  routeLoading.value = true
})
router.afterEach(() => {
  window.clearTimeout(loadingTimer)
  loadingTimer = window.setTimeout(() => { routeLoading.value = false }, 420)
})
onMounted(() => {
  loadingTimer = window.setTimeout(() => { routeLoading.value = false }, 620)
})
</script>

<template>
  <Transition name="route-loader">
    <div v-if="routeLoading" class="route-loader" aria-live="polite">
      <div class="loader">
        <span class="loader-text">loading</span>
        <span class="load"></span>
      </div>
    </div>
  </Transition>
  <RouterView />
</template>
