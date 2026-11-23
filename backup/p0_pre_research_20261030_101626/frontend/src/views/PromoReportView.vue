<script setup lang="ts">
import { ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import { generatePromoReport } from '@/api/propagation'

const themes = ['新曲发布', '节日专题', '海外传播', '非遗推广', '青年圈层']
const platforms = ['推特', '小红书', '微信', 'ins', 'bilibili']
const audiences = ['年轻用户', '传统文化爱好者', '海外华人', '音乐从业者', '泛娱乐用户']

const theme = ref<string>(themes[0] ?? '')
const platform = ref<string>(platforms[0] ?? '')
const audience = ref<string>(audiences[0] ?? '')
const coreText = ref('')
const output = ref('提交后，AI 生成的宣传文案将显示在这里。')
const loading = ref(false)

/** 对接：POST /api/promo/report/ → 传播分析模块 · 文生 */
async function handleSubmit() {
  if (!coreText.value.trim()) {
    output.value = '请先填写核心表达内容。'
    return
  }
  loading.value = true
  try {
    const res = await generatePromoReport({
      theme: theme.value,
      platform: platform.value,
      audience: audience.value,
      core_text: coreText.value.trim(),
    })
    const data = res.data as { content?: string }
    output.value = data?.content || JSON.stringify(res.data)
  } catch (e: unknown) {
    const err = e as { message?: string }
    output.value = `生成失败：${err.message || '网络错误'}`
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page editorial-page promo-page">
    <AppNav />
    <header class="tool-heading"><h1>宣传文案生成</h1></header>
    <div class="layout">
      <section class="input-zone">
        <h2>传播主题</h2>
        <div class="fields">
          <label>
            主题
            <select v-model="theme">
              <option v-for="t in themes" :key="t" :value="t">{{ t }}</option>
            </select>
          </label>
          <label>
            目标平台
            <select v-model="platform">
              <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
            </select>
          </label>
          <label>
            目标人群
            <select v-model="audience">
              <option v-for="a in audiences" :key="a" :value="a">{{ a }}</option>
            </select>
          </label>
          <label class="core">
            核心表达内容
            <input v-model="coreText" type="text" placeholder="输入你想强调的核心信息..." />
          </label>
        </div>
      </section>

      <section class="output-zone">
        <h2>宣传文案</h2>
        <pre>{{ output }}</pre>
      </section>

      <section class="submit-zone">
        <button type="button" :disabled="loading" @click="handleSubmit">
          {{ loading ? '生成中...' : '提交生成' }}
        </button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
  display: flex;
  flex-direction: column;
}

.layout {
  flex: 1;
  display: grid;
  grid-template-rows: 15fr 80fr 5fr;
  min-height: calc(100vh - 56px);
  padding: 0.75rem 1rem 1rem;
  gap: 0.75rem;
}

.input-zone,
.output-zone,
.submit-zone {
  background: #fffdf9;
  border: 1px solid #ddd2c4;
}

.input-zone {
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
}

.fields {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr)) 2fr;
  gap: 0.75rem;
  width: 100%;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #5a4a3a;
}

select,
input {
  padding: 0.5rem 0.65rem;
  border: 1px solid #cfc5b8;
  background: #fff;
  outline: none;
}

.output-zone {
  padding: 1.25rem;
  overflow: auto;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  color: #3d2f24;
  font-family: inherit;
  font-size: 0.98rem;
}

.submit-zone {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.4rem;
}

button {
  min-width: 160px;
  padding: 0.55rem 1.2rem;
  border: none;
  background: #8b3a2a;
  color: #fff;
  cursor: pointer;
  letter-spacing: 0.08em;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .fields {
    grid-template-columns: 1fr 1fr;
  }

  .core {
    grid-column: 1 / -1;
  }
}
</style>
