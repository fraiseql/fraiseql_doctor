<template>
  <div class="interactive-time-series-chart" data-testid="time-series-chart">
    <!-- Chart Canvas -->
    <div class="chart-container relative">
      <canvas ref="chartCanvas" class="w-full h-96"></canvas>

      <!-- Crosshair Overlay -->
      <div
        v-if="crosshairPosition.visible"
        class="absolute pointer-events-none"
        :style="{
          left: crosshairPosition.x + 'px',
          top: crosshairPosition.y + 'px'
        }"
      >
        <div class="crosshair-vertical absolute w-px h-full bg-gray-400 opacity-50"></div>
        <div class="crosshair-horizontal absolute h-px w-full bg-gray-400 opacity-50"></div>
      </div>
    </div>

    <!-- Control Panel -->
    <div class="control-panel mt-4 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <!-- Resolution Selector -->
        <select v-model="currentResolution" class="form-select text-sm">
          <option value="minute">1 Minute</option>
          <option value="5minute">5 Minutes</option>
          <option value="hour">1 Hour</option>
          <option value="day">1 Day</option>
        </select>

        <!-- Overlay Controls -->
        <div class="flex items-center space-x-2">
          <label class="flex items-center">
            <input
              v-model="showMovingAverage"
              type="checkbox"
              class="form-checkbox h-4 w-4"
            >
            <span class="ml-2 text-sm">Moving Average</span>
          </label>

          <label class="flex items-center">
            <input
              v-model="showPercentileBands"
              type="checkbox"
              class="form-checkbox h-4 w-4"
            >
            <span class="ml-2 text-sm">Percentile Bands</span>
          </label>

          <label class="flex items-center">
            <input
              v-model="showAnomalies"
              type="checkbox"
              class="form-checkbox h-4 w-4"
            >
            <span class="ml-2 text-sm">Anomalies</span>
          </label>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-2">
        <button
          @click="resetZoom"
          class="btn btn-sm btn-outline"
        >
          Reset Zoom
        </button>

        <button
          @click="exportToCSV"
          class="btn btn-sm btn-primary"
        >
          Export CSV
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
import type { QueryMetric } from '../services/performanceMonitor'

Chart.register(...registerables, zoomPlugin)

interface Props {
  metrics: QueryMetric[]
  metric: string
  realTimeUpdates?: boolean
  resolution?: string
  timeRange?: {
    start: Date
    end: Date
  }
  autoTimeWindow?: boolean
  windowSize?: number
  showMovingAverage?: boolean
  movingAverageWindow?: number
  showPercentileBands?: boolean
  percentiles?: number[]
  showAnomalies?: boolean
  anomalyThreshold?: number
  maxDataPoints?: number
}

const props = withDefaults(defineProps<Props>(), {
  metric: 'executionTime',
  realTimeUpdates: false,
  resolution: 'auto',
  movingAverageWindow: 20,
  percentiles: () => [25, 75, 95],
  anomalyThreshold: 3,
  maxDataPoints: 1000
})

const emit = defineEmits<{
  'time-range-selected': [{ start: Date; end: Date }]
  'drill-down': [{ dataPoint: any; timeRange: any }]
  'data-updated': [any]
  'annotation-added': [any]
}>()

// Reactive state
const chartCanvas = ref<HTMLCanvasElement>()
const chartInstance = ref<Chart>()
const currentResolution = ref(props.resolution)
const showMovingAverage = ref(props.showMovingAverage)
const showPercentileBands = ref(props.showPercentileBands)
const showAnomalies = ref(props.showAnomalies)
const selectedTimeRange = ref<{ start: Date; end: Date } | null>(null)
const crosshairPosition = ref({ x: 0, y: 0, visible: false })
const animationQueue = ref<any[]>([])
const annotations = ref<any[]>([])

// Computed properties
const optimalResolution = computed(() => {
  if (!props.timeRange) return 'minute'

  const duration = props.timeRange.end.getTime() - props.timeRange.start.getTime()
  const hours = duration / (1000 * 60 * 60)

  if (hours <= 1) return 'minute'
  if (hours <= 24) return '5minute'
  if (hours <= 168) return 'hour'
  return 'day'
})

const displayTimeRange = computed(() => {
  if (props.autoTimeWindow && props.windowSize) {
    return {
      start: new Date(Date.now() - props.windowSize * 60 * 1000),
      end: new Date(),
      duration: props.windowSize * 60 * 1000
    }
  }
  return props.timeRange
})

