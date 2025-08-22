import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { NotificationService } from '../notificationService'
import type { Alert, NotificationPreferences } from '../alertingEngine'

// Mock browser APIs
const mockNotification = vi.fn()
const mockFetch = vi.fn()

// Mock global fetch
Object.defineProperty(global, 'fetch', {
  value: mockFetch,
  configurable: true
})

// Mock Notification API
Object.defineProperty(global, 'Notification', {
  value: mockNotification,
  configurable: true
})

Object.defineProperty(global.Notification, 'permission', {
  value: 'granted',
  configurable: true
})

Object.defineProperty(global.Notification, 'requestPermission', {
  value: vi.fn(() => Promise.resolve('granted')),
  configurable: true
})

// Mock window object for Notification check
Object.defineProperty(global, 'window', {
  value: global,
  configurable: true
})

describe('NotificationService', () => {
  let notificationService: NotificationService

  const createMockAlert = (overrides: Partial<Alert> = {}): Alert => ({
    id: 'alert-1',
    ruleId: 'rule-1',
    endpointId: 'endpoint-1',
    severity: 'medium',
    message: 'Test alert message',
    status: 'active',
    triggeredAt: new Date(),
    metricValues: { executionTime: 300 },
    ...overrides
  })

  beforeEach(() => {
    notificationService = new NotificationService()
    vi.clearAllMocks()
    
    // Reset Notification.permission to 'granted' for each test
    Object.defineProperty(Notification, 'permission', {
      value: 'granted',
      configurable: true
    })
    
    // Reset fetch mock with clone() method for retry logic support
    mockFetch.mockImplementation((url, options) => {
      // Check if the request was aborted
      if (options?.signal?.aborted) {
        return Promise.reject(new DOMException('Request aborted', 'AbortError'))
      }
      
      return Promise.resolve({
        ok: true,
        status: 200,
        clone: () => ({
          json: () => Promise.resolve({ success: true })
        }),
        json: () => Promise.resolve({ success: true })
      })
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Notification Preferences', () => {
    it('should set and get notification preferences', () => {
      const preferences: NotificationPreferences = {
        browserNotifications: true,
        emailNotifications: false,
        webhookUrl: 'https://api.example.com/webhook',
        severityFilter: ['high', 'critical']
      }

      notificationService.setPreferences(preferences)

      // Service merges with defaults, so expect all default properties to be included
      const expectedPreferences = {
        browserNotifications: true,
        emailNotifications: false,
        webhookUrl: 'https://api.example.com/webhook',
        severityFilter: ['high', 'critical'],
        doNotDisturb: false, // Default
        allowCriticalDuringDnD: true // Default
      }

      expect(notificationService.getPreferences()).toEqual(expectedPreferences)
    })

    it('should use default preferences when none set', () => {
      const defaultPreferences = notificationService.getPreferences()

      expect(defaultPreferences.browserNotifications).toBe(true)
      expect(defaultPreferences.emailNotifications).toBe(false)
      expect(defaultPreferences.severityFilter).toEqual(['medium', 'high', 'critical'])
    })

    it('should validate notification preferences', () => {
      const invalidPreferences = {
        browserNotifications: true,
        emailNotifications: true,
        webhookUrl: 'invalid-url',
        severityFilter: ['invalid-severity']
      } as any

      expect(() => {
        notificationService.setPreferences(invalidPreferences)
      }).toThrow('Invalid webhook URL')
    })
  })

  describe('Browser Notifications', () => {
    it('should request notification permission', async () => {
      const permission = await notificationService.requestPermission()

      expect(Notification.requestPermission).toHaveBeenCalled()
      expect(permission).toBe('granted')
    })

    it('should send browser notification for alerts', async () => {
      const alert = createMockAlert({
        severity: 'high',
        message: 'High response time detected on endpoint-1'
      })

      await notificationService.sendBrowserNotification(alert)

      expect(mockNotification).toHaveBeenCalledWith(
        'FraiseQL Doctor Alert',
        expect.objectContaining({
          body: 'High response time detected on endpoint-1',
          icon: expect.any(String),
          tag: 'alert-1'
        })
      )
    })

    it('should not send browser notification if permission denied', async () => {
      Object.defineProperty(Notification, 'permission', {
        value: 'denied',
        configurable: true
      })

      const alert = createMockAlert()
      const result = await notificationService.sendBrowserNotification(alert)

      expect(result).toBe(false)
      expect(mockNotification).not.toHaveBeenCalled()
    })

    it('should filter notifications by severity', async () => {
      notificationService.setPreferences({
        browserNotifications: true,
        emailNotifications: false,
        severityFilter: ['high', 'critical']
      })

      const lowSeverityAlert = createMockAlert({ severity: 'low' })
      const highSeverityAlert = createMockAlert({ severity: 'high' })

      await notificationService.sendNotification(lowSeverityAlert)
      await notificationService.sendNotification(highSeverityAlert)

      expect(mockNotification).toHaveBeenCalledTimes(1) // Only high severity
    })
  })

  describe('Email Notifications', () => {
    it('should send email notification request', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      })
      global.fetch = fetchMock

      notificationService.setPreferences({
        browserNotifications: false,
        emailNotifications: true,
        emailAddress: 'user@example.com'
      })

      const alert = createMockAlert({
        severity: 'critical',
        message: 'Critical performance issue'
      })

      const result = await notificationService.sendEmailNotification(alert)

      expect(result).toBe(true)
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/notifications/email',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('Critical performance issue')
        })
      )
    })

    it('should handle email notification failures', async () => {
      const fetchMock = vi.fn().mockRejectedValue(new Error('Network error'))
      global.fetch = fetchMock

      notificationService.setPreferences({
        browserNotifications: false,
        emailNotifications: true,
        emailAddress: 'user@example.com'
      })

      const alert = createMockAlert()
      const result = await notificationService.sendEmailNotification(alert)

      expect(result).toBe(false)
    })

    it('should not send email if no email address configured', async () => {
      notificationService.setPreferences({
        browserNotifications: false,
        emailNotifications: true
        // No emailAddress set
      })

      const alert = createMockAlert()
      const result = await notificationService.sendEmailNotification(alert)

      expect(result).toBe(false)
    })
  })

  describe('Webhook Notifications', () => {
    it('should send webhook notification', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200
      })
      global.fetch = fetchMock

      notificationService.setPreferences({
        browserNotifications: false,
        emailNotifications: false,
        webhookUrl: 'https://api.example.com/webhook'
      })

      const alert = createMockAlert({
        severity: 'high',
        message: 'High response time alert'
      })

      const result = await notificationService.sendWebhookNotification(alert)

      expect(result).toBe(true)
      expect(fetchMock).toHaveBeenCalledWith(
        'https://api.example.com/webhook',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('High response time alert')
        })
      )
    })

    it('should include alert metadata in webhook payload', async () => {
      const fetchMock = vi.fn().mockResolvedValue({ ok: true })
      global.fetch = fetchMock

      notificationService.setPreferences({
        webhookUrl: 'https://api.example.com/webhook'
      })

      const alert = createMockAlert({
        severity: 'critical',
        endpointId: 'endpoint-123',
        metricValues: { executionTime: 1500, responseSize: 2048 }
      })

      await notificationService.sendWebhookNotification(alert)

      const callArgs = fetchMock.mock.calls[0]
      const payload = JSON.parse(callArgs[1].body)

      expect(payload).toEqual({
        alertId: alert.id,
        severity: 'critical',
        endpointId: 'endpoint-123',
        message: alert.message,
        triggeredAt: alert.triggeredAt.toISOString(),
        metricValues: { executionTime: 1500, responseSize: 2048 },
        source: 'fraiseql-doctor'
      })
    })

    it('should retry webhook on failure', async () => {
      const fetchMock = vi.fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ ok: true })
      global.fetch = fetchMock

      notificationService.setPreferences({
        webhookUrl: 'https://api.example.com/webhook'
      })

      const alert = createMockAlert()
      const result = await notificationService.sendWebhookNotification(alert)

      expect(result).toBe(true)
      expect(fetchMock).toHaveBeenCalledTimes(2) // Initial call + 1 retry
    })

    it('should fail after max retries', async () => {
      const fetchMock = vi.fn().mockRejectedValue(new Error('Network error'))
      global.fetch = fetchMock

      notificationService.setPreferences({
        webhookUrl: 'https://api.example.com/webhook'
      })

      const alert = createMockAlert()
      const result = await notificationService.sendWebhookNotification(alert)

      expect(result).toBe(false)
      expect(fetchMock).toHaveBeenCalledTimes(3) // Initial call + 2 retries
    })
  })

  describe('Unified Notification Sending', () => {
    it('should send notifications via all enabled methods', async () => {
      const fetchMock = vi.fn().mockResolvedValue({ ok: true })
      global.fetch = fetchMock

      notificationService.setPreferences({
        browserNotifications: true,
        emailNotifications: true,
        emailAddress: 'user@example.com',
        webhookUrl: 'https://api.example.com/webhook',
        severityFilter: ['medium', 'high', 'critical']
      })

      const alert = createMockAlert({ severity: 'high' })
      await notificationService.sendNotification(alert)

      // Should send browser notification
      expect(mockNotification).toHaveBeenCalled()

      // Should send email and webhook (2 fetch calls)
      expect(fetchMock).toHaveBeenCalledTimes(2)
    })

    it('should only send notifications matching severity filter', async () => {
      notificationService.setPreferences({
        browserNotifications: true,
        severityFilter: ['high', 'critical']
      })

      const lowAlert = createMockAlert({ severity: 'low' })
      const highAlert = createMockAlert({ severity: 'high' })

      await notificationService.sendNotification(lowAlert)
      await notificationService.sendNotification(highAlert)

      expect(mockNotification).toHaveBeenCalledTimes(1) // Only high severity
    })

    it('should emit events for notification success/failure', async () => {
      const successSpy = vi.fn()
      const failureSpy = vi.fn()

      notificationService.addEventListener('notification-sent', successSpy)
      notificationService.addEventListener('notification-failed', failureSpy)

      notificationService.setPreferences({
        browserNotifications: true
      })

      const alert = createMockAlert()
      await notificationService.sendNotification(alert)

      expect(successSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            alertId: alert.id,
            method: 'browser',
            success: true
          })
        })
      )
    })
  })

  describe('Notification History', () => {
    it('should track notification history', async () => {
      notificationService.setPreferences({
        browserNotifications: true
      })

      const alert = createMockAlert()
      await notificationService.sendNotification(alert)

      const history = notificationService.getNotificationHistory()

      expect(history).toHaveLength(1)
      expect(history[0]).toEqual({
        alertId: alert.id,
        method: 'browser',
        success: true,
        sentAt: expect.any(Date),
        error: undefined
      })
    })

    it('should limit notification history size', async () => {
      notificationService.setPreferences({
        browserNotifications: true
      })

      // Send more notifications than the limit
      for (let i = 0; i < 150; i++) {
        const alert = createMockAlert({ id: `alert-${i}` })
        await notificationService.sendNotification(alert)
      }

      const history = notificationService.getNotificationHistory()
      expect(history.length).toBeLessThanOrEqual(100) // Default limit
    })

    it('should clear notification history', async () => {
      notificationService.setPreferences({
        browserNotifications: true
      })

      const alert = createMockAlert()
      await notificationService.sendNotification(alert)

      expect(notificationService.getNotificationHistory()).toHaveLength(1)

      notificationService.clearNotificationHistory()
      expect(notificationService.getNotificationHistory()).toHaveLength(0)
    })
  })

  describe('Do Not Disturb Mode', () => {
    it('should respect do not disturb mode', async () => {
      notificationService.setPreferences({
        browserNotifications: true,
        doNotDisturb: true
      })

      const alert = createMockAlert()
      await notificationService.sendNotification(alert)

      expect(mockNotification).not.toHaveBeenCalled()
    })

    it('should allow critical alerts during do not disturb', async () => {
      notificationService.setPreferences({
        browserNotifications: true,
        doNotDisturb: true,
        allowCriticalDuringDnD: true
      })

      const criticalAlert = createMockAlert({ severity: 'critical' })
      const mediumAlert = createMockAlert({ severity: 'medium' })

      await notificationService.sendNotification(criticalAlert)
      await notificationService.sendNotification(mediumAlert)

      expect(mockNotification).toHaveBeenCalledTimes(1) // Only critical
    })

    it('should respect do not disturb time window', async () => {
      const now = new Date()
      const dndStart = new Date(now.getTime() - 3600000) // 1 hour ago
      const dndEnd = new Date(now.getTime() + 3600000)   // 1 hour from now

      notificationService.setPreferences({
        browserNotifications: true,
        doNotDisturb: true,
        dndTimeWindow: {
          start: dndStart.toTimeString().substring(0, 5), // HH:MM format
          end: dndEnd.toTimeString().substring(0, 5)
        }
      })

      const alert = createMockAlert()
      await notificationService.sendNotification(alert)

      expect(mockNotification).not.toHaveBeenCalled()
    })
  })
})
