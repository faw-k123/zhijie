/**
 * 联调测试覆盖：文化圈层 / 用户画像
 * 仅当后端 IMAGERY_TEST_MODE=true 时由 AppNav 展示下拉框。
 */
import { ref, watch } from 'vue'
import { fetchTestModeOptions, type TestOption } from '@/api/testMode'

const LS_CIRCLE = 'test_circle_override'
const LS_PERSONA = 'test_music_persona'

const FALLBACK_CIRCLES: TestOption[] = [
  { value: 'auto', label: '真实属性计算' },
  { value: '东亚文化圈', label: '东亚文化圈' },
  { value: '中华文化圈', label: '中华文化圈' },
  { value: '江南文化圈', label: '江南文化圈' },
  { value: '草原文化圈', label: '草原文化圈' },
  { value: '现代流行文化圈', label: '现代流行文化圈' },
]

const FALLBACK_PERSONAS: TestOption[] = [
  { value: 'auto', label: '真实属性计算' },
  { value: '国风挚爱型', label: '国风挚爱型' },
  { value: '潮流融合型', label: '潮流融合型' },
  { value: '社交达人型', label: '社交达人型' },
  { value: '静赏体验型', label: '静赏体验型' },
  { value: '泛兴趣尝鲜型', label: '泛兴趣尝鲜型' },
]

// 导航选择器属于正式的个性化入口，后端暂时离线时也必须可用。
export const testModeEnabled = ref(true)
export const culturalCircleOptions = ref<TestOption[]>([...FALLBACK_CIRCLES])
export const musicPersonaOptions = ref<TestOption[]>([...FALLBACK_PERSONAS])

export const circleOverride = ref(localStorage.getItem(LS_CIRCLE) || 'auto')
export const musicPersonaOverride = ref(localStorage.getItem(LS_PERSONA) || 'auto')

watch(circleOverride, (v) => {
  localStorage.setItem(LS_CIRCLE, v || 'auto')
})

watch(musicPersonaOverride, (v) => {
  localStorage.setItem(LS_PERSONA, v || 'auto')
})

let loaded = false

export async function loadTestModeConfig() {
  if (loaded) return
  try {
    const res = await fetchTestModeOptions()
    const data = res.data
    testModeEnabled.value = true
    culturalCircleOptions.value = data?.cultural_circles?.length
      ? data.cultural_circles
      : [...FALLBACK_CIRCLES]
    musicPersonaOptions.value = data?.music_personas?.length
      ? data.music_personas
      : [...FALLBACK_PERSONAS]
    culturalCircleOptions.value = culturalCircleOptions.value.map((option) =>
      option.value === 'auto' ? { ...option, label: '真实属性计算' } : option,
    )
    musicPersonaOptions.value = musicPersonaOptions.value.map((option) =>
      option.value === 'auto' ? { ...option, label: '真实属性计算' } : option,
    )
    // 兼容旧版编号缓存（1~5）→ 圈层名
    const legacyIdMap: Record<string, string> = {
      '1': '东亚文化圈',
      '2': '朝鲜半岛文化圈',
      '3': '日本文化圈',
      '4': '哈萨克斯坦草原文化圈层',
      '5': '苏联集体主义/工农兵圈层',
    }
    const legacyCircle = legacyIdMap[circleOverride.value]
    if (legacyCircle) {
      circleOverride.value = legacyCircle
    }
    // 校验本地缓存值仍在选项内
    const circleVals = new Set(culturalCircleOptions.value.map((o) => o.value))
    if (!circleVals.has(circleOverride.value)) circleOverride.value = 'auto'
    const personaVals = new Set(musicPersonaOptions.value.map((o) => o.value))
    if (!personaVals.has(musicPersonaOverride.value)) musicPersonaOverride.value = 'auto'
    loaded = true
  } catch {
    testModeEnabled.value = true
    culturalCircleOptions.value = [...FALLBACK_CIRCLES]
    musicPersonaOptions.value = [...FALLBACK_PERSONAS]
  }
}
