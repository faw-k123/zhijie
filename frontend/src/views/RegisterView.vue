<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register, COUNTRY_OPTIONS } from '@/api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const country = ref('中国')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  success.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (!country.value) {
    error.value = '请选择国家'
    return
  }
  loading.value = true
  try {
    const res = await register(username.value.trim(), password.value, country.value)
    if (res.success) {
      success.value = '注册成功，即将跳转登录...'
      setTimeout(() => router.push('/login'), 800)
    } else {
      error.value = res.message
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    error.value = err.response?.data?.message || '注册失败，请检查后端是否启动'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <header class="auth-topbar">
      <span class="auth-logo">智解国音</span>
      <span class="auth-tagline">中国传统音乐国际传播平台</span>
    </header>
    <main class="auth-shell">
      <section class="auth-visual" aria-label="中国传统音乐文化">
        <div class="auth-visual-copy">
          <span>JOIN THE JOURNEY</span>
          <h2>以乐会友<br />让世界听见</h2>
          <p>创建你的文化画像，发现更贴近兴趣与理解路径的中国传统音乐。</p>
        </div>
      </section>
      <section class="auth-card auth-card-register">
        <div class="auth-card-head">
          <span class="auth-eyebrow">CREATE ACCOUNT</span>
          <h1 class="brand">智解国音</h1>
          <p class="subtitle">创建新账号</p>
        </div>
        <form class="auth-form" @submit.prevent="handleSubmit">
        <label>
          <span>用户名</span>
          <input v-model="username" type="text" placeholder="请输入用户名" autocomplete="username" />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            autocomplete="new-password"
          />
        </label>
        <label>
          <span>确认密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </label>
        <label>
          <span>国家/地区</span>
          <select v-model="country">
            <option v-for="c in COUNTRY_OPTIONS" :key="c" :value="c">{{ c }}</option>
          </select>
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
        </form>
        <p class="switch">
          已有账号？
          <router-link to="/login">返回登录</router-link>
        </p>
      </section>
    </main>
    <footer class="auth-footer">传统音乐 · 文化解读 · 国际传播</footer>
  </div>
</template>

<style src="@/assets/auth-layout.css"></style>
