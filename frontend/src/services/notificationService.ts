import type { Alert, NotificationPreferences, NotificationHistory, AlertSeverity } from './alertingEngine'

export class NotificationService extends EventTarget {
  private preferences: NotificationPreferences = {
    browserNotifications: true,
    emailNotifications: false,
    severityFilter: ['medium', 'high', 'critical'],
    doNotDisturb: false,
    allowCriticalDuringDnD: true
  }

  private notificationHistory: NotificationHistory[] = []
  private readonly maxHistorySize = 100

  constructor() {
    super()
  }

  // Preference Management
  setPreferences(preferences: NotificationPreferences): void {
    // Validate webhook URL if provided
    if (preferences.webhookUrl && !this.isValidUrl(preferences.webhookUrl)) {
      throw new Error('Invalid webhook URL')
    }

    this.preferences = { ...this.preferences, ...preferences }
  }

  getPreferences(): NotificationPreferences {
    return { ...this.preferences }
  }

  private isValidUrl(url: string): boolean {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  // Permission Management
  async requestPermission(): Promise<NotificationPermission> {
    if ('Notification' in window) {
      return await Notification.requestPermission()
    }
    return 'denied'
  }

  // Notification Sending
  async sendNotification(alert: Alert): Promise<void> {
    if (!this.shouldSendNotification(alert)) {
      return
    }

    const tasks: Promise<boolean>[] = []

    if (this.preferences.browserNotifications) {
      tasks.push(this.sendBrowserNotification(alert))
    }

    if (this.preferences.emailNotifications && this.preferences.emailAddress) {
      tasks.push(this.sendEmailNotification(alert))
    }

    if (this.preferences.webhookUrl) {
      tasks.push(this.sendWebhookNotification(alert))
    }

    // Wait for all notifications to complete
    const results = await Promise.allSettled(tasks)

    // Track results
    results.forEach((result, index) => {
      const method = this.getMethodByIndex(index)
      const success = result.status === 'fulfilled' && result.value

      this.trackNotification(alert.id, method, success,
        result.status === 'rejected' ? result.reason : undefined)

      this.dispatchEvent(new CustomEvent(
        success ? 'notification-sent' : 'notification-failed',
        {
          detail: {
            alertId: alert.id,
            method,
            success,
            error: result.status === 'rejected' ? result.reason : undefined
          }
        }
      ))
    })
  }

  private shouldSendNotification(alert: Alert): boolean {
    // Check do not disturb mode
    if (this.preferences.doNotDisturb) {
      if (!this.preferences.allowCriticalDuringDnD || alert.severity !== 'critical') {
        // Check time window if specified
        if (this.preferences.dndTimeWindow) {
          const now = new Date()
          const currentTime = now.toTimeString().substring(0, 5)
          const { start, end } = this.preferences.dndTimeWindow

          if (this.isTimeInWindow(currentTime, start, end)) {
            return false
          }
        } else {
          return false
        }
      }
    }

    // Check severity filter
    if (this.preferences.severityFilter) {
      return this.preferences.severityFilter.includes(alert.severity)
    }

    return true
  }

  private isTimeInWindow(current: string, start: string, end: string): boolean {
    const currentMinutes = this.timeToMinutes(current)
    const startMinutes = this.timeToMinutes(start)
    const endMinutes = this.timeToMinutes(end)

    if (startMinutes <= endMinutes) {
      return currentMinutes >= startMinutes && currentMinutes <= endMinutes
    } else {
      // Overnight window
      return currentMinutes >= startMinutes || currentMinutes <= endMinutes
    }
  }

  private timeToMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number)
    return hours * 60 + minutes
  }

  async sendBrowserNotification(alert: Alert): Promise<boolean> {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
      return false
    }

    try {
      new Notification('FraiseQL Doctor Alert', {
        body: alert.message,
        icon: '/favicon.ico',
        tag: alert.id,
        badge: this.getSeverityIcon(alert.severity)
      })
      return true
    } catch (error) {
      console.error('Failed to send browser notification:', error)
      return false
    }
  }

  async sendEmailNotification(alert: Alert): Promise<boolean> {
    if (!this.preferences.emailAddress) {
      return false
    }

    try {
      const response = await fetch('/api/notifications/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          to: this.preferences.emailAddress,
          subject: `FraiseQL Doctor Alert: ${alert.severity.toUpperCase()}`,
          body: this.formatEmailBody(alert)
        })
      })

      return response.ok
    } catch (error) {
      console.error('Failed to send email notification:', error)
      return false
    }
  }

  async sendWebhookNotification(alert: Alert, retries = 2): Promise<boolean> {
    if (!this.preferences.webhookUrl) {
      return false
    }

    const payload = {
      alertId: alert.id,
      severity: alert.severity,
      endpointId: alert.endpointId,
      message: alert.message,
      triggeredAt: alert.triggeredAt.toISOString(),
      metricValues: alert.metricValues,
      source: 'fraiseql-doctor'
    }

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(this.preferences.webhookUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })

        if (response.ok) {
          return true
        }
      } catch (error) {
        console.error(`Webhook attempt ${attempt + 1} failed:`, error)

        if (attempt < retries) {
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
        }
      }
    }

    return false
  }

  private getMethodByIndex(index: number): string {
    const methods = []
    if (this.preferences.browserNotifications) methods.push('browser')
    if (this.preferences.emailNotifications) methods.push('email')
    if (this.preferences.webhookUrl) methods.push('webhook')
    return methods[index] || 'unknown'
  }

  private getSeverityIcon(severity: AlertSeverity): string {
    switch (severity) {
      case 'critical': return '🚨'
      case 'high': return '⚠️'
      case 'medium': return '📊'
      case 'low': return 'ℹ️'
      default: return '📊'
    }
  }

  private formatEmailBody(alert: Alert): string {
    return `
Alert Details:
- Severity: ${alert.severity.toUpperCase()}
- Endpoint: ${alert.endpointId}
- Message: ${alert.message}
- Triggered: ${alert.triggeredAt.toISOString()}
- Metric Values: ${JSON.stringify(alert.metricValues, null, 2)}

View in FraiseQL Doctor Dashboard for more details.
    `.trim()
  }

  // Notification History
  private trackNotification(
    alertId: string,
    method: string,
    success: boolean,
    error?: string
  ): void {
    this.notificationHistory.push({
      alertId,
      method,
      success,
      sentAt: new Date(),
      error: error?.message || error
    })

    // Maintain history size limit
    if (this.notificationHistory.length > this.maxHistorySize) {
      this.notificationHistory.shift()
    }
  }

  getNotificationHistory(): NotificationHistory[] {
    return [...this.notificationHistory]
  }

  clearNotificationHistory(): void {
    this.notificationHistory = []
  }
}
