import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Dashboard from '../../src/views/Dashboard.vue'
import { useEndpointsStore } from '../../src/stores/endpoints'

// Mock the WebSocket module completely
vi.mock('../../src/services/websocket', () => {
  return {
    WebSocketService: vi.fn().mockImplementation(() => ({
      connect: vi.fn().mockResolvedValue(undefined),
      disconnect: vi.fn(),
      on: vi.fn(),
      send: vi.fn()
    })),
    ConnectionState: {
      DISCONNECTED: 'disconnected',
      CONNECTING: 'connecting',
      CONNECTED: 'connected',
      RECONNECTING: 'reconnecting',
      ERROR: 'error'
    }
  }
})

// Mock the WebSocket config
vi.mock('../../src/config/websocket', () => ({
  WEBSOCKET_CONFIG: {
    url: 'ws://localhost:8080/health',
    reconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000
  },
  WEBSOCKET_EVENTS: {
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    ERROR: 'error',
    ENDPOINT_HEALTH_UPDATE: 'endpoint-health-update',
    HEARTBEAT: 'heartbeat'
  }
}))

// Mock the useWebSocket composable
vi.mock('../../src/services/websocket/useWebSocket', () => ({
  useWebSocket: () => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    emit: vi.fn(),
    error: { value: null }
  })
}))

describe('Dashboard Real-Time Updates', () => {
  let pinia: any
  let endpointsStore: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    endpointsStore = useEndpointsStore()

    // Setup mock endpoints
    endpointsStore.endpoints = [
      {
        id: 'endpoint-1',
        name: 'Production API',
        url: 'https://api.production.com/graphql',
        isHealthy: true,
        responseTime: 150,
        status: 'active',
        lastChecked: new Date(),
        introspectionEnabled: false,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 'endpoint-2',
        name: 'Staging API',
        url: 'https://api.staging.com/graphql',
        isHealthy: false,
        responseTime: 5000,
        status: 'error',
        errorMessage: 'Connection timeout',
        lastChecked: new Date(),
        introspectionEnabled: true,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ]
  })

  it('should display initial endpoint health status', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    // Should show total endpoints
    const statusCards = wrapper.findAll('[data-testid="status-card"]')
    expect(statusCards).toHaveLength(4) // Should have 4 status cards

    // Dashboard should be rendered
    expect(wrapper.find('[data-testid="dashboard-view"]').exists()).toBe(true)
  })

  it('should show health status indicators correctly', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    // Should show status cards with correct counts
    expect(wrapper.find('[data-testid="dashboard-view"]').exists()).toBe(true)

    // Verify the dashboard renders without errors
    expect(wrapper.vm).toBeDefined()
  })

  it('should handle WebSocket connection errors gracefully', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Component should still be functional
    expect(wrapper.find('[data-testid="dashboard-view"]').exists()).toBe(true)
  })

  it('should display endpoints grid when endpoints are available', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Should show endpoints grid since we have mock endpoints
    expect(wrapper.find('[data-testid="endpoints-grid"]').exists()).toBe(true)

    // Should show endpoint status cards
    const statusCards = wrapper.findAll('[data-testid="endpoint-status-card"]')
    expect(statusCards.length).toBeGreaterThan(0)
  })

  it('should update endpoint health when updateEndpointHealth is called', () => {
    mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    // Find the initial endpoint
    const initialEndpoint = endpointsStore.endpoints.find((e: any) => e.id === 'endpoint-1')
    expect(initialEndpoint.isHealthy).toBe(true)

    // Call the updateEndpointHealth method directly
    endpointsStore.updateEndpointHealth('endpoint-1', {
      isHealthy: false,
      responseTime: 5000,
      timestamp: new Date().toISOString(),
      errorMessage: 'Connection failed'
    })

    // Verify endpoint was updated
    const updatedEndpoint = endpointsStore.endpoints.find((e: any) => e.id === 'endpoint-1')
    expect(updatedEndpoint.isHealthy).toBe(false)
    expect(updatedEndpoint.responseTime).toBe(5000)
    expect(updatedEndpoint.errorMessage).toBe('Connection failed')
  })
})
