import api from './api'

export const preValidacao = (payload) =>
  api.post('/pre-validacoes', payload)

export const preValidacaoReserva = (payload) =>
  api.post('/pre-validacoes/reservas', payload)

export const cancelarReserva = (payload) =>
  api.put('/reservas/cancelamentos', payload)
