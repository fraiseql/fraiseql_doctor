import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import InteractiveTimeSeriesChart from '../InteractiveTimeSeriesChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Mock Chart.js
vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({
    destroy: vi.fn(),
    update: vi.fn(),
    resetZoom: vi.fn(),
    pan: vi.fn(),
    zoom: vi.fn(),
    getElementsAtEventForMode: vi.fn(() => []),
    canvas: { addEventListener: vi.fn(), removeEventListener: vi.fn() },
    scales: {
      x: { min: 0, max: 100 },
      y: { min: 0, max: 1000 }
    }
  })),
  registerables: []
}))

vi.mock('chartjs-plugin-zoom', () => ({
  default: {}
}))

describe('InteractiveTimeSeriesChart', () => {
  let wrapper: any

  const createMockMetric = (overrides: Partial<QueryMetric> = {}): QueryMetric => ({
    query: 'test query',
    variables: {},
    executionTime: 100,
    responseSize: 1024,
    timestamp: new Date(),
    status: 'success',
    endpointId: 'endpoint-1',
    operationType: 'query',
    ...overrides
  })

  const mockMetrics = Array.from({ length: 100 }, (_, i) =>
    createMockMetric({
      executionTime: 100 + Math.sin(i * 0.1) * 20,
      timestamp: new Date(Date.now() - (100 - i) * 60000)
    })
  )

  beforeEach(() => {
    wrapper = mount(InteractiveTimeSeriesChart, {
      props: {
        metrics: mockMetrics,
        metric: 'executionTime'
      }
    })
  })

  describe('Chart Initialization', () => {
    it('should render chart canvas with proper configuration', () => {
      expect(wrapper.find('canvas').exists()).toBe(true)
      expect(wrapper.find('[data-testid="time-series-chart"]').exists()).toBe(true)
    })

    it('should initialize with zoom and pan capabilities', () => {
      expect(wrapper.vm.chartOptions.plugins.zoom).toBeDefined()
      expect(wrapper.vm.chartOptions.plugins.zoom.pan.enabled).toBe(true)
      expect(wrapper.vm.chartOptions.plugins.zoom.zoom.wheel.enabled).toBe(true)
    })

    it('should support multiple resolution modes', async () => {
      await wrapper.setProps({ resolution: 'minute' })
      expect(wrapper.vm.currentResolution).toBe('minute')

      await wrapper.setProps({ resolution: 'hour' })
      expect(wrapper.vm.currentResolution).toBe('hour')
    })
  })

  describe('Interactive Features', () => {
    it('should handle brush selection for time range filtering', async () => {
      const canvas = wrapper.find('canvas')

      // Simulate brush selection
      await canvas.trigger('mousedown', { clientX: 100, clientY: 100 })
      await canvas.trigger('mousemove', { clientX: 200, clientY: 100 })
      await canvas.trigger('mouseup', { clientX: 200, clientY: 100 })

      expect(wrapper.emitted('time-range-selected')).toBeTruthy()
      expect(wrapper.vm.selectedTimeRange).toBeDefined()
    })

    it('should support drill-down on data point selection', async () => {
      // Simulate clicking on a data point
      wrapper.vm.handleChartClick({
        chart: wrapper.vm.chartInstance,
        native: { offsetX: 150, offsetY: 200 }
      })

      expect(wrapper.emitted('drill-down')).toBeTruthy()
      expect(wrapper.emitted('drill-down')[0]).toEqual([
        expect.objectContaining({
          dataPoint: expect.any(Object),
          timeRange: expect.any(Object)
        })
      ])
    })

    it('should show contextual tooltips with statistical information', () => {
      const tooltipContext = {
        dataIndex: 50,
        dataset: { data: mockMetrics },
        chart: wrapper.vm.chartInstance
      }

      const tooltip = wrapper.vm.generateAdvancedTooltip(tooltipContext)

      expect(tooltip).toContain('Execution Time')
      expect(tooltip).toContain('vs Baseline')
      expect(tooltip).toContain('Percentile')
      expect(tooltip).toContain('Trend')
    })

    it('should support crosshair cursor for precise data inspection', async () => {
      const canvas = wrapper.find('canvas')

      await canvas.trigger('mousemove', { clientX: 250, clientY: 150 })

      expect(wrapper.vm.crosshairPosition).toEqual({
        x: 250,
        y: 150,
        visible: true
      })

      expect(wrapper.find('.crosshair-vertical').isVisible()).toBe(true)
      expect(wrapper.find('.crosshair-horizontal').isVisible()).toBe(true)
    })
  })

  describe('Real-time Data Updates', () => {
    it('should handle streaming data updates efficiently', async () => {
      const newMetrics = [
        ...mockMetrics,
        createMockMetric({
          executionTime: 150,
          timestamp: new Date()
        })
      ]

      await wrapper.setProps({ metrics: newMetrics, realTimeUpdates: true })

      expect(wrapper.vm.chartData.datasets[0].data).toHaveLength(101)
      expect(wrapper.emitted('data-updated')).toBeTruthy()
    })

    it('should maintain smooth animations during real-time updates', async () => {
      wrapper.vm.chartOptions.animation.duration = 750

      const streamingMetrics = [...mockMetrics]
      for (let i = 0; i < 10; i++) {
        streamingMetrics.push(createMockMetric({
          executionTime: 120 + i * 5,
          timestamp: new Date(Date.now() + i * 1000)
        }))

        await wrapper.setProps({ metrics: streamingMetrics })
        await nextTick()
      }

      expect(wrapper.vm.animationQueue.length).toBeLessThanOrEqual(3) // Should limit animation queue
    })

    it('should automatically adjust time window for streaming data', async () => {
      const initialTimeRange = wrapper.vm.displayTimeRange

      await wrapper.setProps({
        autoTimeWindow: true,
        windowSize: 60 // 60 minutes
      })

      expect(wrapper.vm.displayTimeRange.duration).toBe(60 * 60 * 1000) // 60 minutes in ms
      expect(wrapper.vm.displayTimeRange.end.getTime()).toBeCloseTo(Date.now(), -3) // Close to now
    })
  })

  describe('Multi-Resolution Support', () => {
    it('should automatically select appropriate resolution based on time range', async () => {
      // Test 1 hour range -> minute resolution
      await wrapper.setProps({
        timeRange: {
          start: new Date(Date.now() - 60 * 60 * 1000),
          end: new Date()
        }
      })
      expect(wrapper.vm.optimalResolution).toBe('minute')

      // Test 1 day range -> 5-minute resolution
      await wrapper.setProps({
        timeRange: {
          start: new Date(Date.now() - 24 * 60 * 60 * 1000),
          end: new Date()
        }
      })
      expect(wrapper.vm.optimalResolution).toBe('5minute')

      // Test 1 week range -> hourly resolution
      await wrapper.setProps({
        timeRange: {
          start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
          end: new Date()
        }
      })
      expect(wrapper.vm.optimalResolution).toBe('hour')
    })

    it('should aggregate data points for lower resolutions', () => {
      const hourlyData = wrapper.vm.aggregateToResolution(mockMetrics, 'hour')

      expect(hourlyData.length).toBeLessThan(mockMetrics.length)
      expect(hourlyData[0]).toHaveProperty('averageExecutionTime')
      expect(hourlyData[0]).toHaveProperty('minExecutionTime')
      expect(hourlyData[0]).toHaveProperty('maxExecutionTime')
      expect(hourlyData[0]).toHaveProperty('dataPointCount')
    })
  })

  describe('Statistical Overlays', () => {
    it('should display moving averages with configurable windows', async () => {
      await wrapper.setProps({
        showMovingAverage: true,
        movingAverageWindow: 20
      })

      const movingAverageDataset = wrapper.vm.chartData.datasets.find(
        (d: any) => d.label === 'Moving Average (20 periods)'
      )

      expect(movingAverageDataset).toBeDefined()
      expect(movingAverageDataset.borderColor).toBe('#ff6b6b')
      expect(movingAverageDataset.data.length).toBe(mockMetrics.length)
    })

    it('should show percentile bands for performance baselines', async () => {
      await wrapper.setProps({
        showPercentileBands: true,
        percentiles: [25, 75, 95]
      })

      const p25Band = wrapper.vm.chartData.datasets.find((d: any) => d.label === 'P25')
      const p75Band = wrapper.vm.chartData.datasets.find((d: any) => d.label === 'P75')
      const p95Band = wrapper.vm.chartData.datasets.find((d: any) => d.label === 'P95')

      expect(p25Band).toBeDefined()
      expect(p75Band).toBeDefined()
      expect(p95Band).toBeDefined()

      expect(p75Band.fill).toBe('+1') // Fill between P25 and P75
    })

    it('should highlight anomalies with visual indicators', async () => {
      const anomalousMetrics = [
        ...mockMetrics,
        createMockMetric({
          executionTime: 500, // Anomaly
          timestamp: new Date()
        })
      ]

      await wrapper.setProps({
        metrics: anomalousMetrics,
        showAnomalies: true,
        anomalyThreshold: 3 // 3 standard deviations
      })

      const anomalyOverlay = wrapper.vm.chartData.datasets.find(
        (d: any) => d.label === 'Anomalies'
      )

      expect(anomalyOverlay).toBeDefined()
      expect(anomalyOverlay.pointBackgroundColor).toBe('#ff4757')
      expect(anomalyOverlay.data).toContainEqual(
        expect.objectContaining({ y: 500 })
      )
    })
  })

  describe('Performance Optimization', () => {
    it('should implement data decimation for large datasets', async () => {
      const largeDataset = Array.from({ length: 10000 }, (_, i) =>
        createMockMetric({
          executionTime: 100 + Math.random() * 50,
          timestamp: new Date(Date.now() - (10000 - i) * 1000)
        })
      )

      await wrapper.setProps({
        metrics: largeDataset,
        maxDataPoints: 1000
      })

      expect(wrapper.vm.displayData.length).toBeLessThanOrEqual(1000)
      expect(wrapper.vm.decimationRatio).toBeGreaterThan(1)
    })

    it('should use virtualization for off-screen data points', async () => {
      const viewport = { start: 25, end: 75 }
      wrapper.vm.setViewport(viewport)

      expect(wrapper.vm.visibleDataRange.start).toBe(25)
      expect(wrapper.vm.visibleDataRange.end).toBe(75)
      expect(wrapper.vm.renderedDataPoints.length).toBeLessThan(mockMetrics.length)
    })

    it('should debounce rapid updates to prevent performance issues', async () => {
      const updateSpy = vi.spyOn(wrapper.vm, 'updateChart')

      // Rapid fire updates
      for (let i = 0; i < 10; i++) {
        wrapper.vm.handleDataUpdate([createMockMetric()])
        await nextTick()
      }

      // Should debounce to fewer actual chart updates
      expect(updateSpy).toHaveBeenCalledTimes(1)
    })
  })

  describe('Export and Analysis Features', () => {
    it('should export selected data range to CSV', async () => {
      wrapper.vm.selectedTimeRange = {
        start: new Date(Date.now() - 30 * 60000),
        end: new Date()
      }

      const csvData = wrapper.vm.exportToCSV()

      expect(csvData).toContain('timestamp,executionTime,responseSize')
      expect(csvData.split('\n').length).toBeGreaterThan(30)
    })

    it('should generate statistical summary reports', () => {
      const summary = wrapper.vm.generateStatisticalSummary()

      expect(summary).toMatchObject({
        count: expect.any(Number),
        mean: expect.any(Number),
        median: expect.any(Number),
        standardDeviation: expect.any(Number),
        min: expect.any(Number),
        max: expect.any(Number),
        percentiles: {
          p25: expect.any(Number),
          p50: expect.any(Number),
          p75: expect.any(Number),
          p90: expect.any(Number),
          p95: expect.any(Number),
          p99: expect.any(Number)
        }
      })
    })

    it('should support annotation and bookmark features', async () => {
      const annotation = {
        x: new Date(Date.now() - 30 * 60000),
        text: 'Performance spike detected',
        color: '#ff4757'
      }

      wrapper.vm.addAnnotation(annotation)

      expect(wrapper.vm.annotations).toContain(annotation)
      expect(wrapper.emitted('annotation-added')).toBeTruthy()

      const annotationOverlay = wrapper.vm.chartOptions.plugins.annotation.annotations
      expect(annotationOverlay).toContain(
        expect.objectContaining({
          type: 'line',
          scaleID: 'x',
          value: annotation.x
        })
      )
    })
  })
})
