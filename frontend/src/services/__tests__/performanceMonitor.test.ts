import { describe, it, expect, vi, beforeEach } from 'vitest'
import { PerformanceMonitor } from '../performanceMonitor'

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor

  beforeEach(() => {
    monitor = new PerformanceMonitor()
  })

  it('should track query execution metrics', async () => {
    const onMetric = vi.fn()
    monitor.addEventListener('metric-recorded', onMetric)

    await monitor.trackQuery('test-endpoint', 'query { users }', {
      executionTime: 120,
      responseSize: 1024,
      timestamp: new Date('2025-01-21T10:00:00Z')
    })

    expect(onMetric).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: expect.objectContaining({
          endpointId: 'test-endpoint',
          query: 'query { users }',
          executionTime: 120,
          responseSize: 1024
        })
      })
    )
  })

  it('should store metrics history', async () => {
    await monitor.trackQuery('endpoint-1', 'query { users }', {
      executionTime: 120,
      responseSize: 1024,
      timestamp: new Date('2025-01-21T10:00:00Z')
    })

    await monitor.trackQuery('endpoint-1', 'query { posts }', {
      executionTime: 200,
      responseSize: 2048,
      timestamp: new Date('2025-01-21T11:00:00Z')
    })

    const metrics = monitor.getMetrics('endpoint-1')
    expect(metrics).toHaveLength(2)
    expect(metrics[0].query).toBe('query { users }')
    expect(metrics[1].query).toBe('query { posts }')
  })

  it('should calculate average response time', async () => {
    await monitor.trackQuery('endpoint-1', 'query { users }', {
      executionTime: 100,
      responseSize: 1024,
      timestamp: new Date()
    })

    await monitor.trackQuery('endpoint-1', 'query { posts }', {
      executionTime: 200,
      responseSize: 2048,
      timestamp: new Date()
    })

    const avgResponseTime = monitor.getAverageResponseTime('endpoint-1')
    expect(avgResponseTime).toBe(150)
  })

  it('should get metrics for time range', async () => {
    const now = new Date('2025-01-21T12:00:00Z')
    const oneHourAgo = new Date('2025-01-21T11:00:00Z')
    const twoHoursAgo = new Date('2025-01-21T10:00:00Z')

    await monitor.trackQuery('endpoint-1', 'query1', {
      executionTime: 100,
      responseSize: 1024,
      timestamp: twoHoursAgo
    })

    await monitor.trackQuery('endpoint-1', 'query2', {
      executionTime: 150,
      responseSize: 1024,
      timestamp: oneHourAgo
    })

    await monitor.trackQuery('endpoint-1', 'query3', {
      executionTime: 200,
      responseSize: 1024,
      timestamp: now
    })

    const recentMetrics = monitor.getMetricsInRange('endpoint-1', oneHourAgo, now)
    expect(recentMetrics).toHaveLength(2)
    expect(recentMetrics[0].query).toBe('query2')
    expect(recentMetrics[1].query).toBe('query3')
  })

  it('should send metrics to analytics backend', async () => {
    const mockSendToAnalytics = vi.spyOn(monitor as any, 'sendToAnalytics').mockResolvedValue(undefined)

    await monitor.trackQuery('endpoint-1', 'query { users }', {
      executionTime: 120,
      responseSize: 1024,
      timestamp: new Date()
    })

    expect(mockSendToAnalytics).toHaveBeenCalledWith(
      expect.objectContaining({
        endpointId: 'endpoint-1',
        query: 'query { users }',
        executionTime: 120,
        responseSize: 1024
      })
    )
  })

  it('should clear old metrics beyond retention limit', async () => {
    const monitor = new PerformanceMonitor({ maxMetrics: 2 })

    await monitor.trackQuery('endpoint-1', 'query1', {
      executionTime: 100,
      responseSize: 1024,
      timestamp: new Date('2025-01-21T10:00:00Z')
    })

    await monitor.trackQuery('endpoint-1', 'query2', {
      executionTime: 150,
      responseSize: 1024,
      timestamp: new Date('2025-01-21T11:00:00Z')
    })

    await monitor.trackQuery('endpoint-1', 'query3', {
      executionTime: 200,
      responseSize: 1024,
      timestamp: new Date('2025-01-21T12:00:00Z')
    })

    const metrics = monitor.getMetrics('endpoint-1')
    expect(metrics).toHaveLength(2)
    expect(metrics[0].query).toBe('query2')
    expect(metrics[1].query).toBe('query3')
  })
})
