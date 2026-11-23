import http, { type ApiEnvelope } from './http'

export async function analyzeSongEmotion(payload: {
  category: string
  subcategory: string
  song_id: string
  song_title?: string
}) {
  const { data } = await http.post<ApiEnvelope>('/emotion/analyze/', {
    ...payload,
    source: 'music_detail_emotion_tab',
  })
  return data
}

export async function predictEmotionTrend(payload: {
  song_id: string
  days?: number
}) {
  const { data } = await http.post<ApiEnvelope>('/emotion/trend-prediction/', payload)
  return data
}

export async function analyzeCausalImpact(payload: {
  song_id: string
  event_date?: string
}) {
  const { data } = await http.post<ApiEnvelope>('/emotion/causal-impact/', payload)
  return data
}
