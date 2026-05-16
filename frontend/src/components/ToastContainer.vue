<template>
  <div class="fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 pointer-events-none max-w-[400px]">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['flex items-center gap-3 py-3.5 px-4 rounded-xl text-white text-sm font-medium cursor-pointer pointer-events-auto backdrop-blur-[12px] border border-white/15 transition-all duration-300 hover:-translate-x-1', { 'opacity-0 translate-x-full': !toast.visible }, toast.type === 'success' ? 'bg-gradient-to-br from-emerald-600 to-emerald-500' : toast.type === 'error' ? 'bg-gradient-to-br from-red-600 to-red-500' : toast.type === 'warning' ? 'bg-gradient-to-br from-amber-600 to-amber-500' : 'bg-gradient-to-br from-blue-600 to-blue-500']"
        style="box-shadow: 0 8px 30px rgba(0,0,0,0.15), 0 2px 8px rgba(0,0,0,0.1)"
        @click="dismissToast(toast.id)"
      >
        <div class="shrink-0 w-5 h-5">
          <svg v-if="toast.type === 'success'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
          <svg v-else-if="toast.type === 'error'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
          <svg v-else-if="toast.type === 'warning'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
        </div>
        <span class="flex-1 leading-snug">{{ toast.message }}</span>
        <button class="shrink-0 bg-transparent border-0 text-white/70 cursor-pointer p-0.5 rounded flex items-center justify-center transition-colors duration-150 hover:text-white hover:bg-white/15" @click.stop="dismissToast(toast.id)">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToast } from '../composables/useToast'
const { toasts, dismissToast } = useToast()
</script>

<style scoped>
.toast-enter-active { animation: toast-in 0.35s cubic-bezier(0.21, 1.02, 0.73, 1); }
.toast-leave-active { animation: toast-out 0.3s cubic-bezier(0.06, 0.71, 0.55, 1) forwards; }
@keyframes toast-in { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
@keyframes toast-out { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }
</style>
