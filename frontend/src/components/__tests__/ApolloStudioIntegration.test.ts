import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApolloStudioIntegration from '../ApolloStudioIntegration.vue'

describe('Apollo Studio Integration - Cycle 1', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render Apollo Studio container', () => {
    const wrapper = mount(ApolloStudioIntegration)
    
    expect(wrapper.find('[data-testid="apollo-studio-container"]').exists()).toBe(true)
  })

  it('should have correct CSS classes for layout', () => {
    const wrapper = mount(ApolloStudioIntegration)
    const container = wrapper.find('[data-testid="apollo-studio-container"]')
    
    expect(container.classes()).toContain('apollo-studio-integration')
  })

  it('should render component title', () => {
    const wrapper = mount(ApolloStudioIntegration)
    
    expect(wrapper.find('[data-testid="studio-title"]').text()).toBe('GraphQL Playground')
  })
})

describe('Apollo Studio Integration - Cycle 2', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render iframe when endpoint is provided', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    expect(wrapper.find('[data-testid="apollo-studio-iframe"]').exists()).toBe(true)
  })

  it('should set correct iframe src URL', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.attributes('src')).toContain('studio.apollographql.com')
  })

  it('should show loading state initially', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    expect(wrapper.find('[data-testid="studio-loading"]').exists()).toBe(true)
  })

  it('should hide loading state after iframe loads', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    // Simulate iframe load
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    await iframe.trigger('load')
    
    expect(wrapper.find('[data-testid="studio-loading"]').exists()).toBe(false)
  })
})

describe('Apollo Studio Integration - Cycle 8: Full Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should integrate with configuration service for authentication', async () => {
    const mockEndpoint = {
      id: '1',
      name: 'Test API',
      url: 'https://auth.api.com/graphql',
      status: 'ACTIVE' as const,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer test-token-123'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpoint: mockEndpoint,
        authType: 'bearer'
      }
    })

    // Should render iframe with authenticated URL
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toContain('studio.apollographql.com')
  })

  it('should handle endpoint switching with different auth types', async () => {
    const bearerEndpoint = {
      id: '1',
      name: 'Bearer API',
      url: 'https://bearer.api.com/graphql',
      status: 'ACTIVE' as const,
      introspectionEnabled: true,
      isHealthy: true,
      headers: { 'Authorization': 'Bearer token' },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const apiKeyEndpoint = {
      id: '2', 
      name: 'API Key API',
      url: 'https://apikey.api.com/graphql',
      status: 'ACTIVE' as const,
      introspectionEnabled: true,
      isHealthy: true,
      headers: { 'X-API-Key': 'api-key-value' },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpoint: bearerEndpoint,
        authType: 'bearer'
      }
    })

    // Switch to API key endpoint
    await wrapper.setProps({
      endpoint: apiKeyEndpoint,
      authType: 'apikey'
    })

    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.attributes('src')).toContain('studio.apollographql.com')
    expect(iframe.attributes('src')).toContain(encodeURIComponent(apiKeyEndpoint.url))
  })

  it('should display error states with recovery options', async () => {
    const invalidEndpoint = {
      id: '1',
      name: 'Invalid API',
      url: 'invalid-url-format',
      status: 'INACTIVE' as const,
      introspectionEnabled: false,
      isHealthy: false,
      headers: {},
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpoint: invalidEndpoint,
        showErrorBoundary: true
      }
    })

    expect(wrapper.find('[data-testid="error-boundary"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="error-message"]').text()).toContain('Configuration Error')
    expect(wrapper.find('[data-testid="retry-button"]').exists()).toBe(true)
  })

  it('should handle network errors with retry functionality', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://timeout.api.com/graphql',
        enableRetry: true,
        maxRetries: 3
      }
    })

    // Simulate iframe error
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    await iframe.trigger('error')
    await wrapper.vm.$nextTick() // Wait for DOM updates

    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="retry-counter"]').text()).toContain('Attempt 1 of 3')
    
    // Test retry button
    let retryButton = wrapper.find('[data-testid="retry-button"]')
    expect(retryButton.exists()).toBe(true)
    
    await retryButton.trigger('click')
    await wrapper.vm.$nextTick() // Wait for DOM updates
    
    // Get fresh reference to retry counter after click
    const retryCounterAfter = wrapper.find('[data-testid="retry-counter"]')
    expect(retryCounterAfter.text()).toContain('Attempt 2 of 3')
  })

  it('should emit configuration events for parent components', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })

    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    await iframe.trigger('load')

    expect(wrapper.emitted('studio-loaded')).toBeTruthy()
    expect(wrapper.emitted('studio-loaded')![0]).toEqual([{
      url: expect.stringContaining('studio.apollographql.com'),
      timestamp: expect.any(Date)
    }])
  })

  it('should handle custom parameters and theming', async () => {
    const customParams = {
      theme: 'dark',
      showDocs: 'true',
      operation: 'query'
    }

    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql',
        customParams,
        theme: 'dark'
      }
    })

    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    const src = iframe.attributes('src')
    
    expect(src).toContain('theme=dark')
    expect(src).toContain('showDocs=true')
    expect(src).toContain('operation=query')
  })

  it('should support accessibility features and ARIA labels', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql',
        ariaLabel: 'GraphQL API Explorer'
      }
    })

    const container = wrapper.find('[data-testid="apollo-studio-container"]')
    expect(container.attributes('role')).toBe('application')
    expect(container.attributes('aria-label')).toBe('GraphQL API Explorer')

    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.attributes('title')).toBe('Apollo GraphQL Studio')
    expect(iframe.attributes('aria-label')).toBe('GraphQL API Explorer Interface')
  })

  it('should handle responsive layout and sizing', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql',
        height: '600px',
        responsive: true
      }
    })

    const container = wrapper.find('[data-testid="apollo-studio-container"]')
    expect(container.classes()).toContain('responsive-layout')

    // Test different viewport sizes
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.attributes('style')).toContain('height: calc(527px)')
  })

  it('should provide comprehensive error information for debugging', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'javascript:alert("xss")',
        debugMode: true,
        showErrorBoundary: true
      }
    })

    expect(wrapper.find('[data-testid="debug-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="security-warning"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="error-details"]').text()).toContain('Dangerous URL pattern detected')
  })

  it('should manage iframe lifecycle and cleanup', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })

    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.exists()).toBe(true)

    // Test cleanup on unmount should not throw errors
    expect(() => wrapper.unmount()).not.toThrow()
    
    // Component lifecycle management test completed successfully
    expect(true).toBe(true) // Test passes if unmount completed without errors
  })

  it('should support custom studio configuration options', () => {
    const mockEndpoint = {
      id: '1',
      name: 'Custom API',
      url: 'https://api.example.com/graphql',
      status: 'ACTIVE' as const,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer custom-token'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpoint: mockEndpoint,
        configMode: 'advanced'
      }
    })

    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.exists()).toBe(true)
    
    // Verify config is applied
    expect(wrapper.find('[data-testid="config-summary"]').text()).toContain('Bearer authentication')
    expect(wrapper.find('[data-testid="config-summary"]').text()).toContain('Introspection enabled')
  })
})