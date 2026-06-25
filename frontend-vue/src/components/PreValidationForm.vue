<script setup>
import { ref, reactive } from 'vue'
import { preValidacao, preValidacaoReserva } from '../services/fgoService'
import { useToast } from '../composables/useToast'

const props = defineProps({
  withReserve: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['reserveCreated'])

const loading = ref(false)
const { addToast } = useToast()

const result = ref(null)

const formState = reactive({
  codigoAgenteFinanceiro: '',
  codigoFundoGarantidor: '',
  numeroAgenciaContratanteOperacao: '',
  codigoIdentificadorExternoOperacao: '',
  codigoIbgeMunicipio: '',
  codigoTipoPessoa: '1',
  codigoIdentificadorSrf: '',
  codigoTipoPublicoAlvo: '',
  valorFaturamentoBrutoAnual: '',
  numeroCpfQualificadorOperacao: '',
  valorOperacaoCredito: '',
  percentualGarantiaOperacaoCredito: '',
  codigoTipoModalidadeCredito: '',
  codigoTipoFinalidadeCredito: '',
  codigoTipoFonteRecurso: '',
  codigoTipoProgramaCredito: '',
  dataFormalizacaoOperacao: '',
  dataVencimentoOperacao: '',
  codigoTipoCronogramaAmortizacao: '',
  codigoTipoCondicaoEspecial: '',
  codigoTipoFormalizacao: '',
  valorSubsidioCredito: '',
  dataDespachoExternoOperacao: props.withReserve ? '' : '0',
  valorCondicaoEspecial: ''
})

const getFormattedDates = () => {
  const today = new Date()
  const nextYear = new Date()
  nextYear.setFullYear(today.getFullYear() + 1)

  const format = (date) => {
    const yyyy = date.getFullYear()
    const mm = String(date.getMonth() + 1).padStart(2, '0')
    const dd = String(date.getDate()).padStart(2, '0')
    return parseInt(`${yyyy}${mm}${dd}`)
  }

  return {
    today: format(today),
    nextYear: format(nextYear)
  }
}

const fillMockData = () => {
  const dates = getFormattedDates()
  const randomId = Math.floor(1000 + Math.random() * 9000)

  formState.codigoAgenteFinanceiro = 123
  formState.codigoFundoGarantidor = 1
  formState.numeroAgenciaContratanteOperacao = 4820
  formState.codigoIdentificadorExternoOperacao = `FGO-${randomId}`
  formState.codigoIbgeMunicipio = 355030
  formState.codigoTipoPessoa = 2
  formState.codigoIdentificadorSrf = '12345678000199'
  formState.codigoTipoPublicoAlvo = 2
  formState.valorFaturamentoBrutoAnual = 350000.00
  formState.numeroCpfQualificadorOperacao = 11122233344
  formState.valorOperacaoCredito = props.withReserve ? 95000.00 : 75000.00
  formState.percentualGarantiaOperacaoCredito = 80.00
  formState.codigoTipoModalidadeCredito = 1
  formState.codigoTipoFinalidadeCredito = 1
  formState.codigoTipoFonteRecurso = 11
  formState.codigoTipoProgramaCredito = 39
  formState.dataFormalizacaoOperacao = dates.today
  formState.dataVencimentoOperacao = dates.nextYear
  formState.codigoTipoCronogramaAmortizacao = 1
  formState.codigoTipoCondicaoEspecial = 1
  formState.codigoTipoFormalizacao = 1
  formState.valorSubsidioCredito = 0.00
  formState.dataDespachoExternoOperacao = props.withReserve ? dates.today : 0
  formState.valorCondicaoEspecial = ''
  
  addToast('Formulário preenchido com dados de simulação!', 'success')
}

const formatCurrency = (value) => {
  if (value === undefined || value === null) return 'R$ 0,00'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

const handleSubmit = async () => {
  const payload = {}
  
  const numericIntFields = [
    "codigoAgenteFinanceiro", "codigoFundoGarantidor", "numeroAgenciaContratanteOperacao",
    "codigoIbgeMunicipio", "codigoTipoPessoa", "codigoTipoPublicoAlvo", "codigoTipoModalidadeCredito",
    "codigoTipoFinalidadeCredito", "codigoTipoFonteRecurso", "codigoTipoProgramaCredito",
    "dataFormalizacaoOperacao", "dataVencimentoOperacao", "codigoTipoCronogramaAmortizacao",
    "codigoTipoCondicaoEspecial", "dataDespachoExternoOperacao", "codigoTipoFormalizacao",
    "numeroCpfQualificadorOperacao"
  ]
  
  const numericFloatFields = [
    "valorFaturamentoBrutoAnual", "valorOperacaoCredito", "percentualGarantiaOperacaoCredito",
    "valorSubsidioCredito", "valorCondicaoEspecial"
  ]

  Object.keys(formState).forEach(key => {
    const value = formState[key]
    if (value === '' || value === undefined || value === null) {
      return
    }
    
    if (numericIntFields.includes(key)) {
      payload[key] = parseInt(value, 10)
    } else if (numericFloatFields.includes(key)) {
      payload[key] = parseFloat(value)
    } else {
      payload[key] = value
    }
  })

  loading.value = true
  try {
    const serviceCall = props.withReserve ? preValidacaoReserva : preValidacao
    const response = await serviceCall(payload)
    const data = response.data
    result.value = data
    
    if (props.withReserve && data.numeroReservaPreValidacao) {
      emit('reserveCreated', {
        agente: payload.codigoAgenteFinanceiro,
        fundo: payload.codigoFundoGarantidor,
        reserva: data.numeroReservaPreValidacao
      })
    }

    addToast(
      props.withReserve 
        ? 'Reserva FGO criada com sucesso!' 
        : 'Pré-validação consultada com sucesso!', 
      'success'
    )
  } catch (err) {
    // Error is handled globally by Axios interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="panel-header">
      <h2>{{ withReserve ? 'Pré-validação com Reserva' : 'Pré-validação sem Reserva' }}</h2>
      <p>
        {{ withReserve 
          ? 'Valida dados de uma operação de crédito e realiza a RESERVA temporária do limite garantidor no FGO.' 
          : 'Valida dados de uma operação de crédito que se pretende formalizar sem bloquear margem no FGO.' 
        }}
      </p>
      <button class="btn btn-secondary fill-mock-btn" @click="fillMockData">
        ✨ Preencher dados de teste
      </button>
    </div>

    <form @submit.prevent="handleSubmit" class="fgo-form">
      <div class="form-grid">
        <!-- Card: Agente e Fundo -->
        <div class="form-card">
          <h3 class="card-title">1. Informações do Agente e Fundo</h3>
          <div class="form-group">
            <label>Código do Agente Financeiro <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoAgenteFinanceiro" required placeholder="Ex: 2" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Código do Fundo Garantidor <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoFundoGarantidor" required placeholder="Ex: 2" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Agência Contratante <span class="required">*</span></label>
            <input type="number" v-model="formState.numeroAgenciaContratanteOperacao" required placeholder="Ex: 1" :disabled="loading">
          </div>
          <div class="form-group">
            <label>ID Externo da Operação <span class="required">*</span></label>
            <input type="text" v-model="formState.codigoIdentificadorExternoOperacao" required maxlength="20" placeholder="Ex: ABC1234" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Código IBGE Município <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoIbgeMunicipio" required placeholder="Ex: 354340" :disabled="loading">
          </div>
        </div>

        <!-- Card: Mutuário -->
        <div class="form-card">
          <h3 class="card-title">2. Informações do Mutuário</h3>
          <div class="form-group">
            <label>Tipo de Pessoa <span class="required">*</span></label>
            <select v-model="formState.codigoTipoPessoa" required :disabled="loading">
              <option value="1">Pessoa Física (CPF)</option>
              <option value="2">Pessoa Jurídica (CNPJ)</option>
            </select>
          </div>
          <div class="form-group">
            <label>CPF ou CNPJ (Somente números) <span class="required">*</span></label>
            <input type="text" v-model="formState.codigoIdentificadorSrf" required maxlength="14" placeholder="Ex: 19100000000000" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Código do Público Alvo <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoPublicoAlvo" required placeholder="Ex: 2" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Faturamento Bruto Anual / Renda (R$) <span class="required">*</span></label>
            <input type="number" step="0.01" v-model="formState.valorFaturamentoBrutoAnual" required placeholder="Ex: 30000.00" :disabled="loading">
          </div>
          <div class="form-group">
            <label>CPF Qualificador Operação <span class="required">*</span></label>
            <input type="number" v-model="formState.numeroCpfQualificadorOperacao" required placeholder="Ex: 12345678911" :disabled="loading">
          </div>
        </div>

        <!-- Card: Operação Financeira -->
        <div class="form-card">
          <h3 class="card-title">3. Detalhes da Operação de Crédito</h3>
          <div class="form-group">
            <label>Valor da Operação de Crédito (R$) <span class="required">*</span></label>
            <input type="number" step="0.01" v-model="formState.valorOperacaoCredito" required placeholder="Ex: 50000.00" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Percentual de Garantia FGO (%) <span class="required">*</span></label>
            <input type="number" step="0.01" v-model="formState.percentualGarantiaOperacaoCredito" required placeholder="Ex: 80.05" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Modalidade do Crédito <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoModalidadeCredito" required placeholder="Ex: 1" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Finalidade do Crédito <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoFinalidadeCredito" required placeholder="Ex: 1" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Fonte de Recursos <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoFonteRecurso" required placeholder="Ex: 11" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Programa de Crédito <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoProgramaCredito" required placeholder="Ex: 39" :disabled="loading">
          </div>
        </div>

        <!-- Card: Datas e Condições -->
        <div class="form-card">
          <h3 class="card-title">4. Prazos e Condições Especiais</h3>
          <div class="form-group">
            <label>Data de Formalização (AAAAMMDD) <span class="required">*</span></label>
            <input type="number" v-model="formState.dataFormalizacaoOperacao" required placeholder="Ex: 20260101" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Data de Vencimento (AAAAMMDD) <span class="required">*</span></label>
            <input type="number" v-model="formState.dataVencimentoOperacao" required placeholder="Ex: 20270101" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Tipo de Cronograma Amortização <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoCronogramaAmortizacao" required placeholder="Ex: 1" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Tipo Condição Especial <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoCondicaoEspecial" required placeholder="Ex: 1" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Tipo de Formalização <span class="required">*</span></label>
            <input type="number" v-model="formState.codigoTipoFormalizacao" required placeholder="Ex: 1" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Valor Subsídio/Subvenção (R$) <span class="required">*</span></label>
            <input type="number" step="0.01" v-model="formState.valorSubsidioCredito" required placeholder="Ex: 0.00" :disabled="loading">
          </div>
          <div class="form-group" v-if="!withReserve">
            <label>Data Despacho Externo <span class="required">*</span></label>
            <input type="number" v-model="formState.dataDespachoExternoOperacao" required placeholder="Informar 0" :disabled="loading">
          </div>
          <div class="form-group" v-else>
            <label>Data Despacho Externo <span class="required">*</span></label>
            <input type="number" v-model="formState.dataDespachoExternoOperacao" required placeholder="Ex: 20260115" :disabled="loading">
          </div>
          <div class="form-group">
            <label>Valor Condição Especial (Opcional)</label>
            <input type="number" step="0.01" v-model="formState.valorCondicaoEspecial" placeholder="Opcional" :disabled="loading">
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" :class="['btn', 'btn-primary', { 'btn-gold': withReserve }]" :disabled="loading">
          <span class="btn-text">{{ withReserve ? 'Efetuar Reserva FGO' : 'Consultar Pré-validação' }}</span>
          <span class="spinner" v-if="loading"></span>
        </button>
      </div>
    </form>

    <!-- Result Card -->
    <div v-if="result" class="result-card">
      <div class="result-header">
        <h4>{{ withReserve ? 'Resultado da Reserva de Pré-validação' : 'Resultado da Pré-validação' }}</h4>
        <span class="badge badge-success">{{ withReserve ? 'Reserva Efetuada' : 'Concluído' }}</span>
      </div>
      <div class="result-content">
        <div v-if="withReserve && result.numeroReservaPreValidacao" class="result-item highlighted">
          <span class="result-label">Número da Reserva Pre-validação:</span>
          <span class="result-value numeric">{{ result.numeroReservaPreValidacao }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Valor Total Financiado/Comprometido:</span>
          <span class="result-value">{{ formatCurrency(result.valorTotalFinanciado) }}</span>
        </div>
        <div class="result-item" v-if="result.valorMargemDisponivelContratacao !== undefined">
          <span class="result-label">Valor da Margem Disponível para Contratação:</span>
          <span class="result-value">{{ formatCurrency(result.valorMargemDisponivelContratacao) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
