<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, COUNTRY_OPTIONS } from '@/api/auth'
import { useI18n } from '@/i18n'

const router = useRouter()
const { t } = useI18n()
const username = ref('')
const password = ref('')
const country = ref(t('auth.defaultCountry'))
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = t('auth.needUserPwd')
    return
  }
  if (!country.value) {
    error.value = t('auth.needCountry')
    return
  }
  loading.value = true
  try {
    const res = await login(username.value.trim(), password.value, country.value)
    if (res.success) {
      localStorage.setItem('username', res.username || username.value.trim())
      if (res.user_id) {
        localStorage.setItem('user_id', res.user_id)
      }
      localStorage.setItem('country', country.value)
      router.push('/home')
    } else {
      error.value = res.message
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    error.value = err.response?.data?.message || t('auth.loginFail')
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
          <span>CHINESE MUSIC · GLOBAL VOICE</span>
          <h2>听见山河<br />读懂中国</h2>
          <p>从旋律、意象与情感出发，让传统音乐跨越语言与文化边界。</p>
        </div>
      </section>
      <section class="auth-card">
        <div class="auth-card-head">
          <span class="auth-eyebrow">WELCOME BACK</span>
          <h1 class="brand">{{ t('auth.brand') }}</h1>
          <p class="subtitle">{{ t('auth.loginSubtitle') }}</p>
        </div>
        <form class="auth-form" @submit.prevent="handleSubmit">
          <label>
            <span>{{ t('auth.username') }}</span>
            <input v-model="username" type="text" :placeholder="t('auth.placeholderUser')" autocomplete="username" />
          </label>
          <label>
            <span>{{ t('auth.password') }}</span>
            <input
              v-model="password"
              type="password"
              :placeholder="t('auth.placeholderPwd')"
              autocomplete="current-password"
            />
          </label>
          <label>
            <span>{{ t('auth.country') }}</span>
            <select v-model="country">
              <option v-for="c in COUNTRY_OPTIONS" :key="c" :value="c">{{ c }}</option>
            </select>
          </label>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" :disabled="loading">{{ loading ? t('auth.loggingIn') : t('auth.login') }}</button>
        </form>
        <p class="switch">
          {{ t('auth.noAccount') }}
          <router-link to="/register">{{ t('auth.goRegister') }}</router-link>
        </p>
      </section>
    </main>
    <footer class="auth-footer">传统音乐 · 文化解读 · 国际传播</footer>
  </div>
</template>

<style src="@/assets/auth-layout.css"></style>
