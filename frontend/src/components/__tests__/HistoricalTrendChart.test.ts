import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import HistoricalTrendChart from '../HistoricalTrendChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Mock vue-echarts for testing
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="v-chart" data-testid="echarts-instance"><slot /></div>',
    props: ['option', 'theme', 'autoresize'],
    emits: ['click', 'brushselected', 'datazoom', 'finished'],
    methods: {
      resize: vi.fn(),
      getDataURL: vi.fn(() => 'data:image/png;base64,mock-image-data'),
      dispatchAction: vi.fn()
    }
  }
}))

// Mock echarts core to prevent import errors
vi.mock('echarts/core', () => ({ use: vi.fn() }))
vi.mock('echarts/renderers', () => ({ CanvasRenderer: {} }))
vi.mock('echarts/charts', () => ({ LineChart: {}, BarChart: {} }))
vi.mock('echarts/components', () => ({
  TitleComponent: {}, TooltipComponent: {}, LegendComponent: {}, GridComponent: {},
  DataZoomComponent: {}, ToolboxComponent: {}, BrushComponent: {}, MarkLineComponent: {}, MarkPointComponent: {}
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn()
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

  const defaultProps = {
    metrics: [createMockMetric()],
    timeWindow: 'hour' as const,
    metricType: 'executionTime' as const
  }

  describe('Chart Rendering', () => {
    it('should render chart with data', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      expect(wrapper.find('[data-testid="historical-trend-chart"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="echarts-instance"]').exists()).toBe(true)
    })

    it('should show empty state when no metrics provided', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          metrics: []
        }
      })

      expect(wrapper.find('.chart-empty-state').exists()).toBe(true)
      expect(wrapper.text()).toContain('No data available')
    })

    it('should update when metric type changes', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      await wrapper.setProps({ metricType: 'responseSize' })
      await nextTick()

      // Chart should re-render with new metric type
      expect(wrapper.props('metricType')).toBe('responseSize')
    })
  })

  describe('Chart Interactions', () => {
    it('should emit data-point-clicked when chart is clicked', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      // Simulate chart click by calling the handler directly
      const chartInstance = wrapper.vm
      await chartInstance.handleChartClick({
        data: [Date.now(), 150],
        dataIndex: 0
      })

      expect(wrapper.emitted('data-point-clicked')).toBeTruthy()
      const emittedEvents = wrapper.emitted('data-point-clicked') as any[]
      expect(emittedEvents[0][0]).toHaveProperty('metric')
      expect(emittedEvents[0][0]).toHaveProperty('index')
    })

    it('should emit time-range-selected when brush selection is made', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          allowZoom: true
        }
      })

      const chartInstance = wrapper.vm
      const startTime = Date.now()
      const endTime = startTime + 60000 // 1 minute later

      // Simulate brush selection by calling the handler directly
      await chartInstance.handleBrushSelection({
        areas: [{
          coordRange: [[startTime, endTime]]
        }]
      })

      expect(wrapper.emitted('time-range-selected')).toBeTruthy()
      const emittedEvents = wrapper.emitted('time-range-selected') as any[]
      expect(emittedEvents[0][0]).toHaveProperty('start')
      expect(emittedEvents[0][0]).toHaveProperty('end')
    })

    it('should emit zoom-changed when data zoom occurs', async () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          allowZoom: true
        }
      })

      const chartInstance = wrapper.vm

      // Simulate data zoom by calling the handler directly
      await chartInstance.handleDataZoom({ start: 20, end: 80 })

      expect(wrapper.emitted('zoom-changed')).toBeTruthy()
      const emittedEvents = wrapper.emitted('zoom-changed') as any[]
      expect(emittedEvents[0][0]).toEqual({ start: 20, end: 80 })
    })
  })

  describe('Chart Overlays', () => {
    it('should display moving average when enabled', async () => {
      const metrics = Array.from({ length: 10 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + i * 10,
          timestamp: new Date(Date.now() - (10 - i) * 60000)
        })
      )

      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          metrics,
          overlays: {
            movingAverage: { enabled: true, window: 5 }
          }
        }
      })

      // Chart should include moving average data in series
      expect(wrapper.vm.movingAverageData.length).toBeGreaterThan(0)
    })

    it('should detect and highlight anomalies when enabled', async () => {
      const normalMetrics = Array.from({ length: 10 }, () =>
        createMockMetric({ executionTime: 100 })
      )
      const anomalyMetric = createMockMetric({ executionTime: 500 }) // Outlier

      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          metrics: [...normalMetrics, anomalyMetric],
          overlays: {
            anomalyHighlights: { enabled: true, threshold: 2 }
          }
        }
      })

      // Should detect the anomaly
      expect(wrapper.vm.anomalies.length).toBeGreaterThan(0)
      expect(wrapper.vm.anomalies[0].value).toBe(500)
    })

    it('should calculate percentile bands when enabled', async () => {
      const metrics = Array.from({ length: 100 }, (_, i) =>
        createMockMetric({ executionTime: i + 1 })
      )

      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          metrics,
          overlays: {
            percentileBands: { enabled: true, percentiles: [25, 75, 95] }
          }
        }
      })

      const percentileBands = wrapper.vm.percentileBands
      expect(percentileBands).toHaveLength(3)
      expect(percentileBands[0].percentile).toBe(25)
      expect(percentileBands[1].percentile).toBe(75)
      expect(percentileBands[2].percentile).toBe(95)
    })
  })

  describe('Chart Configuration', () => {
    it('should configure chart for execution time metrics', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          metricType: 'executionTime'
        }
      })

      const chartOption = wrapper.vm.chartOption
      expect(chartOption.title.text).toContain('Execution Time')
      expect(chartOption.yAxis.name).toContain('Time (ms)')
    })

    it('should configure chart for response size metrics', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          metricType: 'responseSize'
        }
      })

      const chartOption = wrapper.vm.chartOption
      expect(chartOption.title.text).toContain('Response Size')
      expect(chartOption.yAxis.name).toContain('Size (bytes)')
    })

    it('should enable zoom controls when allowZoom is true', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          allowZoom: true
        }
      })

      const chartOption = wrapper.vm.chartOption
      expect(chartOption.dataZoom).toBeDefined()
      expect(chartOption.brush).toBeDefined()
      expect(chartOption.toolbox).toBeDefined()
    })

    it('should disable zoom controls when allowZoom is false', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          allowZoom: false
        }
      })

      const chartOption = wrapper.vm.chartOption
      expect(chartOption.dataZoom).toBeUndefined()
      expect(chartOption.brush).toBeUndefined()
    })
  })

  describe('Chart Methods', () => {
    it('should expose updateChart method', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      expect(typeof wrapper.vm.updateChart).toBe('function')
    })

    it('should expose exportChart method', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      expect(typeof wrapper.vm.exportChart).toBe('function')

      const imageData = wrapper.vm.exportChart('png')
      expect(imageData).toBe('data:image/png;base64,mock-image-data')
    })

    it('should expose setZoom method', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      expect(typeof wrapper.vm.setZoom).toBe('function')

      // Should not throw when called
      expect(() => wrapper.vm.setZoom(20, 80)).not.toThrow()
    })
  })

  describe('Responsive Behavior', () => {
    it('should handle window resize', () => {
      // Mock ResizeObserver
      const mockResizeObserver = vi.fn().mockImplementation(() => ({
        observe: vi.fn(),
        disconnect: vi.fn()
      }))
      global.ResizeObserver = mockResizeObserver

      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      // Should set up resize observer and component should exist
      expect(mockResizeObserver).toHaveBeenCalled()
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Theme Support', () => {
    it('should apply light theme by default', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: defaultProps
      })

      expect(wrapper.classes()).not.toContain('dark')
    })

    it('should apply dark theme when specified', () => {
      const wrapper = mount(HistoricalTrendChart, {
        props: {
          ...defaultProps,
          theme: 'dark'
        }
      })

      // Verify that dark theme is passed as prop to the component
      expect(wrapper.props('theme')).toBe('dark')
    })
  })
})
