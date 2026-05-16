<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const success = await authStore.login(username.value, password.value)
    if (success) {
      const role = authStore.userRole

      if (role === 'student') {
        router.push('/student/dashboard')
      } else if (role === 'teacher') {
        router.push('/teacher/dashboard')
      } else if (role === 'admin') {
        router.push('/dashboard')
      } else {
        router.push('/')
      }
    } else {
      error.value = 'Login failed. Please check credentials.'
    }
  } catch (err) {
    console.error(err)
    error.value = 'Invalid username or password.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <p class="text-xs uppercase tracking-[0.24em] text-cyan-700/80">Campus Flow</p>
      <h1 class="mt-2 text-3xl font-semibold text-slate-900">Welcome Back</h1>
      <p class="mt-1 text-sm text-slate-600">Sign in to manage academics, enrollment, and people.</p>

      <form class="mt-6 space-y-4" @submit.prevent="handleLogin">
        <div>
          <label class="auth-label">Username</label>
          <input v-model="username" type="text" class="auth-input" placeholder="admin" required />
        </div>
        <div>
          <label class="auth-label">Password</label>
          <input v-model="password" type="password" class="auth-input" placeholder="Password" required />
        </div>

        <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {{ error }}
        </div>

        <button type="submit" :disabled="loading" class="auth-button">
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <p class="mt-5 text-sm text-slate-600">
        New here?
        <RouterLink to="/register" class="font-semibold text-cyan-700 hover:text-cyan-800">Create account</RouterLink>
      </p>
    </div>
  </div>
</template>
