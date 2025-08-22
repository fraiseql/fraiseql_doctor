<template>
  <div class="historical-trend-chart" data-testid="historical-trend-chart">
    <div v-if="!chartData.length" class="chart-empty-state">
      <p class="text-gray-500">No data available for the selected time window</p>
    </div>
    <v-chart
      v-else
      ref="chart"
      class="chart"
      :option="chartOption"
      :theme="theme || 'light'"
      autoresize
      @click="handleChartClick"
      @brushselected="handleBrushSelection"
      @datazoom="handleDataZoom"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  BrushComponent,
  MarkLineComponent,
  MarkPointComponent
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
  ToolboxComponent,
  BrushComponent,
  MarkLineComponent,
  MarkPointComponent
])

interface Props {
  metrics: QueryMetric[]
  timeWindow: 'hour' | 'day' | 'week' | 'month'
  metricType: 'executionTime' | 'responseSize'
  showTrend?: boolean
  allowZoom?: boolean
  theme?: 'light' | 'dark'
  overlays?: {
    movingAverage?: { enabled: boolean; window: number }
    percentileBands?: { enabled: boolean; percentiles: number[] }
    anomalyHighlights?: { enabled: boolean; threshold: number }
    trendLine?: { enabled: boolean; method: string }
  }
}

const props = withDefaults(defineProps<Props>(), {
  showTrend: true,
  allowZoom: true,
  theme: 'light',
  overlays: () => ({})
})

const emit = defineEmits<{
  'time-range-selected': [{ start: Date; end: Date }]
  'data-point-clicked': [{ metric: QueryMetric; index: number }]
  'zoom-changed': [{ start: number; end: number }]
}>()

const chart = ref()

