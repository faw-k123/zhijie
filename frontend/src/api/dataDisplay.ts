/**
 * 模块一相关前端 API：多维度数据展示与问答
 * 对应后端 data_display.services + api.views 中 home_* / music-show / emotion_* / global/comments 等
 */
import http, { type ApiEnvelope } from './http'
import type { LocaleCode } from '@/i18n'

/** 首页右下：图谱 */
export async function fetchHomeGraph(category: string, subcategory: string) {
  const { data } = await http.post<ApiEnvelope>('/home/graph/', {
    category,
    subcategory,
    source: 'home_graph_panel',
  })
  return data
}

/** 首页左下：KG-RAG 问答 */
export async function askHomeQa(question: string, locale: LocaleCode = 'zh-CN') {
  const { data } = await http.post<ApiEnvelope>('/home/qa/', {
    question,
    locale,
    source: 'home_qa_panel',
  })
  return data
}

/** 音乐展示页整包 */
export async function fetchMusicShowBundle(category: string) {
  const { data } = await http.get<ApiEnvelope>('/music-show/', { params: { category } })
  return data
}

/** 情感分析半遮挡：大类 → 小类网格 */
export async function fetchEmotionSubcategories(category: string) {
  const { data } = await http.get<ApiEnvelope>('/emotion/subcategories/', {
    params: { category },
  })
  return data
}

/** 点击小类：歌曲列表 + 首曲资源 */
export async function fetchSubcategorySongs(category: string, subcategory: string) {
  const { data } = await http.get<ApiEnvelope>('/emotion/subcategory-songs/', {
    params: { category, subcategory },
  })
  return data
}

/** 切换歌曲：单曲资源包 */
export async function fetchSongResources(
  category: string,
  subcategory: string,
  songId: string,
  songTitle = '',
) {
  const { data } = await http.get<ApiEnvelope>('/emotion/song-resources/', {
    params: { category, subcategory, song_id: songId, song_title: songTitle },
  })
  return data
}

/** 全球传播：评论前 50 */
export async function fetchGlobalComments(
  category: string,
  subcategory: string,
  songTitle: string,
) {
  const { data } = await http.get<ApiEnvelope>('/global/comments/', {
    params: { category, subcategory, song_title: songTitle },
  })
  return data
}

/** 大类-小类-歌曲 taxonomy */
export async function fetchMusicTaxonomy() {
  const { data } = await http.get<ApiEnvelope>('/music/taxonomy/')
  return data
}

/** 词云数据：按歌曲 ID 获取 ECharts wordcloud 格式数据 */
export async function fetchSongWordcloud(songId: string) {
  const { data } = await http.get<ApiEnvelope>('/music/wordcloud/', { params: { song_id: songId } })
  return data
}

/** 情感极性统计：按歌曲 ID 获取评论情感极性分布 */
export async function fetchSongEmotionPolarity(songId: string) {
  const { data } = await http.get<ApiEnvelope>('/music/emotion-polarity/', { params: { song_id: songId } })
  return data
}
