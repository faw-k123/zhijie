/**
 * 歌曲意象解析模块 API（缓冲池模式）
 */
import http, { type ApiEnvelope } from './http'
import { circleOverride, testModeEnabled } from '@/stores/testOverrides'

export interface ImageryResult {
  text: string
  test_mode?: boolean
  from_buffer?: boolean
  buffer_key?: string
  matched_circle?: { user_circle?: string; similarity?: number; source?: string }
  possible_emotions?: Record<string, unknown>[]
  common_scenes_things?: Record<string, unknown>[]
  input_tags?: {
    scene_tags?: string[]
    thing_tags?: string[]
    emotion_tags?: string[]
  }
  query_error?: string
  message?: string
}

/**
 * 从意象缓冲池取内容：池中没有则后端申请解析并写入后再返回。
 */
export async function fetchSongImagery(
  songId: string,
  language: string,
  options?: {
    userId?: string
    sceneTags?: string[]
    thingTags?: string[]
    emotionTags?: string[]
    circleOverride?: string
  },
) {
  const circle =
    options?.circleOverride ??
    (testModeEnabled.value ? circleOverride.value : 'auto')

  const { data } = await http.post<ApiEnvelope<ImageryResult>>('/imagery/translate/', {
    song_id: songId,
    language,
    user_id: options?.userId || localStorage.getItem('user_id') || '',
    scene_tags: options?.sceneTags || [],
    thing_tags: options?.thingTags || [],
    emotion_tags: options?.emotionTags || [],
    circle_override: circle,
    source: 'music_display_imagery_buffer',
  })
  return data
}
