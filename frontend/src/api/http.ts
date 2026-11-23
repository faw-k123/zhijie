import axios from 'axios'

/** 统一 Axios 实例：经 Vite 代理转发到 Django /api */
const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

export default http

export interface ApiEnvelope<T = unknown> {
  success: boolean
  message?: string
  data?: T
}
