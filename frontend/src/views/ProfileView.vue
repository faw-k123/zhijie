<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import { fetchProfile, updateProfile } from '@/api/auth'

const username = localStorage.getItem('username') || '用户'

const profile = reactive({
  username,
  nickname: username,
  email: '',
  bio: '',
})

const form = reactive({
  nickname: '',
  email: '',
  bio: '',
  password: '',
})

const message = ref('')
const saving = ref(false)

/** 对接：GET /api/user/profile/ */
onMounted(async () => {
  try {
    const res = await fetchProfile(username)
    const data = res.data as {
      nickname?: string
      email?: string
      bio?: string
      username?: string
    }
    if (data) {
      profile.username = data.username || username
      profile.nickname = data.nickname || username
      profile.email = data.email || ''
      profile.bio = data.bio || ''
      form.nickname = profile.nickname
      form.email = profile.email
      form.bio = profile.bio
    }
  } catch {
    form.nickname = profile.nickname
  }
})

/** 对接：PUT /api/user/profile/ → 关系数据库改操作后返回新资料 */
async function handleSubmit() {
  message.value = ''
  saving.value = true
  try {
    const res = await updateProfile({
      username,
      nickname: form.nickname.trim(),
      email: form.email.trim(),
      bio: form.bio.trim(),
      password: form.password || undefined,
    })
    const data = res.data as {
      nickname?: string
      email?: string
      bio?: string
      message?: string
    }
    if (data) {
      profile.nickname = data.nickname || form.nickname
      profile.email = data.email || form.email
      profile.bio = data.bio || form.bio
    }
    form.password = ''
    message.value = data?.message || '资料已更新'
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.value = `保存失败：${err.message || '网络错误'}`
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page">
    <AppNav />
    <div class="layout">
      <section class="display">
        <div class="avatar">{{ profile.nickname.slice(0, 1) }}</div>
        <div class="info">
          <h1>{{ profile.nickname }}</h1>
          <p><span>用户名</span>{{ profile.username }}</p>
          <p><span>邮箱</span>{{ profile.email || '未填写' }}</p>
          <p><span>简介</span>{{ profile.bio || '这个人很懒，什么都没写' }}</p>
        </div>
      </section>

      <section class="edit">
        <h2>编辑资料</h2>
        <form @submit.prevent="handleSubmit">
          <label>
            昵称
            <input v-model="form.nickname" type="text" placeholder="请输入昵称" />
          </label>
          <label>
            邮箱
            <input v-model="form.email" type="email" placeholder="请输入邮箱" />
          </label>
          <label>
            个人简介
            <textarea v-model="form.bio" rows="4" placeholder="介绍一下自己..." />
          </label>
          <label>
            新密码（可选）
            <input v-model="form.password" type="password" placeholder="不修改请留空" />
          </label>
          <p v-if="message" class="msg">{{ message }}</p>
          <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存修改' }}</button>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: transparent;
}

.layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  max-width: 720px;
  margin: 0 auto;
}

.display,
.edit {
  background: #fffdf9;
  border: 1px solid #ddd2c4;
  padding: 1.25rem 1.4rem;
}

.display {
  display: flex;
  gap: 1.25rem;
  align-items: center;
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b3a2a, #c47a4a);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 700;
  flex-shrink: 0;
  border: 2px solid #e8b86d;
}

.info h1 {
  margin: 0 0 0.55rem;
  font-size: 1.35rem;
  color: #2f2a26;
}

.info p {
  margin: 0.25rem 0;
  color: #5a4a3a;
  font-size: 0.92rem;
}

.info span {
  display: inline-block;
  width: 3.2em;
  color: #8a7a6a;
}

.edit h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
  color: #3d2f24;
}

form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.88rem;
  color: #5a4a3a;
}

input,
textarea {
  padding: 0.6rem 0.75rem;
  border: 1px solid #cfc5b8;
  background: #fff;
  outline: none;
  font: inherit;
}

button {
  align-self: flex-start;
  margin-top: 0.3rem;
  padding: 0.65rem 1.3rem;
  border: none;
  background: #8b3a2a;
  color: #fff;
  cursor: pointer;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.msg {
  margin: 0;
  color: #1e7a46;
  font-size: 0.88rem;
}
</style>
