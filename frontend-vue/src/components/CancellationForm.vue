<script setup>
import { reactive, watch, ref } from 'vue'
import { cancelarReserva } from '../services/fgoService'
import { useToast } from '../composables/useToast'

const props = defineProps({
  prefillData: {
    type: Object,
    default: () => ({})
  }
})

const loading = ref(false)
const { addToast } = useToast()

const result = ref(null)

const formState = reactive({
  codigo_agente_financeiro: '',
  codigo_fundo_garantidor: '',
  numero_reserva_pre_validacao: ''
})

watch(() => props.prefillData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    formState.codigo_agente_financeiro = newData.agente || ''
    formState.codigo_fundo_garantidor = newData.fundo || ''
    formState.numero_reserva_pre_validacao = newData.reserva || ''
  }
}, { immediate: true, deep: true })

const handleSubmit = async () => {
  const payload = {
    "Codigo Agente Financeiro": parseInt(formState.codigo_agente_financeiro, 10),
    "Codigo Fundo Garantidor": parseInt(formState.codigo_fundo_garantidor, 10),
    "Numero Reserva Pre Validacao": parseInt(formState.numero_reserva_pre_validacao, 10)
  }

  loading.value = true
  try {
    const response = await cancelarReserva(payload)
    result.value = response.data
    addToast('Solicitação de cancelamento concluída!', 'success')
  } catch (err) {
    // Handled globally by Axios interceptors
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="panel-header">
      <h2>Cancelamento de Reserva</h2>
      <p>Solicita o cancelamento imediato de uma reserva de pré-validação registrada anteriormente no GFG.</p>
    </div>

    <div class="form-grid single-card">
      <div class="form-card">
        <h3 class="card-title">Identificação da Reserva</h3>
        <form @submit.prevent="handleSubmit" class="fgo-form">
          <div class="form-group">
            <label>Código do Agente Financeiro <span class="required">*</span></label>
            <input type="number" v-model="formState.codigo_agente_financeiro" required placeholder="Código atribuído pelo Administrador" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Código do Fundo Garantidor <span class="required">*</span></label>
            <input type="number" v-model="formState.codigo_fundo_garantidor" required placeholder="Identificador do fundo" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Número da Reserva de Pré-validação <span class="required">*</span></label>
            <input type="number" v-model="formState.numero_reserva_pre_validacao" required placeholder="Número registrado no GFG" :disabled="loading">
          </div>

          <div class="form-actions align-left">
            <button type="submit" class="btn btn-danger" :disabled="loading">
              <span class="btn-text">Confirmar Cancelamento de Reserva</span>
              <span class="spinner" v-if="loading"></span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Result Card -->
    <div v-if="result" class="result-card">
      <div class="result-header">
        <h4>Status do Cancelamento</h4>
        <span :class="['badge', result.status === 'SUCESSO' ? 'badge-success' : 'badge-danger']">
          {{ result.status === 'SUCESSO' ? 'Sucesso' : 'Falhou' }}
        </span>
      </div>
      <div class="result-content">
        <div class="result-item">
          <span class="result-label">Status:</span>
          <span class="result-value">{{ result.status }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Mensagem:</span>
          <span class="result-value">{{ result.mensagem }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
