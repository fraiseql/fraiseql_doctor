<template>
  <div class="performance-chart" data-testid="performance-chart">
    <div v-if="metrics.length === 0" class="no-data-message" data-testid="no-data-message">
      <div class="text-center text-gray-500 p-8">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No data available</h3>
        <p class="mt-1 text-sm text-gray-500">No performance metrics to display yet.</p>
      </div>
    </div>
    <div v-else class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { Chart, type ChartConfiguration } from 'chart.js/auto'
import type { QueryMetric } from '../services/performanceMonitor'

interface Props {
  metrics: QueryMetric[]
  chartType: 'responseTime' | 'responseSize'
}

const props = defineProps<Props>()

const chartCanvas = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null

const chartData = computed(() => {
  if (props.metrics.length === 0) {
    return {
      labels: [],
      datasets: []
    }
  }

  const labels = props.metrics.map(metric => {
    const date = new Date(metric.timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  })

  const dataset = {
    label: props.chartType === 'responseTime' ? 'Response Time (ms)' : 'Response Size (bytes)',
    data: props.metrics.map(metric =>
      props.chartType === 'responseTime' ? metric.executionTime : metric.responseSize
    ),
    backgroundColor: props.chartType === 'responseTime'
      ? 'rgba(59, 130, 246, 0.1)'
      : 'rgba(16, 185, 129, 0.1)',
    borderColor: props.chartType === 'responseTime'
      ? 'rgb(59, 130, 246)'
      : 'rgb(16, 185, 129)',
    borderWidth: 2,
    fill: true,
    tension: 0.4
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
    plugins: {
      legend: {
        display: true,
        position: 'top'
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || ''
            const value = context.parsed.y
            const unit = props.chartType === 'responseTime' ? 'ms' : 'bytes'
            return `${label}: ${value} ${unit}`
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time'
        },
        grid: {
          display: false
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: props.chartType === 'responseTime' ? 'Response Time (ms)' : 'Response Size (bytes)'
        },
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    },
    elements: {
      point: {
        radius: 3,
        hoverRadius: 6
      }
    }
  }
}))

function createChart() {
  if (!chartCanvas.value) return

  chartInstance = new Chart(chartCanvas.value, chartConfig.value)
}

function updateChart() {
  if (!chartInstance) return

  chartInstance.data = chartData.value
  chartInstance.update('none') // No animation for real-time updates
}

function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

// Watch for metrics and chart type changes
watch([() => props.metrics, () => props.chartType], () => {
  if (chartInstance) {
    updateChart()
  } else if (props.metrics.length > 0) {
    createChart()
  }
}, { deep: true })

onMounted(() => {
  if (props.metrics.length > 0) {
    createChart()
  }
})

onUnmounted(() => {
  destroyChart()
})

// Expose chart instance for testing
defineExpose({
  chartInstance
})
</script>

<style scoped>
.performance-chart {
  @apply w-full h-64 bg-white rounded-lg border border-gray-200 p-4;
}

.chart-container {
  @apply relative h-full w-full;
}

.no-data-message {
  @apply h-full flex items-center justify-center;
}
</style>
