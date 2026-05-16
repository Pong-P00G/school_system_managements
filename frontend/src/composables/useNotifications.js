import { ref, onMounted, onUnmounted } from 'vue'
import { useToast } from './useToast'

const unreadCount = ref(0)
const notifications = ref([])
let eventSource = null

export function useNotifications() {
  const toast = useToast()

  const connect = () => {
    const token = localStorage.getItem('access_token')
    if (!token || eventSource) return

    const baseURL = window.location.origin
    eventSource = new EventSource(`${baseURL}/api/v1/notifications/stream?token=${encodeURIComponent(token)}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'unread_count') {
          unreadCount.value = data.count
        } else if (data.type === 'new_notification') {
          const notif = data.notification
          notifications.value.unshift(notif)
          unreadCount.value++
          
          // Show toast notification
          toast.info(notif.title || 'New notification', {
            description: notif.message,
            duration: 5000
          })
        }
      } catch (e) {
        console.error('Failed to parse notification:', e)
      }
    }

    eventSource.onerror = () => {
      console.warn('Notification stream disconnected, reconnecting...')
      disconnect()
      setTimeout(connect, 5000)
    }
  }

  const disconnect = () => {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  const markAsRead = (notificationId) => {
    const index = notifications.value.findIndex(n => n.notification_id === notificationId)
    if (index !== -1 && !notifications.value[index].is_read) {
      notifications.value[index].is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return {
    unreadCount,
    notifications,
    connect,
    disconnect,
    markAsRead
  }
}