// Process metrics data for chart display
const chartData = computed(() => {
  if (!props.metrics.length) return []

  return [...props.metrics]
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(metric => ({
      timestamp: new Date(metric.timestamp),
      value: props.metricType === 'executionTime' ? metric.executionTime : metric.responseSize,
      metric
    }))
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

// Calculate percentile bands if enabled
const percentileBands = computed(() => {
  if (!props.overlays?.percentileBands?.enabled || !chartData.value.length) return []

  const percentiles = props.overlays.percentileBands.percentiles || [25, 75, 95]
  const values = chartData.value.map(d => d.value).sort((a, b) => a - b)

  return percentiles.map(p => {
    const index = Math.floor((p / 100) * values.length)
    return {
      percentile: p,
      value: values[index] || 0
    }
  })
})

// Detect anomalies if enabled
const anomalies = computed(() => {
  if (!props.overlays?.anomalyHighlights?.enabled || !chartData.value.length) return []

  const threshold = props.overlays.anomalyHighlights.threshold || 2
  const values = chartData.value.map(d => d.value)
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
  const stdDev = Math.sqrt(variance)

  return chartData.value.filter(d => Math.abs(d.value - mean) > threshold * stdDev)
})

// ECharts option configuration
const chartOption = computed(() => {
  const seriesData = chartData.value.map(d => [d.timestamp.getTime(), d.value])

  const series: any[] = [
    {
      name: props.metricType === 'executionTime' ? 'Execution Time (ms)' : 'Response Size (bytes)',
      type: 'line',
      data: seriesData,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        width: 2,
        color: props.metricType === 'executionTime' ? '#3b82f6' : '#10b981'
      },
      itemStyle: {
        color: props.metricType === 'executionTime' ? '#3b82f6' : '#10b981'
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
      itemStyle: {
        color: '#f59e0b'
      },
      symbol: 'none'
    })
  }

  // Add percentile bands if enabled
  if (percentileBands.value.length > 0) {
    percentileBands.value.forEach((band, index) => {
      series.push({
        name: `P${band.percentile}`,
        type: 'line',
        data: chartData.value.map(d => [d.timestamp.getTime(), band.value]),
        lineStyle: {
          type: 'dashed',
          color: `rgba(99, 102, 241, ${0.3 + index * 0.2})`,
          width: 1
        },
        symbol: 'none'
      })
    })
  }

  // Add anomaly markers
  if (anomalies.value.length > 0) {
    series.push({
      name: 'Anomalies',
      type: 'scatter',
      data: anomalies.value.map(d => [d.timestamp.getTime(), d.value]),
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: {
        color: '#ef4444',
        borderColor: '#fff',
        borderWidth: 2
      },
      tooltip: {
        formatter: (params: any) => {
          const anomaly = anomalies.value[params.dataIndex]
          return `Anomaly detected<br/>
                  Time: ${anomaly.timestamp.toLocaleString()}<br/>
                  Value: ${anomaly.value}<br/>
                  Query: ${anomaly.metric.query?.substring(0, 50) || 'N/A'}...`
        }
      }
    })
  }

  return {
    title: {
      text: props.metricType === 'executionTime' ? 'Query Execution Time' : 'Response Size',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: (params: any) => {
        if (!params.length) return ''
        const time = new Date(params[0].value[0]).toLocaleString()
        let content = `Time: ${time}<br/>`
        params.forEach((param: any) => {
          content += `${param.seriesName}: ${param.value[1]}<br/>`
        })
        return content
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.allowZoom ? '15%' : '3%',
      top: '80px',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      axisLabel: {
        formatter: (value: number) => {
          const date = new Date(value)
          return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      }
    },
    yAxis: {
      type: 'value',
      name: props.metricType === 'executionTime' ? 'Time (ms)' : 'Size (bytes)',
      nameLocation: 'middle',
      nameGap: 50,
      axisLabel: {
        formatter: (value: number) => {
          if (props.metricType === 'responseSize') {
            if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)}MB`
            if (value >= 1024) return `${(value / 1024).toFixed(1)}KB`
            return `${value}B`
          }
          return `${value}ms`
        }
      }
    },
    series,
    dataZoom: props.allowZoom ? [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 40
      }
    ] : undefined,
    brush: props.allowZoom ? {
      toolbox: ['rect', 'polygon', 'clear'],
      xAxisIndex: 0
    } : undefined,
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {},
        saveAsImage: {}
      }
    },
    animation: true,
    animationDuration: 300
  }
})

// Event handlers
const handleChartClick = (params: any) => {
  if (params.data && params.dataIndex !== undefined) {
    const dataPoint = chartData.value[params.dataIndex]
    if (dataPoint) {
      emit('data-point-clicked', { metric: dataPoint.metric, index: params.dataIndex })
    }
  }
}

const handleBrushSelection = (params: any) => {
  if (params.areas && params.areas.length > 0) {
    const area = params.areas[0]
    if (area.coordRange) {
      const start = new Date(area.coordRange[0][0])
      const end = new Date(area.coordRange[0][1])
      emit('time-range-selected', { start, end })
    }
  }
}

const handleDataZoom = (params: any) => {
  emit('zoom-changed', { start: params.start, end: params.end })
}

// Chart resize handler
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (chart.value && chart.value.$el) {
    resizeObserver = new ResizeObserver(() => {
      chart.value?.resize()
    })
    resizeObserver.observe(chart.value.$el)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// Watch for prop changes to update chart
watch([() => props.metrics, () => props.metricType, () => props.timeWindow], () => {
  // Chart will automatically update due to reactive computed properties
}, { deep: true })

// Public methods for parent components
defineExpose({
  updateChart: () => {
    chart.value?.resize()
  },
  exportChart: (type: 'png' | 'jpg' | 'svg' = 'png') => {
    return chart.value?.getDataURL({ type, pixelRatio: 2 })
  },
  setZoom: (start: number, end: number) => {
    chart.value?.dispatchAction({
      type: 'dataZoom',
      start,
      end
    })
  },
  handleChartClick,
  handleBrushSelection,
  handleDataZoom,
  // Expose computed properties for testing
  movingAverageData,
  anomalies,
  percentileBands,
  chartOption
})
</script>

<style scoped>
.historical-trend-chart {
  width: 100%;
  height: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart {
  width: 100%;
  height: 100%;
}

.chart-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f9fafb;
  border-radius: 8px;
  border: 2px dashed #d1d5db;
}

.dark .historical-trend-chart {
  background: #1f2937;
}

.dark .chart-empty-state {
  background: #374151;
  border-color: #4b5563;
}
</style>
