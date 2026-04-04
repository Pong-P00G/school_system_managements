<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="auth-page">
    <div class="auth-card text-center">
      <p class="text-xs uppercase tracking-[0.24em] text-slate-500">Error 404</p>
      <h1 class="mt-2 text-3xl font-semibold text-slate-900">Page not found</h1>
      <p class="mt-2 text-sm text-slate-600">The page you requested does not exist or may have moved.</p>

      <div class="mt-6 flex justify-center">
        <RouterLink to="/" class="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-700">Return to Dashboard</RouterLink>
      </div>
    </div>
  </div>
</template>
