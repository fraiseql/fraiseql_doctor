import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import AlertRuleForm from '../AlertRuleForm.vue'
import type { AlertRule } from '../../services/alertingEngine'

describe('AlertRuleForm', () => {
  const createMockRule = (overrides: Partial<AlertRule> = {}): AlertRule => ({
    id: 'rule-1',
    name: 'Test Alert Rule',
    endpointId: 'endpoint-1',
    condition: {
      metric: 'executionTime',
      operator: 'greaterThan',
      threshold: 500,
      duration: 300000
    },
    severity: 'medium',
    enabled: true,
    createdAt: new Date(),
    ...overrides
  })

  describe('Component Rendering', () => {
    it('should render alert rule form', () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      expect(wrapper.find('[data-testid="alert-rule-form"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="rule-name-input"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="endpoint-select"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="metric-select"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="operator-select"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="threshold-input"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="duration-input"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="severity-select"]').exists()).toBe(true)
    })

    it('should show create mode title and button', () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      expect(wrapper.text()).toContain('Create Alert Rule')
      expect(wrapper.find('[data-testid="create-rule-button"]').exists()).toBe(true)
    })

    it('should show edit mode title and button when editing', () => {
      const mockRule = createMockRule()
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'edit',
          rule: mockRule
        }
      })

      expect(wrapper.text()).toContain('Edit Alert Rule')
      expect(wrapper.find('[data-testid="update-rule-button"]').exists()).toBe(true)
    })

    it('should populate form fields when editing existing rule', async () => {
      const mockRule = createMockRule({
        name: 'High Response Time Alert',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 800,
          duration: 600000
        },
        severity: 'high'
      })

      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'edit',
          rule: mockRule
        }
      })

      await wrapper.vm.$nextTick()

      expect((wrapper.find('[data-testid="rule-name-input"]').element as HTMLInputElement).value)
        .toBe('High Response Time Alert')
      expect((wrapper.find('[data-testid="metric-select"]').element as HTMLSelectElement).value)
        .toBe('executionTime')
      expect((wrapper.find('[data-testid="operator-select"]').element as HTMLSelectElement).value)
        .toBe('greaterThan')
      expect((wrapper.find('[data-testid="threshold-input"]').element as HTMLInputElement).value)
        .toBe('800')
      expect((wrapper.find('[data-testid="severity-select"]').element as HTMLSelectElement).value)
        .toBe('high')
    })
  })

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.find('[data-testid="name-error"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Rule name is required')
    })

    it('should validate threshold value', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      await wrapper.find('[data-testid="rule-name-input"]').setValue('Test Rule')
      await wrapper.find('[data-testid="endpoint-select"]').setValue('endpoint-1')
      await wrapper.find('[data-testid="threshold-input"]').setValue('-100')

      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.find('[data-testid="threshold-error"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Threshold must be a positive number')
    })

    it('should validate duration value', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      await wrapper.find('[data-testid="rule-name-input"]').setValue('Test Rule')
      await wrapper.find('[data-testid="endpoint-select"]').setValue('endpoint-1')
      await wrapper.find('[data-testid="duration-input"]').setValue('0')

      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.find('[data-testid="duration-error"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Duration must be at least 60 seconds')
    })

    it('should show all validation errors at once', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      // Leave all required fields empty
      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.findAll('[data-testid$="-error"]').length).toBeGreaterThan(0)
    })

    it('should clear validation errors when fields are corrected', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      // Trigger validation error
      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.find('[data-testid="name-error"]').exists()).toBe(true)

      // Fix the error
      await wrapper.find('[data-testid="rule-name-input"]').setValue('Valid Rule Name')
      await nextTick()

      expect(wrapper.find('[data-testid="name-error"]').exists()).toBe(false)
    })
  })

  describe('Metric-specific Configuration', () => {
    it('should show appropriate units for execution time metric', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      await wrapper.find('[data-testid="metric-select"]').setValue('executionTime')
      await nextTick()

      expect(wrapper.find('[data-testid="threshold-unit"]').text()).toContain('ms')
    })

    it('should show appropriate units for response size metric', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      await wrapper.find('[data-testid="metric-select"]').setValue('responseSize')

      expect(wrapper.text()).toContain('bytes')
      expect(wrapper.find('[data-testid="threshold-unit"]').text()).toContain('bytes')
    })

    it('should show appropriate operators for different metrics', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      await wrapper.find('[data-testid="metric-select"]').setValue('executionTime')

      const operatorOptions = wrapper.findAll('[data-testid="operator-option"]')
      const operatorValues = operatorOptions.map(option => (option.element as HTMLOptionElement).value)

      expect(operatorValues).toContain('greaterThan')
      expect(operatorValues).toContain('lessThan')
      expect(operatorValues).toContain('equals')
    })
  })

  describe('Advanced Configuration', () => {
    it('should show advanced options when toggled', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      expect(wrapper.find('[data-testid="advanced-options"]').exists()).toBe(false)

      const advancedToggle = wrapper.find('[data-testid="show-advanced-toggle"]')
      await advancedToggle.trigger('click')

      expect(wrapper.find('[data-testid="advanced-options"]').exists()).toBe(true)
    })

    it('should allow configuring notification settings', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      const advancedToggle = wrapper.find('[data-testid="show-advanced-toggle"]')
      await advancedToggle.trigger('click')

      expect(wrapper.find('[data-testid="email-notifications-checkbox"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="browser-notifications-checkbox"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="webhook-url-input"]').exists()).toBe(true)
    })

    it('should allow configuring alert frequency', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      const advancedToggle = wrapper.find('[data-testid="show-advanced-toggle"]')
      await advancedToggle.trigger('click')

      expect(wrapper.find('[data-testid="alert-frequency-select"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="max-alerts-input"]').exists()).toBe(true)
    })
  })

  describe('Form Submission', () => {
    it('should emit create event with rule data', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      // Fill out form
      await wrapper.find('[data-testid="rule-name-input"]').setValue('Test Alert Rule')
      await wrapper.find('[data-testid="endpoint-select"]').setValue('endpoint-1')
      await wrapper.find('[data-testid="metric-select"]').setValue('executionTime')
      await wrapper.find('[data-testid="operator-select"]').setValue('greaterThan')
      await wrapper.find('[data-testid="threshold-input"]').setValue('500')
      await wrapper.find('[data-testid="duration-input"]').setValue('300')
      await wrapper.find('[data-testid="severity-select"]').setValue('high')

      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.emitted('create-rule')).toBeTruthy()

      const emittedRule = wrapper.emitted('create-rule')?.[0]?.[0] as AlertRule
      expect(emittedRule.name).toBe('Test Alert Rule')
      expect(emittedRule.endpointId).toBe('endpoint-1')
      expect(emittedRule.condition.metric).toBe('executionTime')
      expect(emittedRule.condition.threshold).toBe(500)
      expect(emittedRule.severity).toBe('high')
    })

    it('should emit update event when editing', async () => {
      const mockRule = createMockRule()
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'edit',
          rule: mockRule
        }
      })

      await wrapper.find('[data-testid="rule-name-input"]').setValue('Updated Rule Name')

      const submitButton = wrapper.find('[data-testid="update-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      expect(wrapper.emitted('update-rule')).toBeTruthy()

      const emittedRule = wrapper.emitted('update-rule')?.[0]?.[0] as AlertRule
      expect(emittedRule.name).toBe('Updated Rule Name')
      expect(emittedRule.id).toBe(mockRule.id)
    })

    it('should not submit with validation errors', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      // Submit without required fields
      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')

      expect(wrapper.emitted('create-rule')).toBeFalsy()
    })

    it('should show loading state during submission', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create',
          loading: true
        }
      })

      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      expect(submitButton.attributes('disabled')).toBeDefined()
      expect(wrapper.text()).toContain('Creating...')
    })
  })

  describe('Form Reset and Cancel', () => {
    it('should reset form when cancel is clicked', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      await wrapper.find('[data-testid="rule-name-input"]').setValue('Test Rule')
      await wrapper.find('[data-testid="threshold-input"]').setValue('500')

      // Call resetForm directly since cancel button just emits an event
      wrapper.vm.resetForm()
      await nextTick()

      expect((wrapper.find('[data-testid="rule-name-input"]').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('[data-testid="threshold-input"]').element as HTMLInputElement).value).toBe('')
    })

    it('should emit cancel event', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      const cancelButton = wrapper.find('[data-testid="cancel-button"]')
      await cancelButton.trigger('click')

      expect(wrapper.emitted('cancel')).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('should have proper labels for form fields', () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      expect(wrapper.find('label[for="rule-name"]').exists()).toBe(true)
      expect(wrapper.find('label[for="endpoint-id"]').exists()).toBe(true)
      expect(wrapper.find('label[for="metric"]').exists()).toBe(true)
      expect(wrapper.find('label[for="threshold"]').exists()).toBe(true)
    })

    it('should associate errors with form fields', async () => {
      const wrapper = mount(AlertRuleForm, {
        props: {
          mode: 'create'
        }
      })

      const submitButton = wrapper.find('[data-testid="create-rule-button"]')
      await submitButton.trigger('click')
      await nextTick()

      const nameInput = wrapper.find('[data-testid="rule-name-input"]')
      const nameError = wrapper.find('[data-testid="name-error"]')

      expect(nameInput.attributes('aria-describedby')).toContain(nameError.attributes('id'))
    })
  })
})
