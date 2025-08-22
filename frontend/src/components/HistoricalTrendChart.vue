<template>
  <div class="historical-trend-chart" data-testid="historical-trend-chart">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state" data-testid="loading-state">
      <div class="flex items-center justify-center h-64">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p class="mt-2 text-sm text-gray-500">Loading historical data...</p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="metrics.length === 0" class="empty-state" data-testid="empty-state">
      <div class="text-center text-gray-500 p-8">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No historical data available</h3>
        <p class="mt-1 text-sm text-gray-500">Historical performance data will appear here once collected.</p>
      </div>
    </div>

    <!-- Chart Container -->
    <div v-else class="chart-container">
      <!-- Trend Indicator -->
      <div v-if="showTrend && trendAnalysis" class="trend-indicator mb-4" data-testid="trend-indicator" :class="`trend-${trendAnalysis.direction}`">
        <div class="flex items-center space-x-2">
          <div class="trend-icon">
            <!-- Improving Trend -->
            <svg v-if="trendAnalysis.direction === 'improving'" data-testid="trend-arrow-up" class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17L17 7M17 7H7M17 7v10" />
            </svg>

            <!-- Degrading Trend -->
            <svg v-else-if="trendAnalysis.direction === 'degrading'" data-testid="trend-arrow-down" class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7L7 17M7 17h10M7 17V7" />
            </svg>

            <!-- Stable Trend -->
            <svg v-else class="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14" />
            </svg>
          </div>

          <span class="text-sm font-medium" :class="{
            'text-green-600': trendAnalysis.direction === 'improving',
            'text-red-600': trendAnalysis.direction === 'degrading',
            'text-gray-600': trendAnalysis.direction === 'stable'
          }">
            Performance {{ trendAnalysis.direction }}
            <span class="ml-1 text-xs">
              ({{ Math.abs(trendAnalysis.changePercentage).toFixed(1) }}%)
            </span>
          </span>
        </div>
      </div>

      <!-- Chart Canvas -->
      <div class="relative h-full w-full">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { Chart, type ChartConfiguration } from 'chart.js/auto'
import zoomPlugin from 'chartjs-plugin-zoom'
import type { QueryMetric } from '../services/performanceMonitor'
import type { MetricField, TimeWindow } from '../services/performanceAnalytics'
import { PerformanceAnalytics } from '../services/performanceAnalytics'

// Register zoom plugin (with test safety)
if (Chart.register) {
  Chart.register(zoomPlugin)
}

interface Props {
  metrics: QueryMetric[]
  timeWindow: TimeWindow
  metricType: MetricField
  showTrend?: boolean
  allowZoom?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showTrend: false,
  allowZoom: false,
  loading: false
})

const emit = defineEmits<{
  'data-point-selected': [data: { metric: QueryMetric; aggregation: any }]
}>()

const chartCanvas = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null

const analytics = new PerformanceAnalytics()

// Computed properties
const aggregatedData = computed(() => {
  if (props.metrics.length === 0) return []
  return analytics.aggregateByTimeWindow(props.metrics, props.timeWindow)
})

const trendAnalysis = computed(() => {
  if (props.metrics.length < 2) return null
  return analytics.calculatePerformanceTrend(props.metrics, props.metricType)
})

const chartData = computed(() => {
  const data = aggregatedData.value

  if (data.length === 0) {
    return {
      labels: [],
      datasets: []
    }
  }

  const labels = data.map(item => {
    const date = new Date(item.timestamp)
    switch (props.timeWindow) {
      case 'hour':
        return date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        })
      case 'day':
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric'
        })
      case 'week':
        return `Week of ${date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric'
        })}`
      case 'month':
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short'
        })
      default:
        return date.toLocaleString()
    }
  })

  const values = data.map(item =>
    props.metricType === 'executionTime' ? item.avgExecutionTime : item.avgResponseSize
  )

  const dataset = {
    label: props.metricType === 'executionTime'
      ? 'Average Response Time (ms)'
      : 'Average Response Size (bytes)',
    data: values,
    backgroundColor: props.metricType === 'executionTime'
      ? 'rgba(59, 130, 246, 0.1)'
      : 'rgba(16, 185, 129, 0.1)',
    borderColor: props.metricType === 'executionTime'
      ? 'rgb(59, 130, 246)'
      : 'rgb(16, 185, 129)',
    borderWidth: 2,
    fill: true,
    tension: 0.4,
    pointRadius: 4,
    pointHoverRadius: 8,
    pointBackgroundColor: props.metricType === 'executionTime'
      ? 'rgb(59, 130, 246)'
      : 'rgb(16, 185, 129)',
    pointBorderColor: '#ffffff',
    pointBorderWidth: 2
  }

  return {
    labels,
    datasets: [dataset]
  }
})

