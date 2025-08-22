<template>
  <div
    class="metric-chart"
    :data-testid="`metric-chart-${metricType}`"
  >
    <div class="chart-header">
      <h3 class="chart-title">{{ chartTitle }}</h3>
      <div class="chart-controls">
        <button
          v-if="allowZoom"
          @click="resetZoom"
          class="chart-control-btn"
          data-testid="reset-zoom-btn"
        >
          Reset Zoom
        </button>
      </div>
    </div>

    <div v-if="!chartData.length" class="chart-empty-state">
      <p class="text-gray-500">No data available</p>
    </div>

    <v-chart
      v-else
      ref="chart"
      class="chart"
      :option="chartOption"
      :theme="theme || 'light'"
      autoresize
      @click="handleChartClick"
      @datazoom="handleDataZoom"
      @finished="handleChartReady"
    />

    <!-- Chart overlays -->
    <div v-if="overlays?.movingAverage?.enabled" class="chart-overlay">
      <div
        class="overlay-indicator bg-blue-100"
        data-testid="overlay-moving-average"
      >
        MA({{ overlays.movingAverage.window }})
      </div>
    </div>

    <div v-if="overlays?.percentileBands?.enabled" class="chart-overlay">
      <div
        class="overlay-indicator bg-blue-100"
        data-testid="overlay-percentile-bands"
      >
        Percentile Bands
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { QueryMetric } from '../services/performanceMonitor'

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
])

interface Props {
  metricType: 'executionTime' | 'responseSize' | 'errorRate'
  metrics: QueryMetric[]
  theme?: 'light' | 'dark'
  allowZoom?: boolean
  globalTimeRange?: { start: Date; end: Date }
  overlays?: {
    movingAverage?: { enabled: boolean; window: number }
    percentileBands?: { enabled: boolean; percentiles: number[] }
    anomalyHighlights?: { enabled: boolean; threshold: number }
    trendLine?: { enabled: boolean; method: string }
  }
  synchronized?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'light',
  allowZoom: true,
  synchronized: false,
  overlays: () => ({})
})

const emit = defineEmits<{
  'zoom-changed': [{ start: number; end: number; metricType: string }]
  'data-point-selected': [{ metric: QueryMetric; metricType: string }]
}>()

const chart = ref()

// Computed properties
const chartTitle = computed(() => {
  switch (props.metricType) {
    case 'executionTime':
      return 'Execution Time'
    case 'responseSize':
      return 'Response Size'
    case 'errorRate':
      return 'Error Rate'
    default:
      return 'Metric'
  }
})

const chartData = computed(() => {
  if (!props.metrics.length) return []

  let filteredMetrics = props.metrics

  // Apply global time range filter if provided
  if (props.globalTimeRange) {
    filteredMetrics = props.metrics.filter(metric => {
      const timestamp = new Date(metric.timestamp)
      return timestamp >= props.globalTimeRange!.start && timestamp <= props.globalTimeRange!.end
    })
  }

  return filteredMetrics
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(metric => {
      let value: number
      switch (props.metricType) {
        case 'executionTime':
          value = metric.executionTime
          break
        case 'responseSize':
          value = metric.responseSize
          break
        case 'errorRate':
          // Calculate error rate from the metric (this would need to be calculated properly)
          value = metric.errors ? 1 : 0
          break
        default:
          value = 0
      }

      return {
        timestamp: new Date(metric.timestamp),
        value,
        metric
      }
    })
})

// Calculate moving average if enabled
const movingAverageData = computed(() => {
  if (!props.overlays?.movingAverage?.enabled || !chartData.value.length) return []

  const window = props.overlays.movingAverage.window || 5
  const result: { timestamp: Date; value: number }[] = []

  for (let i = window - 1; i < chartData.value.length; i++) {
    const slice = chartData.value.slice(i - window + 1, i + 1)
    const avg = slice.reduce((sum, item) => sum + item.value, 0) / window
    result.push({
      timestamp: chartData.value[i].timestamp,
      value: avg
    })
  }

  return result
})

