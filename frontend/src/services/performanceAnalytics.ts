import type { QueryMetric } from './performanceMonitor'

export interface PerformanceTrend {
  direction: 'improving' | 'degrading' | 'stable'
  slope: number
  confidence: number
  changePercentage: number
}

export interface TimeAggregation {
  window: string
  avgExecutionTime: number
  avgResponseSize: number
  count: number
  timestamp: Date
}

export interface Percentiles {
  p50: number
  p90: number
  p95: number
  p99: number
}

export interface Anomaly {
  metric: QueryMetric
  severity: 'low' | 'medium' | 'high'
  deviationScore: number
  expectedValue: number
  detectedAt: Date
}

export interface ForecastPoint {
  timestamp: Date
  predictedValue: number
  confidence: number
  upperBound: number
  lowerBound: number
}

export type TimeWindow = 'hour' | 'day' | 'week' | 'month'
export type MetricField = 'executionTime' | 'responseSize'

export class PerformanceAnalytics {
  /**
   * Calculate performance trend over time using linear regression
   */
  calculatePerformanceTrend(metrics: QueryMetric[], field: MetricField): PerformanceTrend {
    if (metrics.length < 2) {
      return {
        direction: 'stable',
        slope: 0,
        confidence: 0,
        changePercentage: 0
      }
    }

    // Sort metrics by timestamp
    const sortedMetrics = [...metrics].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

    // Extract values and timestamps
    const values = sortedMetrics.map(m => m[field])
    const timestamps = sortedMetrics.map(m => m.timestamp.getTime())

    // Calculate linear regression
    const n = values.length
    const sumX = timestamps.reduce((sum, t) => sum + t, 0)
    const sumY = values.reduce((sum, v) => sum + v, 0)
    const sumXY = timestamps.reduce((sum, t, i) => sum + t * values[i], 0)
    const sumXX = timestamps.reduce((sum, t) => sum + t * t, 0)

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)

    // Calculate correlation coefficient for confidence
    const meanX = sumX / n
    const meanY = sumY / n

    const numerator = timestamps.reduce((sum, t, i) => sum + (t - meanX) * (values[i] - meanY), 0)
    const denomX = Math.sqrt(timestamps.reduce((sum, t) => sum + (t - meanX) ** 2, 0))
    const denomY = Math.sqrt(values.reduce((sum, v) => sum + (v - meanY) ** 2, 0))

    const correlation = numerator / (denomX * denomY)
    const confidence = Math.abs(correlation)

    // Calculate percentage change
    const firstValue = values[0]
    const lastValue = values[values.length - 1]
    const changePercentage = ((lastValue - firstValue) / firstValue) * 100

    // Determine direction
    let direction: 'improving' | 'degrading' | 'stable'
    if (Math.abs(changePercentage) < 5) {
      direction = 'stable'
    } else if (field === 'executionTime') {
      // For execution time, lower is better
      direction = changePercentage < 0 ? 'improving' : 'degrading'
    } else {
      // For response size, this depends on context, but generally lower is better
      direction = changePercentage < 0 ? 'improving' : 'degrading'
    }

