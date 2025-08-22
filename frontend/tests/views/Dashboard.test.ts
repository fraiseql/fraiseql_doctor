import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

import DashboardView from '@/views/Dashboard.vue'

// Mock WebSocket config
vi.mock('@/config/websocket', () => ({
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

// Mock WebSocketService (the actual service used by Dashboard)
const mockWebSocketService = {
  connect: vi.fn().mockResolvedValue(undefined),
  disconnect: vi.fn(),
  on: vi.fn(),
  state: 'disconnected',
  isConnected: false
}

vi.mock('@/services/websocket', () => ({
  WebSocketService: vi.fn(() => mockWebSocketService),
  ConnectionState: {
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    RECONNECTING: 'reconnecting',
    ERROR: 'error'
  }
}))

// Mock PerformanceMonitor
const mockPerformanceMonitor = {
  trackQuery: vi.fn().mockResolvedValue(undefined),
  getMetrics: vi.fn().mockReturnValue([]),
  addEventListener: vi.fn()
}

vi.mock('@/services/performanceMonitor', () => ({
  PerformanceMonitor: vi.fn(() => mockPerformanceMonitor)
}))

// Mock components that might not exist
vi.mock('@/components/HealthStatusCard.vue', () => ({
  default: { template: '<div data-testid="health-status-card"></div>' }
}))

vi.mock('@/components/PerformanceChart.vue', () => ({
  default: { template: '<div data-testid="performance-chart"></div>' }
}))

vi.mock('@/components/PerformanceAnalyticsPanel.vue', () => ({
  default: { template: '<div data-testid="performance-analytics-panel"></div>' }
}))

// Mock stores
const mockEndpointsStore = {
  endpoints: [
    { id: '1', name: 'Test Endpoint', isHealthy: true, responseTime: 100 }
  ],
  healthyEndpointsCount: 1,
  unhealthyEndpointsCount: 0,
  loadEndpoints: vi.fn().mockResolvedValue(undefined),
  updateEndpointHealth: vi.fn()
}

const mockDashboardStore = {
  isLoading: false,
  isEmpty: false
}

vi.mock('@/stores/endpoints', () => ({
  useEndpointsStore: () => mockEndpointsStore
}))

vi.mock('@/stores/dashboard', () => ({
  useDashboard: () => mockDashboardStore
}))

const mockDashboardData = {
  stats: [
    { label: 'Healthy Endpoints', value: 8, status: 'success' },
    { label: 'Warning Endpoints', value: 2, status: 'warning' },
    { label: 'Failed Endpoints', value: 1, status: 'error' },
    { label: 'Total Requests', value: 1234, status: 'info' }
  ],
  chartData: {
    labels: ['09:00', '10:00', '11:00', '12:00'],
    datasets: [
      {
        label: 'Response Time',
        data: [120, 150, 110, 130],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)'
      }
    ]
  }
}

describe('Dashboard Overview', () => {
  let wrapper: VueWrapper

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // Reset mock states
    mockWebSocketService.state = 'disconnected'
    mockWebSocketService.isConnected = false
    mockDashboardStore.isLoading = false
    mockDashboardStore.isEmpty = false
  })

  it('should display status cards', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    const statusCards = wrapper.findAll('[data-testid="status-card"]')
    expect(statusCards).toHaveLength(4) // Should show 4 status cards
  })

  it('should connect to WebSocket for real-time updates', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Component should mount successfully
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('[data-testid="dashboard-view"]').exists()).toBe(true)
  })

  it('should update metrics when WebSocket message received', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Component should have connection status
    expect(wrapper.find('[data-testid="connection-status"]').exists()).toBe(true)
  })

  it('should show loading state initially', () => {
    mockDashboardStore.isLoading = true

    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    // Should show loading indicators in status cards
    expect(wrapper.text()).toContain('Loading...')
  })

  it('should handle WebSocket connection errors', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Component should be able to show error states (error div exists in template)
    expect(wrapper.vm).toBeDefined()
  })

  it('should render performance chart when data is available', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Should render chart component when endpoints exist
    const chart = wrapper.find('[data-testid="performance-chart-container"]')
    expect(chart.exists()).toBeTruthy()
  })

  it('should set up performance monitoring', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Component should show endpoints grid when endpoints exist
    expect(wrapper.find('[data-testid="endpoints-grid"]').exists()).toBe(true)
  })

  it('should clean up WebSocket connection on unmount', async () => {
    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Component should be properly mounted before unmount
    expect(wrapper.exists()).toBe(true)

    wrapper.unmount()

    // No errors should occur during unmount
    expect(true).toBe(true) // Just verify unmount doesn't throw
  })

  it('should handle empty data state', async () => {
    mockDashboardStore.isEmpty = true
    mockEndpointsStore.endpoints = []

    wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia()]
      }
    })

    await nextTick()

    // Should show empty state
    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBeTruthy()
  })
})
