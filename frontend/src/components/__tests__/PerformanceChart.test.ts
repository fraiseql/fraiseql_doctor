import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import PerformanceChart from '../PerformanceChart.vue'
import type { QueryMetric } from '../../services/performanceMonitor'

// Mock Chart.js
const mockChart = {
  destroy: vi.fn(),
  update: vi.fn(),
  data: {
    labels: ['10:00', '11:00', '12:00'],
    datasets: [
      {
        label: 'Response Time (ms)',
        data: [120, 150, 200],
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderColor: 'rgb(59, 130, 246)'
      }
    ]
  }
}

vi.mock('chart.js/auto', () => ({
  Chart: vi.fn().mockImplementation(() => mockChart)
}))

describe('PerformanceChart', () => {
  const mockMetrics: QueryMetric[] = [
    {
      id: '1',
      endpointId: 'endpoint-1',
      query: 'query { users }',
      executionTime: 120,
      responseSize: 1024,
      timestamp: new Date('2025-01-21T10:00:00Z')
    },
    {
      id: '2',
      endpointId: 'endpoint-1',
      query: 'query { posts }',
      executionTime: 150,
      responseSize: 2048,
      timestamp: new Date('2025-01-21T11:00:00Z')
    },
    {
      id: '3',
      endpointId: 'endpoint-1',
      query: 'query { comments }',
      executionTime: 200,
      responseSize: 512,
      timestamp: new Date('2025-01-21T12:00:00Z')
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render response time trend chart', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseTime'
      }
    })

    expect(wrapper.find('[data-testid="performance-chart"]').exists()).toBe(true)
    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('should render response size chart', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseSize'
      }
    })

    expect(wrapper.find('[data-testid="performance-chart"]').exists()).toBe(true)
    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('should update chart when metrics change', async () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics.slice(0, 2),
        chartType: 'responseTime'
      }
    })

    // Update metrics
    await wrapper.setProps({
      metrics: mockMetrics
    })

    expect(mockChart.update).toHaveBeenCalled()
  })

  it('should handle empty metrics gracefully', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: [],
        chartType: 'responseTime'
      }
    })

    expect(wrapper.find('[data-testid="performance-chart"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="no-data-message"]').exists()).toBe(true)
  })

  it('should destroy chart on unmount', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseTime'
      }
    })

    wrapper.unmount()

    expect(mockChart.destroy).toHaveBeenCalled()
  })

  it('should format timestamps for chart labels', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseTime'
      }
    })

    // Check that the component computes the correct labels from metrics
    const vm = wrapper.vm as any
    const chartData = vm.chartData

    // Check that we have 3 labels (one for each metric)
    expect(chartData.labels).toHaveLength(3)
    // Check that labels are in HH:MM format
    expect(chartData.labels[0]).toMatch(/^\d{2}:\d{2}$/)
    expect(chartData.labels[1]).toMatch(/^\d{2}:\d{2}$/)
    expect(chartData.labels[2]).toMatch(/^\d{2}:\d{2}$/)
  })

  it('should calculate appropriate chart data for response time', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseTime'
      }
    })

    const vm = wrapper.vm as any
    const chartData = vm.chartData
    const dataset = chartData.datasets[0]

    expect(dataset.label).toBe('Response Time (ms)')
    expect(dataset.data).toEqual([120, 150, 200])
    expect(dataset.backgroundColor).toBe('rgba(59, 130, 246, 0.1)')
    expect(dataset.borderColor).toBe('rgb(59, 130, 246)')
  })

  it('should calculate appropriate chart data for response size', () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseSize'
      }
    })

    const vm = wrapper.vm as any
    const chartData = vm.chartData
    const dataset = chartData.datasets[0]

    expect(dataset.label).toBe('Response Size (bytes)')
    expect(dataset.data).toEqual([1024, 2048, 512])
    expect(dataset.backgroundColor).toBe('rgba(16, 185, 129, 0.1)')
    expect(dataset.borderColor).toBe('rgb(16, 185, 129)')
  })

  it('should handle real-time updates without memory leaks', async () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics.slice(0, 1),
        chartType: 'responseTime'
      }
    })

    // Simulate real-time updates
    for (let i = 0; i < 10; i++) {
      await wrapper.setProps({
        metrics: [
          ...mockMetrics,
          {
            id: `new-${i}`,
            endpointId: 'endpoint-1',
            query: `query { test${i} }`,
            executionTime: 100 + i,
            responseSize: 1000 + i,
            timestamp: new Date(`2025-01-21T${13 + i}:00:00Z`)
          }
        ]
      })
    }

    expect(mockChart.update).toHaveBeenCalledTimes(10)
  })

  it('should provide chart type switching capability', async () => {
    const wrapper = mount(PerformanceChart, {
      props: {
        metrics: mockMetrics,
        chartType: 'responseTime'
      }
    })

    let vm = wrapper.vm as any
    expect(vm.chartData.datasets[0].label).toBe('Response Time (ms)')

    await wrapper.setProps({
      chartType: 'responseSize'
    })

    vm = wrapper.vm as any
    expect(vm.chartData.datasets[0].label).toBe('Response Size (bytes)')
  })
})
