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
      class="notification-bell-btn"
      @click.stop="showDropdown = !showDropdown"
      :title="unreadCount > 0 ? `${unreadCount} unread notifications` : 'No new notifications'"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
      <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <Transition name="dropdown">
      <div v-if="showDropdown" class="notification-dropdown">
        <div class="notification-dropdown-header">
          <h3>Notifications</h3>
          <div class="notification-dropdown-actions">
            <button v-if="unreadCount > 0" class="mark-all-btn" @click="markAllAsRead">
              Mark all read
            </button>
            <button class="view-all-btn" @click="goToNotifications">
              View all
            </button>
          </div>
        </div>

        <div class="notification-list">
          <div v-if="loading" class="notification-loading">
            Loading...
          </div>
          <div v-else-if="localNotifications.length === 0" class="notification-empty">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
              style="color: #9ca3af; margin-bottom: 8px"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <p>No new notifications</p>
          </div>
          <div
            v-for="notif in localNotifications"
            :key="notif.notification_id"
            class="notification-item"
            :class="{ unread: !notif.is_read }"
            @click="viewDetails(notif)"
          >
            <div
              class="notification-type-dot"
              :style="{ backgroundColor: typeColors[notif.notification_type] || '#3b82f6' }"
            ></div>
            <div class="notification-content">
              <div class="notification-title">{{ notif.title }}</div>
              <div v-if="notif.message" class="notification-message">{{ notif.message }}</div>
              <div class="notification-time">{{ formatTime(notif.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Notification Detail Modal -->
    <Transition name="modal">
      <div v-if="showDetailModal" class="notification-modal-overlay" @click.self="showDetailModal = false">
        <div class="notification-modal">
          <div class="notification-modal-header">
            <h3>{{ selectedNotification?.title }}</h3>
            <button @click="showDetailModal = false" class="close-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="notification-modal-body">
            <div class="notification-meta">
              <span class="notification-type-badge" :style="{
                backgroundColor: typeColors[selectedNotification?.notification_type] || '#3b82f6',
                color: 'white'
              }">
                {{ selectedNotification?.notification_type || 'info' }}
              </span>
              <span class="notification-date">
                {{ selectedNotification?.created_at ? new Date(selectedNotification.created_at).toLocaleString() : '' }}
              </span>
            </div>
            <div class="notification-message-full">
              {{ selectedNotification?.message || 'No message' }}
            </div>
          </div>
          <div class="notification-modal-footer">
            <button @click="showDetailModal = false" class="btn-close">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.notification-bell-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
}

.notification-bell-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #ef4444;
  color: white;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 480px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15), 0 1px 3px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.notification-dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
}

.notification-dropdown-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.notification-dropdown-actions {
  display: flex;
  gap: 8px;
}

.mark-all-btn,
.view-all-btn {
  padding: 4px 10px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mark-all-btn {
  background: #eff6ff;
  color: #2563eb;
}

.mark-all-btn:hover {
  background: #dbeafe;
}

.view-all-btn {
  background: #f3f4f6;
  color: #374151;
}

.view-all-btn:hover {
  background: #e5e7eb;
}

.notification-list {
  max-height: 380px;
  overflow-y: auto;
}

.notification-loading,
.notification-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9ca3af;
  font-size: 14px;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.15s ease;
  border-bottom: 1px solid #f9fafb;
}

.notification-item:hover {
  background: #f9fafb;
}

.notification-item.unread {
  background: #f0f7ff;
}

.notification-item.unread:hover {
  background: #e5f0ff;
}

.notification-type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 2px;
  line-height: 1.4;
}

.notification-message {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 11px;
  color: #9ca3af;
}

/* Transition */
.dropdown-enter-active {
  transition: all 0.2s ease-out;
}
.dropdown-leave-active {
  transition: all 0.15s ease-in;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

/* Modal */
.notification-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  padding: 1rem;
}

.notification-modal {
  width: 100%;
  max-width: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.notification-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f3f4f6;
}

.notification-modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.notification-modal-body {
  padding: 24px;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.notification-type-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.notification-date {
  font-size: 13px;
  color: #6b7280;
}

.notification-message-full {
  font-size: 15px;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
}

.notification-modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: flex-end;
}

.btn-close {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: #f3f4f6;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-close:hover {
  background: #e5e7eb;
}

.modal-enter-active {
  transition: all 0.2s ease-out;
}
.modal-leave-active {
  transition: all 0.15s ease-in;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .notification-modal {
  transform: scale(0.95) translateY(20px);
}
.modal-leave-to .notification-modal {
  transform: scale(0.98) translateY(10px);
}
</style>
