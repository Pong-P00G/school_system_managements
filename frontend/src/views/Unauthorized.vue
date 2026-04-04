<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleRegisterAccount = async () => {
  await authStore.logout()
  router.push('/register')
}

const handleSwitchAccount = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="auth-page relative z-50">
    <div class="auth-card text-center relative z-[60]">
      <p class="text-xs uppercase tracking-[0.24em] text-amber-700/80">Access Restricted</p>
      <h1 class="mt-2 text-3xl font-semibold text-slate-900">You do not have permission</h1>
      <p class="mt-2 text-sm text-slate-600">Your account does not have access to this page.</p>

      <div class="mt-6 flex justify-center gap-3">
        <button @click="handleRegisterAccount"
          class="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-700 transition shadow-lg shadow-cyan-900/20">
          Go to Register
        </button>
        <button @click="handleSwitchAccount"
          class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-cyan-600 hover:text-cyan-700 transition cursor-pointer">
          Switch Account
        </button>
      </div>
    </div>
  </div>
</template>
