import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import HistoricalTrendChart from '../HistoricalTrendChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Simple Chart.js mock
vi.mock('chart.js/auto', () => ({
  Chart: vi.fn().mockImplementation(() => ({
    destroy: vi.fn(),
    update: vi.fn(),
    data: {},
    options: {}
  }))
}))

vi.mock('chartjs-plugin-zoom', () => ({
  default: {}
}))

describe('HistoricalTrendChart - Simple Tests', () => {
  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}_${Math.random()}`,
    endpointId: 'endpoint-1',
    query: 'test_query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    ...overrides
  })

  it('should render component', () => {
    const wrapper = mount(HistoricalTrendChart, {
      props: {
        metrics: [],
        timeWindow: 'hour' as const,
        metricType: 'executionTime' as const
      }
    })

    expect(wrapper.find('[data-testid="historical-trend-chart"]').exists()).toBe(true)
  })

  it('should show empty state when no metrics', () => {
    const wrapper = mount(HistoricalTrendChart, {
      props: {
        metrics: [],
        timeWindow: 'hour' as const,
        metricType: 'executionTime' as const
      }
    })

    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('No historical data available')
  })

  it('should show loading state', () => {
    const wrapper = mount(HistoricalTrendChart, {
      props: {
        metrics: [],
        timeWindow: 'hour' as const,
        metricType: 'executionTime' as const,
        loading: true
      }
    })

    expect(wrapper.find('[data-testid="loading-state"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Loading historical data')
  })

  it('should handle metrics data', () => {
    const metrics = [
      createMockMetric({ executionTime: 100 }),
      createMockMetric({ executionTime: 120 })
    ]

    const wrapper = mount(HistoricalTrendChart, {
      props: {
        metrics,
        timeWindow: 'hour' as const,
        metricType: 'executionTime' as const
      }
    })

    expect(wrapper.vm.aggregatedData.length).toBeGreaterThan(0)
  })

  it('should calculate trend analysis', () => {
    const metrics = [
      createMockMetric({
        executionTime: 100,
        timestamp: new Date('2024-01-01T10:00:00Z')
      }),
      createMockMetric({
        executionTime: 80,
        timestamp: new Date('2024-01-01T11:00:00Z')
      })
    ]

    const wrapper = mount(HistoricalTrendChart, {
      props: {
        metrics,
        timeWindow: 'hour' as const,
        metricType: 'executionTime' as const,
        showTrend: true
      }
    })

    expect(wrapper.vm.trendAnalysis).toBeTruthy()
    expect(wrapper.vm.trendAnalysis.direction).toBe('improving')
  })
})
