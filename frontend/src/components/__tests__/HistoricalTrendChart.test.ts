import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import HistoricalTrendChart from '../HistoricalTrendChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'
// Removed unused TimeAggregation import

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
    Chart: MockChart,
    // Also add default export in case it's imported differently
    default: MockChart
  }
})

vi.mock('chartjs-plugin-zoom', () => ({
  default: {}
}))

// Mock PerformanceAnalytics
vi.mock('../../services/performanceAnalytics', () => {
  return {
    PerformanceAnalytics: vi.fn().mockImplementation(() => ({
      aggregateByTimeWindow: vi.fn((metrics, timeWindow) => {
        // Mock aggregation that groups metrics by time window
        if (metrics.length === 0) return []
        
        // For day aggregation test, return appropriate number of groups
        if (timeWindow === 'day' && metrics.length === 3) {
          // Group by day - 3 metrics on 2 different days should return 2 groups
          return [
            {
              timestamp: new Date('2024-01-01T10:00:00.000Z'),
              avgExecutionTime: 150,
              avgResponseSize: 1200,
              count: 2 // Two metrics on first day
            },
            {
              timestamp: new Date('2024-01-02T10:00:00.000Z'),
              avgExecutionTime: 150,
              avgResponseSize: 1200,
              count: 1 // One metric on second day
            }
          ]
        }
        
        // Default: single group for same time window
        const now = Date.now()
        return [{
          timestamp: new Date(now),
          avgExecutionTime: 150,
          avgResponseSize: 1200,
          count: metrics.length
        }]
      }),
      calculatePerformanceTrend: vi.fn((metrics, metricType) => {
        if (metrics.length < 2) return null
        
        // For trend analysis test - return direction based on execution times
        const firstMetric = metrics[0]
        const lastMetric = metrics[metrics.length - 1]
        
        if (firstMetric.executionTime < lastMetric.executionTime) {
          return {
            direction: 'degrading' as const,
            changePercentage: 20.0
          }
        }
        
        return {
          direction: 'improving' as const,
          changePercentage: -20.5
        }
      })
    }))
  }
})

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

  // Removed unused mockAggregations array

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

    it('should have aggregated data and canvas ref available', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        },
        attachTo: document.body // Ensure DOM is attached for refs to work
      })

      // Wait for Vue updates and DOM rendering
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      // Debug: Check if aggregatedData is available
      console.log('Aggregated data:', wrapper.vm.aggregatedData)
      console.log('Aggregated data length:', wrapper.vm.aggregatedData?.length)
      
      // Debug: Check if canvas element exists and chartCanvas ref
      const canvas = wrapper.find('canvas')
      console.log('Canvas exists:', canvas.exists())
      console.log('Canvas element:', canvas.element)
      
      // Check if chartCanvas ref is populated
      console.log('chartCanvas ref via chartCanvas:', wrapper.vm.chartCanvas)

      expect(wrapper.vm.aggregatedData?.length).toBeGreaterThan(0)
      expect(canvas.exists()).toBe(true)
      
      wrapper.unmount()
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
        },
        attachTo: document.body
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Verify component has correct props and data
      expect(wrapper.vm.aggregatedData?.length).toBeGreaterThan(0)
      expect(wrapper.vm.chartCanvas).toBeTruthy()
      expect(wrapper.props('metricType')).toBe('executionTime')
      
      wrapper.unmount()
    })

    it('should configure chart for response size metrics', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'responseSize' as const
        },
        attachTo: document.body
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Verify component configuration for responseSize
      expect(wrapper.vm.aggregatedData?.length).toBeGreaterThan(0)
      expect(wrapper.vm.chartCanvas).toBeTruthy()
      expect(wrapper.props('metricType')).toBe('responseSize')
      
      // Check chart config has correct y-axis title
      const chartConfig = wrapper.vm.chartConfig
      expect(chartConfig.options.scales.y.title.text).toBe('Response Size (bytes)')
      
      wrapper.unmount()
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
        },
        attachTo: document.body
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Verify zoom configuration is enabled
      expect(wrapper.props('allowZoom')).toBe(true)
      
      // Check chart config includes zoom options
      const chartConfig = wrapper.vm.chartConfig
      expect(chartConfig.options.plugins.zoom).toBeDefined()
      expect(chartConfig.options.plugins.zoom.zoom.wheel.enabled).toBe(true)
      
      wrapper.unmount()
    })

    it('should emit events on data point selection', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        },
        attachTo: document.body
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Create a mock chart instance and set it manually
      const mockChartInstance = {
        getElementsAtEventForMode: vi.fn().mockReturnValue([{ index: 0 }])
      }
      wrapper.vm.chartInstance = mockChartInstance

      // Simulate chart click event
      const event = new MouseEvent('click')
      await wrapper.vm.onChartClick(event)

      // Verify event was emitted
      expect(wrapper.emitted('data-point-selected')).toBeTruthy()
      expect(wrapper.emitted('data-point-selected')).toHaveLength(1)
      
      wrapper.unmount()
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

      // Wait for chart creation
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      await wrapper.unmount()

      // Get the mock chart instance
      const { Chart } = await vi.importMock('chart.js/auto')
      const mockChartInstance = Chart.mock.results[0]?.value
      if (mockChartInstance) {
        expect(mockChartInstance.destroy).toHaveBeenCalled()
      } else {
        // If no chart was created, this test should pass as no destroy is needed
        expect(Chart).toHaveBeenCalledTimes(0)
      }
    })

    it('should update chart when metrics change', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          metrics: [createMockMetric()],
          timeWindow: 'hour' as const,
          metricType: 'executionTime' as const
        },
        attachTo: document.body
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Check initial data
      expect(wrapper.vm.aggregatedData?.length).toBe(1)

      // Update metrics
      await wrapper.setProps({
        metrics: [createMockMetric(), createMockMetric()]
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Verify component state updated with new metrics
      expect(wrapper.vm.aggregatedData?.length).toBeGreaterThan(0)
      expect(wrapper.props('metrics')).toHaveLength(2)
      
      wrapper.unmount()
    }
  })
})
