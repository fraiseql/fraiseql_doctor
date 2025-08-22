<template>
  <div class="api-configuration-admin p-6">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">GraphQL API Configuration</h1>
        <p class="text-gray-600">Monitor and configure your GraphQL endpoints</p>
      </div>
      <button
        data-testid="add-api-btn"
        class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
      >
        + Add API
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <ApiEndpointCard
        v-for="endpoint in endpoints"
        :key="endpoint.id"
        :endpoint="endpoint"
        data-testid="api-endpoint-card"
        @configure="openConfigModal"
        @test="testConnection"
      />
    </div>

    <ApiConfigurationModal
      v-model="showConfigModal"
      :endpoint="selectedEndpoint"
      data-testid="api-config-modal"
      @save="handleConfigSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ApiEndpointCard from './components/ApiEndpointCard.vue'
import ApiConfigurationModal from './components/ApiConfigurationModal.vue'
import type { ApiEndpoint } from '@/types/admin'

const endpoints = ref<ApiEndpoint[]>([
  {
    id: 'api-example-dev',
    name: 'Example Dev API',
    url: 'https://api.example.dev/graphql',
    environment: 'dev',
    isHealthy: true,
    responseTime: 45,
    errorRate: 0.1,
    lastCheck: new Date()
  },
  {
    id: 'api-example-st',
    name: 'Example Staging API',
    url: 'https://api.example.st/graphql',
    environment: 'staging',
    isHealthy: false,
    responseTime: 250,
    errorRate: 2.1,
    lastCheck: new Date()
  },
  {
    id: 'api-example-io',
    name: 'Example Production API',
    url: 'https://api.example.io/graphql',
    environment: 'prod',
    isHealthy: true,
    responseTime: 38,
    errorRate: 0.0,
    lastCheck: new Date()
  }
])

const showConfigModal = ref(false)
const selectedEndpoint = ref<ApiEndpoint | null>(null)

const openConfigModal = (endpoint: ApiEndpoint) => {
  selectedEndpoint.value = endpoint
  showConfigModal.value = true
}

const testConnection = (endpoint: ApiEndpoint) => {
  console.log('Testing connection for:', endpoint.name)
}

const handleConfigSave = (config: any) => {
  console.log('Saving config:', config)
  showConfigModal.value = false
}
</script>
