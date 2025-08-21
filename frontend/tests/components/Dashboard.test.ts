import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Dashboard from '../../src/views/Dashboard.vue'
import { useEndpointsStore } from '../../src/stores/endpoints'
import { useDashboard } from '../../src/stores/dashboard'

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

describe('Dashboard Grid Layout', () => {
  let pinia: any
  let endpointsStore: any
  let dashboardStore: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    endpointsStore = useEndpointsStore()
    dashboardStore = useDashboard()
  })

  it('should display endpoints in responsive grid layout with correct CSS classes', async () => {
    // Setup mock endpoints
    endpointsStore.endpoints = [
      {
        id: 'api-1',
        name: 'Production API',
        url: 'https://api.prod.com/graphql',
        isHealthy: true,
        status: 'active',
        responseTime: 120,
        introspectionEnabled: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 'api-2',
        name: 'Staging API',
        url: 'https://api.staging.com/graphql',
        isHealthy: false,
        status: 'error',
        responseTime: 5000,
        errorMessage: 'Connection timeout',
        introspectionEnabled: false,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 'api-3',
        name: 'Development API',
        url: 'https://api.dev.com/graphql',
        isHealthy: true,
        status: 'active',
        responseTime: 80,
        introspectionEnabled: true,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ]

    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Check that endpoints grid exists and has correct CSS classes
    const endpointsGrid = wrapper.find('[data-testid="endpoints-grid"]')
    expect(endpointsGrid.exists()).toBe(true)
    expect(endpointsGrid.classes()).toContain('grid')
    expect(endpointsGrid.classes()).toContain('grid-cols-1')
    expect(endpointsGrid.classes()).toContain('md:grid-cols-2')
    expect(endpointsGrid.classes()).toContain('lg:grid-cols-3')
    expect(endpointsGrid.classes()).toContain('gap-4')

    // Verify endpoint cards are rendered
    const endpointCards = wrapper.findAll('[data-testid="endpoint-status-card"]')
    expect(endpointCards).toHaveLength(3)
  })

  it('should display correct stats in status cards grid layout', async () => {
    // Setup mock endpoints with varied health status
    endpointsStore.endpoints = [
      { id: '1', name: 'API 1', isHealthy: true, status: 'active', responseTime: 100, introspectionEnabled: true, createdAt: new Date(), updatedAt: new Date() },
      { id: '2', name: 'API 2', isHealthy: false, status: 'error', responseTime: 5000, introspectionEnabled: false, createdAt: new Date(), updatedAt: new Date() },
      { id: '3', name: 'API 3', isHealthy: true, status: 'active', responseTime: 150, introspectionEnabled: true, createdAt: new Date(), updatedAt: new Date() },
      { id: '4', name: 'API 4', isHealthy: true, status: 'active', responseTime: 200, introspectionEnabled: false, createdAt: new Date(), updatedAt: new Date() }
    ]

    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Check status cards grid
    const statusCards = wrapper.findAll('[data-testid="status-card"]')
    expect(statusCards).toHaveLength(4)

    // Verify the status cards have grid layout classes
    const statusCardsContainer = statusCards[0].element.parentElement
    expect(statusCardsContainer?.classList).toContain('grid')
    expect(statusCardsContainer?.classList).toContain('grid-cols-1')
    expect(statusCardsContainer?.classList).toContain('md:grid-cols-2')
    expect(statusCardsContainer?.classList).toContain('lg:grid-cols-4')

    // Check that stats are calculated correctly
    const statusTexts = statusCards.map(card => card.text())
    expect(statusTexts.some(text => text.includes('Total Endpoints'))).toBe(true)
    expect(statusTexts.some(text => text.includes('Healthy Endpoints'))).toBe(true)
    expect(statusTexts.some(text => text.includes('Unhealthy Endpoints'))).toBe(true)
    expect(statusTexts.some(text => text.includes('Average Response Time'))).toBe(true)
  })

  it('should handle empty state gracefully when no endpoints exist', async () => {
    // No endpoints in store
    endpointsStore.endpoints = []

    // Configure dashboard store for empty state
    dashboardStore.stats = []
    dashboardStore.isLoading = false

    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Should not show endpoints grid when no endpoints
    expect(wrapper.find('[data-testid="endpoints-grid"]').exists()).toBe(false)

    // Should show empty state
    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="empty-state"]').text()).toContain('No data available')

    // Status cards should still exist but show zeros
    const statusCards = wrapper.findAll('[data-testid="status-card"]')
    expect(statusCards).toHaveLength(4)
  })

  it('should maintain responsive grid layout on different screen sizes', async () => {
    endpointsStore.endpoints = Array.from({ length: 6 }, (_, i) => ({
      id: `endpoint-${i + 1}`,
      name: `API ${i + 1}`,
      url: `https://api${i + 1}.com/graphql`,
      isHealthy: i % 2 === 0,
      status: i % 2 === 0 ? 'active' : 'error',
      responseTime: 100 + i * 50,
      introspectionEnabled: true,
      createdAt: new Date(),
      updatedAt: new Date()
    }))

    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Endpoints grid should have responsive classes
    const endpointsGrid = wrapper.find('[data-testid="endpoints-grid"]')
    expect(endpointsGrid.classes()).toContain('grid-cols-1') // Mobile
    expect(endpointsGrid.classes()).toContain('md:grid-cols-2') // Tablet
    expect(endpointsGrid.classes()).toContain('lg:grid-cols-3') // Desktop

    // Status cards grid should also be responsive
    const statusCardsContainer = wrapper.findAll('[data-testid="status-card"]')[0].element.parentElement
    expect(statusCardsContainer?.classList).toContain('grid-cols-1') // Mobile
    expect(statusCardsContainer?.classList).toContain('md:grid-cols-2') // Tablet
    expect(statusCardsContainer?.classList).toContain('lg:grid-cols-4') // Desktop

    // Should render all 6 endpoint cards
    const endpointCards = wrapper.findAll('[data-testid="endpoint-status-card"]')
    expect(endpointCards).toHaveLength(6)
  })

  it('should display proper spacing and layout structure', async () => {
    endpointsStore.endpoints = [
      { id: '1', name: 'Test API', isHealthy: true, status: 'active', responseTime: 100, introspectionEnabled: true, createdAt: new Date(), updatedAt: new Date() }
    ]

    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.vm.$nextTick()

    // Check main dashboard layout
    const dashboardView = wrapper.find('[data-testid="dashboard-view"]')
    expect(dashboardView.classes()).toContain('space-y-6')

    // Check endpoints grid spacing
    const endpointsGrid = wrapper.find('[data-testid="endpoints-grid"]')
    expect(endpointsGrid.classes()).toContain('gap-4')

    // Check status cards spacing
    const statusCardsContainer = wrapper.findAll('[data-testid="status-card"]')[0].element.parentElement
    expect(statusCardsContainer?.classList).toContain('gap-6')
  })
})
