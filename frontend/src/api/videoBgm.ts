import http from './http'

export interface VideoAnalysis {
  scene: string
  mood: string
  character: string
  rhythm: string
}

export interface RecommendSong {
  id: number
  title: string
  genre: string
  audio_url: string
  cover_url: string
}

export interface AnalyzeResponse {
  success: boolean
  analysis: VideoAnalysis
  recommendations: RecommendSong[]
  reason: string
}

export async function analyzeVideo(image: string) {
  const { data } = await http.post<AnalyzeResponse>('/video-bgm/analyze/', { image })
  return data
}
