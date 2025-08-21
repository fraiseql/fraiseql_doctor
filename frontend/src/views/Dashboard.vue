<template>
  <div data-testid="dashboard-view" class="space-y-6">
    <!-- Header -->
    <div>
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p class="mt-2 text-gray-600">Real-time monitoring of your FraiseQL endpoints</p>
        </div>

        <!-- Connection Status -->
        <div class="flex items-center space-x-2" data-testid="connection-status">
          <div
            :class="[
              'w-3 h-3 rounded-full',
              {
                'bg-green-500': connectionState === 'connected',
                'bg-yellow-500': connectionState === 'connecting' || connectionState === 'reconnecting',
                'bg-red-500': connectionState === 'error',
                'bg-gray-500': connectionState === 'disconnected'
              }
            ]"
          />
          <span class="text-sm text-gray-600 capitalize">
            {{ connectionState === 'connected' ? 'Live' : connectionState }}
          </span>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-if="error"
      data-testid="error-message"
      class="bg-red-50 border border-red-200 rounded-md p-4"
    >
      <div class="flex">
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Connection Error</h3>
          <div class="mt-2 text-sm text-red-700">
            {{ error }}
          </div>
        </div>
      </div>
    </div>

    <!-- Status Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div
        v-for="stat in displayStats"
        :key="stat.label"
        data-testid="status-card"
        class="bg-white overflow-hidden shadow rounded-lg"
      >
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div
                :class="[
                  'w-8 h-8 rounded-full',
                  {
                    'bg-green-500': stat.status === 'success',
                    'bg-yellow-500': stat.status === 'warning',
                    'bg-red-500': stat.status === 'error',
                    'bg-blue-500': stat.status === 'info',
                    'bg-gray-200': dashboardStore.isLoading
                  }
                ]"
              ></div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  {{ stat.label }}
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ dashboardStore.isLoading ? 'Loading...' : `${stat.status === 'success' ? 'Healthy' : stat.status === 'warning' ? 'Warning' : stat.status === 'error' ? 'Failed' : ''}: ${stat.value}` }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Endpoints Grid -->
    <div v-if="endpointsStore.endpoints.length > 0" class="bg-white shadow rounded-lg p-6">
      <h2 class="text-lg font-medium text-gray-900 mb-4">Endpoint Status</h2>
      <div
        class="endpoints-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        data-testid="endpoints-grid"
      >
        <HealthStatusCard
          v-for="endpoint in endpointsStore.endpoints"
          :key="endpoint.id"
          :endpoint="endpoint"
          data-testid="endpoint-status-card"
        />
      </div>
    </div>

    <!-- Chart Section -->
    <div v-if="dashboardStore.chartData && !dashboardStore.isEmpty" class="bg-white shadow rounded-lg p-6">
      <h2 class="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h2>
      <div data-testid="health-chart" class="h-64 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg">
        <div class="text-center">
          <div class="text-gray-500">Chart.js integration</div>
          <div class="text-sm text-gray-400 mt-1">{{ dashboardStore.chartData.datasets[0]?.data?.join(', ') }}ms avg response time</div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="dashboardStore.isEmpty"
      data-testid="empty-state"
      class="text-center py-12"
    >
      <div class="text-gray-500">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2-2V7a2 2 0 002-2h2a2 2 0 002 2v2a2 2 0 002 2h6a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2-2V3a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 002 2h2a2 2 0 002 2v2a2 2 0 00-2 2h-2a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 002-2h2a2 2 0 002-2v-2a2 2 0 00-2-2h-2a2 2 0 00-2-2v-2a2 2 0 002-2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2-2V3a2 2 0 00-2-2z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No data available</h3>
        <p class="mt-1 text-sm text-gray-500">Waiting for endpoint data...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref } from 'vue'
import { useEndpointsStore } from '@/stores/endpoints'
import { useDashboard } from '@/stores/dashboard'
import { WebSocketService, ConnectionState } from '@/services/websocket'
import { WEBSOCKET_EVENTS } from '@/config/websocket'
import HealthStatusCard from '@/components/HealthStatusCard.vue'

// Store setup
const endpointsStore = useEndpointsStore()
const dashboardStore = useDashboard()

// WebSocket setup
const webSocketService = ref<WebSocketService | null>(null)
const error = ref<string | null>(null)
const connectionState = ref<ConnectionState>(ConnectionState.DISCONNECTED)

// Computed properties
const displayStats = computed(() => {
  const healthyCount = endpointsStore.healthyEndpointsCount
  const unhealthyCount = endpointsStore.unhealthyEndpointsCount
  const totalCount = endpointsStore.endpoints.length

  return [
    { label: 'Total Endpoints', value: totalCount, status: 'info' as const },
    { label: 'Healthy Endpoints', value: healthyCount, status: 'success' as const },
    { label: 'Unhealthy Endpoints', value: unhealthyCount, status: 'error' as const },
    { label: 'Average Response Time', value: calculateAverageResponseTime(), status: 'info' as const }
  ]
})

function calculateAverageResponseTime(): number {
  const endpoints = endpointsStore.endpoints
  if (endpoints.length === 0) return 0

  const total = endpoints.reduce((sum, endpoint) => sum + (endpoint.responseTime || 0), 0)
  return Math.round(total / endpoints.length)
}

// WebSocket handlers
const handleHealthUpdate = (healthData: any) => {
  endpointsStore.updateEndpointHealth(healthData.endpointId, {
    isHealthy: healthData.isHealthy,
    responseTime: healthData.responseTime,
    timestamp: healthData.timestamp,
    errorMessage: healthData.errorMessage
  })
}

const handleConnectionStateChange = (data: { state: ConnectionState }) => {
  connectionState.value = data.state
  if (data.state === ConnectionState.CONNECTED) {
    error.value = null
  }
}

const handleWebSocketError = (errorData: any) => {
  error.value = errorData?.message || 'WebSocket connection error'
  connectionState.value = ConnectionState.ERROR
}

const handleDisconnection = (data: { reason: string; code: number }) => {
  connectionState.value = ConnectionState.DISCONNECTED
  if (data.reason !== 'Manual disconnect') {
    error.value = `Connection lost: ${data.reason}`
  }
}

const setupWebSocket = async () => {
  try {
    webSocketService.value = new WebSocketService()

    webSocketService.value.on(WEBSOCKET_EVENTS.CONNECTED, handleConnectionStateChange)
    webSocketService.value.on(WEBSOCKET_EVENTS.DISCONNECTED, handleDisconnection)
    webSocketService.value.on(WEBSOCKET_EVENTS.ENDPOINT_HEALTH_UPDATE, handleHealthUpdate)
    webSocketService.value.on(WEBSOCKET_EVENTS.ERROR, handleWebSocketError)

    await webSocketService.value.connect()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to initialize WebSocket'
    connectionState.value = ConnectionState.ERROR
  }
}

// Lifecycle hooks
onMounted(async () => {
  // Load initial endpoints data
  await endpointsStore.loadEndpoints()

  // Setup WebSocket for real-time updates
  await setupWebSocket()
})

onUnmounted(() => {
  if (webSocketService.value) {
    webSocketService.value.disconnect()
  }
})
</script>
