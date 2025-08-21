export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved'
export type MetricOperator = 'greaterThan' | 'lessThan' | 'equals' | 'notEquals'
export type MetricField = 'executionTime' | 'responseSize' | 'errorRate'

export interface AlertCondition {
  metric: MetricField
  operator: MetricOperator
  threshold: number
  duration: number // milliseconds
}

export interface AlertRule {
  id: string
  name: string
  endpointId: string
  condition: AlertCondition
  severity: AlertSeverity
  enabled: boolean
  createdAt: Date
  updatedAt?: Date
  notifications?: {
    email?: boolean
    browser?: boolean
    webhook?: string
  }
}

export interface Alert {
  id: string
  ruleId: string
  endpointId: string
  severity: AlertSeverity
  message: string
  status: AlertStatus
  triggeredAt: Date
  acknowledgedAt?: Date
  acknowledgedBy?: string
  resolvedAt?: Date
  metricValues: Record<string, number>
}

export interface AlertStatistics {
  totalAlerts: number
  activeAlerts: number
  alertsByEndpoint: Record<string, number>
  alertsBySeverity: Record<AlertSeverity, number>
}

export interface NotificationMethod {
  type: 'browser' | 'email' | 'webhook'
  enabled: boolean
  config?: Record<string, any>
}

export interface NotificationPreferences {
  browserNotifications?: boolean
  emailNotifications?: boolean
  emailAddress?: string
  webhookUrl?: string
  severityFilter?: AlertSeverity[]
  doNotDisturb?: boolean
  allowCriticalDuringDnD?: boolean
  dndTimeWindow?: {
    start: string // HH:MM format
    end: string   // HH:MM format
  }
}

export interface NotificationHistory {
  alertId: string
  method: string
  success: boolean
  sentAt: Date
  error?: string
}

export class AlertingEngine extends EventTarget {
  private rules: Map<string, AlertRule> = new Map()
  private alerts: Map<string, Alert> = new Map()
  private alertHistory: Alert[] = []

  constructor() {
    super()
  }

  // Alert Rule Management
  addRule(rule: AlertRule): void {
    this.rules.set(rule.id, rule)
  }

  updateRule(ruleId: string, updates: Partial<AlertRule>): void {
    const existingRule = this.rules.get(ruleId)
    if (existingRule) {
      const updatedRule = { ...existingRule, ...updates, updatedAt: new Date() }
      this.rules.set(ruleId, updatedRule)
    }
  }

  deleteRule(ruleId: string): void {
    this.rules.delete(ruleId)
  }

  getRule(ruleId: string): AlertRule | undefined {
    return this.rules.get(ruleId)
  }

  getRules(): AlertRule[] {
    return Array.from(this.rules.values())
  }

  // Alert Evaluation
  async evaluateMetrics(metrics: any[]): Promise<Alert[]> {
    const newAlerts: Alert[] = []

    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue

      const endpointMetrics = metrics.filter(m => m.endpointId === rule.endpointId)
      if (endpointMetrics.length === 0) continue

      const shouldTrigger = this.evaluateRule(rule, endpointMetrics)
      
      if (shouldTrigger) {
        const existingAlert = this.findActiveAlertForRule(rule.id)
        
        if (!existingAlert) {
          const alert = this.createAlert(rule, endpointMetrics)
          newAlerts.push(alert)
          this.alerts.set(alert.id, alert)
          
          this.dispatchEvent(new CustomEvent('alert-triggered', {
            detail: alert
          }))
        }
      } else {
        // Check if we should resolve existing alerts
        const existingAlert = this.findActiveAlertForRule(rule.id)
        if (existingAlert && existingAlert.status === 'active') {
          existingAlert.status = 'resolved'
          existingAlert.resolvedAt = new Date()
          
          // Add to history when resolved
          this.alertHistory.push({...existingAlert})
          
          this.dispatchEvent(new CustomEvent('alert-resolved', {
            detail: existingAlert
          }))
        }
      }
    }

    return newAlerts
  }

  private evaluateRule(rule: AlertRule, metrics: any[]): boolean {
    if (metrics.length === 0) return false

    // Check if threshold is sustained over duration
    const now = Date.now()
    const durationStart = now - rule.condition.duration

    const recentMetrics = metrics.filter(m => 
      m.timestamp.getTime() >= durationStart
    )

    if (recentMetrics.length === 0) return false

    // For duration-based alerts, check if we have enough sustained data
    if (rule.condition.duration > 0) {
      const oldestMetric = Math.min(...recentMetrics.map(m => m.timestamp.getTime()))
      const metricSpan = now - oldestMetric
      
      // For short durations (< 5 min), just need 3+ metrics
      // For longer durations, need at least 10% coverage
      const isShortDuration = rule.condition.duration < 300000 // 5 minutes
      const hasAdequateCoverage = isShortDuration 
        ? recentMetrics.length >= 3
        : metricSpan >= (rule.condition.duration * 0.1) && recentMetrics.length >= 3
      
      if (!hasAdequateCoverage) return false
    }

    // Check if all recent metrics exceed threshold
    return recentMetrics.every(metric => {
      const value = metric[rule.condition.metric]
      if (value === undefined) return false

      switch (rule.condition.operator) {
        case 'greaterThan':
          return value > rule.condition.threshold
        case 'lessThan':
          return value < rule.condition.threshold
        case 'equals':
          return value === rule.condition.threshold
        case 'notEquals':
          return value !== rule.condition.threshold
        default:
          return false
      }
    })
  }

  private findActiveAlertForRule(ruleId: string): Alert | undefined {
    return Array.from(this.alerts.values()).find(
      alert => alert.ruleId === ruleId && alert.status === 'active'
    )
  }

  private createAlert(rule: AlertRule, metrics: any[]): Alert {
    const latestMetric = metrics[metrics.length - 1]
    
    return {
      id: this.generateAlertId(),
      ruleId: rule.id,
      endpointId: rule.endpointId,
      severity: rule.severity,
      message: `${rule.name} - Threshold exceeded`,
      status: 'active',
      triggeredAt: new Date(),
      metricValues: {
        [rule.condition.metric]: latestMetric[rule.condition.metric]
      }
    }
  }

  private generateAlertId(): string {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Alert Management
  getActiveAlerts(): Alert[] {
    return Array.from(this.alerts.values()).filter(
      alert => alert.status === 'active'
    )
  }

  getAlert(alertId: string): Alert | undefined {
    return this.alerts.get(alertId)
  }

  acknowledgeAlert(alertId: string, userId: string): void {
    const alert = this.alerts.get(alertId)
    if (alert && alert.status === 'active') {
      alert.status = 'acknowledged'
      alert.acknowledgedAt = new Date()
      alert.acknowledgedBy = userId
    }
  }

  getAlertHistory(): Alert[] {
    return this.alertHistory
  }

  getAlertStatistics(): AlertStatistics {
    const allAlerts = Array.from(this.alerts.values())
    
    const stats: AlertStatistics = {
      totalAlerts: allAlerts.length,
      activeAlerts: allAlerts.filter(a => a.status === 'active').length,
      alertsByEndpoint: {},
      alertsBySeverity: {
        low: 0,
        medium: 0,
        high: 0,
        critical: 0
      }
    }

    for (const alert of allAlerts) {
      // Count by endpoint
      stats.alertsByEndpoint[alert.endpointId] = 
        (stats.alertsByEndpoint[alert.endpointId] || 0) + 1
      
      // Count by severity
      stats.alertsBySeverity[alert.severity]++
    }

    return stats
  }
}