import { nextTick, watch } from 'vue'
import type { Router } from 'vue-router'
import { translateTexts } from '@/api/i18n'
import { locale, translateKnownText, type LocaleCode } from '@/i18n'

type TextRecord = { original: string; translated: string; locale: LocaleCode }
type AttrRecord = { original: string; translated: string; locale: LocaleCode }

const textRecords = new WeakMap<Text, TextRecord>()
const attrRecords = new WeakMap<Element, Map<string, AttrRecord>>()
const translationCache = new Map<string, string>()
const failedAttempts = new Map<string, number>()
const translatableAttributes = ['placeholder', 'title', 'aria-label', 'alt'] as const
const chinesePattern = /[\u3400-\u9fff]/

let observer: MutationObserver | null = null
let timer: ReturnType<typeof setTimeout> | null = null
let translating = false
let rerunRequested = false
let retryTimer: ReturnType<typeof setTimeout> | null = null

function cacheKey(target: LocaleCode, text: string) {
  return `${target}\u0000${text}`
}

function isIgnored(element: Element | null) {
  if (!element) return false
  return !!element.closest('script,style,noscript,[data-no-auto-translate]')
}

function sourceText(value: string) {
  return value.trim()
}

function restoreChinese(root: ParentNode) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let node = walker.nextNode() as Text | null
  while (node) {
    const record = textRecords.get(node)
    if (record && node.data === record.translated) node.data = record.original
    textRecords.delete(node)
    node = walker.nextNode() as Text | null
  }

  if (root instanceof Element) restoreAttributes(root)
  root.querySelectorAll?.('*').forEach((element) => restoreAttributes(element))
}

function restoreAttributes(element: Element) {
  const records = attrRecords.get(element)
  if (!records) return
  for (const [name, record] of records) {
    if (element.getAttribute(name) === record.translated) element.setAttribute(name, record.original)
  }
  attrRecords.delete(element)
}

async function translatePage() {
  if (translating) {
    rerunRequested = true
    return
  }

  const target = locale.value
  const root = document.querySelector('#app')
  if (!root) return
  document.documentElement.lang = target

  if (target === 'zh-CN') {
    restoreChinese(root)
    return
  }

  translating = true
  try {
    const textTargets: Array<{ node: Text; exact: string; source: string }> = []
    const attrTargets: Array<{ element: Element; name: string; exact: string; source: string }> = []
    const requested = new Set<string>()
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
    let node = walker.nextNode() as Text | null

    while (node) {
      if (!isIgnored(node.parentElement)) {
        const existing = textRecords.get(node)
        if (existing && node.data === existing.translated && existing.locale === target) {
          node = walker.nextNode() as Text | null
          continue
        }
        if (existing && node.data !== existing.translated && !chinesePattern.test(node.data)) {
          textRecords.delete(node)
          node = walker.nextNode() as Text | null
          continue
        }
        const exact = existing && node.data === existing.translated ? existing.original : node.data
        const source = sourceText(exact)
        if (source && source.length <= 4000 && chinesePattern.test(source)) {
          const known = translateKnownText(source, target)
          if (known) translationCache.set(cacheKey(target, source), known)
          textTargets.push({ node, exact, source })
          const key = cacheKey(target, source)
          if (!translationCache.has(key) && (failedAttempts.get(key) || 0) < 3) requested.add(source)
        }
      }
      node = walker.nextNode() as Text | null
    }

    root.querySelectorAll('*').forEach((element) => {
      if (isIgnored(element)) return
      for (const name of translatableAttributes) {
        const value = element.getAttribute(name)
        if (!value) continue
        const records = attrRecords.get(element)
        const existing = records?.get(name)
        if (existing && value === existing.translated && existing.locale === target) continue
        if (existing && value !== existing.translated && !chinesePattern.test(value)) {
          records?.delete(name)
          continue
        }
        const exact = existing && value === existing.translated ? existing.original : value
        const source = sourceText(exact)
        if (source && source.length <= 4000 && chinesePattern.test(source)) {
          const known = translateKnownText(source, target)
          if (known) translationCache.set(cacheKey(target, source), known)
          attrTargets.push({ element, name, exact, source })
          const key = cacheKey(target, source)
          if (!translationCache.has(key) && (failedAttempts.get(key) || 0) < 3) requested.add(source)
        }
      }
    })

    const pending = [...requested]
    let needsRetry = false
    for (let start = 0; start < pending.length; start += 90) {
      const chunk = pending.slice(start, start + 90)
      try {
        const response = await translateTexts(target, chunk)
        const translations = response.data?.translations || []
        chunk.forEach((source, index) => {
          const key = cacheKey(target, source)
          const translated = translations[index]
          if (translated && translated !== source) {
            translationCache.set(key, translated)
            failedAttempts.delete(key)
          } else {
            failedAttempts.set(key, (failedAttempts.get(key) || 0) + 1)
            needsRetry = true
          }
        })
      } catch (error) {
        console.error('[i18n] 页面翻译批次失败，将继续处理后续内容', error)
        chunk.forEach((source) => {
          const key = cacheKey(target, source)
          failedAttempts.set(key, (failedAttempts.get(key) || 0) + 1)
        })
        needsRetry = true
      }
    }

    for (const item of textTargets) {
      const translated = translationCache.get(cacheKey(target, item.source))
      if (!translated || !item.node.isConnected) continue
      const replacement = item.exact.replace(item.source, translated)
      textRecords.set(item.node, { original: item.exact, translated: replacement, locale: target })
      item.node.data = replacement
    }

    for (const item of attrTargets) {
      const translated = translationCache.get(cacheKey(target, item.source))
      if (!translated || !item.element.isConnected) continue
      const replacement = item.exact.replace(item.source, translated)
      let records = attrRecords.get(item.element)
      if (!records) {
        records = new Map()
        attrRecords.set(item.element, records)
      }
      records.set(item.name, { original: item.exact, translated: replacement, locale: target })
      item.element.setAttribute(item.name, replacement)
    }

    if (needsRetry) {
      if (retryTimer) clearTimeout(retryTimer)
      retryTimer = setTimeout(() => void translatePage(), 1400)
    }
  } catch (error) {
    console.error('[i18n] 页面自动翻译失败', error)
  } finally {
    translating = false
    if (rerunRequested) {
      rerunRequested = false
      scheduleTranslation()
    }
  }
}

function scheduleTranslation(delay = 180) {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => void translatePage(), delay)
}

export function installDomTranslation(router: Router) {
  observer?.disconnect()
  observer = new MutationObserver(() => scheduleTranslation())
  const root = document.querySelector('#app')
  if (root) {
    observer.observe(root, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: [...translatableAttributes],
    })
  }

  watch(locale, async () => {
    await nextTick()
    scheduleTranslation(0)
  })
  router.afterEach(async () => {
    await nextTick()
    scheduleTranslation(80)
  })
  scheduleTranslation(0)
}
