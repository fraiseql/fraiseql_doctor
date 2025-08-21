import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import HistoricalTrendChart from '../HistoricalTrendChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'
import type { TimeAggregation } from '../../services/performanceAnalytics'

// Mock Chart.js
vi.mock('chart.js/auto', () => {
  const mockChart = {
    destroy: vi.fn(),
    update: vi.fn(),
    data: {},
    options: {},
    getElementsAtEventForMode: vi.fn(() => [])
  }

  const MockChart = vi.fn().mockImplementation(() => mockChart)
  MockChart.register = vi.fn()

  return {
    Chart: MockChart
  }
})

vi.mock('chartjs-plugin-zoom', () => ({
  default: {}
}))

describe('HistoricalTrendChart', () => {
  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}_${Math.random()}`,
    endpointId: 'endpoint-1',
    query: 'test_query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    ...overrides
  })

  const mockAggregations: TimeAggregation[] = [
    {
      window: '2024-01-01T10:00:00.000Z',
      avgExecutionTime: 100,
      avgResponseSize: 1024,
      count: 10,
      timestamp: new Date('2024-01-01T10:00:00.000Z')
    },
    {
      window: '2024-01-01T11:00:00.000Z',
      avgExecutionTime: 120,
      avgResponseSize: 1200,
      count: 15,
      timestamp: new Date('2024-01-01T11:00:00.000Z')
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render chart with historical data', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        }
      })

      expect(wrapper.find('[data-testid="historical-trend-chart"]').exists()).toBe(true)
      expect(wrapper.find('canvas').exists()).toBe(true)
    })

    it('should show empty state when no data is available', () => {
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

    it('should display loading state', () => {
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
  })

  describe('Chart Configuration', () => {
    it('should configure chart for execution time metrics', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        }
      })

      await wrapper.vm.$nextTick()

      // Chart should be created with proper configuration
      const { Chart } = await vi.importMock('chart.js/auto')
      expect(Chart).toHaveBeenCalledWith(
        expect.any(HTMLCanvasElement),
        expect.objectContaining({
          type: 'line',
          options: expect.objectContaining({
            scales: expect.objectContaining({
              y: expect.objectContaining({
                title: expect.objectContaining({
                  text: 'Execution Time (ms)'
                })
              })
            })
          })
        })
      )
    })

    it('should configure chart for response size metrics', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'responseSize' as const
        }
      })

      await wrapper.vm.$nextTick()

      const { Chart } = await vi.importMock('chart.js/auto')
      expect(Chart).toHaveBeenCalledWith(
        expect.any(HTMLCanvasElement),
        expect.objectContaining({
          options: expect.objectContaining({
            scales: expect.objectContaining({
              y: expect.objectContaining({
                title: expect.objectContaining({
                  text: 'Response Size (bytes)'
                })
              })
            })
          })
        })
      )
    })
  })

  describe('Time Window Handling', () => {
    it('should aggregate data by hour', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [
            createMockMetric({ timestamp: new Date('2024-01-01T10:30:00.000Z') }),
            createMockMetric({ timestamp: new Date('2024-01-01T10:45:00.000Z') })
          ],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        }
      })

      await wrapper.vm.$nextTick()

      // Should group metrics by hour
      expect(wrapper.vm.aggregatedData).toHaveLength(1) // Same hour
    })

    it('should aggregate data by day', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [
            createMockMetric({ timestamp: new Date('2024-01-01T10:00:00.000Z') }),
            createMockMetric({ timestamp: new Date('2024-01-01T15:00:00.000Z') }),
            createMockMetric({ timestamp: new Date('2024-01-02T10:00:00.000Z') })
          ],
          timeWindow: 'day' as const,
          metricType: 'executionTime' as const
        }
      })

      await wrapper.vm.$nextTick()

      // Should group metrics by day
      expect(wrapper.vm.aggregatedData).toHaveLength(2) // Two different days
    })
  })

  describe('Trend Analysis', () => {
    it('should display trend information', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [
            createMockMetric({
              executionTime: 100,
              timestamp: new Date('2024-01-01T10:00:00.000Z')
            }),
            createMockMetric({
              executionTime: 80,
              timestamp: new Date('2024-01-01T11:00:00.000Z')
            })
          ],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const,
          showTrend: true
        }
      })

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="trend-indicator"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('improving') // Performance improved
    })

    it('should show trend arrow indicators', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [
            createMockMetric({ executionTime: 100 }),
            createMockMetric({ executionTime: 120 }) // Performance degraded
          ],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const,
          showTrend: true
        }
      })

      await wrapper.vm.$nextTick()

      const trendIndicator = wrapper.find('[data-testid="trend-indicator"]')
      expect(trendIndicator.classes()).toContain('trend-degrading')
    })
  })

  describe('Interactive Features', () => {
    it('should support zooming functionality', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const,
          allowZoom: true
        }
      })

      await wrapper.vm.$nextTick()

      const { Chart } = await vi.importMock('chart.js/auto')
      expect(Chart).toHaveBeenCalledWith(
        expect.any(HTMLCanvasElement),
        expect.objectContaining({
          options: expect.objectContaining({
            plugins: expect.objectContaining({
              zoom: expect.objectContaining({
                zoom: expect.objectContaining({
                  wheel: expect.objectContaining({
                    enabled: true
                  })
                })
              })
            })
          })
        })
      )
    })

    it('should emit events on data point selection', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        }
      })

      await wrapper.vm.$nextTick()

      // Mock chart click event
      const event = new MouseEvent('click')
      const elements = [{ index: 0 }]
      mockChart.getElementsAtEventForMode.mockReturnValue(elements)

      // Simulate chart click
      await wrapper.vm.onChartClick(event)

      expect(wrapper.emitted('data-point-selected')).toBeTruthy()
    })
  })

  describe('Chart Lifecycle', () => {
    it('should destroy chart on component unmount', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        }
      })

      await wrapper.unmount()

      expect(mockChart.destroy).toHaveBeenCalled()
    })

    it('should update chart when metrics change', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        }
      })

      await wrapper.setProps({
        metrics: [createMockMetric(), createMockMetric()]
      })

      expect(mockChart.update).toHaveBeenCalled()
    })
  })
})
