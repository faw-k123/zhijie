/**
 * 联调测试开关与下拉选项
 */
import http, { type ApiEnvelope } from './http'

export interface TestOption {
  value: string
  label: string
}

export interface TestModeOptions {
  test_mode: boolean
  cultural_circles: TestOption[]
  music_personas: TestOption[]
}

export async function fetchTestModeOptions() {
  const { data } = await http.get<ApiEnvelope<TestModeOptions>>('/test/options/')
  return data
}
