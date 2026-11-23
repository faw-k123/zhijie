/**
 * 内容展示模块相关前端 API
 * 对应后端 data_display.services + api.views 中 content_* / user/profile 等
 */
import http, { type ApiEnvelope } from './http'

export interface MusicResourceUrls {
  id: string
  title: string
  intro: string
  mv_url: string
  audio_url: string
  lyrics_url: string
  /** 资源详情接口地址（前端再请求渲染） */
  resource_url: string
}

export interface LyricLine {
  time: number
  text: string
}

export interface MusicResourceDetail {
  id: string
  title: string
  intro: string
  mv_url: string
  audio_url: string
  cover_url?: string
  lyrics_lrc_url?: string
  /** LRC 解析后的时间轴歌词 */
  lyrics: LyricLine[] | string[]
  /** 意象解析：场景标签（N编号） */
  scene_tags?: string[]
  /** 意象解析：事物标签（T编号） */
  thing_tags?: string[]
  /** 意象解析：情感标签（F编号） */
  emotion_tags?: string[]
}

/** 首页内容区：最多 9 条资源 URL 列表 */
export async function fetchHomeFeed(params?: { keyword?: string; refresh?: boolean }) {
  const { data } = await http.get<ApiEnvelope<{ items: MusicResourceUrls[]; suggestions?: string[] }>>(
    '/content/home-feed/',
    {
      params: {
        keyword: params?.keyword || '',
        refresh: params?.refresh ? 1 : 0,
      },
    },
  )
  return data
}

/** 按 id 拉取单曲完整资源包 */
export async function fetchMusicResource(id: string) {
  const { data } = await http.get<ApiEnvelope<MusicResourceDetail>>('/content/music-resource/', {
    params: { id },
  })
  return data
}

/** 首页搜索框：建议搜索内容 */
export async function fetchSearchSuggestions(keyword = '') {
  const { data } = await http.get<ApiEnvelope<{ suggestions: string[] }>>('/content/search-suggestions/', {
    params: { keyword },
  })
  return data
}