import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import RealTimeAnalyticsDashboard from '../RealTimeAnalyticsDashboard.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Mock WebSocket and real-time services
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: 1 // OPEN
}

global.WebSocket = vi.fn(() => mockWebSocket) as any

describe('RealTimeAnalyticsDashboard', () => {
  let wrapper: any
  let mockTimeSeriesAnalytics: any

  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}`,
    query: 'test query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    endpointId: 'endpoint-1',
    ...overrides
  })

  beforeEach(() => {
    mockTimeSeriesAnalytics = {
      processStreamingData: vi.fn(() => ({
        dataPoints: [],
        smoothedTrend: [],
        realtimeStatistics: {
          currentRate: 10,
          averageLatency: 120,
          errorRate: 0.02
        },
        qualityMetrics: {
          invalidDataPoints: 0,
          outlierCount: 1,
          completenessRatio: 0.98
        }
      })),
      detectAnomalies: vi.fn(() => []),
      generateForecast: vi.fn(() => ({
        predictions: [],
        modelAccuracy: { mae: 5.2, rmse: 8.1 }
      })),
      addDataPoint: vi.fn(),
      getBuffer: vi.fn(() => [])
    }

    wrapper = mount(RealTimeAnalyticsDashboard, {
      props: {
        endpointId: 'test-endpoint',
        autoRefresh: true,
        refreshInterval: 1000
      },
      global: {
        provide: {
          timeSeriesAnalytics: mockTimeSeriesAnalytics
        }
      }
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Real-time Data Streaming', () => {
    it('should establish WebSocket connection for live data', () => {
      expect(wrapper.vm.wsConnection).toBeDefined()
      expect(wrapper.vm.connectionStatus).toBe('connected')
      expect(wrapper.find('[data-testid="connection-status"]').text()).toContain('Connected')
    })

    it('should handle incoming streaming data and update charts', async () => {
      const streamingData = Array.from({ length: 5 }, () => createMockMetric())

      wrapper.vm.handleStreamingData(streamingData)
      await nextTick()

      expect(mockTimeSeriesAnalytics.processStreamingData).toHaveBeenCalledWith(streamingData)
      expect(wrapper.vm.realtimeBuffer.length).toBeGreaterThan(0)
      expect(wrapper.emitted('data-received')).toBeTruthy()
    })

    it('should maintain connection health and auto-reconnect on failures', async () => {
      // Simulate connection loss
      wrapper.vm.handleConnectionLoss()

      expect(wrapper.vm.connectionStatus).toBe('reconnecting')
      expect(wrapper.find('[data-testid="connection-status"]').classes()).toContain('text-yellow-500')

      // Wait for reconnection attempt
      await new Promise(resolve => setTimeout(resolve, 1100))

      expect(wrapper.vm.reconnectAttempts).toBe(1)
      expect(wrapper.vm.connectionStatus).toBe('connected')
    })

    it('should buffer data during disconnection and replay on reconnect', async () => {
      const offlineData = Array.from({ length: 10 }, () => createMockMetric())

      wrapper.vm.connectionStatus = 'disconnected'

      for (const data of offlineData) {
        wrapper.vm.bufferOfflineData(data)
      }

      expect(wrapper.vm.offlineBuffer.length).toBe(10)

      // Reconnect and replay
      wrapper.vm.handleReconnection()
      await nextTick()

      expect(wrapper.vm.offlineBuffer.length).toBe(0)
      expect(mockTimeSeriesAnalytics.processStreamingData).toHaveBeenCalledWith(offlineData)
    })
  })

  describe('Live Performance Metrics Display', () => {
    it('should display real-time key performance indicators', async () => {
      const kpiData = {
        currentThroughput: 150.5,
        averageLatency: 85.2,
        errorRate: 0.015,
        p95Latency: 180.7
      }

      wrapper.vm.updateKPIs(kpiData)
      await nextTick()

      expect(wrapper.find('[data-testid="throughput-kpi"]').text()).toContain('150.5')
      expect(wrapper.find('[data-testid="latency-kpi"]').text()).toContain('85.2')
      expect(wrapper.find('[data-testid="error-rate-kpi"]').text()).toContain('1.5%')
      expect(wrapper.find('[data-testid="p95-latency-kpi"]').text()).toContain('180.7')
    })

    it('should show trending indicators for each KPI', async () => {
      const trendingData = {
        throughput: { current: 150, previous: 140, trend: 'increasing' },
        latency: { current: 85, previous: 95, trend: 'decreasing' },
        errorRate: { current: 0.015, previous: 0.02, trend: 'decreasing' }
      }

      wrapper.vm.updateTrends(trendingData)
      await nextTick()

      expect(wrapper.find('[data-testid="throughput-trend"]').classes()).toContain('text-green-500')
      expect(wrapper.find('[data-testid="latency-trend"]').classes()).toContain('text-green-500')
      expect(wrapper.find('[data-testid="error-rate-trend"]').classes()).toContain('text-green-500')

      expect(wrapper.find('[data-testid="throughput-trend"] svg').attributes('data-icon')).toBe('arrow-up')
      expect(wrapper.find('[data-testid="latency-trend"] svg').attributes('data-icon')).toBe('arrow-down')
    })

    it('should highlight metrics that exceed thresholds', async () => {
      const alertingMetrics = {
        latency: { value: 250, threshold: 200, status: 'warning' },
        errorRate: { value: 0.08, threshold: 0.05, status: 'critical' },
        throughput: { value: 50, threshold: 100, status: 'warning' }
      }

      wrapper.vm.checkThresholds(alertingMetrics)
      await nextTick()

      expect(wrapper.find('[data-testid="latency-kpi"]').classes()).toContain('border-yellow-400')
      expect(wrapper.find('[data-testid="error-rate-kpi"]').classes()).toContain('border-red-500')
      expect(wrapper.find('[data-testid="throughput-kpi"]').classes()).toContain('border-yellow-400')
    })
  })

  describe('Interactive Chart Features', () => {
    it('should support multiple simultaneous metric views', async () => {
      await wrapper.setProps({
        metrics: ['executionTime', 'responseSize', 'errorRate'],
        chartLayout: 'grid'
      })

      expect(wrapper.findAll('[data-testid^="metric-chart-"]')).toHaveLength(3)
      expect(wrapper.find('[data-testid="metric-chart-executionTime"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="metric-chart-responseSize"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="metric-chart-errorRate"]').exists()).toBe(true)
    })

    it('should allow synchronized zooming across multiple charts', async () => {
      const timeRange = {
        start: new Date(Date.now() - 30 * 60000),
        end: new Date(Date.now() - 10 * 60000)
      }

      wrapper.vm.synchronizeZoom(timeRange)
      await nextTick()

      expect(wrapper.vm.globalTimeRange).toEqual(timeRange)
      expect(wrapper.emitted('time-range-changed')).toBeTruthy()
      expect(wrapper.emitted('time-range-changed')[0][0]).toEqual(timeRange)
    })

    it('should provide chart overlay controls for statistical analysis', async () => {
      const overlayConfig = {
        movingAverage: { enabled: true, window: 20 },
        percentileBands: { enabled: true, percentiles: [25, 75, 95] },
        anomalyHighlights: { enabled: true, threshold: 2.5 },
        trendLine: { enabled: true, method: 'linear' }
      }

      wrapper.vm.configureOverlays(overlayConfig)
      await nextTick()

      expect(wrapper.vm.chartOverlays).toEqual(overlayConfig)
      expect(wrapper.find('[data-testid="overlay-moving-average"]').classes()).toContain('bg-blue-100')
      expect(wrapper.find('[data-testid="overlay-percentile-bands"]').classes()).toContain('bg-blue-100')
    })
  })

  describe('Predictive Analytics Integration', () => {
    it('should display forecast predictions with confidence intervals', async () => {
      const forecastData = {
        predictions: Array.from({ length: 24 }, (_, i) => ({
          timestamp: new Date(Date.now() + i * 60 * 60 * 1000),
          predictedValue: 100 + Math.sin(i * 0.1) * 10,
          confidenceInterval: { lower: 80, upper: 120 }
        })),
        modelAccuracy: { mae: 5.2, rmse: 8.1, confidence: 0.85 }
      }

      wrapper.vm.updateForecast(forecastData)
      await nextTick()

      expect(wrapper.find('[data-testid="forecast-display"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="forecast-accuracy"]').text()).toContain('85%')
      expect(wrapper.vm.forecastData.predictions).toHaveLength(24)
    })

    it('should trigger alerts based on forecast predictions', async () => {
      const alertingForecast = {
        predictions: [
          { predictedValue: 250, threshold: 200, exceedsThreshold: true },
          { predictedValue: 180, threshold: 200, exceedsThreshold: false }
        ]
      }

      wrapper.vm.analyzeForecastAlerts(alertingForecast)
      await nextTick()

      expect(wrapper.vm.forecastAlerts).toHaveLength(1)
      expect(wrapper.emitted('forecast-alert')).toBeTruthy()
      expect(wrapper.find('[data-testid="forecast-alert-badge"]').exists()).toBe(true)
    })

    it('should show model performance metrics and retraining indicators', async () => {
      const modelMetrics = {
        accuracy: 0.78,
        lastRetrained: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        trainingDataPoints: 10000,
        modelAge: '2 days',
        recommendRetraining: true
      }

      wrapper.vm.updateModelMetrics(modelMetrics)
      await nextTick()

      expect(wrapper.find('[data-testid="model-accuracy"]').text()).toContain('78%')
      expect(wrapper.find('[data-testid="model-age"]').text()).toContain('2 days')
      expect(wrapper.find('[data-testid="retrain-recommendation"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="retrain-recommendation"]').classes()).toContain('text-orange-500')
    })
  })

  describe('Anomaly Detection and Alerting', () => {
    it('should detect and highlight real-time anomalies', async () => {
      const anomalies = [
        {
          timestamp: new Date(),
          metric: 'executionTime',
          value: 500,
          severity: 'high',
          anomalyScore: 0.95,
          explanation: 'Execution time significantly above normal range'
        }
      ]

      wrapper.vm.handleAnomalyDetection(anomalies)
      await nextTick()

      expect(wrapper.vm.currentAnomalies).toHaveLength(1)
      expect(wrapper.find('[data-testid="anomaly-alert"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="anomaly-severity"]').classes()).toContain('bg-red-500')
      expect(wrapper.emitted('anomaly-detected')).toBeTruthy()
    })

    it('should provide anomaly investigation tools', async () => {
      const investigationData = {
        anomalyId: 'anomaly-123',
        affectedQueries: ['query1', 'query2'],
        timeRange: { start: new Date(), end: new Date() },
        correlatedMetrics: ['responseSize', 'errorRate'],
        rootCauseHypotheses: ['database slowdown', 'memory pressure']
      }

      wrapper.vm.investigateAnomaly(investigationData)
      await nextTick()

      expect(wrapper.vm.activeInvestigation).toEqual(investigationData)
      expect(wrapper.find('[data-testid="investigation-panel"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="affected-queries"]').text()).toContain('query1')
      expect(wrapper.find('[data-testid="root-cause-hypotheses"]').exists()).toBe(true)
    })

    it('should maintain anomaly history and patterns', () => {
      const historicalAnomalies = Array.from({ length: 50 }, (_, i) => ({
        id: `anomaly-${i}`,
        timestamp: new Date(Date.now() - i * 60 * 60 * 1000),
        severity: ['low', 'medium', 'high'][i % 3],
        resolved: i % 4 !== 0
      }))

      wrapper.vm.loadAnomalyHistory(historicalAnomalies)

      expect(wrapper.vm.anomalyHistory).toHaveLength(50)
      expect(wrapper.vm.anomalyPatterns.dailyFrequency).toBeDefined()
      expect(wrapper.vm.anomalyPatterns.commonTypes).toBeDefined()
      expect(wrapper.vm.anomalyPatterns.resolutionRate).toBeCloseTo(0.75, 1)
    })
  })

  describe('Dashboard Customization and Configuration', () => {
    it('should support drag-and-drop widget arrangement', async () => {
      const widgetLayout = [
        { id: 'kpi-panel', x: 0, y: 0, w: 6, h: 2 },
        { id: 'main-chart', x: 0, y: 2, w: 8, h: 4 },
        { id: 'anomaly-feed', x: 8, y: 0, w: 4, h: 6 }
      ]

      wrapper.vm.updateLayout(widgetLayout)
      await nextTick()

      expect(wrapper.vm.dashboardLayout).toEqual(widgetLayout)
      expect(wrapper.emitted('layout-changed')).toBeTruthy()
    })

    it('should save and restore user preferences', async () => {
      const userPreferences = {
        defaultTimeRange: '1hour',
        preferredMetrics: ['executionTime', 'errorRate'],
        chartColors: { executionTime: '#3b82f6', errorRate: '#ef4444' },
        alertThresholds: { latency: 200, errorRate: 0.05 },
        refreshInterval: 5000
      }

      wrapper.vm.savePreferences(userPreferences)
      await nextTick()

      expect(localStorage.getItem('dashboard-preferences')).toBeTruthy()

      wrapper.vm.loadPreferences()
      expect(wrapper.vm.userPreferences).toEqual(userPreferences)
    })

    it('should support multiple dashboard themes', async () => {
      await wrapper.setProps({ theme: 'dark' })

      expect(wrapper.find('.dashboard-container').classes()).toContain('dark-theme')
      expect(wrapper.vm.chartOptions.plugins.legend.labels.color).toBe('#ffffff')

      await wrapper.setProps({ theme: 'light' })

      expect(wrapper.find('.dashboard-container').classes()).toContain('light-theme')
      expect(wrapper.vm.chartOptions.plugins.legend.labels.color).toBe('#374151')
    })
  })

  describe('Performance and Optimization', () => {
    it('should implement efficient data buffering for high-frequency updates', async () => {
      const highFrequencyData = Array.from({ length: 1000 }, () => createMockMetric())

      // Simulate rapid data ingestion
      for (let i = 0; i < 1000; i++) {
        wrapper.vm.addDataPoint(highFrequencyData[i])
      }

      expect(wrapper.vm.dataBuffer.length).toBeLessThanOrEqual(500) // Buffer limit
      expect(wrapper.vm.updateQueue.length).toBeLessThanOrEqual(10) // Update batching
    })

    it('should use requestAnimationFrame for smooth visual updates', async () => {
      const rafSpy = vi.spyOn(window, 'requestAnimationFrame')

      wrapper.vm.scheduleChartUpdate()

      expect(rafSpy).toHaveBeenCalled()
      expect(wrapper.vm.pendingUpdates).toBe(true)
    })

    it('should implement memory management for long-running sessions', async () => {
      // Simulate 24 hours of data
      for (let i = 0; i < 1440; i++) { // 1440 minutes
        wrapper.vm.addDataPoint(createMockMetric({
          timestamp: new Date(Date.now() - (1440 - i) * 60000)
        }))
      }

      wrapper.vm.performMemoryCleanup()

      expect(wrapper.vm.totalDataPoints).toBeLessThanOrEqual(1000) // Memory limit
      expect(wrapper.vm.memoryUsage.dataPoints).toBeLessThan(10000) // Bytes estimate
    })
  })
})
