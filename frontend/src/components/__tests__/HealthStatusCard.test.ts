import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HealthStatusCard from '../HealthStatusCard.vue'
import { EndpointStatus, type GraphQLEndpoint } from '../../types/endpoint'

describe('HealthStatusCard', () => {
  const baseEndpoint: GraphQLEndpoint = {
    id: 'test-1',
    name: 'Test API',
    url: 'http://localhost:4000/graphql',
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: true,
    isHealthy: true,
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
    lastChecked: new Date()
  }

  it('should display healthy endpoint with green indicator', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      isHealthy: true,
      responseTime: 150,
      lastChecked: new Date()
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="status-indicator"]').classes()).toContain('bg-green-500')
    expect(wrapper.find('[data-testid="response-time"]').text()).toBe('150ms')
    expect(wrapper.find('[data-testid="error-message"]').exists()).toBe(false)
  })

  it('should display unhealthy endpoint with red indicator and error state', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      isHealthy: false,
      responseTime: 5000,
      errorMessage: 'Connection timeout',
      lastChecked: new Date()
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="status-indicator"]').classes()).toContain('bg-red-500')
    expect(wrapper.find('[data-testid="error-message"]').text()).toBe('Connection timeout')
    expect(wrapper.find('[data-testid="response-time"]').text()).toBe('5000ms')
  })

  it('should display checking status with yellow indicator', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      status: EndpointStatus.CHECKING,
      isHealthy: true,
      responseTime: 0
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="status-indicator"]').classes()).toContain('bg-yellow-500')
    expect(wrapper.find('[data-testid="response-time"]').text()).toBe('0ms')
  })

  it('should format last checked time correctly', () => {
    const now = new Date()
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000)

    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      lastChecked: fiveMinutesAgo
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="last-checked"]').text()).toBe('5m ago')
  })

  it('should display "Never" when lastChecked is undefined', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint
    }
    delete (endpoint as any).lastChecked

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="last-checked"]').text()).toBe('Never')
  })

  it('should display "Just now" for very recent checks', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      lastChecked: new Date() // Current time
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="last-checked"]').text()).toBe('Just now')
  })

  it('should display endpoint name and URL', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      name: 'My Test API',
      url: 'https://api.example.com/graphql'
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('h3').text()).toBe('My Test API')
    expect(wrapper.text()).toContain('https://api.example.com/graphql')
  })

  it('should not display error message when endpoint is healthy', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint,
      isHealthy: true,
      errorMessage: 'This should not be shown'
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="error-message"]').exists()).toBe(false)
  })

  it('should handle missing response time gracefully', () => {
    const endpoint: GraphQLEndpoint = {
      ...baseEndpoint
    }
    delete (endpoint as any).responseTime

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="response-time"]').text()).toBe('0ms')
  })
})
