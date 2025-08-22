import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MetricChart from '../MetricChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Mock vue-echarts for testing
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="v-chart" data-testid="echarts-instance"><slot /></div>',
    props: ['option', 'theme', 'autoresize'],
    emits: ['click', 'datazoom', 'finished'],
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
  DataZoomComponent: {}, ToolboxComponent: {}
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn()
}))

describe('MetricChart', () => {
  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    id: `metric_${Date.now()}_${Math.random()}`,
    endpointId: 'endpoint-1',
    query: 'test_query',
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    errors: null,
    ...overrides
  })

  const defaultProps = {
    metricType: 'executionTime' as const,
    metrics: [createMockMetric()]
  }

  describe('Chart Rendering', () => {
    it('should render metric chart with correct test id', () => {
      const wrapper = mount(MetricChart, {
        props: defaultProps
      })

      expect(wrapper.find('[data-testid="metric-chart-executionTime"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="echarts-instance"]').exists()).toBe(true)
    })

    it('should render different test ids for different metric types', () => {
      const executionTimeWrapper = mount(MetricChart, {
        props: { ...defaultProps, metricType: 'executionTime' }
      })
      const responseSizeWrapper = mount(MetricChart, {
        props: { ...defaultProps, metricType: 'responseSize' }
      })
      const errorRateWrapper = mount(MetricChart, {
        props: { ...defaultProps, metricType: 'errorRate' }
      })

      expect(executionTimeWrapper.find('[data-testid="metric-chart-executionTime"]').exists()).toBe(true)
      expect(responseSizeWrapper.find('[data-testid="metric-chart-responseSize"]').exists()).toBe(true)
      expect(errorRateWrapper.find('[data-testid="metric-chart-errorRate"]').exists()).toBe(true)
    })

    it('should show empty state when no metrics provided', () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          metrics: []
        }
      })

      expect(wrapper.find('.chart-empty-state').exists()).toBe(true)
      expect(wrapper.text()).toContain('No data available')
    })

    it('should display correct chart title for each metric type', () => {
      const executionTimeWrapper = mount(MetricChart, {
        props: { ...defaultProps, metricType: 'executionTime' }
      })
      const responseSizeWrapper = mount(MetricChart, {
        props: { ...defaultProps, metricType: 'responseSize' }
      })
      const errorRateWrapper = mount(MetricChart, {
        props: { ...defaultProps, metricType: 'errorRate' }
      })

      expect(executionTimeWrapper.find('.chart-title').text()).toBe('Execution Time')
      expect(responseSizeWrapper.find('.chart-title').text()).toBe('Response Size')
      expect(errorRateWrapper.find('.chart-title').text()).toBe('Error Rate')
    })
  })

  describe('Chart Interactions', () => {
    it('should show reset zoom button when allowZoom is true', () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          allowZoom: true
        }
      })

      expect(wrapper.find('[data-testid="reset-zoom-btn"]').exists()).toBe(true)
    })

    it('should hide reset zoom button when allowZoom is false', () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          allowZoom: false
        }
      })

      expect(wrapper.find('[data-testid="reset-zoom-btn"]').exists()).toBe(false)
    })

    it('should emit data-point-selected when chart is clicked', async () => {
      const wrapper = mount(MetricChart, {
        props: defaultProps
      })

      const chartInstance = wrapper.vm

      // Simulate chart click by calling the handler directly
      await chartInstance.handleChartClick({
        data: [Date.now(), 150],
        dataIndex: 0
      })

      expect(wrapper.emitted('data-point-selected')).toBeTruthy()
      const emittedEvents = wrapper.emitted('data-point-selected') as any[]
      expect(emittedEvents[0][0]).toHaveProperty('metric')
      expect(emittedEvents[0][0]).toHaveProperty('metricType')
      expect(emittedEvents[0][0].metricType).toBe('executionTime')
    })

    it('should emit zoom-changed when synchronized and data zoom occurs', async () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          synchronized: true
        }
      })

      const chartInstance = wrapper.vm

      // Simulate data zoom by calling the handler directly
      await chartInstance.handleDataZoom({ start: 20, end: 80 })

      expect(wrapper.emitted('zoom-changed')).toBeTruthy()
      const emittedEvents = wrapper.emitted('zoom-changed') as any[]
      expect(emittedEvents[0][0]).toEqual({
        start: 20,
        end: 80,
        metricType: 'executionTime'
      })
    })

    it('should reset zoom when reset button is clicked', async () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          allowZoom: true
        }
      })

      const resetBtn = wrapper.find('[data-testid="reset-zoom-btn"]')
      await resetBtn.trigger('click')

      // Should call resetZoom method
      const chartInstance = wrapper.vm
      expect(typeof chartInstance.resetZoom).toBe('function')

      // Verify resetZoom doesn't throw
      expect(() => chartInstance.resetZoom()).not.toThrow()
    })
  })

  describe('Global Time Range Filtering', () => {
    it('should filter metrics by global time range when provided', async () => {
      const now = new Date()
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000)

      const metrics = [
        createMockMetric({ timestamp: twoHoursAgo }), // Should be filtered out
        createMockMetric({ timestamp: oneHourAgo }),   // Should be included
        createMockMetric({ timestamp: now })           // Should be included
      ]

      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          metrics,
          globalTimeRange: {
            start: oneHourAgo,
            end: now
          }
        }
      })

      // Should only include metrics within the time range
      expect(wrapper.vm.chartData).toHaveLength(2)
      expect(wrapper.vm.chartData[0].timestamp.getTime()).toBeGreaterThanOrEqual(oneHourAgo.getTime())
    })
  })

  describe('Chart Overlays', () => {
    it('should display moving average overlay indicator when enabled', () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          overlays: {
            movingAverage: { enabled: true, window: 5 }
          }
        }
      })

      expect(wrapper.find('[data-testid="overlay-moving-average"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="overlay-moving-average"]').text()).toContain('MA(5)')
    })

    it('should display percentile bands overlay indicator when enabled', () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          overlays: {
            percentileBands: { enabled: true, percentiles: [25, 75, 95] }
          }
        }
      })

      expect(wrapper.find('[data-testid="overlay-percentile-bands"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="overlay-percentile-bands"]').text()).toContain('Percentile Bands')
    })

    it('should hide overlay indicators when overlays are disabled', () => {
      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          overlays: {
            movingAverage: { enabled: false, window: 5 },
            percentileBands: { enabled: false, percentiles: [25, 75, 95] }
          }
        }
      })

      expect(wrapper.find('[data-testid="overlay-moving-average"]').exists()).toBe(false)
      expect(wrapper.find('[data-testid="overlay-percentile-bands"]').exists()).toBe(false)
    })
  })

  describe('Metric Value Processing', () => {
    it('should process execution time values correctly', async () => {
      const metrics = [
        createMockMetric({ executionTime: 150 }),
        createMockMetric({ executionTime: 200 })
      ]

      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          metricType: 'executionTime',
          metrics
        }
      })

      const chartData = wrapper.vm.chartData
      expect(chartData[0].value).toBe(150)
      expect(chartData[1].value).toBe(200)
    })

    it('should process response size values correctly', async () => {
      const metrics = [
        createMockMetric({ responseSize: 2048 }),
        createMockMetric({ responseSize: 4096 })
      ]

      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          metricType: 'responseSize',
          metrics
        }
      })

      const chartData = wrapper.vm.chartData
      expect(chartData[0].value).toBe(2048)
      expect(chartData[1].value).toBe(4096)
    })

    it('should process error rate values correctly', async () => {
      const metrics = [
        createMockMetric({ errors: null }),     // No error = 0
        createMockMetric({ errors: ['error'] }) // Has error = 1
      ]

      const wrapper = mount(MetricChart, {
        props: {
          ...defaultProps,
          metricType: 'errorRate',
          metrics
        }
      })

      const chartData = wrapper.vm.chartData
      expect(chartData[0].value).toBe(0)
      expect(chartData[1].value).toBe(1)
    })
  })

  describe('Chart Methods', () => {
    it('should expose updateChart method', () => {
      const wrapper = mount(MetricChart, {
        props: defaultProps
      })

      expect(typeof wrapper.vm.updateChart).toBe('function')
    })

    it('should expose setZoom method', () => {
      const wrapper = mount(MetricChart, {
        props: defaultProps
      })

      expect(typeof wrapper.vm.setZoom).toBe('function')
      expect(() => wrapper.vm.setZoom(20, 80)).not.toThrow()
    })

    it('should expose exportChart method', () => {
      const wrapper = mount(MetricChart, {
        props: defaultProps
      })

      expect(typeof wrapper.vm.exportChart).toBe('function')

      const imageData = wrapper.vm.exportChart('png')
      expect(imageData).toBe('data:image/png;base64,mock-image-data')
    })
  })

  describe('Theme Support', () => {
    it('should apply light theme by default', () => {
      const wrapper = mount(MetricChart, {
        props: defaultProps
      })

      // Verify that default theme (light) is used
      expect(wrapper.props('theme')).toBe('light') // Default theme is 'light' as defined in withDefaults
    })

    it('should apply dark theme when specified', () => {
      const wrapper = mount(MetricChart, {
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
