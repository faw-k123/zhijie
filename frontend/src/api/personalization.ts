/**
 * 模块四：个性化与互动性
 */
import http, { type ApiEnvelope } from './http'
import type { MusicResourceUrls } from './contentDisplay'

export interface RecommendItem {
  id: string
  title: string
  intro?: string
  cover_url?: string
  mv_url?: string
  audio_url?: string
  resource_url?: string
  recommend_reason?: string
  recommend_score?: number
}

export interface FavoriteFolderSummary {
  id: string
  name: string
  icon_url?: string
  song_count?: number
  songs?: { id: string; title: string; intro?: string; mv_url?: string }[]
}

export interface PersonalityResult {
  image_url?: string
  title?: string
  report?: string
  songs?: RecommendItem[]
  tags?: string[]
}

/** 获取人格测试题库 */
export async function fetchQuestions() {
  const { data } = await http.get<ApiEnvelope>('/fun/questions/')
  return data
}

/** 提交人格测试答案 */
export async function submitPersonality(user_id: string, answers: unknown[]) {
  const { data } = await http.post<ApiEnvelope>('/fun/personality/', {
    user_id,
    answers,
    source: 'personality_test_page',
  })
  return data
}

/** 获取用户人格画像 */
export async function fetchProfile(user_id: string) {
  const { data } = await http.get<ApiEnvelope>('/fun/profile/', {
    params: { user_id },
  })
  return data
}

export async function fetchGuessLike(user_id: string) {
  const { data } = await http.post<ApiEnvelope>('/fun/guess-like/', {
    user_id,
    source: 'guess_like_page',
  })
  return data
}

export async function recordListen(user_id: string, song: Record<string, unknown>) {
  const { data } = await http.post<ApiEnvelope>('/fun/listen/', {
    user_id,
    song,
    source: 'listen_recorder',
  })
  return data
}

export async function generateAiMusic(user_id: string, form: Record<string, unknown>) {
  const { data } = await http.post<ApiEnvelope>('/fun/ai-music/', {
    user_id,
    form,
    source: 'ai_music_page',
  }, {
    timeout: 300000, // Suno 生成需要 2-3 分钟，延长到 5 分钟
  })
  return data
}

export async function getAiMusicStatus(taskId: string) {
  const { data } = await http.get<ApiEnvelope>('/fun/ai-music/status/', {
    params: { task_id: taskId },
  })
  return data
}

export async function generateAiLyrics(username: string, params: Record<string, unknown>) {
  const { data } = await http.post<ApiEnvelope>('/fun/ai-lyrics/', {
    username,
    ...params,
  })
  return data
}

export async function sendReaction(
  username: string,
  songId: string,
  reaction: 'like' | 'cry',
) {
  const { data } = await http.post<ApiEnvelope>('/personal/reaction/', {
    username,
    song_id: songId,
    reaction,
    source: 'music_display_reaction',
  })
  return data
}

export async function fetchFavorites(user_id: string) {
  const { data } = await http.get<{ success: boolean; message?: string; data?: { folders: FavoriteFolderSummary[] } }>(
    '/personal/favorites/',
    { params: { user_id } },
  )
  return data
}

export async function fetchFolderSongs(user_id: string, folderId: string) {
  const { data } = await http.get<
    {
      success: boolean
      message?: string
      data?: {
        folder_id: string
        folder_name: string
        songs: { id: string; title: string; intro?: string; mv_url?: string; audio_url?: string }[]
      }
    }
  >('/personal/favorites/songs/', {
    params: { user_id, folder_id: folderId },
  })
  return data
}

export async function createFavoriteFolder(user_id: string, name: string) {
  const { data } = await http.post<{ success: boolean; message?: string; data?: { folder: FavoriteFolderSummary } }>('/personal/favorites/create/', {
    user_id,
    name,
    source: 'favorite_create',
  })
  return data
}

export async function deleteFavoriteFolder(user_id: string, folderId: string) {
  const { data } = await http.delete<{ success: boolean; message?: string }>('/personal/favorites/delete/', {
    params: { user_id, folder_id: folderId },
  })
  return data
}

export async function saveToFavorite(user_id: string, songId: string, folderId: string) {
  const { data } = await http.post<{ success: boolean; message?: string; data?: { folder_id: string; song_id: string } }>('/personal/favorites/save/', {
    user_id,
    song_id: songId,
    folder_id: folderId,
    source: 'favorite_save',
  })
  return data
}

export async function removeFavoriteSong(user_id: string, folderId: string, songId: string) {
  const { data } = await http.delete<{ success: boolean; message?: string; data?: { folder_id: string; song_id: string } }>('/personal/favorites/remove-song/', {
    params: { user_id, folder_id: folderId, song_id: songId },
  })
  return data
}

export async function getFavoriteStatus(user_id: string, songId: string) {
  const { data } = await http.get<{ success: boolean; message?: string; data?: { favorited: boolean; folder_id?: string } }>('/personal/favorites/status/', {
    params: { user_id, song_id: songId },
  })
  return data
}

export async function fetchPersonalRecommend(
  user_id: string,
  options?: { personaOverride?: string; circleOverride?: string },
) {
  const { data } = await http.post<
    ApiEnvelope<{ items: RecommendItem[]; message?: string; recommend_mode?: string }>
  >('/personal/recommend/', {
    user_id,
    persona_override: options?.personaOverride || 'auto',
    circle_override: options?.circleOverride || 'auto',
    source: 'private_space_recommend',
  })
  return data
}

export async function fetchSimilarSongs(username: string, songId: string) {
  const { data } = await http.post<
    ApiEnvelope<{ items: (MusicResourceUrls & { title: string; intro: string; mv_url: string })[] }>
  >('/personal/similar/', {
    username,
    song_id: songId,
    source: 'music_display_recommend',
  })
  return data
}

export async function toggleSongLike(user_id: string, song_id: string, reaction_type: 'like' | 'dislike') {
  const { data } = await http.post<{ success: boolean; message?: string; liked?: boolean }>('/personal/like/', {
    user_id,
    song_id,
    reaction_type,
  })
  return data
}

export async function getSongLikeStatus(user_id: string, song_id: string) {
  const { data } = await http.get<ApiEnvelope<{ liked: boolean; disliked: boolean }>>(
    '/personal/like/status/',
    { params: { user_id, song_id } },
  )
  return data
}

export async function fetchLikedSongs(user_id: string) {
  const { data } = await http.get<ApiEnvelope<{ songs: { id: string; title: string; intro?: string; mv_url?: string; audio_url?: string; cover_url?: string }[] }>>(
    '/personal/liked-songs/',
    { params: { user_id } },
  )
  return data
}
