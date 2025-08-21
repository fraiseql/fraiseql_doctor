import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EndpointDetails from '../EndpointDetails.vue'
import type { GraphQLEndpoint } from '../../types/endpoint'
import { EndpointStatus } from '../../types/endpoint'

// Mock the GraphQL client service
vi.mock('../../services/graphql/client', () => ({
  useGraphQLClient: () => ({
    testEndpoint: vi.fn().mockResolvedValue({
      success: true,
      responseTime: 100,
      statusCode: 200
    }),
    getIntrospectionSchema: vi.fn().mockResolvedValue('mock schema')
  })
}))

describe('EndpointDetails', () => {
  const mockEndpoint: GraphQLEndpoint = {
    id: 'test-endpoint',
    name: 'Test GraphQL API',
    url: 'https://api.test.com/graphql',
    description: 'Test endpoint for GraphQL operations',
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: true,
    isHealthy: true,
    responseTime: 150,
    lastChecked: new Date('2023-12-01T10:00:00Z'),
    headers: {
      'Authorization': 'Bearer test-token',
      'Content-Type': 'application/json'
    },
    createdAt: new Date('2023-11-01T10:00:00Z'),
    updatedAt: new Date('2023-12-01T10:00:00Z')
  }

  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('loading state', () => {
    it('should render loading state when no endpoint provided', () => {
      const wrapper = mount(EndpointDetails)
      
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Loading endpoint details...')
    })
  })

  describe('endpoint display', () => {
    it('should render endpoint information', () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="endpoint-name"]').text()).toBe('Test GraphQL API')
      expect(wrapper.find('[data-testid="endpoint-url"]').text()).toBe('https://api.test.com/graphql')
      expect(wrapper.find('[data-testid="endpoint-description"]').text()).toBe('Test endpoint for GraphQL operations')
    })

    it('should render status information correctly', () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="status-healthy"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="response-time"]').text()).toContain('150ms')
      expect(wrapper.find('[data-testid="last-checked"]').exists()).toBe(true)
    })

    it('should render error status correctly', () => {
      const errorEndpoint = {
        ...mockEndpoint,
        isHealthy: false,
        status: EndpointStatus.ERROR,
        errorMessage: 'Connection timeout'
      }

      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: errorEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="status-error"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="error-message"]').text()).toBe('Connection timeout')
    })

    it('should render headers when present', () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="headers-section"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Authorization')
      expect(wrapper.text()).toContain('Bearer test-token')
      expect(wrapper.text()).toContain('Content-Type')
      expect(wrapper.text()).toContain('application/json')
    })

    it('should hide headers section when no headers', () => {
      const endpointWithoutHeaders = {
        ...mockEndpoint,
        headers: undefined
      }

      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: endpointWithoutHeaders
        }
      })
      
      expect(wrapper.find('[data-testid="headers-section"]').exists()).toBe(false)
    })

    it('should show introspection status', () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="introspection-enabled"]').exists()).toBe(true)
    })

    it('should show introspection disabled', () => {
      const endpointWithoutIntrospection = {
        ...mockEndpoint,
        introspectionEnabled: false
      }

      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: endpointWithoutIntrospection
        }
      })
      
      expect(wrapper.find('[data-testid="introspection-disabled"]').exists()).toBe(true)
    })
  })

  describe('user actions', () => {
    it('should emit edit event when edit button clicked', async () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      await wrapper.find('[data-testid="edit-btn"]').trigger('click')
      
      expect(wrapper.emitted('edit')).toBeTruthy()
    })

    it('should emit delete event when delete button clicked', async () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      await wrapper.find('[data-testid="delete-btn"]').trigger('click')
      
      expect(wrapper.emitted('delete')).toBeTruthy()
    })

    it('should emit health check event when check button clicked', async () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      await wrapper.find('[data-testid="health-check-btn"]').trigger('click')
      
      expect(wrapper.emitted('health-check')).toBeTruthy()
    })
  })

  describe('schema introspection', () => {
    it('should load schema when introspection enabled', async () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      await wrapper.find('[data-testid="load-schema-btn"]').trigger('click')
      
      expect(wrapper.find('[data-testid="schema-loading"]').exists()).toBe(true)
    })

    it('should display schema after loading', async () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      await wrapper.find('[data-testid="load-schema-btn"]').trigger('click')
      
      // Wait for async operation
      await new Promise(resolve => setTimeout(resolve, 50))
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('[data-testid="schema-content"]').exists()).toBe(true)
    })

    it('should not show load schema button when introspection disabled', () => {
      const endpointWithoutIntrospection = {
        ...mockEndpoint,
        introspectionEnabled: false
      }

      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: endpointWithoutIntrospection
        }
      })
      
      expect(wrapper.find('[data-testid="load-schema-btn"]').exists()).toBe(false)
    })
  })

  describe('timestamps', () => {
    it('should display formatted timestamps', () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="created-at"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="updated-at"]').exists()).toBe(true)
    })
  })

  describe('responsive behavior', () => {
    it('should render action buttons in correct order', () => {
      const wrapper = mount(EndpointDetails, {
        props: {
          endpoint: mockEndpoint
        }
      })
      
      const actionButtons = wrapper.find('[data-testid="action-buttons"]')
      expect(actionButtons.exists()).toBe(true)
      
      // Check that all action buttons are present
      expect(wrapper.find('[data-testid="health-check-btn"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="edit-btn"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(true)
    })
  })
})