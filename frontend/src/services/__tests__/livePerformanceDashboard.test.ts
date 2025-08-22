import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { LivePerformanceDashboard } from '../livePerformanceDashboard'
import type { QueryPerformanceData } from '../graphqlSubscriptionClient'

describe('LivePerformanceDashboard', () => {
  let dashboard: LivePerformanceDashboard
  let mockSubscriptionClient: any
  let mockAnalyticsEngine: any

  beforeEach(() => {
    mockSubscriptionClient = {
      subscribeToPerformanceMetrics: vi.fn(),
      subscribeToAggregatedMetrics: vi.fn(),
      unsubscribe: vi.fn(),
      disconnect: vi.fn(),
      getActiveSubscriptions: vi.fn().mockReturnValue([])
    }

    mockAnalyticsEngine = {
      processStreamingData: vi.fn(),
      detectAnomalies: vi.fn(),
      generateForecast: vi.fn(),
      updateBaseline: vi.fn()
    }

    dashboard = new LivePerformanceDashboard({
      subscriptionClient: mockSubscriptionClient,
      analyticsEngine: mockAnalyticsEngine,
      updateInterval: 1000,
      maxDataPoints: 1000,
      alertThresholds: {
        executionTime: { warning: 500, critical: 1000 },
        errorRate: { warning: 0.05, critical: 0.1 },
        throughput: { warning: 0.5, critical: 0.2 }
      }
    })
  })

  afterEach(() => {
    dashboard?.destroy()
    vi.clearAllMocks()
  })

  describe('Real-time Data Integration', () => {
    it('should initialize and connect to real-time data streams', async () => {
      const mockSubscription = { id: 'sub-001', status: 'active' }
      mockSubscriptionClient.subscribeToPerformanceMetrics.mockResolvedValue(mockSubscription)
      mockSubscriptionClient.subscribeToAggregatedMetrics.mockResolvedValue(mockSubscription)

      await dashboard.initialize(['endpoint-1', 'endpoint-2'])

      expect(mockSubscriptionClient.subscribeToPerformanceMetrics).toHaveBeenCalledTimes(2)
      expect(mockSubscriptionClient.subscribeToAggregatedMetrics).toHaveBeenCalledTimes(2)

      // Verify endpoint registration
      expect(dashboard.getMonitoredEndpoints()).toEqual(['endpoint-1', 'endpoint-2'])
      expect(dashboard.isInitialized()).toBe(true)
    })

    it('should process incoming real-time query performance data', async () => {
      const mockPerformanceData: QueryPerformanceData = {
        id: 'query-001',
        endpointId: 'endpoint-1',
        operationName: 'GetUsers',
        query: 'query GetUsers { users { id name } }',
        variables: {},
        executionTime: 250,
        responseSize: 2048,
        timestamp: new Date(),
        status: 'success',
        errors: null,
        fieldExecutionTimes: {
          'users': 200,
          'users.id': 25,
          'users.name': 25
        }
      }

      await dashboard.initialize(['endpoint-1'])

      // Get the callback function passed to subscription
      const subscriptionCallback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[0][0].callback

      // Trigger data processing
      subscriptionCallback(mockPerformanceData)

      expect(mockAnalyticsEngine.processStreamingData).toHaveBeenCalledWith([mockPerformanceData])

      // Verify data is stored in dashboard
      const currentMetrics = dashboard.getCurrentMetrics('endpoint-1')
      expect(currentMetrics.recentQueries).toContain(mockPerformanceData)
      expect(currentMetrics.averageExecutionTime).toBeCloseTo(250, 1)
    })

    it('should integrate with time-series analytics for advanced forecasting', async () => {
      const mockForecastResult = {
        predictions: [
          { timestamp: new Date(), predictedValue: 280 },
          { timestamp: new Date(), predictedValue: 290 }
        ],
        confidenceInterval: { lower: 250, upper: 320 },
        accuracy: { mae: 15, mape: 8.5 }
      }

      mockAnalyticsEngine.generateForecast.mockReturnValue(mockForecastResult)

      await dashboard.initialize(['endpoint-1'])

      // Simulate enough data points for forecasting
      const mockDataPoints = Array.from({ length: 50 }, (_, i) => ({
        id: `query-${i}`,
        endpointId: 'endpoint-1',
        operationName: 'TestQuery',
        query: 'query Test { test }',
        variables: {},
        executionTime: 200 + Math.random() * 100,
        responseSize: 1024,
        timestamp: new Date(Date.now() - (50 - i) * 60000),
        status: 'success' as const,
        errors: null,
        fieldExecutionTimes: {}
      }))

      // Process data points
      const subscriptionCallback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[0][0].callback
      mockDataPoints.forEach(dataPoint => subscriptionCallback(dataPoint))

      // Trigger forecast generation
      const forecast = await dashboard.generatePerformanceForecast('endpoint-1', {
        horizonHours: 2,
        includeTrends: true
      })

      expect(mockAnalyticsEngine.generateForecast).toHaveBeenCalled()
      expect(forecast.predictions).toHaveLength(2)
      expect(forecast.accuracy.mae).toBe(15)
    })
  })

  describe('Real-time Alerting and Monitoring', () => {
    it('should trigger alerts when performance thresholds are exceeded', async () => {
      const alertCallback = vi.fn()
      dashboard.addEventListener('performance-alert', alertCallback)

      await dashboard.initialize(['endpoint-1'])

      // Simulate high execution time query
      const highLatencyQuery: QueryPerformanceData = {
        id: 'query-slow-001',
        endpointId: 'endpoint-1',
        operationName: 'SlowQuery',
        query: 'query SlowQuery { complexOperation }',
        variables: {},
        executionTime: 1500, // Exceeds critical threshold (1000ms)
        responseSize: 4096,
        timestamp: new Date(),
        status: 'success',
        errors: null,
        fieldExecutionTimes: {}
      }

      const subscriptionCallback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[0][0].callback
      subscriptionCallback(highLatencyQuery)

      // Wait for debounced alert to fire
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(alertCallback).toHaveBeenCalledWith({
        type: 'execution_time_critical',
        endpointId: 'endpoint-1',
        queryId: 'query-slow-001',
        threshold: 1000,
        actualValue: 1500,
        severity: 'critical',
        timestamp: expect.any(Date),
        recommendation: expect.stringContaining('Investigate query optimization')
      })
    })

    it('should detect and alert on anomalous patterns using analytics engine', async () => {
      const mockAnomalies = [
        {
          detectionMethod: ['isolation_forest'],
          anomalyScore: 0.95,
          severity: 'high' as const,
          explanation: 'Execution time significantly above normal pattern',
          timestamp: new Date(),
          affectedQuery: 'GetUserPosts'
        }
      ]

      mockAnalyticsEngine.detectAnomalies.mockReturnValue(mockAnomalies)

      const anomalyCallback = vi.fn()
      dashboard.addEventListener('anomaly-detected', anomalyCallback)

      await dashboard.initialize(['endpoint-1'])

      // Process enough data to trigger anomaly detection
      const normalQueries = Array.from({ length: 20 }, (_, i) => ({
        id: `query-normal-${i}`,
        endpointId: 'endpoint-1',
        operationName: 'NormalQuery',
        query: 'query Normal { data }',
        variables: {},
        executionTime: 150 + Math.random() * 50,
        responseSize: 1024,
        timestamp: new Date(Date.now() - (20 - i) * 30000),
        status: 'success' as const,
        errors: null,
        fieldExecutionTimes: {}
      }))

      const subscriptionCallback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[0][0].callback
      normalQueries.forEach(query => subscriptionCallback(query))

      // Wait for anomaly check to be scheduled and executed
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(mockAnalyticsEngine.detectAnomalies).toHaveBeenCalled()
      expect(anomalyCallback).toHaveBeenCalledWith({
        endpointId: 'endpoint-1',
        anomalies: mockAnomalies,
        detectionTimestamp: expect.any(Date)
      })
    })

    it('should provide real-time performance dashboard updates', async () => {
      const updateCallback = vi.fn()
      dashboard.addEventListener('metrics-updated', updateCallback)

      await dashboard.initialize(['endpoint-1'])

      const mockQueries = [
        {
          id: 'query-1',
          endpointId: 'endpoint-1',
          operationName: 'Query1',
          query: 'query Query1 { data1 }',
          variables: {},
          executionTime: 150,
          responseSize: 1024,
          timestamp: new Date(),
          status: 'success' as const,
          errors: null,
          fieldExecutionTimes: {}
        },
        {
          id: 'query-2',
          endpointId: 'endpoint-1',
          operationName: 'Query2',
          query: 'query Query2 { data2 }',
          variables: {},
          executionTime: 200,
          responseSize: 2048,
          timestamp: new Date(),
          status: 'success' as const,
          errors: null,
          fieldExecutionTimes: {}
        }
      ]

      const subscriptionCallback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[0][0].callback
      mockQueries.forEach(query => subscriptionCallback(query))

      expect(updateCallback).toHaveBeenCalledWith({
        endpointId: 'endpoint-1',
        metrics: {
          totalQueries: 2,
          averageExecutionTime: 175,
          throughput: expect.any(Number),
          errorRate: 0,
          recentQueries: mockQueries,
          performanceTrend: expect.any(String)
        },
        timestamp: expect.any(Date),
        dataQuality: expect.any(Object)
      })
    })
  })

  describe('Dashboard State Management', () => {
    it('should maintain rolling window of performance data', async () => {
      await dashboard.initialize(['endpoint-1'])

      // Generate more data than max limit
      const excessiveQueries = Array.from({ length: 1200 }, (_, i) => ({
        id: `query-${i}`,
        endpointId: 'endpoint-1',
        operationName: 'TestQuery',
        query: 'query Test { test }',
        variables: {},
        executionTime: 100 + i,
        responseSize: 1024,
        timestamp: new Date(Date.now() - (1200 - i) * 1000),
        status: 'success' as const,
        errors: null,
        fieldExecutionTimes: {}
      }))

      const subscriptionCallback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[0][0].callback
      excessiveQueries.forEach(query => subscriptionCallback(query))

      const metrics = dashboard.getCurrentMetrics('endpoint-1')
      expect(metrics.recentQueries.length).toBeLessThanOrEqual(1000) // Respects maxDataPoints

      // Should keep most recent data
      const latestQuery = metrics.recentQueries[metrics.recentQueries.length - 1]
      expect(latestQuery.id).toBe('query-1199')
    })

    it('should handle multiple endpoint monitoring simultaneously', async () => {
      await dashboard.initialize(['endpoint-1', 'endpoint-2', 'endpoint-3'])

      // Send data to different endpoints
      const queries = [
        {
          id: 'query-e1',
          endpointId: 'endpoint-1',
          operationName: 'Endpoint1Query',
          executionTime: 100
        },
        {
          id: 'query-e2',
          endpointId: 'endpoint-2',
          operationName: 'Endpoint2Query',
          executionTime: 150
        },
        {
          id: 'query-e3',
          endpointId: 'endpoint-3',
          operationName: 'Endpoint3Query',
          executionTime: 200
        }
      ].map(partial => ({
        ...partial,
        query: 'query Test { test }',
        variables: {},
        responseSize: 1024,
        timestamp: new Date(),
        status: 'success' as const,
        errors: null,
        fieldExecutionTimes: {}
      }))

      // Each endpoint has its own subscription callback
      queries.forEach((query, index) => {
        const callback = mockSubscriptionClient.subscribeToPerformanceMetrics.mock.calls[index][0].callback
        callback(query)
      })

      expect(dashboard.getCurrentMetrics('endpoint-1').averageExecutionTime).toBeCloseTo(100, 1)
      expect(dashboard.getCurrentMetrics('endpoint-2').averageExecutionTime).toBeCloseTo(150, 1)
      expect(dashboard.getCurrentMetrics('endpoint-3').averageExecutionTime).toBeCloseTo(200, 1)
    })

    it('should handle graceful shutdown and cleanup', async () => {
      await dashboard.initialize(['endpoint-1', 'endpoint-2'])

      expect(mockSubscriptionClient.subscribeToPerformanceMetrics).toHaveBeenCalledTimes(2)

      dashboard.destroy()

      expect(mockSubscriptionClient.disconnect).toHaveBeenCalled()
      expect(dashboard.isInitialized()).toBe(false)
    })
  })
})
