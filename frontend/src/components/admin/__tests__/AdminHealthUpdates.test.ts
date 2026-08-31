import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApiConfigurationAdmin from '../ApiConfigurationAdmin.vue'

// Mock WebSocket integration
const mockWebSocketService = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  emit: vi.fn(),
  on: vi.fn(),
  isConnected: vi.fn(() => true)
}

// Mock the websocket service
vi.mock('@/services/websocket/useWebSocket', () => ({
  useWebSocket: () => mockWebSocketService
}))

describe('AdminHealthUpdates', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should update health status via WebSocket', async () => {
    const wrapper = mount(ApiConfigurationAdmin)

    // Get the initial healthy status
    const devStatusElement = wrapper.find('[data-testid="api-example-dev-status"]')
    expect(devStatusElement.classes()).toContain('status-healthy')

    // Simulate WebSocket health update message
    const healthUpdate = {
      apiId: 'api-example-dev',
      isHealthy: false,
      responseTime: 5000,
      errorRate: 15.5,
      timestamp: new Date()
    }

    // Trigger the health update through the component's method
    await wrapper.vm.handleHealthUpdate(healthUpdate)
    await wrapper.vm.$nextTick()

    // Verify the status indicator updated to unhealthy
    const updatedStatusElement = wrapper.find('[data-testid="api-example-dev-status"]')
    expect(updatedStatusElement.classes()).toContain('status-unhealthy')
  })

  it('should show last check timestamps', () => {
    const wrapper = mount(ApiConfigurationAdmin)

    // Check that all endpoint cards show last check time
    const timeElements = wrapper.findAll('[data-testid="last-check-time"]')
    expect(timeElements.length).toBeGreaterThan(0)

    // Verify the timestamp format (should show relative time like "Just now", "2min ago")
    timeElements.forEach(timeEl => {
      const timeText = timeEl.text()
      expect(timeText).toMatch(/just now|ago|min|hour|day/i)
    })
  })

  it('should display response times and error rates', () => {
    const wrapper = mount(ApiConfigurationAdmin)

    // Check response time elements exist and show correct format
    const responseTimeElements = wrapper.findAll('[data-testid="response-time"]')
    expect(responseTimeElements.length).toBe(3) // One for each API

    responseTimeElements.forEach(rtEl => {
      expect(rtEl.text()).toMatch(/\d+ms/)
    })

    // Check error rate elements exist
    const errorRateElements = wrapper.findAll('[data-testid="error-rate"]')
    expect(errorRateElements.length).toBe(3)

    errorRateElements.forEach(erEl => {
      expect(erEl.text()).toMatch(/\d+(\.\d+)?%/)
    })
  })

  it('should establish WebSocket connection on mount', () => {
    mount(ApiConfigurationAdmin)

    // Verify WebSocket connection was established
    expect(mockWebSocketService.connect).toHaveBeenCalledWith(
      'api-health-updates',
      expect.any(Function)
    )
  })

  it('should handle multiple health updates for different APIs', async () => {
    const wrapper = mount(ApiConfigurationAdmin)

    // Update multiple APIs
    const updates = [
      { apiId: 'api-example-dev', isHealthy: false, responseTime: 1000 },
      { apiId: 'api-example-st', isHealthy: true, responseTime: 150 },
      { apiId: 'api-example-io', isHealthy: false, responseTime: 800 }
    ]

    for (const update of updates) {
      await wrapper.vm.handleHealthUpdate(update)
    }
    await wrapper.vm.$nextTick()

    // Verify each API status was updated correctly
    expect(wrapper.find('[data-testid="api-example-dev-status"]').classes()).toContain('status-unhealthy')
    expect(wrapper.find('[data-testid="api-example-st-status"]').classes()).toContain('status-healthy')
    expect(wrapper.find('[data-testid="api-example-io-status"]').classes()).toContain('status-unhealthy')
  })

  it('should disconnect WebSocket on unmount', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    wrapper.unmount()

    // Verify WebSocket was disconnected
    expect(mockWebSocketService.disconnect).toHaveBeenCalledWith('api-health-updates')
  })
})
