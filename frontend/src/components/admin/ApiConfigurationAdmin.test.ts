import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApiConfigurationAdmin from './ApiConfigurationAdmin.vue'

describe('ApiConfigurationAdmin', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should display 3 endpoint cards for api.example.dev, api.example.st, api.example.io', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    const cards = wrapper.findAll('[data-testid="api-endpoint-card"]')
    expect(cards).toHaveLength(3)
    expect(wrapper.text()).toContain('api.example.dev')
    expect(wrapper.text()).toContain('api.example.st')
    expect(wrapper.text()).toContain('api.example.io')
  })

  it('should show health indicators (green/yellow/red) for each API', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    expect(wrapper.find('[data-testid="api-example-dev-status"]').exists()).toBe(true)
    const statusElement = wrapper.find('[data-testid="api-example-dev-status"]')
    expect(statusElement.classes()).toContain('status-indicator')
  })

  it('should open configuration modal on Configure button click', async () => {
    const wrapper = mount(ApiConfigurationAdmin)
    const configBtn = wrapper.find('[data-testid="configure-api-example-dev"]')
    await configBtn.trigger('click')
    expect(wrapper.find('[data-testid="api-config-modal"]').exists()).toBe(true)
  })

  it('should display page title and description', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    expect(wrapper.text()).toContain('GraphQL API Configuration')
    expect(wrapper.text()).toContain('Monitor and configure your GraphQL endpoints')
  })

  it('should show Add API button', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    expect(wrapper.find('[data-testid="add-api-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="add-api-btn"]').text()).toContain('Add API')
  })
})
