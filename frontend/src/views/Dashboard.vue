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
                    'bg-yellow-500': stat.status === 'warning' as any,
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
                  {{ dashboardStore.isLoading ? 'Loading...' : formatStatDisplay(stat) }}
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

    <!-- Performance Charts Section -->
    <div v-if="endpointsStore.endpoints.length > 0" class="bg-white shadow rounded-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-medium text-gray-900">Performance Analytics</h2>

        <!-- Chart Controls -->
        <div class="flex items-center space-x-4">
          <!-- Endpoint Filter -->
          <select
            v-model="selectedEndpointId"
            class="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            data-testid="endpoint-filter"
          >
            <option value="">All Endpoints</option>
            <option v-for="endpoint in endpointsStore.endpoints" :key="endpoint.id" :value="endpoint.id">
              {{ endpoint.name }}
            </option>
          </select>

          <!-- Chart Type Toggle -->
          <div class="flex bg-gray-100 rounded-lg p-1" data-testid="chart-type-toggle">
            <button
              @click="chartType = 'responseTime'"
              :class="[
                'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                chartType === 'responseTime'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              Response Time
            </button>
            <button
              @click="chartType = 'responseSize'"
              :class="[
                'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                chartType === 'responseSize'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              Response Size
            </button>
          </div>
        </div>
      </div>

      <!-- Performance Chart - Replaced with eCharts in future implementation -->
      <div data-testid="performance-chart-container" class="h-80">
        <div class="flex items-center justify-center h-full bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
          <p class="text-gray-500 text-center">
            Performance Chart<br>
            <span class="text-sm">Will be implemented with eCharts</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Advanced Performance Analytics Section -->
    <div v-if="endpointsStore.endpoints.length > 0 && performanceMetrics.length > 10" class="bg-white shadow rounded-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-medium text-gray-900">Advanced Analytics</h2>
        <p class="text-sm text-gray-500">Historical trends, anomaly detection, and performance insights</p>
      </div>

      <!-- Analytics Panel -->
      <PerformanceAnalyticsPanel
        :metrics="filteredMetrics"
        :endpoint-id="selectedEndpointId || 'all'"
        @export-analytics="handleAnalyticsExport"
        @anomaly-selected="handleAnomalySelected"
        @data-point-selected="handleDataPointSelected"
      />
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
import PerformanceAnalyticsPanel from '@/components/PerformanceAnalyticsPanel.vue'
import { PerformanceMonitor, type QueryMetric } from '@/services/performanceMonitor'

// Store setup
const endpointsStore = useEndpointsStore()
const dashboardStore = useDashboard()

// WebSocket setup
const webSocketService = ref<WebSocketService | null>(null)
const error = ref<string | null>(null)
const connectionState = ref<ConnectionState>(ConnectionState.DISCONNECTED)

// Performance monitoring setup
const performanceMonitor = ref<PerformanceMonitor>(new PerformanceMonitor())
const chartType = ref<'responseTime' | 'responseSize'>('responseTime')
const selectedEndpointId = ref<string>('')
const performanceMetrics = ref<QueryMetric[]>([])

// Computed properties
// Computed properties for metrics filtering
const filteredMetrics = computed(() => {
  if (!selectedEndpointId.value) {
    return performanceMetrics.value
  }
  return performanceMetrics.value.filter(metric => metric.endpointId === selectedEndpointId.value)
})

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

function formatStatDisplay(stat: { status: string; value: number }): string {
  const statusText = stat.status === 'success' ? 'Healthy' :
                    stat.status === 'warning' ? 'Warning' :
                    stat.status === 'error' ? 'Failed' :
                    stat.status === 'info' ? 'Info' : ''
  return `${statusText}: ${stat.value}`
}

// WebSocket handlers
const handleHealthUpdate = async (healthData: any) => {
  endpointsStore.updateEndpointHealth(healthData.endpointId, {
    isHealthy: healthData.isHealthy,
    responseTime: healthData.responseTime,
    timestamp: healthData.timestamp,
    errorMessage: healthData.errorMessage
  })

  // Track performance metrics
  if (healthData.responseTime && healthData.isHealthy) {
    await performanceMonitor.value.trackQuery(
      healthData.endpointId,
      'health_check',
      {
        executionTime: healthData.responseTime,
        responseSize: 1024, // Estimated size for health check
        timestamp: new Date(healthData.timestamp)
      }
    )

    // Update local metrics for chart display - get all metrics for all endpoints
    const allMetrics: QueryMetric[] = []
    endpointsStore.endpoints.forEach(endpoint => {
      allMetrics.push(...performanceMonitor.value.getMetrics(endpoint.id))
    })
    performanceMetrics.value = allMetrics
  }
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

const setupPerformanceMonitoring = () => {
  // Listen for performance metric updates
  performanceMonitor.value.addEventListener('metric-recorded', () => {
    // Refresh metrics display when new metrics are recorded
    const allMetrics: QueryMetric[] = []
    endpointsStore.endpoints.forEach(endpoint => {
      allMetrics.push(...performanceMonitor.value.getMetrics(endpoint.id))
    })
    performanceMetrics.value = allMetrics
  })

  // Generate some sample data for demonstration
  generateSamplePerformanceData()
}

const generateSamplePerformanceData = async () => {
  // Generate sample metrics for existing endpoints
  const sampleQueries = ['health_check', 'introspection', 'user_query']

  for (const endpoint of endpointsStore.endpoints) {
    for (let i = 0; i < 10; i++) {
      const baseTime = new Date(Date.now() - (i * 300000)) // 5 minutes apart
      await performanceMonitor.value.trackQuery(
        endpoint.id,
        sampleQueries[i % sampleQueries.length],
        {
          executionTime: Math.random() * 200 + 50, // 50-250ms
          responseSize: Math.random() * 5000 + 500, // 500-5500 bytes
          timestamp: baseTime
        }
      )
    }
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

  // Setup performance monitoring
  setupPerformanceMonitoring()

  // Setup WebSocket for real-time updates
  await setupWebSocket()
})

onUnmounted(() => {
  if (webSocketService.value) {
    webSocketService.value.disconnect()
  }
})

// Analytics event handlers
const handleAnalyticsExport = (data: any) => {
  console.log('Exporting analytics data:', data)

  // Create and download JSON file
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `performance-analytics-${data.endpointId}-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const handleAnomalySelected = (anomaly: any) => {
  console.log('Anomaly selected:', anomaly)
  // Could trigger a modal or detailed view
}

const handleDataPointSelected = (data: any) => {
  console.log('Data point selected:', data)
  // Could show detailed metrics for that time period
}
</script>
