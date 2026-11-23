/**
 * 模块三：传播分析与宣传报告生成
 */
import http, { type ApiEnvelope } from './http'

export async function fetchPropagationAnalysis(payload: {
  category: string
  subcategory: string
  song_title: string
}) {
  const { data } = await http.post<ApiEnvelope>('/global/propagation/', {
    ...payload,
    source: 'global_effect_right_panels',
  })
  return data
}

export async function fetchSongAiReport(payload: {
  category: string
  subcategory: string
  song_id: string
  song_title?: string
}) {
  const { data } = await http.post<ApiEnvelope>('/emotion/ai-report/', {
    ...payload,
    source: 'music_detail_ai_report_tab',
  }, { timeout: 120000 })
  return data
}

export async function generatePromoReport(payload: {
  theme: string
  platform: string
  audience: string
  core_text: string
}) {
  const { data } = await http.post<ApiEnvelope>('/promo/report/', {
    ...payload,
    source: 'promo_report_page',
  })
  return data
}
