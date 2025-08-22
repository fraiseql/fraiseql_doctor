import { describe, it, expect, beforeEach } from 'vitest'
import { PerformanceAnalytics } from '../performanceAnalytics'
import type { QueryMetric } from '../performanceMonitor'

describe('PerformanceAnalytics', () => {
  let analytics: PerformanceAnalytics

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
    analytics = new PerformanceAnalytics()
  })

  describe('Historical Trend Analysis', () => {
    it('should calculate performance trends over time', () => {
      const now = new Date()
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 100, timestamp: new Date(now.getTime() - 3600000) }), // 1 hour ago
        createMockMetric({ executionTime: 120, timestamp: new Date(now.getTime() - 1800000) }), // 30 min ago
        createMockMetric({ executionTime: 80, timestamp: new Date(now.getTime() - 600000) }),   // 10 min ago
        createMockMetric({ executionTime: 90, timestamp: now })
      ]

      const trend = analytics.calculatePerformanceTrend(metrics, 'executionTime')

      expect(trend).toEqual({
        direction: 'improving', // Overall trend from 100 to 90
        slope: expect.any(Number),
        confidence: expect.any(Number),
        changePercentage: expect.any(Number)
      })
    })

    it('should detect deteriorating performance trends', () => {
      const now = new Date()
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 50, timestamp: new Date(now.getTime() - 3600000) }),
        createMockMetric({ executionTime: 80, timestamp: new Date(now.getTime() - 1800000) }),
        createMockMetric({ executionTime: 120, timestamp: new Date(now.getTime() - 600000) }),
        createMockMetric({ executionTime: 150, timestamp: now })
      ]

      const trend = analytics.calculatePerformanceTrend(metrics, 'executionTime')

      expect(trend.direction).toBe('degrading')
      expect(trend.changePercentage).toBeGreaterThan(0)
    })

    it('should handle stable performance trends', () => {
      const now = new Date()
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 100, timestamp: new Date(now.getTime() - 3600000) }),
        createMockMetric({ executionTime: 102, timestamp: new Date(now.getTime() - 1800000) }),
        createMockMetric({ executionTime: 98, timestamp: new Date(now.getTime() - 600000) }),
        createMockMetric({ executionTime: 101, timestamp: now })
      ]

      const trend = analytics.calculatePerformanceTrend(metrics, 'executionTime')

      expect(trend.direction).toBe('stable')
      expect(Math.abs(trend.changePercentage)).toBeLessThan(5) // Less than 5% change
    })
  })

  describe('Time-based Aggregation', () => {
    it('should aggregate metrics by hour', () => {
      // Create timestamps that clearly fall in different hours
      const baseTime = new Date('2024-01-01T12:00:00Z') // Noon
      const hourBefore = new Date('2024-01-01T11:30:00Z') // 11:30 AM (previous hour)
      
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 100, timestamp: hourBefore }),
        createMockMetric({ executionTime: 120, timestamp: new Date('2024-01-01T11:45:00Z') }), // Same hour as first
        createMockMetric({ executionTime: 80, timestamp: baseTime }),
        createMockMetric({ executionTime: 90, timestamp: new Date('2024-01-01T12:15:00Z') }) // Same hour as third
      ]

      const aggregated = analytics.aggregateByTimeWindow(metrics, 'hour')

      expect(aggregated).toHaveLength(2) // Two different hours
      expect(aggregated[0]).toEqual({
        window: expect.any(String),
        avgExecutionTime: 110, // (100 + 120) / 2 for 11:00 hour
        avgResponseSize: 1024,
        count: 2,
        timestamp: expect.any(Date)
      })
      expect(aggregated[1]).toEqual({
        window: expect.any(String),
        avgExecutionTime: 85, // (80 + 90) / 2 for 12:00 hour
        avgResponseSize: 1024,
        count: 2,
        timestamp: expect.any(Date)
      })
    })

    it('should aggregate metrics by day', () => {
      const now = new Date()
      const yesterday = new Date(now.getTime() - 86400000)
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 100, timestamp: yesterday }),
        createMockMetric({ executionTime: 120, timestamp: now })
      ]

      const aggregated = analytics.aggregateByTimeWindow(metrics, 'day')

      expect(aggregated).toHaveLength(2)
      expect(aggregated[0].count).toBe(1)
      expect(aggregated[1].count).toBe(1)
    })
  })

  describe('Performance Percentiles', () => {
    it('should calculate performance percentiles', () => {
      const metrics: QueryMetric[] = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({ executionTime: i + 1 }) // 1ms to 100ms
      )

      const percentiles = analytics.calculatePercentiles(metrics, 'executionTime')

      expect(percentiles.p50).toBeCloseTo(50.5, 1)
      expect(percentiles.p90).toBeCloseTo(90.1, 1)
      expect(percentiles.p95).toBeCloseTo(95.05, 1)
      expect(percentiles.p99).toBeCloseTo(99.01, 1)
    })

    it('should handle edge cases for percentiles', () => {
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 100 })
      ]

      const percentiles = analytics.calculatePercentiles(metrics, 'executionTime')

      expect(percentiles).toEqual({
        p50: 100,
        p90: 100,
        p95: 100,
        p99: 100
      })
    })
  })

  describe('Anomaly Detection', () => {
    it('should detect performance anomalies using statistical methods', () => {
      const normalMetrics = Array.from({ length: 50 }, () =>
        createMockMetric({ executionTime: 100 + Math.random() * 20 }) // 100-120ms
      )
      const anomaly = createMockMetric({ executionTime: 300 }) // Outlier

      const metrics = [...normalMetrics, anomaly]
      const anomalies = analytics.detectAnomalies(metrics, 'executionTime')

      expect(anomalies).toHaveLength(1)
      expect(anomalies[0].metric.executionTime).toBe(300)
      expect(['low', 'medium', 'high']).toContain(anomalies[0].severity)
      expect(anomalies[0].deviationScore).toBeGreaterThan(2) // More than 2 standard deviations
    })

    it('should not detect anomalies in consistent data', () => {
      const metrics = Array.from({ length: 50 }, () =>
        createMockMetric({ executionTime: 100 + Math.random() * 5 }) // Very consistent
      )

      const anomalies = analytics.detectAnomalies(metrics, 'executionTime')

      expect(anomalies).toHaveLength(0)
    })
  })

  describe('Performance Forecasting', () => {
    it('should generate performance forecasts based on historical data', () => {
      const now = new Date()
      const metrics: QueryMetric[] = Array.from({ length: 20 }, (_, i) => {
        const timestamp = new Date(now.getTime() - (19 - i) * 3600000) // Last 20 hours
        return createMockMetric({
          executionTime: 100 + i * 2, // Gradual increase
          timestamp
        })
      })

      const forecast = analytics.generatePerformanceForecast(metrics, 'executionTime', 5)

      expect(forecast).toHaveLength(5) // 5 forecast points
      expect(forecast[0]).toEqual({
        timestamp: expect.any(Date),
        predictedValue: expect.any(Number),
        confidence: expect.any(Number),
        upperBound: expect.any(Number),
        lowerBound: expect.any(Number)
      })
    })

    it('should handle insufficient data for forecasting', () => {
      const metrics: QueryMetric[] = [
        createMockMetric({ executionTime: 100 })
      ]

      expect(() => {
        analytics.generatePerformanceForecast(metrics, 'executionTime', 5)
      }).toThrow('Insufficient data for forecasting')
    })
  })
})
