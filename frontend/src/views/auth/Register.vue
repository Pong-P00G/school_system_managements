<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { register } from '../../services/api'

const router = useRouter()

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})
const loading = ref(false)
const error = ref('')
const success = ref('')

const handleRegister = async () => {
  error.value = ''
  success.value = ''

  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Passwords do not match.'
    return
  }

  loading.value = true
  try {
    await register(form.value.username, form.value.email, form.value.password)
    success.value = 'Account created successfully. Redirecting to login...'
    setTimeout(() => {
      router.push('/login')
    }, 900)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create account.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <p class="text-xs uppercase tracking-[0.24em] text-cyan-700/80">Campus Flow</p>
      <h1 class="mt-2 text-3xl font-semibold text-slate-900">Create Account</h1>
      <p class="mt-1 text-sm text-slate-600">Register a new user for the School Management System.</p>

      <form class="mt-6 space-y-4" @submit.prevent="handleRegister">
        <div>
          <label class="auth-label">Username</label>
          <input v-model="form.username" type="text" class="auth-input" placeholder="new-user" required />
        </div>
        <div>
          <label class="auth-label">Email</label>
          <input v-model="form.email" type="email" class="auth-input" placeholder="user@school.edu" required />
        </div>
        <div>
          <label class="auth-label">Password</label>
          <input v-model="form.password" type="password" class="auth-input" placeholder="Password" required />
        </div>
        <div>
          <label class="auth-label">Confirm Password</label>
          <input v-model="form.confirmPassword" type="password" class="auth-input" placeholder="Confirm password" required />
        </div>

        <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {{ error }}
        </div>
        <div v-if="success" class="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {{ success }}
        </div>

        <button type="submit" :disabled="loading" class="auth-button">
          {{ loading ? 'Creating account...' : 'Create Account' }}
        </button>
      </form>

      <p class="mt-5 text-sm text-slate-600">
        Already have an account?
        <RouterLink to="/login" class="font-semibold text-cyan-700 hover:text-cyan-800">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>
