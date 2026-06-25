import axios from 'axios'
import { useToast } from '../composables/useToast'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add response interceptor for global error handling (401, 403, 422, 500)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { addToast } = useToast()
    let message = 'Ocorreu um erro na comunicação.'

    if (error.response) {
      const { status, data } = error.response
      // BB details are usually in 'detail' or 'message' property
      const detail = data?.detail || data?.message || ''

      if (status === 401) {
        message = detail || 'Não autorizado. Verifique suas credenciais de acesso.'
      } else if (status === 403) {
        message = detail || 'Acesso negado. Permissões insuficientes.'
      } else if (status === 422) {
        message = detail || 'Erro de validação de dados. Verifique os dados enviados.'
      } else if (status === 500) {
        message = detail || 'Erro interno no servidor do Banco do Brasil.'
      } else {
        message = detail || `Erro HTTP ${status}: ${error.message}`
      }
    } else if (error.request) {
      message = 'Sem resposta do servidor. Verifique sua conexão de rede.'
    } else {
      message = error.message
    }

    addToast(message, 'error')
    return Promise.reject(error)
  }
)

// Custom communication helper for non-API route health check
export const checkBackendHealth = () => {
  return axios.get('/health', {
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

export default api
