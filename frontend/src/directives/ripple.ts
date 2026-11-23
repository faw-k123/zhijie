import type { Directive, DirectiveBinding } from 'vue'

const ripple: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    el.classList.add('ripple-container')

    el.addEventListener('click', (e: MouseEvent) => {
      const rect = el.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      const size = Math.max(rect.width, rect.height)

      const rippleEl = document.createElement('span')
      rippleEl.classList.add('ripple')
      rippleEl.style.width = `${size}px`
      rippleEl.style.height = `${size}px`
      rippleEl.style.left = `${x - size / 2}px`
      rippleEl.style.top = `${y - size / 2}px`

      if (binding.value) {
        rippleEl.style.background = binding.value
      }

      el.appendChild(rippleEl)

      setTimeout(() => {
        rippleEl.remove()
      }, 600)
    })
  },

  unmounted(el: HTMLElement) {
    el.classList.remove('ripple-container')
  }
}

export default ripple
