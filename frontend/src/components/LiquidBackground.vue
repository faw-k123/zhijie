<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  imageUrl: string
  metalness?: number
  roughness?: number
  displacementScale?: number
  enableChromaticAberration?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  metalness: 0.35,
  roughness: 0.45,
  displacementScale: 2,
  enableChromaticAberration: true
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let script: HTMLScriptElement | null = null

onMounted(() => {
  if (!canvasRef.value) return

  script = document.createElement('script')
  script.type = 'module'
  script.textContent = `
    import LiquidBackground from 'https://cdn.jsdelivr.net/npm/threejs-components@0.0.30/build/backgrounds/liquid1.min.js';
    const canvas = document.getElementById('liquid-refraction-canvas');
    if (canvas) {
      const app = LiquidBackground(canvas);
      app.loadImage('${props.imageUrl}');
      app.liquidPlane.material.metalness = ${props.metalness};
      app.liquidPlane.material.roughness = ${props.roughness};
      app.liquidPlane.uniforms.displacementScale.value = ${props.displacementScale};
      app.setRain(false);
      window.__liquidRefractionApp = app;
    }
  `
  document.body.appendChild(script)

  if (props.enableChromaticAberration) {
    let prevX = 0, prevY = 0, intensity = 1.5
    const onMouseMove = (e: MouseEvent) => {
      const speed = Math.sqrt((e.clientX - prevX) ** 2 + (e.clientY - prevY) ** 2)
      intensity = Math.min(1.5 + speed * 0.15, 8)
      prevX = e.clientX
      prevY = e.clientY
    }
    window.addEventListener('mousemove', onMouseMove)

    let animId: number
    const tick = () => {
      intensity = intensity > 1.5 ? intensity * 0.92 : 1.5
      const r = document.getElementById('ca-r')
      const b = document.getElementById('ca-b')
      if (r) r.setAttribute('dx', String(-intensity))
      if (b) b.setAttribute('dx', String(intensity))
      animId = requestAnimationFrame(tick)
    }
    tick()

    onUnmounted(() => {
      if ((window as any).__liquidRefractionApp?.dispose) {
        (window as any).__liquidRefractionApp.dispose()
      }
      script?.parentNode?.removeChild(script)
      window.removeEventListener('mousemove', onMouseMove)
      cancelAnimationFrame(animId)
    })
  }
})

watch(() => props.imageUrl, (newUrl) => {
  if ((window as any).__liquidRefractionApp?.dispose) {
    (window as any).__liquidRefractionApp.dispose()
  }
  script?.parentNode?.removeChild(script!)
  
  script = document.createElement('script')
  script.type = 'module'
  script.textContent = `
    import LiquidBackground from 'https://cdn.jsdelivr.net/npm/threejs-components@0.0.30/build/backgrounds/liquid1.min.js';
    const canvas = document.getElementById('liquid-refraction-canvas');
    const imageUrl = ${JSON.stringify(newUrl)};
    const metalness = ${props.metalness};
    const roughness = ${props.roughness};
    const displacementScale = ${props.displacementScale};
    if (canvas) {
      const app = LiquidBackground(canvas);
      app.loadImage(imageUrl);
      app.liquidPlane.material.metalness = metalness;
      app.liquidPlane.material.roughness = roughness;
      app.liquidPlane.uniforms.displacementScale.value = displacementScale;
      app.setRain(false);
      window.__liquidRefractionApp = app;
    }
  `
  document.body.appendChild(script)
})
</script>

<template>
  <div class="liquid-container">
    <svg v-if="enableChromaticAberration" style="position: absolute; width: 0; height: 0;">
      <defs>
        <filter id="ca" x="-5%" y="-5%" width="110%" height="110%">
          <feColorMatrix in="SourceGraphic" type="matrix"
            values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="red" />
          <feOffset id="ca-r" dx="-1.5" dy="0" in="red" result="red-out" />
          <feColorMatrix in="SourceGraphic" type="matrix"
            values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="green" />
          <feColorMatrix in="SourceGraphic" type="matrix"
            values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="blue" />
          <feOffset id="ca-b" dx="1.5" dy="0" in="blue" result="blue-out" />
          <feBlend in="red-out" in2="green" mode="screen" result="rg" />
          <feBlend in="rg" in2="blue-out" mode="screen" />
        </filter>
      </defs>
    </svg>
    <canvas
      ref="canvasRef"
      id="liquid-refraction-canvas"
      class="liquid-canvas"
      :style="{ filter: enableChromaticAberration ? 'url(#ca)' : undefined }"
    />
  </div>
</template>

<style scoped>
.liquid-container {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.liquid-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
</style>