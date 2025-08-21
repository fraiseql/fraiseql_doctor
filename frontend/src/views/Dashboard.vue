<template>
  <div data-testid="dashboard-view" class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
      <p class="mt-2 text-gray-600">Real-time monitoring of your FraiseQL endpoints</p>
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
import { onMounted, onUnmounted, computed } from 'vue'
import { useWebSocket } from '@/services/websocket/useWebSocket'
import { useDashboard } from '@/stores/dashboard'

// Store and WebSocket setup
const dashboardStore = useDashboard()
const { connect, disconnect, emit, error: wsError } = useWebSocket()

// Computed properties
const error = computed(() => wsError?.value?.message || dashboardStore.error)

// Display stats with fallback for empty state
const displayStats = computed(() => {
  if (dashboardStore.stats && dashboardStore.stats.length > 0) {
    return dashboardStore.stats
  }
  
  // Fallback placeholder stats for loading state
  return [
    { label: 'Healthy Endpoints', value: 0, status: 'success' as const },
    { label: 'Warning Endpoints', value: 0, status: 'warning' as const },
    { label: 'Failed Endpoints', value: 0, status: 'error' as const },
    { label: 'Total Requests', value: 0, status: 'info' as const }
  ]
})

// WebSocket message handler
const handleWebSocketMessage = (data: any) => {
  if (data.stats && Array.isArray(data.stats)) {
    dashboardStore.updateDashboardData(data)
  } else if (data.stats && data.stats.length === 0) {
    // Handle empty data case
    dashboardStore.updateDashboardData({ stats: [], chartData: null })
  }
}

// Lifecycle hooks
onMounted(() => {
  // Connect to WebSocket for real-time updates
  connect('dashboard', handleWebSocketMessage)
  
  // Request initial data
  emit('request-update')
})

onUnmounted(() => {
  disconnect('dashboard')
})
</script>