const displayData = computed(() => {
  let data = [...props.metrics]

  // Apply time range filter
  if (displayTimeRange.value) {
    data = data.filter(m =>
      m.timestamp >= displayTimeRange.value!.start &&
      m.timestamp <= displayTimeRange.value!.end
    )
  }

  // Apply data decimation for large datasets
  if (data.length > props.maxDataPoints) {
    const step = Math.ceil(data.length / props.maxDataPoints)
    data = data.filter((_, index) => index % step === 0)
  }

  return data
})

// Removed unused computed properties

// Removed unused visibleDataRange

const chartData = computed(() => {
  const baseData = displayData.value.map(m => ({
    x: m.timestamp,
    y: m[props.metric as keyof QueryMetric] as number
  }))

  const datasets: any[] = [
    {
      label: props.metric,
      data: baseData,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: false,
      tension: 0.1
    }
  ]

  // Add moving average
  if (showMovingAverage.value) {
    const movingAvgData = calculateMovingAverage(baseData, props.movingAverageWindow)
    datasets.push({
      label: `Moving Average (${props.movingAverageWindow} periods)`,
      data: movingAvgData,
      borderColor: '#ff6b6b',
      backgroundColor: 'transparent',
      fill: false,
      borderWidth: 2
    })
  }

  // Add percentile bands
  if (showPercentileBands.value) {
    const values = baseData.map(d => d.y).sort((a, b) => a - b)

    for (const percentile of props.percentiles) {
      const value = getPercentile(values, percentile)
      datasets.push({
        label: `P${percentile}`,
        data: baseData.map(d => ({ x: d.x, y: value })),
        borderColor: getPercentileColor(percentile),
        backgroundColor: `${getPercentileColor(percentile)}20`,
        fill: percentile === 75 ? '+1' : false, // Fill between P25 and P75
        borderWidth: 1,
        pointRadius: 0
      })
    }
  }

  // Add anomaly overlay
  if (showAnomalies.value) {
    const anomalies = detectAnomalies(baseData)
    datasets.push({
      label: 'Anomalies',
      data: anomalies,
      backgroundColor: '#ff4757',
      pointBackgroundColor: '#ff4757',
      borderColor: 'transparent',
      showLine: false,
      pointRadius: 6,
      pointHoverRadius: 8
    })
  }

  return { datasets }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: props.realTimeUpdates ? 300 : 750
  },
  interaction: {
    intersect: false,
    mode: 'index' as const
  },
  plugins: {
    legend: {
      labels: {
        color: '#374151'
      }
    },
    zoom: {
      pan: {
        enabled: true,
        mode: 'x' as const
      },
      zoom: {
        wheel: {
          enabled: true
        },
        pinch: {
          enabled: true
        },
        mode: 'x' as const
      }
    },
    tooltip: {
      callbacks: {
        title: (context: any) => {
          return new Date(context[0].parsed.x).toLocaleString()
        },
        label: (context: any) => {
          return generateAdvancedTooltip(context)
        }
      }
    },
    annotation: {
      annotations: annotations.value
    }
  },
  scales: {
    x: {
      type: 'time' as const,
      time: {
        displayFormats: {
          minute: 'HH:mm',
          hour: 'MMM DD HH:mm',
          day: 'MMM DD'
        }
      },
      title: {
        display: true,
        text: 'Time'
      }
    },
    y: {
      title: {
        display: true,
        text: getMetricLabel(props.metric)
      },
      beginAtZero: false
    }
  },
  onHover: handleChartHover,
  onClick: handleChartClick
}))

// Methods
function initializeChart() {
  if (!chartCanvas.value) return

  chartInstance.value = new Chart(chartCanvas.value, {
    type: 'line',
    data: chartData.value,
    options: chartOptions.value
  })
}

function updateChart() {
  if (!chartInstance.value) return

  // Limit animation queue
  if (animationQueue.value.length > 3) {
    animationQueue.value = animationQueue.value.slice(-2)
  }

  chartInstance.value.data = chartData.value
  chartInstance.value.options = chartOptions.value
  chartInstance.value.update('none') // Skip animation for performance
}

// Removed unused updateChartDebounced

// Removed unused _handleDataUpdate

function handleChartHover(_event: any, _elements: any) {
  if (!chartCanvas.value) return

  const rect = chartCanvas.value.getBoundingClientRect()
  crosshairPosition.value = {
    x: (_event as MouseEvent).clientX - rect.left,
    y: (_event as MouseEvent).clientY - rect.top,
    visible: true
  }
}

function handleChartClick(event: any) {
  const elements = chartInstance.value?.getElementsAtEventForMode(
    event.native,
    'nearest',
    { intersect: true },
    true
  )

  if (elements && elements.length > 0) {
    const dataIndex = elements[0].index
    const dataPoint = displayData.value[dataIndex]

    emit('drill-down', {
      dataPoint,
      timeRange: {
        start: new Date(dataPoint.timestamp.getTime() - 30 * 60000),
        end: new Date(dataPoint.timestamp.getTime() + 30 * 60000)
      }
    })
  }
}

