import http, { type ApiEnvelope } from './http'
import type { LocaleCode } from '@/i18n'

export async function translateTexts(locale: LocaleCode, texts: string[]) {
  const { data } = await http.post<
    ApiEnvelope<{
      locale: LocaleCode
      translations: string[]
      translated: boolean
      cached: number
      failed: number
    }>
  >('/i18n/translate/', { locale, texts })
  return data
}
