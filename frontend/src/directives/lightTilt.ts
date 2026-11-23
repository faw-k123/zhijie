import type { Directive } from 'vue'

const cleanups = new WeakMap<HTMLElement, () => void>()

const lightTilt: Directive<HTMLElement> = {
  mounted(el) {
    const media = window.matchMedia('(prefers-reduced-motion: reduce), (hover: none)')
    const reset = () => {
      el.style.removeProperty('--tilt-x')
      el.style.removeProperty('--tilt-y')
      el.style.removeProperty('--light-x')
      el.style.removeProperty('--light-y')
    }
    const move = (event: PointerEvent) => {
      if (media.matches) return
      const rect = el.getBoundingClientRect()
      const x = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width))
      const y = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height))
      el.style.setProperty('--tilt-x', `${(0.5 - y) * 5}deg`)
      el.style.setProperty('--tilt-y', `${(x - 0.5) * 5}deg`)
      el.style.setProperty('--light-x', `${x * 100}%`)
      el.style.setProperty('--light-y', `${y * 100}%`)
    }
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerleave', reset)
    media.addEventListener('change', reset)
    cleanups.set(el, () => {
      el.removeEventListener('pointermove', move)
      el.removeEventListener('pointerleave', reset)
      media.removeEventListener('change', reset)
    })
  },
  unmounted(el) {
    cleanups.get(el)?.()
    cleanups.delete(el)
  },
}

export default lightTilt
