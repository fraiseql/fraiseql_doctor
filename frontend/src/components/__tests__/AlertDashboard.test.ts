import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AlertDashboard from '../AlertDashboard.vue'
import type { Alert, AlertRule, AlertSeverity } from '../../services/alertingEngine'

// Mock the AlertingEngine
vi.mock('../../services/alertingEngine', () => ({
  AlertingEngine: vi.fn().mockImplementation(() => ({
    getActiveAlerts: vi.fn(() => []),
    getAlertHistory: vi.fn(() => []),
    getRules: vi.fn(() => []),
    getAlertStatistics: vi.fn(() => ({
      totalAlerts: 0,
      activeAlerts: 0,
      alertsByEndpoint: {},
      alertsBySeverity: { low: 0, medium: 0, high: 0, critical: 0 }
    })),
    acknowledgeAlert: vi.fn(),
    deleteRule: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
  }))
}))

describe('AlertDashboard', () => {
  const createMockAlert = (overrides: Partial<Alert> = {}): Alert => ({
    id: `alert_${Date.now()}_${Math.random()}`,
    ruleId: 'rule-1',
    endpointId: 'endpoint-1',
    severity: 'medium',
    message: 'Test alert message',
    status: 'active',
    triggeredAt: new Date(),
    metricValues: { executionTime: 300 },
    ...overrides
  })

  const createMockRule = (overrides: Partial<AlertRule> = {}): AlertRule => ({
    id: `rule_${Date.now()}_${Math.random()}`,
    name: 'Test Alert Rule',
    endpointId: 'endpoint-1',
    condition: {
      metric: 'executionTime',
      operator: 'greaterThan',
      threshold: 200,
      duration: 300000
    },
    severity: 'medium',
    enabled: true,
    createdAt: new Date(),
    ...overrides
  })

  describe('Component Rendering', () => {
    it('should render alert dashboard', () => {
      const wrapper = mount(AlertDashboard)

      expect(wrapper.find('[data-testid="alert-dashboard"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="alert-overview"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="active-alerts-section"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="alert-rules-section"]').exists()).toBe(true)
    })

    it('should display alert statistics', async () => {
      const mockStats = {
        totalAlerts: 15,
        activeAlerts: 3,
        alertsByEndpoint: { 'endpoint-1': 10, 'endpoint-2': 5 },
        alertsBySeverity: { low: 2, medium: 8, high: 4, critical: 1 }
      }

      const wrapper = mount(AlertDashboard)
      wrapper.vm.alertStats = mockStats
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('15') // Total alerts
      expect(wrapper.text()).toContain('3') // Active alerts
      expect(wrapper.find('[data-testid="total-alerts"]').text()).toContain('15')
      expect(wrapper.find('[data-testid="active-alerts"]').text()).toContain('3')
    })
  })

  describe('Active Alerts Display', () => {
    it('should display list of active alerts', async () => {
      const mockAlerts = [
        createMockAlert({
          id: 'alert-1',
          severity: 'high',
          message: 'High response time detected',
          triggeredAt: new Date('2024-01-01T10:00:00Z')
        }),
        createMockAlert({
          id: 'alert-2',
          severity: 'medium',
          message: 'Moderate performance degradation',
          triggeredAt: new Date('2024-01-01T11:00:00Z')
        })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.activeAlerts = mockAlerts
      await wrapper.vm.$nextTick()

      const alertItems = wrapper.findAll('[data-testid="alert-item"]')
      expect(alertItems).toHaveLength(2)

      expect(wrapper.text()).toContain('High response time detected')
      expect(wrapper.text()).toContain('Moderate performance degradation')
    })

    it('should show empty state when no active alerts', () => {
      const wrapper = mount(AlertDashboard)

      expect(wrapper.find('[data-testid="no-active-alerts"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('No active alerts')
    })

    it('should display alert severity with appropriate styling', async () => {
      const mockAlerts = [
        createMockAlert({ id: 'alert-1', severity: 'high' }),
        createMockAlert({ id: 'alert-2', severity: 'medium' }),
        createMockAlert({ id: 'alert-3', severity: 'low' })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.activeAlerts = mockAlerts
      await wrapper.vm.$nextTick()

      const highSeverityAlert = wrapper.find('[data-testid="alert-severity-high"]')
      const mediumSeverityAlert = wrapper.find('[data-testid="alert-severity-medium"]')
      const lowSeverityAlert = wrapper.find('[data-testid="alert-severity-low"]')

      expect(highSeverityAlert.exists()).toBe(true)
      expect(mediumSeverityAlert.exists()).toBe(true)
      expect(lowSeverityAlert.exists()).toBe(true)

      expect(highSeverityAlert.classes()).toContain('severity-high')
      expect(mediumSeverityAlert.classes()).toContain('severity-medium')
      expect(lowSeverityAlert.classes()).toContain('severity-low')
    })
  })

  describe('Alert Actions', () => {
    it('should acknowledge alerts', async () => {
      const mockAlert = createMockAlert({ id: 'alert-1', status: 'active' })
      const wrapper = mount(AlertDashboard)

      wrapper.vm.activeAlerts = [mockAlert]
      await wrapper.vm.$nextTick()

      const acknowledgeButton = wrapper.find('[data-testid="acknowledge-button"]')
      await acknowledgeButton.trigger('click')

      expect(wrapper.emitted('alert-acknowledged')).toBeTruthy()
      expect(wrapper.emitted('alert-acknowledged')[0]).toEqual(['alert-1'])
    })

    it('should show acknowledge confirmation dialog', async () => {
      const mockAlert = createMockAlert({ id: 'alert-1' })
      const wrapper = mount(AlertDashboard)

      wrapper.vm.activeAlerts = [mockAlert]
      await wrapper.vm.$nextTick()

      const acknowledgeButton = wrapper.find('[data-testid="acknowledge-button"]')
      await acknowledgeButton.trigger('click')

      expect(wrapper.find('[data-testid="acknowledge-dialog"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Acknowledge Alert')
    })

    it('should filter alerts by severity', async () => {
      const mockAlerts = [
        createMockAlert({ id: 'alert-1', severity: 'high' }),
        createMockAlert({ id: 'alert-2', severity: 'medium' }),
        createMockAlert({ id: 'alert-3', severity: 'high' })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.activeAlerts = mockAlerts
      await wrapper.vm.$nextTick()

      const severityFilter = wrapper.find('[data-testid="severity-filter"]')
      await severityFilter.setValue('high')

      const visibleAlerts = wrapper.findAll('[data-testid="alert-item"]:not(.hidden)')
      expect(visibleAlerts).toHaveLength(2) // Only high severity alerts
    })

    it('should filter alerts by endpoint', async () => {
      const mockAlerts = [
        createMockAlert({ id: 'alert-1', endpointId: 'endpoint-1' }),
        createMockAlert({ id: 'alert-2', endpointId: 'endpoint-2' }),
        createMockAlert({ id: 'alert-3', endpointId: 'endpoint-1' })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.activeAlerts = mockAlerts
      await wrapper.vm.$nextTick()

      const endpointFilter = wrapper.find('[data-testid="endpoint-filter"]')
      await endpointFilter.setValue('endpoint-1')

      const visibleAlerts = wrapper.findAll('[data-testid="alert-item"]:not(.hidden)')
      expect(visibleAlerts).toHaveLength(2) // Only endpoint-1 alerts
    })
  })

  describe('Alert Rules Management', () => {
    it('should display list of alert rules', async () => {
      const mockRules = [
        createMockRule({
          id: 'rule-1',
          name: 'High Response Time',
          enabled: true
        }),
        createMockRule({
          id: 'rule-2',
          name: 'Error Rate Threshold',
          enabled: false
        })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.alertRules = mockRules
      await wrapper.vm.$nextTick()

      const ruleItems = wrapper.findAll('[data-testid="alert-rule-item"]')
      expect(ruleItems).toHaveLength(2)

      expect(wrapper.text()).toContain('High Response Time')
      expect(wrapper.text()).toContain('Error Rate Threshold')
    })

    it('should show rule enabled/disabled status', async () => {
      const mockRules = [
        createMockRule({ id: 'rule-1', enabled: true }),
        createMockRule({ id: 'rule-2', enabled: false })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.alertRules = mockRules
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="rule-status-enabled"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="rule-status-disabled"]').exists()).toBe(true)
    })

    it('should allow editing alert rules', async () => {
      const mockRule = createMockRule({ id: 'rule-1', name: 'Test Rule' })
      const wrapper = mount(AlertDashboard)

      wrapper.vm.alertRules = [mockRule]
      await wrapper.vm.$nextTick()

      const editButton = wrapper.find('[data-testid="edit-rule-button"]')
      await editButton.trigger('click')

      expect(wrapper.emitted('edit-rule')).toBeTruthy()
      expect(wrapper.emitted('edit-rule')[0]).toEqual(['rule-1'])
    })

    it('should allow deleting alert rules', async () => {
      const mockRule = createMockRule({ id: 'rule-1', name: 'Test Rule' })
      const wrapper = mount(AlertDashboard)

      wrapper.vm.alertRules = [mockRule]
      await wrapper.vm.$nextTick()

      const deleteButton = wrapper.find('[data-testid="delete-rule-button"]')
      await deleteButton.trigger('click')

      expect(wrapper.find('[data-testid="delete-confirmation"]').exists()).toBe(true)
    })

    it('should confirm rule deletion', async () => {
      const mockRule = createMockRule({ id: 'rule-1', name: 'Test Rule' })
      const wrapper = mount(AlertDashboard)

      wrapper.vm.alertRules = [mockRule]
      await wrapper.vm.$nextTick()

      // Open delete confirmation
      const deleteButton = wrapper.find('[data-testid="delete-rule-button"]')
      await deleteButton.trigger('click')

      // Confirm deletion
      const confirmButton = wrapper.find('[data-testid="confirm-delete-button"]')
      await confirmButton.trigger('click')

      expect(wrapper.emitted('delete-rule')).toBeTruthy()
      expect(wrapper.emitted('delete-rule')[0]).toEqual(['rule-1'])
    })
  })

  describe('Real-time Updates', () => {
    it('should update when new alerts are triggered', async () => {
      const wrapper = mount(AlertDashboard)
      const initialAlertCount = wrapper.vm.activeAlerts.length

      // Simulate new alert
      const newAlert = createMockAlert({ id: 'new-alert-1' })
      wrapper.vm.handleNewAlert(newAlert)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.activeAlerts.length).toBe(initialAlertCount + 1)
      expect(wrapper.text()).toContain('Test alert message')
    })

    it('should update statistics when alerts change', async () => {
      const wrapper = mount(AlertDashboard)

      // Initial state
      expect(wrapper.vm.alertStats.activeAlerts).toBe(0)

      // Add alert
      const newAlert = createMockAlert({ severity: 'high' })
      wrapper.vm.handleNewAlert(newAlert)
      await wrapper.vm.$nextTick()

      wrapper.vm.updateStatistics()

      expect(wrapper.vm.alertStats.activeAlerts).toBe(1)
      expect(wrapper.vm.alertStats.alertsBySeverity.high).toBe(1)
    })

    it('should handle alert resolution updates', async () => {
      const activeAlert = createMockAlert({ id: 'alert-1', status: 'active' })
      const wrapper = mount(AlertDashboard)

      wrapper.vm.activeAlerts = [activeAlert]
      await wrapper.vm.$nextTick()

      // Simulate alert resolution
      const resolvedAlert = { ...activeAlert, status: 'resolved', resolvedAt: new Date() }
      wrapper.vm.handleAlertResolved(resolvedAlert)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.activeAlerts.find(a => a.id === 'alert-1')).toBeUndefined()
    })
  })

  describe('Alert History', () => {
    it('should display alert history section', () => {
      const wrapper = mount(AlertDashboard)

      expect(wrapper.find('[data-testid="alert-history-section"]').exists()).toBe(true)
    })

    it('should show resolved alerts in history', async () => {
      const mockHistory = [
        createMockAlert({
          id: 'alert-1',
          status: 'resolved',
          resolvedAt: new Date('2024-01-01T12:00:00Z')
        }),
        createMockAlert({
          id: 'alert-2',
          status: 'acknowledged',
          acknowledgedAt: new Date('2024-01-01T11:30:00Z')
        })
      ]

      const wrapper = mount(AlertDashboard)
      wrapper.vm.alertHistory = mockHistory
      await wrapper.vm.$nextTick()

      const historyItems = wrapper.findAll('[data-testid="history-item"]')
      expect(historyItems).toHaveLength(2)
    })

    it('should paginate alert history', async () => {
      const mockHistory = Array.from({ length: 25 }, (_, i) =>
        createMockAlert({
          id: `alert-${i}`,
          status: 'resolved'
        })
      )

      const wrapper = mount(AlertDashboard)
      wrapper.vm.alertHistory = mockHistory
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="pagination"]').exists()).toBe(true)

      const historyItems = wrapper.findAll('[data-testid="history-item"]')
      expect(historyItems.length).toBeLessThanOrEqual(10) // Page size
    })
  })

  describe('Export Functionality', () => {
    it('should export alert data', async () => {
      const wrapper = mount(AlertDashboard)

      const exportButton = wrapper.find('[data-testid="export-alerts-button"]')
      await exportButton.trigger('click')

      expect(wrapper.emitted('export-alerts')).toBeTruthy()
    })

    it('should export alert rules configuration', async () => {
      const wrapper = mount(AlertDashboard)

      const exportButton = wrapper.find('[data-testid="export-rules-button"]')
      await exportButton.trigger('click')

      expect(wrapper.emitted('export-rules')).toBeTruthy()
    })
  })
})
