import { ref, onUnmounted } from 'vue'

// Mock WebSocket for development and testing
class MockWebSocketService {
  private connections: Map<string, {
    handler: (data: any) => void,
    errorHandler?: (error: Error) => void
  }> = new Map()

  private intervalId: number | null = null

  connect(channel: string, messageHandler: (data: any) => void) {
    this.connections.set(channel, { handler: messageHandler })

    // Simulate connection and start sending mock data
    setTimeout(() => {
      this.startMockDataFlow(channel)
    }, 100)

    return true
  }

  disconnect(channel?: string) {
    if (channel) {
      this.connections.delete(channel)
    } else {
      this.connections.clear()
    }

    if (this.intervalId) {
      window.clearInterval(this.intervalId)
      this.intervalId = null
    }
  }

  emit(event: string, data?: any) {
    // In a real implementation, this would send data to the server
    // For mock, we can simulate immediate response
    console.log('WebSocket emit:', event, data)

    if (event === 'request-update') {
      // Simulate immediate response with updated data
      setTimeout(() => {
        this.sendMockDashboardData()
      }, 50)
    }
  }

  on(event: string, handler: (data: any) => void) {
    // For error handling
    if (event === 'error') {
      for (const connection of this.connections.values()) {
        connection.errorHandler = handler
      }
    }
  }

  private startMockDataFlow(channel: string) {
    if (channel === 'dashboard') {
      // Send initial data
      this.sendMockDashboardData()

      // Set up periodic updates
      this.intervalId = window.setInterval(() => {
        this.sendMockDashboardData()
      }, 5000) // Update every 5 seconds
    }
  }

  private sendMockDashboardData() {
    const connection = this.connections.get('dashboard')
    if (!connection) return

    const mockData = {
      stats: [
        {
          label: 'Healthy Endpoints',
          value: Math.floor(Math.random() * 10) + 5,
          status: 'success'
        },
        {
          label: 'Warning Endpoints',
          value: Math.floor(Math.random() * 3) + 1,
          status: 'warning'
        },
        {
          label: 'Failed Endpoints',
          value: Math.floor(Math.random() * 2),
          status: 'error'
        },
        {
          label: 'Total Requests',
          value: Math.floor(Math.random() * 1000) + 1000,
          status: 'info'
        }
      ],
      chartData: {
        labels: ['09:00', '10:00', '11:00', '12:00'],
        datasets: [
          {
            label: 'Response Time',
            data: [
              Math.floor(Math.random() * 100) + 100,
              Math.floor(Math.random() * 100) + 100,
              Math.floor(Math.random() * 100) + 100,
              Math.floor(Math.random() * 100) + 100
            ],
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)'
          }
        ]
      }
    }

    connection.handler(mockData)
  }
}

// Global WebSocket service instance
let wsService: MockWebSocketService | null = null

function getWebSocketService() {
  if (!wsService) {
    wsService = new MockWebSocketService()
  }
  return wsService
}

export function useWebSocket() {
  const service = getWebSocketService()

  const isConnected = ref(false)
  const error = ref<Error | null>(null)

  const connect = (channel: string, messageHandler: (data: any) => void) => {
    try {
      const success = service.connect(channel, messageHandler)
      isConnected.value = success
      error.value = null

      // Set up error handler
      service.on('error', (err: Error) => {
        error.value = err
        isConnected.value = false
      })

      return success
    } catch (err) {
      error.value = err as Error
      isConnected.value = false
      return false
    }
  }

  const disconnect = (channel?: string) => {
    service.disconnect(channel)
    isConnected.value = false
    error.value = null
  }

  const emit = (event: string, data?: any) => {
    service.emit(event, data)
  }

  // Auto-cleanup on component unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    error,
    connect,
    disconnect,
    emit,
    on: service.on.bind(service)
  }
}
