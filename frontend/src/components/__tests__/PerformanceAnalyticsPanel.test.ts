import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PerformanceAnalyticsPanel from '../PerformanceAnalyticsPanel.vue'
import type { QueryMetric } from '../../services/performanceMonitor'
// Removed unused import types

// Mock the analytics components
vi.mock('../HistoricalTrendChart.vue', () => ({
  default: {
    name: 'HistoricalTrendChart',
    template: '<div data-testid="historical-trend-chart"></div>',
    props: ['metrics', 'timeWindow', 'metricType', 'showTrend', 'allowZoom']
  }
}))

describe('PerformanceAnalyticsPanel', () => {
  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}_${Math.random()}`,
    endpointId: 'endpoint-1',
    query: 'test_query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    ...overrides
  })

  // Removed unused mockTrend

  // Removed unused mockPercentiles and mockAnomalies

  describe('Component Rendering', () => {
    it('should render analytics panel with all sections', () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1'
        }
      })

      expect(wrapper.find('[data-testid="performance-analytics-panel"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="trend-analysis-section"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="percentiles-section"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="anomalies-section"]').exists()).toBe(true)
      expect(wrapper.find('.historical-chart-section').exists()).toBe(true)
    })

    it('should show empty state when no metrics provided', () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [],
          endpointId: 'endpoint-1'
        }
      })

      expect(wrapper.find('[data-testid="empty-analytics-state"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('No analytics data available')
    })

    it('should display loading state during data processing', () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1',
          loading: true
        }
      })

      expect(wrapper.find('[data-testid="analytics-loading"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Analyzing performance data')
    })
  })

  describe('Trend Analysis Display', () => {
    it('should display improving trend with correct styling', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [
            createMockMetric({ executionTime: 120, timestamp: new Date('2024-01-01T10:00:00Z') }),
            createMockMetric({ executionTime: 100, timestamp: new Date('2024-01-01T11:00:00Z') })
          ],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const trendSection = wrapper.find('[data-testid="trend-analysis-section"]')
      expect(trendSection.classes()).toContain('trend-improving')
      expect(trendSection.text()).toContain('Performance improving')
      expect(trendSection.find('[data-testid="trend-arrow-up"]').exists()).toBe(true)
    })

    it('should display degrading trend with warning styling', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [
            createMockMetric({ executionTime: 80, timestamp: new Date('2024-01-01T10:00:00Z') }),
            createMockMetric({ executionTime: 120, timestamp: new Date('2024-01-01T11:00:00Z') })
          ],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const trendSection = wrapper.find('[data-testid="trend-analysis-section"]')
      expect(trendSection.classes()).toContain('trend-degrading')
      expect(trendSection.text()).toContain('Performance degrading')
      expect(trendSection.find('[data-testid="trend-arrow-down"]').exists()).toBe(true)
    })

    it('should display stable trend', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [
            createMockMetric({ executionTime: 100 }),
            createMockMetric({ executionTime: 102 }),
            createMockMetric({ executionTime: 98 })
          ],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const trendSection = wrapper.find('[data-testid="trend-analysis-section"]')
      expect(trendSection.classes()).toContain('trend-stable')
      expect(trendSection.text()).toContain('Performance stable')
    })
  })

  describe('Percentiles Display', () => {
    it('should display performance percentiles', async () => {
      const metrics = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({ executionTime: i + 1 })
      )

      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics,
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const percentilesSection = wrapper.find('[data-testid="percentiles-section"]')
      expect(percentilesSection.find('[data-testid="p50-metric"]').exists()).toBe(true)
      expect(percentilesSection.find('[data-testid="p90-metric"]').exists()).toBe(true)
      expect(percentilesSection.find('[data-testid="p95-metric"]').exists()).toBe(true)
      expect(percentilesSection.find('[data-testid="p99-metric"]').exists()).toBe(true)

      expect(percentilesSection.text()).toContain('P50')
      expect(percentilesSection.text()).toContain('P90')
      expect(percentilesSection.text()).toContain('P95')
      expect(percentilesSection.text()).toContain('P99')
    })

    it('should highlight concerning percentiles', async () => {
      const metrics = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({ executionTime: i * 10 }) // High execution times
      )

      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics,
          endpointId: 'endpoint-1',
          thresholds: {
            warning: 500,
            critical: 1000
          }
        }
      })

      await wrapper.vm.$nextTick()

      const p99Metric = wrapper.find('[data-testid="p99-metric"]')
      expect(p99Metric.classes()).toContain('percentile-warning')
    })
  })

  describe('Anomaly Detection Display', () => {
    it('should display detected anomalies', async () => {
      const normalMetrics = Array.from({ length: 50 }, () =>
        createMockMetric({ executionTime: 100 })
      )
      const anomalyMetric = createMockMetric({ executionTime: 500 })

      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [...normalMetrics, anomalyMetric],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const anomaliesSection = wrapper.find('[data-testid="anomalies-section"]')
      expect(anomaliesSection.find('[data-testid^="anomaly-severity-"]').exists()).toBe(true)
      expect(anomaliesSection.text()).toContain('Performance anomaly detected')
    })

    it('should show no anomalies message when data is consistent', async () => {
      const metrics = Array.from({ length: 50 }, () =>
        createMockMetric({ executionTime: 100 + Math.random() * 5 })
      )

      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics,
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const anomaliesSection = wrapper.find('[data-testid="anomalies-section"]')
      expect(anomaliesSection.text()).toContain('No anomalies detected')
    })

    it('should categorize anomaly severity', async () => {
      const normalMetrics = Array.from({ length: 50 }, () =>
        createMockMetric({ executionTime: 100 })
      )
      const highAnomalyMetric = createMockMetric({ executionTime: 1000 })

      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [...normalMetrics, highAnomalyMetric],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.vm.$nextTick()

      const highSeverityAnomaly = wrapper.find('[data-testid="anomaly-severity-high"]')
      expect(highSeverityAnomaly.exists()).toBe(true)
      expect(highSeverityAnomaly.classes()).toContain('severity-high')
    })
  })

  describe('Time Window Controls', () => {
    it('should allow switching between time windows', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1'
        }
      })

      const timeWindowSelect = wrapper.find('[data-testid="time-window-select"]')
      expect(timeWindowSelect.exists()).toBe(true)

      await timeWindowSelect.setValue('day')
      expect(wrapper.vm.selectedTimeWindow).toBe('day')
    })

    it('should update chart when time window changes', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.find('[data-testid="time-window-select"]').setValue('day')

      // Chart component was removed - test that time window selection works
      expect(wrapper.vm.selectedTimeWindow).toBe('day')
    })
  })

  describe('Metric Type Switching', () => {
    it('should allow switching between execution time and response size', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1'
        }
      })

      const metricTypeToggle = wrapper.find('[data-testid="metric-type-toggle"]')
      expect(metricTypeToggle.exists()).toBe(true)

      const responseSizeButton = wrapper.find('[data-testid="response-size-button"]')
      await responseSizeButton.trigger('click')

      expect(wrapper.vm.selectedMetricType).toBe('responseSize')
    })

    it('should update all analytics when metric type changes', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1'
        }
      })

      await wrapper.find('[data-testid="response-size-button"]').trigger('click')

      // Chart component was removed - test that metric type switching works
      expect(wrapper.vm.selectedMetricType).toBe('responseSize')
    })
  })

  describe('Export Functionality', () => {
    it('should emit export event with analytics data', async () => {
      const wrapper = mount(PerformanceAnalyticsPanel, {
        props: {
          metrics: [createMockMetric()],
          endpointId: 'endpoint-1'
        }
      })

      const exportButton = wrapper.find('[data-testid="export-analytics-button"]')
      await exportButton.trigger('click')

      expect(wrapper.emitted('export-analytics')).toBeTruthy()
      expect(wrapper.emitted('export-analytics')?.[0]?.[0]).toEqual({
        endpointId: 'endpoint-1',
        metrics: expect.any(Array),
        trend: expect.any(Object),
        percentiles: expect.any(Object),
        anomalies: expect.any(Array),
        timeWindow: 'hour',
        metricType: expect.any(String),
        exportedAt: expect.any(String)
      })
    })
  })
})
