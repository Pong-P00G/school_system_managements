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
  <div class="notifications-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Notifications</h1>
        <p class="page-subtitle">
          {{ unreadCount > 0 ? `${unreadCount} unread` : 'No unread notifications' }}
        </p>
      </div>
      <div class="page-actions">
        <button
          v-if="unreadCount > 0"
          class="btn btn-secondary"
          @click="markAllAsRead"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="9 11 12 14 22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
          Mark all read
        </button>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="filter-tabs">
      <button
        v-for="type in Object.keys(typeLabels)"
        :key="type"
        class="filter-tab"
        :class="{ active: filterType === type }"
        @click="applyFilter(type)"
      >
        {{ typeLabels[type] }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading notifications...</p>
    </div>

    <!-- Notifications List -->
    <div v-else-if="notifications.length > 0" class="notifications-list">
      <div
        v-for="notif in notifications"
        :key="notif.notification_id"
        class="notification-card"
        :class="{ unread: !notif.is_read }"
        @click="markAsRead(notif)"
      >
        <div class="notification-indicator">
          <div
            class="type-dot"
            :style="{ backgroundColor: typeColors[notif.notification_type] || '#3b82f6' }"
          ></div>
        </div>
        <div class="notification-body">
          <div class="notification-header">
            <span class="notification-type-badge" :style="{
              backgroundColor: (typeColors[notif.notification_type] || '#3b82f6') + '20',
              color: typeColors[notif.notification_type] || '#3b82f6'
            }">
              {{ typeIcons[notif.notification_type] || 'ℹ️' }}
              {{ typeLabels[notif.notification_type] || 'Info' }}
            </span>
            <span class="notification-date">{{ formatDate(notif.created_at) }}</span>
          </div>
          <h3 class="notification-title">{{ notif.title }}</h3>
          <p v-if="notif.message" class="notification-message">{{ notif.message }}</p>
          <div class="notification-footer">
            <span v-if="!notif.is_read" class="unread-badge">New</span>
          </div>
        </div>
        <button
          class="notification-delete"
          @click="removeNotification(notif, $event)"
          title="Delete notification"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        style="color: #d1d5db; margin-bottom: 16px"
      >
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      <h3>No notifications</h3>
      <p>You're all caught up! New notifications will appear here.</p>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination-wrapper">
      <button
        class="page-btn"
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        Previous
      </button>
      <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
      <button
        class="page-btn"
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>

<style scoped>
.notifications-page {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.page-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

/* Filter Tabs */
.filter-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 10px;
  width: fit-content;
}

.filter-tab {
  padding: 6px 14px;
  border: none;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab:hover {
  color: #374151;
}

.filter-tab.active {
  background: white;
  color: #111827;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Notifications List */
.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-card {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #f3f4f6;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.notification-card:hover {
  border-color: #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.notification-card.unread {
  background: #f0f7ff;
  border-color: #bfdbfe;
}

.notification-card.unread:hover {
  background: #e5f0ff;
}

.notification-indicator {
  padding-top: 2px;
}

.type-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.notification-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.notification-date {
  font-size: 12px;
  color: #9ca3af;
}

.notification-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 4px;
}

.notification-message {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-footer {
  margin-top: 8px;
}

.unread-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #2563eb;
  color: white;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.notification-delete {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #d1d5db;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
}

.notification-card:hover .notification-delete {
  opacity: 1;
}

.notification-delete:hover {
  background: #fef2f2;
  color: #ef4444;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: #9ca3af;
  margin: 0;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Pagination */
.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding: 16px 0;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: #2563eb;
  color: #2563eb;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #6b7280;
}
</style>
