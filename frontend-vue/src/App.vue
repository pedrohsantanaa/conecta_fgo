<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Navigation from './components/Navigation.vue'
import PreValidationForm from './components/PreValidationForm.vue'
import CancellationForm from './components/CancellationForm.vue'
import ToastContainer from './components/ToastContainer.vue'

import { checkBackendHealth } from './services/api'

const activeTab = ref('pre-val-no-reserve')
const systemStatus = ref({
  statusClass: 'warning',
  text: 'Verificando backend...'
})
const prefillData = ref({})

const handleReserveCreated = (data) => {
  prefillData.value = data
}

let healthInterval = null

const checkHealth = async () => {
  try {
    const response = await checkBackendHealth()
    const data = response.data
    
    if (data.status === 'healthy') {
      if (data.mock_mode) {
        systemStatus.value = {
          statusClass: 'warning',
          text: 'Conectado <strong>(Modo Simulado)</strong>'
        }
      } else if (data.mtls_configured) {
        systemStatus.value = {
          statusClass: 'success',
          text: 'Conectado <strong>(BB Integrado - mTLS)</strong>'
        }
      } else {
        systemStatus.value = {
          statusClass: 'warning',
          text: 'Conectado <strong>(Sem mTLS)</strong>'
        }
      }
    } else {
      systemStatus.value = {
        statusClass: 'error',
        text: 'Backend Instável'
      }
    }
  } catch (err) {
    systemStatus.value = {
      statusClass: 'error',
      text: 'Backend Offline'
    }
  }
}

onMounted(() => {
  checkHealth()
  healthInterval = setInterval(checkHealth, 15000)
})

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
})
</script>

<template>
  <div>
    <!-- Top Bar -->
    <header class="top-bar">
      <div class="logo-container">
        <span class="logo-bb-icon"></span>
        <h1>Conecta <span>FGO</span></h1>
      </div>
      <div class="system-status" id="system-status">
        <span :class="['status-indicator', systemStatus.statusClass]"></span>
        <span class="status-text" v-html="systemStatus.text"></span>
      </div>
    </header>

    <!-- App Container -->
    <div class="app-container">
      <!-- Sidebar Navigation -->
      <Navigation v-model="activeTab" />

      <!-- Main Content -->
      <main class="main-content">
        <!-- Tab panels rendered dynamically -->
        <PreValidationForm
          v-if="activeTab === 'pre-val-no-reserve'"
          :with-reserve="false"
          key="no-reserve"
        />

        <PreValidationForm
          v-if="activeTab === 'pre-val-with-reserve'"
          :with-reserve="true"
          @reserve-created="handleReserveCreated"
          key="with-reserve"
        />

        <CancellationForm
          v-if="activeTab === 'cancel-reserve'"
          :prefill-data="prefillData"
          key="cancel-reserve"
        />
      </main>
    </div>

    <!-- Toast Notifications -->
    <ToastContainer />
  </div>
</template>
