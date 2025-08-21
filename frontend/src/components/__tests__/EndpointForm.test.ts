import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EndpointForm from '../EndpointForm.vue'
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
    getIntrospectionSchema: vi.fn().mockResolvedValue('schema')
  })
}))

describe('EndpointForm', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('create mode', () => {
    it('should render form in create mode', () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      expect(wrapper.find('[data-testid="form-title"]').text()).toBe('Add New Endpoint')
      expect(wrapper.find('[data-testid="submit-btn"]').text()).toBe('Add Endpoint')
    })

    it('should have empty form fields initially', () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      expect(wrapper.find('[data-testid="name-input"]').element.value).toBe('')
      expect(wrapper.find('[data-testid="url-input"]').element.value).toBe('')
      expect(wrapper.find('[data-testid="description-input"]').element.value).toBe('')
    })

    it('should validate required fields', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('[data-testid="name-error"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="url-error"]').exists()).toBe(true)
    })

    it('should validate URL format', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="name-input"]').setValue('Test')
      await wrapper.find('[data-testid="url-input"]').setValue('invalid-url')
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      
      const urlError = wrapper.find('[data-testid="url-error"]')
      expect(urlError.exists()).toBe(true)
      expect(urlError.text()).toContain('valid URL')
    })

    it('should emit create event with form data', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="name-input"]').setValue('Test Endpoint')
      await wrapper.find('[data-testid="url-input"]').setValue('https://api.example.com/graphql')
      await wrapper.find('[data-testid="description-input"]').setValue('Test description')
      await wrapper.find('[data-testid="introspection-checkbox"]').setChecked(true)
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.emitted('create')).toBeTruthy()
      expect(wrapper.emitted('create')?.[0]).toEqual([{
        name: 'Test Endpoint',
        url: 'https://api.example.com/graphql',
        description: 'Test description',
        introspectionEnabled: true,
        headers: {}
      }])
    })
  })

  describe('edit mode', () => {
    const mockEndpoint: GraphQLEndpoint = {
      id: 'test-id',
      name: 'Existing Endpoint',
      url: 'https://existing.com/graphql',
      description: 'Existing description',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer token'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    it('should render form in edit mode', () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'edit',
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="form-title"]').text()).toBe('Edit Endpoint')
      expect(wrapper.find('[data-testid="submit-btn"]').text()).toBe('Update Endpoint')
    })

    it('should populate form with endpoint data', () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'edit',
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.find('[data-testid="name-input"]').element.value).toBe('Existing Endpoint')
      expect(wrapper.find('[data-testid="url-input"]').element.value).toBe('https://existing.com/graphql')
      expect(wrapper.find('[data-testid="description-input"]').element.value).toBe('Existing description')
      expect(wrapper.find('[data-testid="introspection-checkbox"]').element.checked).toBe(true)
    })

    it('should emit update event with form data', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'edit',
          endpoint: mockEndpoint
        }
      })
      
      await wrapper.find('[data-testid="name-input"]').setValue('Updated Name')
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.emitted('update')).toBeTruthy()
      expect(wrapper.emitted('update')?.[0]).toEqual([{
        name: 'Updated Name',
        url: 'https://existing.com/graphql',
        description: 'Existing description',
        introspectionEnabled: true,
        headers: {
          'Authorization': 'Bearer token'
        }
      }])
    })
  })

  describe('headers management', () => {
    it('should add new header', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="add-header-btn"]').trigger('click')
      
      expect(wrapper.find('[data-testid="header-row-0"]').exists()).toBe(true)
    })

    it('should remove header', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="add-header-btn"]').trigger('click')
      await wrapper.find('[data-testid="remove-header-0"]').trigger('click')
      
      expect(wrapper.find('[data-testid="header-row-0"]').exists()).toBe(false)
    })

    it('should update headers in form data', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="add-header-btn"]').trigger('click')
      await wrapper.vm.$nextTick()
      await wrapper.find('[data-testid="header-key-0"]').setValue('Authorization')
      await wrapper.find('[data-testid="header-value-0"]').setValue('Bearer token')
      
      await wrapper.find('[data-testid="name-input"]').setValue('Test')
      await wrapper.find('[data-testid="url-input"]').setValue('https://api.example.com/graphql')
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.emitted('create')?.[0][0].headers).toEqual({
        'Authorization': 'Bearer token'
      })
    })
  })

  describe('test endpoint functionality', () => {
    it('should test endpoint connectivity', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="url-input"]').setValue('https://api.example.com/graphql')
      await wrapper.find('[data-testid="test-btn"]').trigger('click')
      
      // Wait for async operation to complete
      await new Promise(resolve => setTimeout(resolve, 50))
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('[data-testid="test-result"]').exists()).toBe(true)
    })

    it('should show test loading state', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="url-input"]').setValue('https://api.example.com/graphql')
      
      // Trigger test and immediately check loading state
      const testPromise = wrapper.find('[data-testid="test-btn"]').trigger('click')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('[data-testid="test-loading"]').exists()).toBe(true)
      
      await testPromise
      await new Promise(resolve => setTimeout(resolve, 50))
      await wrapper.vm.$nextTick()
    })
  })

  describe('form state', () => {
    it('should handle loading state', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create',
          loading: true
        }
      })
      
      expect(wrapper.find('[data-testid="submit-btn"]').attributes('disabled')).toBeDefined()
    })

    it('should handle cancel action', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="cancel-btn"]').trigger('click')
      
      expect(wrapper.emitted('cancel')).toBeTruthy()
    })

    it('should reset form when cancelled', async () => {
      const wrapper = mount(EndpointForm, {
        props: {
          mode: 'create'
        }
      })
      
      await wrapper.find('[data-testid="name-input"]').setValue('Test')
      await wrapper.find('[data-testid="cancel-btn"]').trigger('click')
      
      expect(wrapper.find('[data-testid="name-input"]').element.value).toBe('')
    })
  })
})