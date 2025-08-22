import { describe, it, expect, beforeEach } from 'vitest'
import { TimeSeriesAnalytics } from '../timeSeriesAnalytics'
import type { QueryMetric } from '../performanceMonitor'

describe('TimeSeriesAnalytics', () => {
  let timeSeriesAnalytics: TimeSeriesAnalytics

  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    query: 'test query',
    variables: {},
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    status: 'success',
    endpointId: 'endpoint-1',
    operationType: 'query',
    ...overrides
  })

  beforeEach(() => {
    timeSeriesAnalytics = new TimeSeriesAnalytics()
  })

  describe('Real-time Data Processing', () => {
    it('should process streaming metrics in real-time', () => {
      const streamingData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 50 + Math.sin(i * 0.1) * 20,
          timestamp: new Date(Date.now() - (100 - i) * 1000)
        })
      )

      const result = timeSeriesAnalytics.processStreamingData(streamingData)

      expect(result.dataPoints).toHaveLength(100)
      expect(result.smoothedTrend).toBeDefined()
      expect(result.realtimeStatistics.currentRate).toBeGreaterThan(0)
      expect(result.realtimeStatistics.averageLatency).toBeGreaterThan(0)
    })

    it('should detect data quality issues in real-time stream', () => {
      const corruptedData = [
        createMockMetric({ executionTime: 100 }),
        createMockMetric({ executionTime: -1 }), // Invalid
        createMockMetric({ executionTime: 10000 }), // Outlier
        createMockMetric({ executionTime: NaN }), // Corrupted
      ]

      const result = timeSeriesAnalytics.processStreamingData(corruptedData)

      expect(result.qualityMetrics.invalidDataPoints).toBe(2)
      expect(result.qualityMetrics.outlierCount).toBe(1)
      expect(result.qualityMetrics.completenessRatio).toBe(0.5)
    })

    it('should maintain sliding window buffer for real-time processing', () => {
      const analytics = new TimeSeriesAnalytics({ bufferSize: 50 })

      // Add 75 data points
      for (let i = 0; i < 75; i++) {
        analytics.addDataPoint(createMockMetric({
          executionTime: i,
          timestamp: new Date(Date.now() + i * 1000)
        }))
      }

      const buffer = analytics.getBuffer()
      expect(buffer).toHaveLength(50) // Should maintain buffer limit
      expect(buffer[0].executionTime).toBe(25) // Should contain latest 50 points
    })
  })

  describe('Interactive Chart Data Processing', () => {
    it('should generate multi-resolution data for zoom levels', () => {
      const metrics = Array.from({ length: 1000 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.random() * 50,
          timestamp: new Date(Date.now() - (1000 - i) * 60000) // 1000 minutes of data
        })
      )

      const multiRes = timeSeriesAnalytics.generateMultiResolutionData(metrics)

      expect(multiRes.minute).toHaveLength(1000)
      expect(multiRes.fiveMinute.length).toBeGreaterThan(0)
      expect(multiRes.hour.length).toBeGreaterThan(0)
      expect(multiRes.day.length).toBeGreaterThan(0)
    })

    it('should support brush selection and time range filtering', () => {
      const metrics = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const startTime = new Date(Date.now() - 50 * 60000)
      const endTime = new Date(Date.now() - 20 * 60000)

      const filtered = timeSeriesAnalytics.filterByTimeRange(metrics, startTime, endTime)

      expect(filtered.length).toBe(31) // 31 minutes of data (inclusive range: 50-20 = 30 + 1 for inclusive)
      expect(filtered[0].timestamp.getTime()).toBeGreaterThanOrEqual(startTime.getTime())
      expect(filtered[filtered.length - 1].timestamp.getTime()).toBeLessThanOrEqual(endTime.getTime())
    })

    it('should calculate drill-down statistics for selected regions', () => {
      const metrics = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i,
          responseSize: 1024 + i * 10
        })
      )

      const selection = timeSeriesAnalytics.calculateSelectionStatistics(metrics.slice(20, 40))

      expect(selection.mean.executionTime).toBe(129.5) // Average of 120-139
      expect(selection.median.executionTime).toBe(129.5)
      expect(selection.standardDeviation.executionTime).toBeGreaterThan(0)
      expect(selection.percentiles.p95.executionTime).toBeGreaterThan(selection.mean.executionTime)
    })
  })

  describe('Baseline Comparison Analytics', () => {
    it('should establish performance baselines from historical data', () => {
      const historicalMetrics = Array.from({ length: 1000 }, () =>
        createMockMetric({
          executionTime: 100 + Math.random() * 20, // Normal performance
          timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000) // Last week
        })
      )

      const baseline = timeSeriesAnalytics.establishBaseline(historicalMetrics)

      expect(baseline.metrics.executionTime.mean).toBeCloseTo(110, 0)
      expect(baseline.metrics.executionTime.upperBound).toBeGreaterThan(baseline.metrics.executionTime.mean)
      expect(baseline.metrics.executionTime.lowerBound).toBeLessThan(baseline.metrics.executionTime.mean)
      expect(baseline.confidence).toBeGreaterThan(0.8)
    })

    it('should detect performance deviations from baseline', () => {
      const baseline = {
        metrics: {
          executionTime: { mean: 100, upperBound: 120, lowerBound: 80 }
        },
        confidence: 0.95
      }

      const currentMetrics = [
        createMockMetric({ executionTime: 150 }), // Above upper bound
        createMockMetric({ executionTime: 60 }),  // Below lower bound
        createMockMetric({ executionTime: 100 }), // Normal
      ]

      const deviations = timeSeriesAnalytics.detectDeviations(currentMetrics, baseline)

      expect(deviations).toHaveLength(2)
      expect(deviations[0].type).toBe('performance_degradation')
      expect(deviations[1].type).toBe('unexpected_improvement')
      expect(deviations[0].severity).toBe('high')
    })

    it('should compare current period with historical periods', () => {
      const lastWeekMetrics = Array.from({ length: 100 }, () =>
        createMockMetric({ executionTime: 100 + Math.random() * 20 })
      )

      const thisWeekMetrics = Array.from({ length: 100 }, () =>
        createMockMetric({ executionTime: 120 + Math.random() * 20 })
      )

      const comparison = timeSeriesAnalytics.comparePeriods(thisWeekMetrics, lastWeekMetrics)

      expect(comparison.performanceChange.executionTime.percentageChange).toBeGreaterThan(15)
      expect(comparison.performanceChange.executionTime.percentageChange).toBeLessThan(25) // Allow reasonable range for random data
      expect(comparison.performanceChange.executionTime.direction).toBe('degradation')
      expect(comparison.significance.isStatisticallySignificant).toBe(true)
      expect(comparison.significance.pValue).toBeLessThan(0.05)
    })
  })

  describe('Advanced Forecasting', () => {
    it('should generate time series forecasts using ARIMA-like models', () => {
      const historicalData = Array.from({ length: 200 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.sin(i * 0.1) * 10 + Math.random() * 5, // Trending with noise
          timestamp: new Date(Date.now() - (200 - i) * 60000)
        })
      )

      const forecast = timeSeriesAnalytics.generateForecast(historicalData, 24) // 24 hours ahead

      expect(forecast.predictions).toHaveLength(24)
      expect(forecast.predictions[0].predictedValue).toBeGreaterThan(0)
      expect(forecast.predictions[0].confidenceInterval.upper).toBeGreaterThan(
        forecast.predictions[0].confidenceInterval.lower
      )
      expect(forecast.modelAccuracy.mae).toBeGreaterThan(0) // Mean Absolute Error
      expect(forecast.modelAccuracy.rmse).toBeGreaterThan(0) // Root Mean Square Error
    })

    it('should detect seasonal patterns in time series data', () => {
      const seasonalData = Array.from({ length: 24 * 7 }, (_, i) => { // One week hourly
        const hourOfDay = i % 24
        const dayOfWeek = Math.floor(i / 24)
        const baseValue = 100
        const dailyPattern = Math.sin((hourOfDay / 24) * 2 * Math.PI) * 20 // Daily cycle
        const weeklyPattern = dayOfWeek < 5 ? 10 : -10 // Weekday vs weekend

        return createMockMetric({
          executionTime: baseValue + dailyPattern + weeklyPattern + Math.random() * 5,
          timestamp: new Date(Date.now() - (24 * 7 - i) * 60 * 60 * 1000)
        })
      })

      const seasonality = timeSeriesAnalytics.detectSeasonality(seasonalData)

      expect(seasonality.patterns.daily.detected).toBe(true)
      expect(seasonality.patterns.weekly.detected).toBe(true)
      expect(seasonality.patterns.daily.strength).toBeGreaterThan(0.5)
      expect(seasonality.decomposition.trend).toHaveLength(seasonalData.length)
      expect(seasonality.decomposition.seasonal).toHaveLength(seasonalData.length)
    })

    it('should provide forecast accuracy metrics and confidence bands', () => {
      const trainingData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 0.5 + Math.random() * 10, // Linear trend with noise
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const testData = Array.from({ length: 20 }, (_, i) =>
        createMockMetric({
          executionTime: 150 + i * 0.5 + Math.random() * 10,
          timestamp: new Date(Date.now() + i * 60000)
        })
      )

      const forecast = timeSeriesAnalytics.generateForecast(trainingData, 20)
      const accuracy = timeSeriesAnalytics.evaluateForecastAccuracy(forecast, testData)

      expect(accuracy.mae).toBeGreaterThan(0)
      expect(accuracy.mape).toBeGreaterThan(0) // Mean Absolute Percentage Error
      expect(accuracy.coverageRatio).toBeGreaterThanOrEqual(0) // How often actual values fall within confidence bands
      expect(accuracy.coverageRatio).toBeLessThanOrEqual(1)
      expect(accuracy.sharpness).toBeGreaterThan(0) // Average width of confidence intervals
    })
  })

  describe('Advanced Anomaly Detection', () => {
    it('should detect statistical anomalies using multiple algorithms', () => {
      const normalData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({ executionTime: 100 + (i % 20) }) // More predictable pattern
      )

      const anomalousData = [
        ...normalData,
        createMockMetric({ executionTime: 500 }), // Statistical outlier (high)
        createMockMetric({ executionTime: 1 }),   // Extremely fast (low)
      ]

      const anomalies = timeSeriesAnalytics.detectAnomalies(anomalousData)

      expect(anomalies.length).toBeGreaterThanOrEqual(1) // Should detect at least the high anomaly
      expect(anomalies[0].detectionMethod).toContain('isolation_forest')
      expect(anomalies[0].anomalyScore).toBeGreaterThan(0.8)
      expect(anomalies[0].severity).toBe('high')
      expect(anomalies[0].explanation).toContain('statistical outlier')
    })

    it('should classify different types of anomalies', () => {
      const timeSeriesData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: i < 50 ? 100 : 200, // Step change at midpoint
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const anomalies = timeSeriesAnalytics.detectAnomalies(timeSeriesData)

      const stepChange = anomalies.find(a => a.type === 'step_change')
      expect(stepChange).toBeDefined()
      expect(stepChange?.changePoint).toBeCloseTo(50, -1) // Allow ±5 difference (precision -1 means ±5)
      expect(stepChange?.magnitude).toBeGreaterThan(70) // Step change magnitude should be substantial
      expect(stepChange?.magnitude).toBeLessThan(120)
    })

    it('should provide contextual anomaly explanations', () => {
      const contextualData = Array.from({ length: 48 }, (_, i) => {
        const hour = i % 24
        const isBusinessHours = hour >= 9 && hour <= 17
        const expectedValue = isBusinessHours ? 150 : 50

        return createMockMetric({
          executionTime: i === 25 ? 200 : expectedValue, // Anomaly at 1 AM (usually low traffic)
          timestamp: new Date(Date.now() - (48 - i) * 60 * 60 * 1000)
        })
      })

      const anomalies = timeSeriesAnalytics.detectContextualAnomalies(contextualData)

      expect(anomalies).toHaveLength(1)
      expect(anomalies[0].context.expectedPattern).toBe('low_traffic_hours')
      expect(anomalies[0].context.actualValue).toBe(200)
      expect(anomalies[0].context.expectedRange.max).toBeLessThan(100)
    })
  })

  describe('Interactive Dashboard Features', () => {
    it('should support multi-metric correlation analysis', () => {
      const correlatedData = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 0.5,
          responseSize: 1000 + i * 10, // Correlated with execution time
          timestamp: new Date(Date.now() - (100 - i) * 60000)
        })
      )

      const correlation = timeSeriesAnalytics.calculateCorrelationMatrix(correlatedData)

      expect(correlation.matrix.executionTime_responseSize).toBeGreaterThan(0.8)
      expect(correlation.significantCorrelations).toHaveLength(1)
      expect(correlation.significantCorrelations[0].strength).toBe('strong')
    })

    it('should generate drill-down reports for selected time periods', () => {
      const detailedData = Array.from({ length: 1000 }, (_, i) =>
        createMockMetric({
          query: `query_${i % 10}`,
          executionTime: 100 + Math.random() * 50,
          timestamp: new Date(Date.now() - (1000 - i) * 60000)
        })
      )

      const startTime = new Date(Date.now() - 100 * 60000)
      const endTime = new Date(Date.now() - 50 * 60000)

      const report = timeSeriesAnalytics.generateDrillDownReport(detailedData, startTime, endTime)

      expect(report.summary.totalQueries).toBe(51) // Inclusive range: 100-50 = 50 + 1
      expect(report.topQueries).toHaveLength(10)
      expect(report.performanceBreakdown.byQueryType).toBeDefined()
      expect(report.timeDistribution.hourlyBreakdown).toBeDefined()
    })

    it('should support real-time alerting based on streaming analytics', () => {
      const analytics = new TimeSeriesAnalytics()
      const alertRules = [
        {
          metric: 'executionTime',
          threshold: 150,
          operator: 'greater_than',
          windowSize: 5,
          severity: 'warning'
        }
      ]

      analytics.configureRealTimeAlerts(alertRules)

      // Simulate streaming data that should trigger alert
      const streamData = Array.from({ length: 10 }, () =>
        createMockMetric({ executionTime: 200 })
      )

      const alerts = analytics.processStreamForAlerts(streamData)

      expect(alerts).toHaveLength(1)
      expect(alerts[0].rule.metric).toBe('executionTime')
      expect(alerts[0].triggeredAt).toBeInstanceOf(Date)
      expect(alerts[0].severity).toBe('warning')
    })
  })
})
