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