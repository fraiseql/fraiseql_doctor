import { onMounted, onUnmounted, type Ref } from 'vue'
import type { ApiEndpoint, ApiHealthUpdate } from '@/types/admin'
import { useWebSocket } from '@/services/websocket/useWebSocket'

export function useApiHealthUpdates(endpoints: Ref<ApiEndpoint[]>) {
  const { connect, disconnect } = useWebSocket()

  // Health update handler
  const handleHealthUpdate = (update: ApiHealthUpdate) => {
    const endpointIndex = endpoints.value.findIndex(e => e.id === update.apiId)
    if (endpointIndex !== -1) {
      endpoints.value[endpointIndex] = {
        ...endpoints.value[endpointIndex],
        isHealthy: update.isHealthy,
        responseTime: update.responseTime,
        ...(update.errorRate !== undefined && { errorRate: update.errorRate }),
        lastCheck: update.timestamp || new Date()
      }
    }
  }

  // Lifecycle management
  onMounted(() => {
    // Establish WebSocket connection for real-time health updates
    connect('api-health-updates', handleHealthUpdate)
  })

  onUnmounted(() => {
    // Clean up WebSocket connection
    disconnect('api-health-updates')
  })

  return {
    handleHealthUpdate
  }
}
