import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PerformanceAnalyticsPanel from '../PerformanceAnalyticsPanel.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Mock the HistoricalTrendChart component
vi.mock('../HistoricalTrendChart.vue', () => ({
  default: {
    name: 'HistoricalTrendChart',
    template: '<div data-testid="historical-trend-chart"></div>',
    props: ['metrics', 'timeWindow', 'metricType', 'showTrend', 'allowZoom']
  }
}))

describe('PerformanceAnalyticsPanel - Simple Tests', () => {
  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}_${Math.random()}`,
    endpointId: 'endpoint-1',
    query: 'test_query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    ...overrides
  })

  it('should render analytics panel', () => {
    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics: [],
        endpointId: 'endpoint-1'
      }
    })

    expect(wrapper.find('[data-testid="performance-analytics-panel"]').exists()).toBe(true)
  })

  it('should show empty state when no metrics', () => {
    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics: [],
        endpointId: 'endpoint-1'
      }
    })

    expect(wrapper.find('[data-testid="empty-analytics-state"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('No analytics data available')
  })

  it('should show loading state', () => {
    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics: [],
        endpointId: 'endpoint-1',
        loading: true
      }
    })

    expect(wrapper.find('[data-testid="analytics-loading"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Analyzing performance data')
  })

  it('should display analytics dashboard with metrics', async () => {
    const metrics = Array.from({ length: 20 }, (_, i) =>
      createMockMetric({
        executionTime: 100 + i * 5,
        timestamp: new Date(Date.now() - i * 60000) // 1 minute apart
      })
    )

    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics,
        endpointId: 'endpoint-1'
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="trend-analysis-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="percentiles-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="anomalies-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="historical-trend-chart"]').exists()).toBe(true)
  })

  it('should calculate and display trend analysis', async () => {
    const metrics = [
      createMockMetric({
        executionTime: 120,
        timestamp: new Date('2024-01-01T10:00:00Z')
      }),
      createMockMetric({
        executionTime: 100,
        timestamp: new Date('2024-01-01T11:00:00Z')
      })
    ]

    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics,
        endpointId: 'endpoint-1'
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.vm.trendAnalysis).toBeTruthy()
    expect((wrapper.vm as any).trendAnalysis?.direction).toBe('improving')
    expect(wrapper.text()).toContain('Performance improving')
  })

  it('should calculate percentiles', async () => {
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

    expect(wrapper.vm.percentiles).toBeTruthy()
    expect(wrapper.vm.percentiles.p50).toBeCloseTo(50.5, 1)
    expect(wrapper.vm.percentiles.p90).toBeCloseTo(90.1, 1)
    expect(wrapper.vm.percentiles.p95).toBeCloseTo(95.05, 1)
    expect(wrapper.vm.percentiles.p99).toBeCloseTo(99.01, 1)
  })

  it('should detect anomalies', async () => {
    const normalMetrics = Array.from({ length: 50 }, () =>
      createMockMetric({ executionTime: 100 + Math.random() * 10 })
    )
    const anomalyMetric = createMockMetric({ executionTime: 300 })

    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics: [...normalMetrics, anomalyMetric],
        endpointId: 'endpoint-1'
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.vm.anomalies).toBeTruthy()
    expect(wrapper.vm.anomalies.length).toBeGreaterThan(0)
    expect(wrapper.vm.anomalies[0].metric.executionTime).toBe(300)
  })

  it('should allow metric type switching', async () => {
    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics: [createMockMetric()],
        endpointId: 'endpoint-1'
      }
    })

    expect(wrapper.vm.selectedMetricType).toBe('executionTime')

    const responseSizeButton = wrapper.find('[data-testid="response-size-button"]')
    await responseSizeButton.trigger('click')

    expect(wrapper.vm.selectedMetricType).toBe('responseSize')
  })

  it('should allow time window switching', async () => {
    const wrapper = mount(PerformanceAnalyticsPanel, {
      props: {
        metrics: [createMockMetric()],
        endpointId: 'endpoint-1'
      }
    })

    expect(wrapper.vm.selectedTimeWindow).toBe('hour')

    const timeWindowSelect = wrapper.find('[data-testid="time-window-select"]')
    await timeWindowSelect.setValue('day')

    expect(wrapper.vm.selectedTimeWindow).toBe('day')
  })

  it('should emit export analytics event', async () => {
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
      metricType: 'executionTime',
      exportedAt: expect.any(String)
    })
  })
})