const chartConfig = computed((): ChartConfiguration => ({
  type: 'line',
  data: chartData.value,
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index'
    },
    onClick: (_event, elements) => {
      if (elements.length > 0) {
        const elementIndex = elements[0].index
        const aggregation = aggregatedData.value[elementIndex]

        // Find metrics that contributed to this aggregation
        const windowStart = new Date(aggregation.timestamp)
        const windowEnd = new Date(windowStart)

        switch (props.timeWindow) {
          case 'hour':
            windowEnd.setHours(windowEnd.getHours() + 1)
            break
          case 'day':
            windowEnd.setDate(windowEnd.getDate() + 1)
            break
          case 'week':
            windowEnd.setDate(windowEnd.getDate() + 7)
            break
          case 'month':
            windowEnd.setMonth(windowEnd.getMonth() + 1)
            break
        }

        const contributingMetrics = props.metrics.filter(metric =>
          metric.timestamp >= windowStart && metric.timestamp < windowEnd
        )

        if (contributingMetrics.length > 0) {
          emit('data-point-selected', {
            metric: contributingMetrics[0], // Representative metric
            aggregation
          })
        }
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'top'
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const index = context[0].dataIndex
            const aggregation = aggregatedData.value[index]
            const date = new Date(aggregation.timestamp)

            switch (props.timeWindow) {
              case 'hour':
                return `Hour: ${date.toLocaleString()}`
              case 'day':
                return `Day: ${date.toLocaleDateString()}`
              case 'week':
                return `Week of: ${date.toLocaleDateString()}`
              case 'month':
                return `Month: ${date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })}`
              default:
                return date.toLocaleString()
            }
          },
          label: (context) => {
            const value = context.parsed.y
            const index = context.dataIndex
            const aggregation = aggregatedData.value[index]
            const unit = props.metricType === 'executionTime' ? 'ms' : 'bytes'

            return [
              `Average: ${value.toFixed(2)} ${unit}`,
              `Sample Count: ${aggregation.count}`,
              `Time Window: ${props.timeWindow}`
            ]
          }
        }
      },
      ...(props.allowZoom ? {
        zoom: {
          limits: {
            y: { min: 0 }
          },
          pan: {
            enabled: true,
            mode: 'x'
          },
          zoom: {
            wheel: {
              enabled: true
            },
            pinch: {
              enabled: true
            },
            mode: 'x'
          }
        }
      } : {})
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: `Time (${props.timeWindow}s)`
        },
        grid: {
          display: false
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: props.metricType === 'executionTime'
            ? 'Execution Time (ms)'
            : 'Response Size (bytes)'
        },
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    },
    elements: {
      point: {
        radius: 4,
        hoverRadius: 8
      }
    }
  }
}))

// Chart management functions
function createChart() {
  if (!chartCanvas.value || aggregatedData.value.length === 0) return

  chartInstance = new Chart(chartCanvas.value, chartConfig.value)
}

function updateChart() {
  if (!chartInstance) return

  chartInstance.data = chartData.value
  if (chartConfig.value.options) {
    chartInstance.options = chartConfig.value.options
  }
  chartInstance.update('none') // No animation for performance
}

function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

// Handle chart click events
function onChartClick(event: any) {
  if (chartInstance) {
    const elements = chartInstance.getElementsAtEventForMode(event, 'nearest', { intersect: true }, false)
    if (elements.length > 0) {
      const elementIndex = elements[0].index
      const aggregation = aggregatedData.value[elementIndex]

      emit('data-point-selected', {
        metric: props.metrics[0], // Representative metric
        aggregation
      })
    }
  }
}

// Watchers
watch([() => props.metrics, () => props.timeWindow, () => props.metricType], () => {
  if (chartInstance && aggregatedData.value.length > 0) {
    updateChart()
  } else if (!chartInstance && aggregatedData.value.length > 0) {
    createChart()
  } else if (aggregatedData.value.length === 0) {
    destroyChart()
  }
}, { deep: true })

// Lifecycle hooks
onMounted(() => {
  if (aggregatedData.value.length > 0) {
    createChart()
  }
})

onUnmounted(() => {
  destroyChart()
})

// Expose for testing
defineExpose({
  chartInstance,
  aggregatedData,
  trendAnalysis,
  onChartClick
})
</script>

<style scoped>
.historical-trend-chart {
  @apply w-full h-80 bg-white rounded-lg border border-gray-200 p-4;
}

.chart-container {
  @apply relative h-full w-full;
}

.loading-state,
.empty-state {
  @apply h-full flex items-center justify-center;
}

.trend-indicator {
  @apply rounded-md px-3 py-2 text-sm;
}

.trend-indicator.trend-improving {
  @apply bg-green-50 border border-green-200;
}

.trend-indicator.trend-degrading {
  @apply bg-red-50 border border-red-200;
}

.trend-indicator.trend-stable {
  @apply bg-gray-50 border border-gray-200;
}
</style>
