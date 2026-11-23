<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'

interface WordItem { name: string; value: number }
const props = defineProps<{ words: WordItem[] }>()
const mountRef = ref<HTMLDivElement | null>(null)
const paused = ref(false)
const focusedWord = ref('')

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let cloudGroup: THREE.Group | null = null
let animationFrame = 0
let observer: ResizeObserver | null = null
let raycaster: THREE.Raycaster | null = null
let pointer: THREE.Vector2 | null = null
let hovered: THREE.Sprite | null = null
let reduceMotion = false
let dragging = false
let lastPointerX = 0
let lastPointerY = 0
let spinX = 0
let spinY = 0.0017

function makeTexture(label: string, strength: number) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')!
  const scale = window.devicePixelRatio > 1 ? 2 : 1
  canvas.width = 300 * scale
  canvas.height = 88 * scale
  ctx.scale(scale, scale)
  ctx.font = `${Math.round(23 + strength * 13)}px "Songti SC", "SimSun", serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.shadowColor = 'rgba(144, 215, 187, .45)'
  ctx.shadowBlur = 12
  ctx.fillStyle = '#dcece5'
  ctx.fillText(label, 150, 44)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  texture.minFilter = THREE.LinearFilter
  return texture
}

function clearCloud() {
  if (!cloudGroup) return
  for (const child of cloudGroup.children) {
    const sprite = child as THREE.Sprite
    sprite.material.map?.dispose()
    sprite.material.dispose()
  }
  cloudGroup.clear()
}

function buildCloud() {
  if (!cloudGroup) return
  clearCloud()
  const source = props.words.length ? props.words : [{ name: '静候数据', value: 1 }]
  const max = Math.max(...source.map((item) => Number(item.value) || 1))
  source.slice(0, 56).forEach((item, index, list) => {
    const y = 1 - (2 * (index + 0.5)) / list.length
    const radial = Math.sqrt(Math.max(0, 1 - y * y))
    const angle = index * Math.PI * (3 - Math.sqrt(5))
    const weight = Math.max(0.15, (Number(item.value) || 1) / max)
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
      map: makeTexture(item.name, weight), transparent: true, depthWrite: false,
      opacity: 0.72 + weight * 0.28,
    }))
    sprite.position.set(radial * Math.cos(angle) * 4.35, y * 4.35, radial * Math.sin(angle) * 4.35)
    const size = 1.2 + weight * 0.95
    sprite.scale.set(size * 3.15, size, 1)
    sprite.userData = { label: item.name, baseScale: sprite.scale.clone() }
    cloudGroup!.add(sprite)
  })
}

function resize() {
  if (!mountRef.value || !renderer || !camera) return
  const { clientWidth: width, clientHeight: height } = mountRef.value
  renderer.setSize(width, height, false)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8))
  camera.aspect = width / Math.max(height, 1)
  camera.position.z = Math.max(16, 16 / camera.aspect)
  camera.updateProjectionMatrix()
}

function animate() {
  if (!renderer || !scene || !camera || !cloudGroup) return
  if (!paused.value && !reduceMotion && !dragging) {
    cloudGroup.rotation.x += spinX
    cloudGroup.rotation.y += spinY
    spinX *= 0.94
    spinY += (0.0017 - spinY) * 0.035
    cloudGroup.rotation.x = THREE.MathUtils.clamp(cloudGroup.rotation.x, -0.72, 0.72)
  }
  renderer.render(scene, camera)
  animationFrame = requestAnimationFrame(animate)
}

function onPointerMove(event: PointerEvent) {
  if (!mountRef.value || !camera || !cloudGroup || !raycaster || !pointer) return
  if (dragging) {
    const dx = event.clientX - lastPointerX
    const dy = event.clientY - lastPointerY
    cloudGroup.rotation.y += dx * 0.006
    cloudGroup.rotation.x = THREE.MathUtils.clamp(cloudGroup.rotation.x + dy * 0.004, -0.72, 0.72)
    spinY = dx * 0.0009
    spinX = dy * 0.0006
    lastPointerX = event.clientX
    lastPointerY = event.clientY
    return
  }
  const rect = mountRef.value.getBoundingClientRect()
  pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1)
  raycaster.setFromCamera(pointer, camera)
  const hit = raycaster.intersectObjects(cloudGroup.children, false)[0]?.object as THREE.Sprite | undefined
  if (hovered && hovered !== hit) hovered.scale.copy(hovered.userData.baseScale)
  hovered = hit || null
  focusedWord.value = hit?.userData.label || ''
  if (hit) hit.scale.copy(hit.userData.baseScale).multiplyScalar(1.18)
}

function onPointerDown(event: PointerEvent) {
  dragging = true
  lastPointerX = event.clientX
  lastPointerY = event.clientY
  mountRef.value?.setPointerCapture(event.pointerId)
}

function onPointerUp(event: PointerEvent) {
  dragging = false
  mountRef.value?.releasePointerCapture(event.pointerId)
}

function init() {
  if (!mountRef.value) return
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100)
  camera.position.z = 12.5
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
  renderer.setClearColor(0x000000, 0)
  renderer.domElement.setAttribute('aria-label', '可旋转的三维情绪词云')
  mountRef.value.appendChild(renderer.domElement)
  cloudGroup = new THREE.Group()
  cloudGroup.rotation.x = -0.08
  scene.add(cloudGroup)
  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()
  buildCloud()
  resize()
  observer = new ResizeObserver(resize)
  observer.observe(mountRef.value)
  animate()
}

watch(() => props.words, buildCloud, { deep: true })
onMounted(init)
onUnmounted(() => {
  cancelAnimationFrame(animationFrame)
  observer?.disconnect()
  clearCloud()
  renderer?.dispose()
  renderer?.domElement.remove()
})
</script>

<template>
  <div class="cloud-shell" @pointerleave="focusedWord = ''">
    <div
      ref="mountRef"
      class="wordcloud-chart"
      :class="{ dragging }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    />
    <div class="cloud-caption">
      <span>{{ focusedWord || '情绪星体' }}</span>
      <button type="button" :aria-pressed="paused" @click="paused = !paused">
        {{ paused ? '继续旋转' : '暂停旋转' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.cloud-shell { position: relative; width: 100%; height: 100%; min-height: 460px; overflow: hidden; border-radius: 8px; background-color: #03090d; background-image: radial-gradient(circle at 50% 48%, rgba(42, 113, 112, .25), transparent 47%), radial-gradient(circle at 16% 18%, rgba(255,255,255,.72) 0 1px, transparent 1.5px), radial-gradient(circle at 72% 30%, rgba(255,255,255,.45) 0 1px, transparent 1.5px), radial-gradient(circle at 42% 76%, rgba(255,255,255,.5) 0 1px, transparent 1.5px); background-size: auto, 91px 83px, 137px 121px, 173px 149px; box-shadow: inset 0 0 80px rgba(0,0,0,.7); }
.wordcloud-chart { width: 100%; height: 100%; min-height: 460px; cursor: grab; touch-action: none; }
.wordcloud-chart.dragging { cursor: grabbing; }
.cloud-shell { height:520px; min-height:0; min-width:0; }
.wordcloud-chart { position:absolute; inset:0; min-height:0; }
.wordcloud-chart :deep(canvas) { display:block; width:100% !important; height:100% !important; }
.cloud-caption { position: absolute; inset: auto 1.25rem 1.1rem; display: flex; align-items: center; justify-content: space-between; color: #c8ded5; font-size: .8rem; pointer-events: none; }
.cloud-caption span { font-family: 'Songti SC', 'SimSun', serif; font-size: 1.1rem; }
.cloud-caption button { pointer-events: auto; border: 1px solid rgba(178, 211, 197, .35); border-radius: 6px; background: rgba(7, 28, 25, .72); color: #dcece5; padding: .55rem .85rem; cursor: pointer; }
@media (prefers-reduced-motion: reduce) { .cloud-caption button { display: none; } }
</style>
