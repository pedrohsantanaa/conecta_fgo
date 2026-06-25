import { ref } from 'vue'
import { useToast } from './useToast'

export function useFgoApi() {
  const { addToast } = useToast()
  const loading = ref(false)
  const error = ref(null)

  const request = async (path, method = 'GET', payload = null, silent = false) => {
    loading.value = true
    error.value = null
    
    // Resolve relative path to absolute
    const url = `${window.location.origin}${path}`
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    }
    
    if (payload !== null) {
      options.body = JSON.stringify(payload)
    }

    try {
      const response = await fetch(url, options)
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `Erro na requisição HTTP: ${response.statusText}`)
      }
      
      return await response.json()
    } catch (err) {
      error.value = err.message
      if (!silent) {
        addToast(err.message, 'error')
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    request
  }
}
