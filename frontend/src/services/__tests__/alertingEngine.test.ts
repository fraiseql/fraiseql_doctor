import { describe, it, expect, beforeEach, vi } from 'vitest'
import { AlertingEngine } from '../alertingEngine'
import type { QueryMetric } from '../performanceMonitor'
import type { AlertRule, Alert, AlertSeverity } from '../alertingEngine'

describe('AlertingEngine', () => {
  let alertingEngine: AlertingEngine

  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}_${Math.random()}`,
    endpointId: 'endpoint-1',
    query: 'test_query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    ...overrides
  })

  beforeEach(() => {
    alertingEngine = new AlertingEngine()
  })

  describe('Alert Rule Management', () => {
    it('should create and store alert rules', () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 500,
          duration: 300000 // 5 minutes
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)
      
      expect(alertingEngine.getRules()).toHaveLength(1)
      expect(alertingEngine.getRule('rule-1')).toEqual(rule)
    })

    it('should update existing alert rules', () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 500,
          duration: 300000
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)
      
      const updatedRule = { ...rule, threshold: 800 }
      alertingEngine.updateRule('rule-1', { condition: { ...rule.condition, threshold: 800 } })

      expect(alertingEngine.getRule('rule-1')?.condition.threshold).toBe(800)
    })

    it('should delete alert rules', () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Rule',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 500,
          duration: 300000
        },
        severity: 'medium',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)
      expect(alertingEngine.getRules()).toHaveLength(1)

      alertingEngine.deleteRule('rule-1')
      expect(alertingEngine.getRules()).toHaveLength(0)
      expect(alertingEngine.getRule('rule-1')).toBeUndefined()
    })
  })

  describe('Alert Generation', () => {
    it('should trigger alerts when thresholds are exceeded', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 200,
          duration: 60000 // 1 minute
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Create metrics that exceed threshold
      const slowMetrics = Array.from({ length: 5 }, () =>
        createMockMetric({ 
          executionTime: 300, // Above threshold
          timestamp: new Date()
        })
      )

      const alerts = await alertingEngine.evaluateMetrics(slowMetrics)

      expect(alerts).toHaveLength(1)
      expect(alerts[0].severity).toBe('high')
      expect(alerts[0].ruleId).toBe('rule-1')
      expect(alerts[0].message).toContain('High Response Time')
    })

    it('should not trigger alerts when thresholds are not exceeded', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 500,
          duration: 60000
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Create metrics that don't exceed threshold
      const normalMetrics = Array.from({ length: 5 }, () =>
        createMockMetric({ 
          executionTime: 100, // Below threshold
          timestamp: new Date()
        })
      )

      const alerts = await alertingEngine.evaluateMetrics(normalMetrics)

      expect(alerts).toHaveLength(0)
    })

    it('should respect alert rule duration requirements', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Sustained High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 200,
          duration: 300000 // 5 minutes - must be sustained
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Create metrics that exceed threshold but not for duration
      const now = Date.now()
      const recentMetrics = Array.from({ length: 3 }, (_, i) =>
        createMockMetric({ 
          executionTime: 300,
          timestamp: new Date(now - i * 1000) // Only spans 3 seconds, not 5 minutes
        })
      )

      const alerts = await alertingEngine.evaluateMetrics(recentMetrics)

      expect(alerts).toHaveLength(0) // Should not trigger due to duration requirement
    })

    it('should trigger alerts for sustained threshold violations', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Sustained High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 200,
          duration: 300000 // 5 minutes
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Create metrics spread over 6 minutes, all exceeding threshold
      const sustainedMetrics = Array.from({ length: 10 }, (_, i) =>
        createMockMetric({ 
          executionTime: 300,
          timestamp: new Date(Date.now() - (i * 60000)) // 1 minute intervals, going back 10 minutes
        })
      )

      const alerts = await alertingEngine.evaluateMetrics(sustainedMetrics)

      expect(alerts).toHaveLength(1)
      expect(alerts[0].severity).toBe('high')
      expect(alerts[0].message).toContain('Sustained High Response Time')
    })
  })

  describe('Alert Management', () => {
    it('should store and retrieve active alerts', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Alert',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 100,
          duration: 60000
        },
        severity: 'medium',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      const badMetrics = Array.from({ length: 3 }, () => createMockMetric({ executionTime: 200 }))
      const alerts = await alertingEngine.evaluateMetrics(badMetrics)

      expect(alertingEngine.getActiveAlerts()).toHaveLength(1)
      expect(alertingEngine.getActiveAlerts()[0].status).toBe('active')
    })

    it('should acknowledge alerts', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Alert',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 100,
          duration: 60000
        },
        severity: 'medium',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      const badMetrics = Array.from({ length: 3 }, () => createMockMetric({ executionTime: 200 }))
      const alerts = await alertingEngine.evaluateMetrics(badMetrics)
      const alertId = alerts[0].id

      alertingEngine.acknowledgeAlert(alertId, 'user-1')

      const acknowledgedAlert = alertingEngine.getAlert(alertId)
      expect(acknowledgedAlert?.status).toBe('acknowledged')
      expect(acknowledgedAlert?.acknowledgedBy).toBe('user-1')
      expect(acknowledgedAlert?.acknowledgedAt).toBeInstanceOf(Date)
    })

    it('should resolve alerts when conditions improve', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'High Response Time',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 200,
          duration: 60000
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // First trigger an alert with duration coverage
      const now = Date.now()
      const badMetrics = Array.from({ length: 3 }, (_, i) => 
        createMockMetric({ 
          executionTime: 300, 
          timestamp: new Date(now - (60000 - i * 1000)) // Cover the duration window
        })
      )
      await alertingEngine.evaluateMetrics(badMetrics)

      expect(alertingEngine.getActiveAlerts()).toHaveLength(1)
      const alertId = alertingEngine.getActiveAlerts()[0].id

      // Then resolve with good metrics
      const goodMetrics = Array.from({ length: 5 }, () =>
        createMockMetric({ executionTime: 100 })
      )
      await alertingEngine.evaluateMetrics(goodMetrics)

      const resolvedAlert = alertingEngine.getAlert(alertId)
      expect(resolvedAlert?.status).toBe('resolved')
      expect(resolvedAlert?.resolvedAt).toBeInstanceOf(Date)
    })
  })

  describe('Alert History and Analytics', () => {
    it('should maintain alert history', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Alert',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 100,
          duration: 60000
        },
        severity: 'medium',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Generate multiple alerts over time
      for (let i = 0; i < 3; i++) {
        // Create metrics with proper duration coverage
        const now = Date.now()
        const badMetrics = Array.from({ length: 3 }, (_, j) =>
          createMockMetric({ 
            executionTime: 200,
            timestamp: new Date(now - (60000 - j * 1000)) // Cover duration window
          })
        )
        await alertingEngine.evaluateMetrics(badMetrics)
        
        // Resolve each alert
        const goodMetrics = [createMockMetric({ executionTime: 50 })]
        await alertingEngine.evaluateMetrics(goodMetrics)
        
        // Small delay to ensure different timestamps
        await new Promise(resolve => setTimeout(resolve, 10))
      }

      const history = alertingEngine.getAlertHistory()
      expect(history).toHaveLength(3)
      expect(history.every(alert => alert.status === 'resolved')).toBe(true)
    })

    it('should provide alert statistics', async () => {
      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Alert',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 100,
          duration: 60000
        },
        severity: 'high',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Generate some alerts
      const badMetrics = Array.from({ length: 3 }, () => createMockMetric({ executionTime: 200 }))
      await alertingEngine.evaluateMetrics(badMetrics)

      const stats = alertingEngine.getAlertStatistics()
      
      expect(stats.totalAlerts).toBe(1)
      expect(stats.activeAlerts).toBe(1)
      expect(stats.alertsByEndpoint['endpoint-1']).toBe(1)
      expect(stats.alertsBySeverity.high).toBe(1)
    })
  })

  describe('Event Emission', () => {
    it('should emit events when alerts are triggered', async () => {
      const alertTriggeredSpy = vi.fn()
      alertingEngine.addEventListener('alert-triggered', alertTriggeredSpy)

      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Alert',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 100,
          duration: 60000
        },
        severity: 'medium',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      const badMetrics = Array.from({ length: 3 }, () => createMockMetric({ executionTime: 200 }))
      await alertingEngine.evaluateMetrics(badMetrics)

      expect(alertTriggeredSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            id: expect.any(String),
            severity: 'medium',
            ruleId: 'rule-1'
          })
        })
      )
    })

    it('should emit events when alerts are resolved', async () => {
      const alertResolvedSpy = vi.fn()
      alertingEngine.addEventListener('alert-resolved', alertResolvedSpy)

      const rule: AlertRule = {
        id: 'rule-1',
        name: 'Test Alert',
        endpointId: 'endpoint-1',
        condition: {
          metric: 'executionTime',
          operator: 'greaterThan',
          threshold: 100,
          duration: 60000
        },
        severity: 'medium',
        enabled: true,
        createdAt: new Date()
      }

      alertingEngine.addRule(rule)

      // Trigger alert
      const badMetrics = Array.from({ length: 3 }, () => createMockMetric({ executionTime: 200 }))
      await alertingEngine.evaluateMetrics(badMetrics)

      // Resolve alert
      const goodMetrics = Array.from({ length: 3 }, () => createMockMetric({ executionTime: 50 }))
      await alertingEngine.evaluateMetrics(goodMetrics)

      expect(alertResolvedSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            status: 'resolved',
            resolvedAt: expect.any(Date)
          })
        })
      )
    })
  })
})