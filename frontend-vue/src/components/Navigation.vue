<script setup>
const props = defineProps({
  modelValue: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const menuItems = [
  { id: 'pre-val-no-reserve', label: 'Pré-validação sem Reserva', icon: '📊' },
  { id: 'pre-val-with-reserve', label: 'Pré-validação com Reserva', icon: '🔒' },
  { id: 'cancel-reserve', label: 'Cancelamento de Reserva', icon: '🚫' }
]

const selectTab = (tabId) => {
  emit('update:modelValue', tabId)
}
</script>

<template>
  <aside class="sidebar">
    <nav class="nav-menu">
      <button
        v-for="item in menuItems"
        :key="item.id"
        :class="['nav-item', { active: modelValue === item.id }]"
        @click="selectTab(item.id)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>
    <div class="sidebar-footer">
      <p>Banco do Brasil S.A.</p>
      <p class="small">Integração API FGO v2.0.1</p>
    </div>
  </aside>
</template>
