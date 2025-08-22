export interface QueryMetrics {
  executionTime: number
  responseSize: number
  timestamp: Date
}

export interface QueryMetric {
  id: string
  endpointId: string
  query: string
  executionTime: number
  responseSize: number
  timestamp: Date
  errors?: string[] | null
}

export interface PerformanceMonitorOptions {
  maxMetrics?: number
  analyticsEndpoint?: string
  enableAnalytics?: boolean
}

export class PerformanceMonitor extends EventTarget {
  private metrics: QueryMetric[] = []
  private options: Required<PerformanceMonitorOptions>

  constructor(options: PerformanceMonitorOptions = {}) {
    super()
    this.options = {
      maxMetrics: options.maxMetrics ?? 1000,
      analyticsEndpoint: options.analyticsEndpoint ?? '/api/analytics/metrics',
      enableAnalytics: options.enableAnalytics ?? (typeof window !== 'undefined' && window.location.origin !== 'http://localhost:3000')
    }
  }

  async trackQuery(endpointId: string, query: string, metrics: QueryMetrics): Promise<void> {
    const metric: QueryMetric = {
      id: this.generateId(),
      endpointId,
      query,
      executionTime: metrics.executionTime,
      responseSize: metrics.responseSize,
      timestamp: metrics.timestamp
    }

    // Add to local storage
    this.metrics.push(metric)

    // Enforce retention limit
    if (this.metrics.length > this.options.maxMetrics) {
      this.metrics.shift()
    }

    // Dispatch event
    this.dispatchEvent(new CustomEvent('metric-recorded', {
      detail: metric
    }))

    // Send to analytics backend
    if (this.options.enableAnalytics) {
      await this.sendToAnalytics(metric)
    }
  }

  getMetrics(endpointId: string): QueryMetric[] {
    return this.metrics.filter(metric => metric.endpointId === endpointId)
  }

  getAverageResponseTime(endpointId: string): number {
    const endpointMetrics = this.getMetrics(endpointId)
    if (endpointMetrics.length === 0) return 0

    const totalTime = endpointMetrics.reduce((sum, metric) => sum + metric.executionTime, 0)
    return totalTime / endpointMetrics.length
  }

  getMetricsInRange(endpointId: string, startTime: Date, endTime: Date): QueryMetric[] {
    return this.metrics.filter(metric =>
      metric.endpointId === endpointId &&
      metric.timestamp >= startTime &&
      metric.timestamp <= endTime
    )
  }

  private generateId(): string {
    return `metric_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private async sendToAnalytics(metric: QueryMetric): Promise<void> {
    try {
      // Build full URL if needed
      let url = this.options.analyticsEndpoint
      if (url.startsWith('/') && typeof window !== 'undefined') {
        url = window.location.origin + url
      }

      await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(metric)
      })
    } catch (error) {
      console.warn('Failed to send metrics to analytics:', error)
    }
  }
}
