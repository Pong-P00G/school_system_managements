<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotifications } from '../composables/useNotifications'
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const showDropdown = ref(false)
const localNotifications = ref([])
const loading = ref(false)

const { unreadCount, notifications: realtimeNotifications } = useNotifications()

const typeColors = {
  info: '#3b82f6',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
}

async function loadNotifications() {
  loading.value = true
  try {
    const res = await getNotifications(0, 5, true)
    localNotifications.value = res.data.notifications || []
  } catch (err) {
    console.error('Failed to load notifications:', err)
  } finally {
    loading.value = false
  }
}

const showDetailModal = ref(false)
const selectedNotification = ref(null)

async function viewDetails(notif) {
  selectedNotification.value = notif
  showDetailModal.value = true
  if (!notif.is_read) {
    await markAsRead(notif)
  }
}

async function markAsRead(notification) {
  try {
    await markNotificationRead(notification.notification_id)
    notification.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (err) {
    console.error('Failed to mark notification as read:', err)
  }
}

async function markAllAsRead() {
  try {
    await markAllNotificationsRead()
    localNotifications.value = []
    unreadCount.value = 0
  } catch (err) {
    console.error('Failed to mark all as read:', err)
  }
}

function goToNotifications() {
  showDropdown.value = false
  const role = authStore.userRole
  if (role === 'student') router.push('/student/notifications')
  else if (role === 'teacher') router.push('/teacher/notifications')
  else router.push('/notifications')
}

function handleClickOutside(event) {
  const el = document.querySelector('.notification-bell-container')
  if (el && !el.contains(event.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  loadNotifications()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

watch(showDropdown, (val) => {
  if (val) loadNotifications()
})

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}
</script>

<template>
  <div class="notification-bell-container" style="position: relative">
    <button
      class="relative flex items-center justify-center w-9 h-9 border-0 rounded-lg bg-transparent text-gray-500 cursor-pointer transition-all duration-200 hover:bg-gray-100 hover:text-gray-700"
      @click.stop="showDropdown = !showDropdown"
      :title="unreadCount > 0 ? `${unreadCount} unread notifications` : 'No new notifications'"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>
      <span v-if="unreadCount > 0" class="absolute top-0.5 right-0.5 min-w-4 h-4 px-1 rounded-lg bg-red-500 text-white text-[10px] font-bold leading-4 text-center shadow-[0_2px_4px_rgba(239,68,68,0.3)]">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <Transition name="dropdown">
      <div v-if="showDropdown" class="absolute top-[calc(100%+8px)] right-0 w-[360px] max-h-[480px] bg-white rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.15),0_1px_3px_rgba(0,0,0,0.1)] z-[1000] overflow-hidden">
        <div class="flex items-center justify-between py-4 px-5 border-b border-gray-100">
          <h3 class="m-0 text-[15px] font-semibold text-gray-900">Notifications</h3>
          <div class="flex gap-2">
            <button v-if="unreadCount > 0" class="py-1 px-2.5 border-0 rounded-md text-xs font-medium cursor-pointer transition-all duration-200 bg-blue-50 text-blue-600 hover:bg-blue-100" @click="markAllAsRead">Mark all read</button>
            <button class="py-1 px-2.5 border-0 rounded-md text-xs font-medium cursor-pointer transition-all duration-200 bg-gray-100 text-gray-700 hover:bg-gray-200" @click="goToNotifications">View all</button>
          </div>
        </div>

        <div class="max-h-[380px] overflow-y-auto">
          <div v-if="loading" class="flex flex-col items-center justify-center py-10 px-5 text-gray-400 text-sm">Loading...</div>
          <div v-else-if="localNotifications.length === 0" class="flex flex-col items-center justify-center py-10 px-5 text-gray-400 text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 mb-2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
            <p>No new notifications</p>
          </div>
          <div
            v-for="notif in localNotifications"
            :key="notif.notification_id"
            class="flex gap-3 py-3 px-5 cursor-pointer transition-colors duration-150 border-b border-gray-50"
            :class="notif.is_read ? 'hover:bg-gray-50' : 'bg-blue-50 hover:bg-blue-100'"
            @click="viewDetails(notif)"
          >
            <div class="w-2 h-2 rounded-full mt-1.5 shrink-0" :style="{ backgroundColor: typeColors[notif.notification_type] || '#3b82f6' }"></div>
            <div class="flex-1 min-w-0">
              <div class="text-[13px] font-semibold text-gray-900 mb-0.5 leading-snug">{{ notif.title }}</div>
              <div v-if="notif.message" class="text-xs text-gray-500 leading-snug mb-1 line-clamp-2">{{ notif.message }}</div>
              <div class="text-[11px] text-gray-400">{{ formatTime(notif.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Notification Detail Modal -->
    <Transition name="modal">
      <div v-if="showDetailModal" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" @click.self="showDetailModal = false">
        <div class="w-full max-w-[500px] bg-white rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.3)] overflow-hidden">
          <div class="flex items-center justify-between py-5 px-6 border-b border-gray-100">
            <h3 class="m-0 text-lg font-semibold text-gray-900">{{ selectedNotification?.title }}</h3>
            <button @click="showDetailModal = false" class="flex items-center justify-center w-8 h-8 border-0 rounded-md bg-transparent text-gray-500 cursor-pointer transition-all duration-150 hover:bg-gray-100 hover:text-gray-900">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="p-6">
            <div class="flex items-center gap-3 mb-4">
              <span class="py-1 px-3 rounded-xl text-xs font-semibold uppercase tracking-wide text-white" :style="{ backgroundColor: typeColors[selectedNotification?.notification_type] || '#3b82f6' }">
                {{ selectedNotification?.notification_type || 'info' }}
              </span>
              <span class="text-[13px] text-gray-500">
                {{ selectedNotification?.created_at ? new Date(selectedNotification.created_at).toLocaleString() : '' }}
              </span>
            </div>
            <div class="text-[15px] leading-relaxed text-gray-700 whitespace-pre-wrap">
              {{ selectedNotification?.message || 'No message' }}
            </div>
          </div>
          <div class="py-4 px-6 border-t border-gray-100 flex justify-end">
            <button @click="showDetailModal = false" class="py-2 px-5 border-0 rounded-md bg-gray-100 text-gray-700 text-sm font-medium cursor-pointer transition-all duration-150 hover:bg-gray-200">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active { transition: all 0.2s ease-out; }
.dropdown-leave-active { transition: all 0.15s ease-in; }
.dropdown-enter-from { opacity: 0; transform: translateY(-8px) scale(0.96); }
.dropdown-leave-to { opacity: 0; transform: translateY(-4px) scale(0.98); }
.modal-enter-active { transition: all 0.2s ease-out; }
.modal-leave-active { transition: all 0.15s ease-in; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