    return {
      direction,
      slope,
      confidence,
      changePercentage
    }
  }

  /**
   * Aggregate metrics by time window
   */
  aggregateByTimeWindow(metrics: QueryMetric[], timeWindow: TimeWindow): TimeAggregation[] {
    const groupedMetrics = new Map<string, QueryMetric[]>()

    for (const metric of metrics) {
      const windowKey = this.getTimeWindowKey(metric.timestamp, timeWindow)
      if (!groupedMetrics.has(windowKey)) {
        groupedMetrics.set(windowKey, [])
      }
      groupedMetrics.get(windowKey)!.push(metric)
    }

    const aggregations: TimeAggregation[] = []

    for (const [windowKey, windowMetrics] of groupedMetrics) {
      const avgExecutionTime = windowMetrics.reduce((sum, m) => sum + m.executionTime, 0) / windowMetrics.length
      const avgResponseSize = windowMetrics.reduce((sum, m) => sum + m.responseSize, 0) / windowMetrics.length

      aggregations.push({
        window: windowKey,
        avgExecutionTime,
        avgResponseSize,
        count: windowMetrics.length,
        timestamp: new Date(windowKey)
      })
    }

    return aggregations.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
  }

  /**
   * Calculate performance percentiles
   */
  calculatePercentiles(metrics: QueryMetric[], field: MetricField): Percentiles {
    if (metrics.length === 0) {
      return { p50: 0, p90: 0, p95: 0, p99: 0 }
    }

    const values = metrics.map(m => m[field]).sort((a, b) => a - b)

    const getPercentile = (p: number): number => {
      const index = (p / 100) * (values.length - 1)
      const lower = Math.floor(index)
      const upper = Math.ceil(index)

      if (lower === upper) {
        return values[lower]
      }

      const weight = index - lower
      return values[lower] * (1 - weight) + values[upper] * weight
    }

    return {
      p50: getPercentile(50),
      p90: getPercentile(90),
      p95: getPercentile(95),
      p99: getPercentile(99)
    }
  }

  /**
   * Detect performance anomalies using statistical methods
   */
  detectAnomalies(metrics: QueryMetric[], field: MetricField): Anomaly[] {
    if (metrics.length < 10) {
      return [] // Need sufficient data for anomaly detection
    }

    const values = metrics.map(m => m[field])
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length
    const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length
    const stdDev = Math.sqrt(variance)

    const anomalies: Anomaly[] = []

    for (const metric of metrics) {
      const value = metric[field]
      const deviationScore = Math.abs(value - mean) / stdDev

      if (deviationScore > 2) { // More than 2 standard deviations
        let severity: 'low' | 'medium' | 'high'
        if (deviationScore > 3) {
          severity = 'high'
        } else if (deviationScore > 2.5) {
          severity = 'medium'
        } else {
          severity = 'low'
        }

        anomalies.push({
          metric,
          severity,
          deviationScore,
          expectedValue: mean,
          detectedAt: new Date()
        })
      }
    }

    return anomalies.sort((a, b) => b.deviationScore - a.deviationScore)
  }

  /**
   * Generate performance forecast based on historical data
   */
  generatePerformanceForecast(
    metrics: QueryMetric[],
    field: MetricField,
    forecastPoints: number
  ): ForecastPoint[] {
    if (metrics.length < 5) {
      throw new Error('Insufficient data for forecasting')
    }

    // Sort metrics by timestamp
    const sortedMetrics = [...metrics].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

    // Use simple linear trend for forecasting
    const trend = this.calculatePerformanceTrend(sortedMetrics, field)
    const lastMetric = sortedMetrics[sortedMetrics.length - 1]
    const lastValue = lastMetric[field]
    const lastTimestamp = lastMetric.timestamp.getTime()

    // Calculate time interval between measurements
    const timeIntervals = []
    for (let i = 1; i < sortedMetrics.length; i++) {
      timeIntervals.push(
        sortedMetrics[i].timestamp.getTime() - sortedMetrics[i - 1].timestamp.getTime()
      )
    }
    const avgInterval = timeIntervals.reduce((sum, interval) => sum + interval, 0) / timeIntervals.length

    // Calculate prediction uncertainty
    const values = sortedMetrics.map(m => m[field])
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length
    const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length
    const stdDev = Math.sqrt(variance)

    const forecast: ForecastPoint[] = []

    for (let i = 1; i <= forecastPoints; i++) {
      const futureTimestamp = new Date(lastTimestamp + i * avgInterval)
      const timeDelta = i * avgInterval

      // Simple linear prediction
      const predictedValue = lastValue + (trend.slope * timeDelta)

      // Confidence decreases with distance into future
      const confidence = Math.max(0.1, trend.confidence * Math.exp(-i * 0.1))

      // Prediction bounds based on standard deviation and confidence
      const uncertaintyFactor = (1 - confidence) * stdDev * Math.sqrt(i)
      const upperBound = predictedValue + uncertaintyFactor
      const lowerBound = Math.max(0, predictedValue - uncertaintyFactor)

      forecast.push({
        timestamp: futureTimestamp,
        predictedValue: Math.max(0, predictedValue),
        confidence,
        upperBound,
        lowerBound
      })
    }

    return forecast
  }

  /**
   * Get time window key for grouping
   */
  private getTimeWindowKey(timestamp: Date, timeWindow: TimeWindow): string {
    const date = new Date(timestamp)

    switch (timeWindow) {
      case 'hour':
        // Round to the hour
        date.setMinutes(0, 0, 0)
        break
      case 'day':
        // Round to the day
        date.setHours(0, 0, 0, 0)
        break
      case 'week': {
        // Round to the start of the week (Sunday)
        const dayOfWeek = date.getDay()
        date.setDate(date.getDate() - dayOfWeek)
        date.setHours(0, 0, 0, 0)
        break
      }
      case 'month':
        // Round to the start of the month
        date.setDate(1)
        date.setHours(0, 0, 0, 0)
        break
    }

    return date.toISOString()
  }
}
