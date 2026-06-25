import { ref } from 'vue'

const toasts = ref([])

export function useToast() {
  const addToast = (message, type = 'info', duration = 5000) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 9)
    let icon = 'ℹ️'
    if (type === 'success') icon = '✅'
    if (type === 'error') icon = '❌'

    toasts.value.push({ id, message, type, icon })

    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  const removeToast = (id) => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return {
    toasts,
    addToast,
    removeToast
  }
}
