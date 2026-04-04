import { reactive } from 'vue'

const state = reactive({
  toasts: []
})

let nextId = 0

export function useToast() {
  const showToast = (message, type = 'info', duration = 3500) => {
    const id = nextId++
    state.toasts.push({ id, message, type, visible: true })

    setTimeout(() => {
      dismissToast(id)
    }, duration)
  }

  const dismissToast = (id) => {
    const index = state.toasts.findIndex(t => t.id === id)
    if (index !== -1) {
      state.toasts[index].visible = false
      setTimeout(() => {
        state.toasts = state.toasts.filter(t => t.id !== id)
      }, 300)
    }
  }

  return {
    toasts: state.toasts,
    showToast,
    dismissToast,
    success: (msg, dur) => showToast(msg, 'success', dur),
    error: (msg, dur) => showToast(msg, 'error', dur),
    warning: (msg, dur) => showToast(msg, 'warning', dur),
    info: (msg, dur) => showToast(msg, 'info', dur),
  }
}