function generateAdvancedTooltip(context: any): string {
  const dataPoint = context.dataset.data[context.dataIndex]
  const value = dataPoint.y

  // Calculate baseline comparison (simplified)
  const allValues = displayData.value.map(m => m[props.metric as keyof QueryMetric] as number)
  const mean = allValues.reduce((sum, v) => sum + v, 0) / allValues.length
  const percentile = getPercentileRank(allValues, value)

  return [
    `${getMetricLabel(props.metric)}: ${value.toFixed(2)}`,
    `vs Baseline: ${((value - mean) / mean * 100).toFixed(1)}%`,
    `Percentile: ${percentile.toFixed(1)}%`,
    `Trend: ${getTrendDirection(context.dataIndex)}`
  ].join('\n')
}

function resetZoom() {
  chartInstance.value?.resetZoom()
}

function exportToCSV(): string {
  const headers = ['timestamp', 'executionTime', 'responseSize']
  const rows = [headers.join(',')]

  const dataToExport = selectedTimeRange.value
    ? displayData.value.filter(m =>
        m.timestamp >= selectedTimeRange.value!.start &&
        m.timestamp <= selectedTimeRange.value!.end
      )
    : displayData.value

  for (const metric of dataToExport) {
    rows.push([
      metric.timestamp.toISOString(),
      metric.executionTime.toString(),
      metric.responseSize.toString()
    ].join(','))
  }

  const csvContent = rows.join('\n')

  // Create download link
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `metrics_${Date.now()}.csv`
  link.click()

  return csvContent
}

// Removed unused _generateStatisticalSummary

// Removed unused _addAnnotation

// Removed unused _setViewport

// Removed unused _aggregateToResolution

// Helper functions
function calculateMovingAverage(data: any[], window: number) {
  return data.map((_, index) => {
    const start = Math.max(0, index - window + 1)
    const slice = data.slice(start, index + 1)
    const avg = slice.reduce((sum, d) => sum + d.y, 0) / slice.length
    return { x: data[index].x, y: avg }
  })
}

function getPercentile(values: number[], percentile: number): number {
  const index = Math.ceil((percentile / 100) * values.length) - 1
  return values[Math.max(0, Math.min(index, values.length - 1))]
}

function getPercentileRank(values: number[], value: number): number {
  const sorted = [...values].sort((a, b) => a - b)
  const index = sorted.findIndex(v => v >= value)
  return (index / sorted.length) * 100
}

function getPercentileColor(percentile: number): string {
  const colors = {
    25: '#10b981',
    50: '#3b82f6',
    75: '#f59e0b',
    90: '#ef4444',
    95: '#dc2626',
    99: '#991b1b'
  }
  return colors[percentile as keyof typeof colors] || '#6b7280'
}

function detectAnomalies(data: any[]) {
  const values = data.map(d => d.y)
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length
  const std = Math.sqrt(values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length)
  const threshold = mean + props.anomalyThreshold * std

  return data.filter(d => d.y > threshold)
}

function getMetricLabel(metric: string): string {
  const labels = {
    executionTime: 'Execution Time (ms)',
    responseSize: 'Response Size (bytes)',
    errorRate: 'Error Rate (%)'
  }
  return labels[metric as keyof typeof labels] || metric
}

function getTrendDirection(index: number): string {
  if (index < 2) return 'stable'
  const current = displayData.value[index]?.[props.metric as keyof QueryMetric] as number
  const previous = displayData.value[index - 1]?.[props.metric as keyof QueryMetric] as number
  return current > previous ? 'increasing' : 'decreasing'
}

// Removed unused getResolutionWindow

// Removed unused debounce function

// Lifecycle
onMounted(async () => {
  await nextTick()
  initializeChart()
})

onUnmounted(() => {
  chartInstance.value?.destroy()
})

// Watchers
watch(() => props.metrics, () => {
  emit('data-updated', props.metrics)
  updateChart()
}, { deep: true })

watch(chartData, updateChart, { deep: true })

watch(currentResolution, (newResolution) => {
  if (newResolution === 'auto') {
    currentResolution.value = optimalResolution.value
  }
  updateChart()
})
</script>

<style scoped>
.form-select {
  @apply block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500;
}

.form-checkbox {
  @apply rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50;
}

.btn {
  @apply inline-flex items-center px-3 py-1.5 border font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-sm {
  @apply text-xs;
}

.btn-outline {
  @apply border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-gray-500;
}

.btn-primary {
  @apply border-transparent text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500;
}
</style>
