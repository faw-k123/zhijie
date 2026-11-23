import { computed, ref } from 'vue'

export type LocaleCode = 'zh-CN' | 'zh-TW' | 'en' | 'ru' | 'th' | 'ko' | 'ja'

export interface LocaleOption {
  code: LocaleCode
  label: string
  country: string
  countryName: string
}

export const LOCALE_OPTIONS: LocaleOption[] = [
  { code: 'zh-CN', label: '中文（简体）', country: 'CN', countryName: '中国' },
  { code: 'zh-TW', label: '中文（繁體）', country: 'TW', countryName: '中國台灣' },
  { code: 'en', label: 'English', country: 'US', countryName: 'United States' },
  { code: 'ru', label: 'Русский', country: 'RU', countryName: 'Россия' },
  { code: 'th', label: 'ไทย', country: 'TH', countryName: 'ประเทศไทย' },
  { code: 'ko', label: '한국어', country: 'KR', countryName: '대한민국' },
  { code: 'ja', label: '日本語', country: 'JP', countryName: '日本' },
]

const STORAGE_KEY = 'app_locale'

function readInitialLocale(): LocaleCode {
  const saved = localStorage.getItem(STORAGE_KEY) as LocaleCode | null
  if (saved && LOCALE_OPTIONS.some((o) => o.code === saved)) return saved
  return 'zh-CN'
}

const locale = ref<LocaleCode>(readInitialLocale())

type Dict = Record<string, string>
const messages: Record<LocaleCode, Dict> = {
  'zh-CN': {},
  'zh-TW': {},
  en: {},
  ru: {},
  th: {},
  ko: {},
  ja: {},
}

export function registerMessages(code: LocaleCode, dict: Dict) {
  messages[code] = { ...messages[code], ...dict }
}

export function translateKnownText(source: string, target: LocaleCode) {
  if (target === 'zh-CN') return source
  const sourceEntries = Object.entries(messages['zh-CN'])
  for (const [key, value] of sourceEntries) {
    if (value === source) {
      const translated = messages[target][key]
      if (translated && translated !== value) return translated
    }
  }
  return null
}

export function setLocale(code: LocaleCode) {
  if (!LOCALE_OPTIONS.some((o) => o.code === code)) return
  locale.value = code
  localStorage.setItem(STORAGE_KEY, code)
}

export function getLocale() {
  return locale.value
}

export function getLocaleOption(code: LocaleCode = locale.value) {
  return LOCALE_OPTIONS.find((o) => o.code === code) || LOCALE_OPTIONS[0]
}

export function t(key: string, params?: Record<string, string | number>) {
  const dict = messages[locale.value] || messages['zh-CN']
  let text = dict[key] ?? messages['zh-CN'][key] ?? key
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v))
    }
  }
  return text
}

export function useI18n() {
  const current = computed(() => locale.value)
  const option = computed(() => getLocaleOption(locale.value))
  return {
    locale: current,
    option,
    t,
    setLocale,
    locales: LOCALE_OPTIONS,
  }
}

export { locale }
