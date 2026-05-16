<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
} from '../services/api'
import { useToast } from '../composables/useToast'

const router = useRouter()
const toast = useToast()

const notifications = ref([])
const total = ref(0)
const unreadCount = ref(0)
const loading = ref(false)
const filterType = ref('all')
const currentPage = ref(1)
const pageSize = 20

const typeColors = {
  info: '#3b82f6',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
}

const typeIcons = {
  info: 'ℹ️',
  success: '✅',
  warning: '⚠️',
  error: '❌',
}

const typeLabels = {
  all: 'All',
  info: 'Info',
  success: 'Success',
  warning: 'Warning',
  error: 'Error',
}

const totalPages = computed(() => Math.ceil(total.value / pageSize))

async function loadNotifications() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize,
    }
    if (filterType.value !== 'all') {
      params.notification_type = filterType.value
    }
    const [notifRes, countRes] = await Promise.all([
      getNotifications(params.skip, params.limit, false, params.notification_type || null),
      getUnreadNotificationCount(),
    ])
    notifications.value = notifRes.data.notifications || []
    total.value = notifRes.data.total || 0
    unreadCount.value = countRes.data.unread_count || 0
  } catch (err) {
    console.error('Failed to load notifications:', err)
    toast.error('Failed to load notifications')
  } finally {
    loading.value = false
  }
}

async function markAsRead(notification) {
  try {
    await markNotificationRead(notification.notification_id)
    notification.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (err) {
    console.error('Failed to mark as read:', err)
  }
}

async function markAllAsRead() {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => (n.is_read = true))
    unreadCount.value = 0
    toast.success('All notifications marked as read')
  } catch (err) {
    console.error('Failed to mark all as read:', err)
    toast.error('Failed to mark all as read')
  }
}

async function removeNotification(notification, event) {
  event.stopPropagation()
  try {
    await deleteNotification(notification.notification_id)
    notifications.value = notifications.value.filter(
      n => n.notification_id !== notification.notification_id
    )
    total.value = Math.max(0, total.value - 1)
    if (!notification.is_read) {
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
    toast.success('Notification deleted')
  } catch (err) {
    console.error('Failed to delete notification:', err)
    toast.error('Failed to delete notification')
  }
}

function applyFilter(type) {
  filterType.value = type
  currentPage.value = 1
  loadNotifications()
}

function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadNotifications()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(loadNotifications)
</script>

<template>
  <div class="max-w-[800px] mx-auto">
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 m-0 mb-1">Notifications</h1>
        <p class="text-sm text-gray-500 m-0">
          {{ unreadCount > 0 ? `${unreadCount} unread` : 'No unread notifications' }}
        </p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="unreadCount > 0"
          class="inline-flex items-center gap-1.5 py-2 px-4 border-0 rounded-lg text-[13px] font-medium cursor-pointer transition-all duration-200 bg-gray-100 text-gray-700 hover:bg-gray-200"
          @click="markAllAsRead"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
          Mark all read
        </button>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="flex gap-1 mb-5 bg-gray-100 p-1 rounded-[10px] w-fit">
      <button
        v-for="type in Object.keys(typeLabels)"
        :key="type"
        class="py-1.5 px-3.5 border-0 rounded-[7px] text-[13px] font-medium cursor-pointer transition-all duration-200"
        :class="filterType === type ? 'bg-white text-gray-900 shadow-sm' : 'bg-transparent text-gray-500 hover:text-gray-700'"
        @click="applyFilter(type)"
      >
        {{ typeLabels[type] }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-15 px-5 text-gray-400">
      <div class="w-8 h-8 border-3 border-gray-200 border-t-blue-600 rounded-full animate-spin mb-3"></div>
      <p>Loading notifications...</p>
    </div>

    <!-- Notifications List -->
    <div v-else-if="notifications.length > 0" class="flex flex-col gap-2">
      <div
        v-for="notif in notifications"
        :key="notif.notification_id"
        class="group flex gap-4 py-4 px-5 bg-white rounded-xl border cursor-pointer transition-all duration-200 relative"
        :class="notif.is_read ? 'border-gray-100 hover:border-gray-200 hover:shadow-sm' : 'bg-blue-50 border-blue-200 hover:bg-blue-100'"
        @click="markAsRead(notif)"
      >
        <div class="pt-0.5">
          <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: typeColors[notif.notification_type] || '#3b82f6' }"></div>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1.5">
            <span class="inline-flex items-center gap-1 py-0.5 px-2 rounded-md text-[11px] font-semibold" :style="{
              backgroundColor: (typeColors[notif.notification_type] || '#3b82f6') + '20',
              color: typeColors[notif.notification_type] || '#3b82f6'
            }">
              {{ typeIcons[notif.notification_type] || 'ℹ️' }}
              {{ typeLabels[notif.notification_type] || 'Info' }}
            </span>
            <span class="text-xs text-gray-400">{{ formatDate(notif.created_at) }}</span>
          </div>
          <h3 class="text-[15px] font-semibold text-gray-900 m-0 mb-1">{{ notif.title }}</h3>
          <p v-if="notif.message" class="text-[13px] text-gray-500 leading-relaxed m-0 line-clamp-3">{{ notif.message }}</p>
          <div class="mt-2">
            <span v-if="!notif.is_read" class="inline-block py-0.5 px-2 bg-blue-600 text-white rounded-md text-[11px] font-semibold">New</span>
          </div>
        </div>
        <button
          class="absolute top-3 right-3 flex items-center justify-center w-7 h-7 border-0 rounded-md bg-transparent text-gray-300 cursor-pointer opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-red-50 hover:text-red-500"
          @click="removeNotification(notif, $event)"
          title="Delete notification"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-15 px-5 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-gray-300 mb-4"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
      <h3 class="text-lg font-semibold text-gray-700 m-0 mb-2">No notifications</h3>
      <p class="text-sm text-gray-400 m-0">You're all caught up! New notifications will appear here.</p>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-4 mt-6 py-4">
      <button
        class="py-2 px-4 border border-gray-200 rounded-lg bg-white text-gray-700 text-[13px] font-medium cursor-pointer transition-all duration-200 hover:border-blue-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        Previous
      </button>
      <span class="text-[13px] text-gray-500">Page {{ currentPage }} of {{ totalPages }}</span>
      <button
        class="py-2 px-4 border border-gray-200 rounded-lg bg-white text-gray-700 text-[13px] font-medium cursor-pointer transition-all duration-200 hover:border-blue-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>


