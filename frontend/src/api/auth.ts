import http, { type ApiEnvelope } from './http'

export interface AuthResponse {
  success: boolean
  message: string
  username?: string
  user_id?: string
  country?: string
}

export async function login(username: string, password: string, country: string) {
  const { data } = await http.post<AuthResponse>('/login/', { username, password, country })
  return data
}

export async function register(username: string, password: string, country: string) {
  const { data } = await http.post<AuthResponse>('/register/', { username, password, country })
  return data
}

/** 个人资料 */
export async function fetchProfile(username: string) {
  const { data } = await http.get<ApiEnvelope>('/user/profile/', { params: { username } })
  return data
}

export async function updateProfile(payload: {
  username: string
  nickname?: string
  email?: string
  bio?: string
  password?: string
}) {
  const { data } = await http.put<ApiEnvelope>('/user/profile/', payload)
  return data
}

/** 国家列表 */
export const COUNTRY_OPTIONS = [
  '中国', '美国', '日本', '韩国', '英国', '法国', '德国',
  '加拿大', '澳大利亚', '新加坡', '马来西亚', '泰国', '越南',
  '俄罗斯', '意大利', '西班牙', '荷兰', '其他',
]
