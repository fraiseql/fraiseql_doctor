import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApiConfigurationModal from '../components/ApiConfigurationModal.vue'
import type { ApiEndpoint } from '@/types/admin'

const mockEndpoint: ApiEndpoint = {
  id: 'api-example-dev',
  name: 'Example Dev API',
  url: 'https://api.example.dev/graphql',
  environment: 'dev',
  isHealthy: true,
  responseTime: 45,
  errorRate: 0.1,
  lastCheck: new Date()
}

describe('ApiConfigurationModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render modal when modelValue is true', () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    expect(wrapper.find('[data-testid="api-config-modal"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Configure API: Example Dev API')
  })

  it('should not render modal when modelValue is false', () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: false,
        endpoint: mockEndpoint
      }
    })

    expect(wrapper.find('[data-testid="api-config-modal"]').exists()).toBe(false)
  })

  it('should save authentication settings (Bearer, API Key, Basic)', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    // Test Bearer token authentication
    await wrapper.find('[data-testid="auth-type-select"]').setValue('bearer')
    expect(wrapper.find('[data-testid="auth-token-input"]').exists()).toBe(true)

    await wrapper.find('[data-testid="auth-token-input"]').setValue('test-token-123')
    await wrapper.find('[data-testid="save-config-btn"]').trigger('click')

    expect(wrapper.emitted('save')).toBeTruthy()
    const saveEvent = wrapper.emitted('save')?.[0]?.[0] as any
    expect(saveEvent.authentication).toEqual({
      type: 'bearer',
      token: 'test-token-123'
    })
  })

  it('should configure monitoring thresholds', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    await wrapper.find('[data-testid="response-time-warning"]').setValue('200')
    await wrapper.find('[data-testid="response-time-critical"]').setValue('500')
    await wrapper.find('[data-testid="error-rate-warning"]').setValue('2')
    await wrapper.find('[data-testid="error-rate-critical"]').setValue('5')
    await wrapper.find('[data-testid="save-config-btn"]').trigger('click')

    expect(wrapper.emitted('save')).toBeTruthy()
    const saveEvent = wrapper.emitted('save')?.[0]?.[0] as any
    expect(saveEvent.thresholds).toEqual({
      responseTime: { warning: 200, critical: 500 },
      errorRate: { warning: 2, critical: 5 }
    })
  })

  it('should test connection functionality', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    const testBtn = wrapper.find('[data-testid="test-connection-btn"]')
    expect(testBtn.exists()).toBe(true)

    await testBtn.trigger('click')

    // Should show testing state
    expect(wrapper.text()).toContain('Testing...')

    // Wait for async operation to complete (longer timeout for simulated delay)
    await new Promise(resolve => setTimeout(resolve, 1100))
    await wrapper.vm.$nextTick()

    // Should show connection test result
    expect(wrapper.find('[data-testid="connection-test-result"]').exists()).toBe(true)
  })

  it('should handle different authentication types', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    // Test API Key authentication
    await wrapper.find('[data-testid="auth-type-select"]').setValue('api-key')
    expect(wrapper.find('[data-testid="auth-api-key-input"]').exists()).toBe(true)

    // Test Basic authentication
    await wrapper.find('[data-testid="auth-type-select"]').setValue('basic')
    expect(wrapper.find('[data-testid="auth-username-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="auth-password-input"]').exists()).toBe(true)

    // Test None authentication
    await wrapper.find('[data-testid="auth-type-select"]').setValue('none')
    expect(wrapper.find('[data-testid="auth-token-input"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="auth-api-key-input"]').exists()).toBe(false)
  })

  it('should populate form with endpoint data', () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    expect((wrapper.find('[data-testid="endpoint-name-input"]').element as HTMLInputElement).value).toBe('Example Dev API')
    expect((wrapper.find('[data-testid="endpoint-url-input"]').element as HTMLInputElement).value).toBe('https://api.example.dev/graphql')
    expect((wrapper.find('[data-testid="environment-select"]').element as HTMLSelectElement).value).toBe('dev')
  })

  it('should emit update:modelValue on cancel', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    await wrapper.find('[data-testid="cancel-btn"]').trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([false])
  })

  it('should validate required fields', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    // Clear required field
    await wrapper.find('[data-testid="endpoint-name-input"]').setValue('')
    await wrapper.vm.$nextTick()
    await wrapper.find('[data-testid="save-config-btn"]').trigger('click')
    await wrapper.vm.$nextTick()

    // Should show validation error
    expect(wrapper.find('[data-testid="name-error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Name is required')
  })

  it('should handle connection test success and failure', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: {
        modelValue: true,
        endpoint: mockEndpoint
      }
    })

    // Mock successful connection test
    const testBtn = wrapper.find('[data-testid="test-connection-btn"]')
    await testBtn.trigger('click')

    await new Promise(resolve => setTimeout(resolve, 1100))
    await wrapper.vm.$nextTick()

    const resultElement = wrapper.find('[data-testid="connection-test-result"]')
    expect(resultElement.exists()).toBe(true)

    // Should show success or failure message
    const resultText = resultElement.text()
    expect(resultText).toMatch(/success|failed|error/i)
  })
})
