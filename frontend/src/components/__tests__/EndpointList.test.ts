import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EndpointList from '../EndpointList.vue'
import { useEndpointsStore } from '../../stores/endpoints'
import type { GraphQLEndpoint } from '../../types/endpoint'
import { EndpointStatus } from '../../types/endpoint'

// Mock the router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock the GraphQL client service
vi.mock('../../services/graphql/client', () => ({
  useGraphQLClient: () => ({
    testEndpoint: vi.fn().mockResolvedValue({
      success: true,
      responseTime: 100,
      statusCode: 200
    }),
    getIntrospectionSchema: vi.fn().mockResolvedValue('schema')
  })
}))

describe('EndpointList', () => {
  let store: ReturnType<typeof useEndpointsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useEndpointsStore()
  })

  describe('rendering', () => {
    it('should render empty state when no endpoints', async () => {
      const wrapper = mount(EndpointList)
      
      expect(wrapper.text()).toContain('No endpoints')
    })

    it('should render loading state', async () => {
      store.isLoading = true
      
      const wrapper = mount(EndpointList)
      
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true)
    })

    it('should render error state', async () => {
      store.error = 'Failed to load endpoints'
      
      const wrapper = mount(EndpointList)
      
      expect(wrapper.text()).toContain('Failed to load endpoints')
    })

    it('should render endpoints list', async () => {
      store.endpoints = [
        createMockEndpoint('1', { name: 'Test Endpoint 1' }),
        createMockEndpoint('2', { name: 'Test Endpoint 2' })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      expect(wrapper.text()).toContain('Test Endpoint 1')
      expect(wrapper.text()).toContain('Test Endpoint 2')
    })
  })

  describe('endpoint status display', () => {
    it('should show healthy status for working endpoints', async () => {
      store.endpoints = [
        createMockEndpoint('1', { 
          name: 'Healthy Endpoint',
          isHealthy: true,
          status: EndpointStatus.ACTIVE 
        })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      expect(wrapper.find('[data-testid="status-healthy"]').exists()).toBe(true)
    })

    it('should show error status for failed endpoints', async () => {
      store.endpoints = [
        createMockEndpoint('1', { 
          name: 'Failed Endpoint',
          isHealthy: false,
          status: EndpointStatus.ERROR,
          errorMessage: 'Connection failed'
        })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      expect(wrapper.find('[data-testid="status-error"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Connection failed')
    })

    it('should show checking status for endpoints being tested', async () => {
      store.endpoints = [
        createMockEndpoint('1', { 
          name: 'Checking Endpoint',
          status: EndpointStatus.CHECKING
        })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      expect(wrapper.find('[data-testid="status-checking"]').exists()).toBe(true)
    })
  })

  describe('user interactions', () => {
    it('should handle add new endpoint button click', async () => {
      const wrapper = mount(EndpointList)
      
      await wrapper.find('[data-testid="add-endpoint-btn"]').trigger('click')
      
      expect(wrapper.emitted('add-endpoint')).toBeTruthy()
    })

    it('should handle endpoint selection', async () => {
      store.endpoints = [
        createMockEndpoint('test-id', { name: 'Test Endpoint' })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      await wrapper.find('[data-testid="endpoint-item-test-id"]').trigger('click')
      
      expect(wrapper.emitted('select-endpoint')).toBeTruthy()
      expect(wrapper.emitted('select-endpoint')?.[0]).toEqual(['test-id'])
    })

    it('should handle endpoint edit action', async () => {
      store.endpoints = [
        createMockEndpoint('test-id', { name: 'Test Endpoint' })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      await wrapper.find('[data-testid="edit-endpoint-test-id"]').trigger('click')
      
      expect(wrapper.emitted('edit-endpoint')).toBeTruthy()
      expect(wrapper.emitted('edit-endpoint')?.[0]).toEqual(['test-id'])
    })

    it('should handle endpoint delete action', async () => {
      store.endpoints = [
        createMockEndpoint('test-id', { name: 'Test Endpoint' })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      await wrapper.find('[data-testid="delete-endpoint-test-id"]').trigger('click')
      
      expect(wrapper.emitted('delete-endpoint')).toBeTruthy()
      expect(wrapper.emitted('delete-endpoint')?.[0]).toEqual(['test-id'])
    })

    it('should handle health check action', async () => {
      store.endpoints = [
        createMockEndpoint('test-id', { name: 'Test Endpoint' })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      
      await wrapper.find('[data-testid="check-health-test-id"]').trigger('click')
      
      expect(wrapper.emitted('check-health')).toBeTruthy()
      expect(wrapper.emitted('check-health')?.[0]).toEqual(['test-id'])
    })
  })

  describe('lifecycle', () => {
    it('should load endpoints on mount', () => {
      const loadEndpoints = vi.spyOn(store, 'loadEndpoints')
      
      mount(EndpointList)
      
      expect(loadEndpoints).toHaveBeenCalled()
    })
  })

  describe('filtering and search', () => {
    it('should filter endpoints by status', async () => {
      // Mock loadEndpoints to prevent it from overriding our test data
      vi.spyOn(store, 'loadEndpoints').mockResolvedValue()
      
      store.endpoints = [
        createMockEndpoint('1', { name: 'Healthy', status: EndpointStatus.ACTIVE, isHealthy: true }),
        createMockEndpoint('2', { name: 'Failed', status: EndpointStatus.ERROR, isHealthy: false })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      await wrapper.vm.$nextTick()
      
      // Filter by healthy status
      await wrapper.find('[data-testid="filter-healthy"]').trigger('click')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.text()).toContain('Healthy')
      expect(wrapper.text()).not.toContain('Failed')
    })

    it('should search endpoints by name', async () => {
      // Mock loadEndpoints to prevent it from overriding our test data
      vi.spyOn(store, 'loadEndpoints').mockResolvedValue()
      
      store.endpoints = [
        createMockEndpoint('1', { name: 'Production API' }),
        createMockEndpoint('2', { name: 'Staging API' })
      ]
      store.isLoading = false
      
      const wrapper = mount(EndpointList)
      await wrapper.vm.$nextTick()
      
      const searchInput = wrapper.find('[data-testid="search-input"]')
      await searchInput.setValue('Production')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.text()).toContain('Production API')
      expect(wrapper.text()).not.toContain('Staging API')
    })
  })
})

function createMockEndpoint(id: string, overrides?: Partial<GraphQLEndpoint>): GraphQLEndpoint {
  return {
    id,
    name: `Endpoint ${id}`,
    url: `https://api${id}.example.com/graphql`,
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: true,
    isHealthy: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides
  }
}