const chartOption = computed(() => {
  const seriesData = chartData.value.map(d => [d.timestamp.getTime(), d.value])

  const series: any[] = [
    {
      name: chartTitle.value,
      type: 'line',
      data: seriesData,
      smooth: true,
      symbol: 'circle',
      symbolSize: 3,
      lineStyle: {
        width: 2,
        color: getChartColor()
      },
      itemStyle: {
        color: getChartColor()
      },
      areaStyle: {
        opacity: 0.1,
        color: getChartColor()
      }
    }
  ]

  // Add moving average series
  if (movingAverageData.value.length > 0) {
    series.push({
      name: 'Moving Average',
      type: 'line',
      data: movingAverageData.value.map(d => [d.timestamp.getTime(), d.value]),
      smooth: true,
      lineStyle: {
        width: 1,
        color: '#f59e0b',
        type: 'dashed'
      },
      symbol: 'none'
    })
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        if (!params.length) return ''
        const time = new Date(params[0].value[0]).toLocaleString()
        let content = `Time: ${time}<br/>`
        params.forEach((param: any) => {
          const value = formatValue(param.value[1])
          content += `${param.seriesName}: ${value}<br/>`
        })
        return content
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.allowZoom ? '15%' : '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      axisLabel: {
        fontSize: 11,
        formatter: (value: number) => {
          const date = new Date(value)
          return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 11,
        formatter: (value: number) => formatValue(value)
      }
    },
    series,
    dataZoom: props.allowZoom ? [
      {
        type: 'inside',
        start: 0,
        end: 100
      }
    ] : undefined,
    animation: true,
    animationDuration: 300
  }
})

// Helper functions
function getChartColor(): string {
  switch (props.metricType) {
    case 'executionTime':
      return '#3b82f6'
    case 'responseSize':
      return '#10b981'
    case 'errorRate':
      return '#ef4444'
    default:
      return '#6b7280'
  }
}

function formatValue(value: number): string {
  switch (props.metricType) {
    case 'executionTime':
      return `${value}ms`
    case 'responseSize':
      if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)}MB`
      if (value >= 1024) return `${(value / 1024).toFixed(1)}KB`
      return `${value}B`
    case 'errorRate':
      return `${(value * 100).toFixed(2)}%`
    default:
      return value.toString()
  }
}

// Event handlers
const handleChartClick = (params: any) => {
  if (params.data && params.dataIndex !== undefined) {
    const dataPoint = chartData.value[params.dataIndex]
    if (dataPoint) {
      emit('data-point-selected', { metric: dataPoint.metric, metricType: props.metricType })
    }
  }
}

const handleDataZoom = (params: any) => {
  if (props.synchronized) {
    emit('zoom-changed', { start: params.start, end: params.end, metricType: props.metricType })
  }
}

const handleChartReady = () => {
  // Chart is ready for interaction
}

const resetZoom = () => {
  chart.value?.dispatchAction({
    type: 'dataZoom',
    start: 0,
    end: 100
  })
}

// Watch for external zoom changes when synchronized
watch(() => props.globalTimeRange, () => {
  nextTick(() => {
    chart.value?.resize()
  })
}, { deep: true })

// Public methods
defineExpose({
  updateChart: () => {
    chart.value?.resize()
  },
  setZoom: (start: number, end: number) => {
    chart.value?.dispatchAction({
      type: 'dataZoom',
      start,
      end
    })
  },
  exportChart: (type: 'png' | 'jpg' | 'svg' = 'png') => {
    return chart.value?.getDataURL({ type, pixelRatio: 2 })
  },
  resetZoom,
  handleChartClick,
  handleDataZoom,
  // Expose computed properties for testing
  chartData
})
</script>

<style scoped>
.metric-chart {
  position: relative;
  width: 100%;
  height: 300px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.chart-controls {
  display: flex;
  gap: 8px;
}

.chart-control-btn {
  padding: 4px 8px;
  font-size: 12px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.chart-control-btn:hover {
  background: #e5e7eb;
}

.chart {
  width: 100%;
  height: calc(100% - 40px);
}

.chart-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(100% - 40px);
  background: #f9fafb;
  border-radius: 4px;
  border: 2px dashed #d1d5db;
}

.chart-overlay {
  position: absolute;
  top: 50px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overlay-indicator {
  padding: 2px 6px;
  font-size: 10px;
  border-radius: 3px;
  background: rgba(59, 130, 246, 0.1);
  color: #1d4ed8;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.dark .metric-chart {
  background: #1f2937;
  border-color: #374151;
}

.dark .chart-title {
  color: #f9fafb;
}

.dark .chart-control-btn {
  background: #374151;
  border-color: #4b5563;
  color: #f9fafb;
}

.dark .chart-control-btn:hover {
  background: #4b5563;
}

.dark .chart-empty-state {
  background: #374151;
  border-color: #4b5563;
}
</style>
