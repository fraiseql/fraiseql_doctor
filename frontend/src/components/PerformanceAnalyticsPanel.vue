<template>
  <div class="performance-analytics-panel" data-testid="performance-analytics-panel">
    <!-- Loading State -->
    <div v-if="loading" class="analytics-loading" data-testid="analytics-loading">
      <div class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p class="mt-2 text-sm text-gray-500">Analyzing performance data...</p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="metrics.length === 0" class="empty-analytics-state" data-testid="empty-analytics-state">
      <div class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h3 class="mt-2 text-lg font-medium text-gray-900">No analytics data available</h3>
        <p class="mt-1 text-sm text-gray-500">Performance analytics will appear here once sufficient data is collected.</p>
      </div>
    </div>

    <!-- Analytics Dashboard -->
    <div v-else class="analytics-dashboard space-y-6">
      <!-- Control Panel -->
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900">Performance Analytics</h3>

        <div class="flex items-center space-x-4">
          <!-- Time Window Selector -->
          <select
            v-model="selectedTimeWindow"
            class="block w-32 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            data-testid="time-window-select"
          >
            <option value="hour">Hourly</option>
            <option value="day">Daily</option>
            <option value="week">Weekly</option>
            <option value="month">Monthly</option>
          </select>

          <!-- Metric Type Toggle -->
          <div class="flex bg-gray-100 rounded-lg p-1" data-testid="metric-type-toggle">
            <button
              @click="selectedMetricType = 'executionTime'"
              :class="[
                'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                selectedMetricType === 'executionTime'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              Response Time
            </button>
            <button
              @click="selectedMetricType = 'responseSize'"
              :class="[
                'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                selectedMetricType === 'responseSize'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
              data-testid="response-size-button"
            >
              Response Size
            </button>
          </div>

          <!-- Export Button -->
          <button
            @click="exportAnalytics"
            class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            data-testid="export-analytics-button"
          >
            <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export
          </button>
        </div>
      </div>

      <!-- Key Metrics Row -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- Trend Analysis -->
        <div
          class="trend-analysis-card bg-white p-4 rounded-lg border border-gray-200"
          data-testid="trend-analysis-section"
          :class="`trend-${trendAnalysis?.direction || 'stable'}`"
        >
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <!-- Improving Trend -->
              <svg v-if="trendAnalysis?.direction === 'improving'" data-testid="trend-arrow-up" class="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17L17 7M17 7H7M17 7v10" />
              </svg>

              <!-- Degrading Trend -->
              <svg v-else-if="trendAnalysis?.direction === 'degrading'" data-testid="trend-arrow-down" class="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7L7 17M7 17h10M7 17V7" />
              </svg>

              <!-- Stable Trend -->
              <svg v-else class="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14" />
              </svg>
            </div>

            <div class="ml-3">
              <p class="text-sm font-medium text-gray-500">Trend</p>
              <p class="text-lg font-semibold" :class="{
                'text-green-600': trendAnalysis?.direction === 'improving',
                'text-red-600': trendAnalysis?.direction === 'degrading',
                'text-gray-600': trendAnalysis?.direction === 'stable'
              }">
                Performance {{ trendAnalysis?.direction || 'stable' }}
              </p>
              <p class="text-xs text-gray-500">
                {{ Math.abs(trendAnalysis?.changePercentage || 0).toFixed(1) }}% change
              </p>
            </div>
          </div>
        </div>

        <!-- Percentiles Display -->
        <div class="percentiles-grid col-span-3 grid grid-cols-4 gap-4" data-testid="percentiles-section">
          <div
            v-for="(percentile, key) in percentiles"
            :key="key"
            class="percentile-card bg-white p-4 rounded-lg border border-gray-200"
            :class="getPercentileClass(percentile)"
            :data-testid="`${key}-metric`"
          >
            <p class="text-sm font-medium text-gray-500">{{ key.toUpperCase() }}</p>
            <p class="text-2xl font-bold text-gray-900">
              {{ formatMetricValue(percentile) }}
            </p>
            <p class="text-xs text-gray-500">
              {{ selectedMetricType === 'executionTime' ? 'ms' : 'bytes' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Historical Trend Chart -->
      <div class="historical-chart-section">
        <HistoricalTrendChart
          :metrics="metrics"
          :time-window="selectedTimeWindow"
          :metric-type="selectedMetricType"
          :show-trend="true"
          :allow-zoom="true"
          @data-point-selected="onDataPointSelected"
        />
      </div>

      <!-- Anomalies Section -->
      <div class="anomalies-section" data-testid="anomalies-section">
        <h4 class="text-lg font-medium text-gray-900 mb-4">Anomaly Detection</h4>

        <div v-if="anomalies.length === 0" class="text-center py-8">
          <svg class="mx-auto h-8 w-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="mt-2 text-sm text-gray-500">No anomalies detected</p>
          <p class="text-xs text-gray-400">Performance is within expected parameters</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="anomaly in anomalies.slice(0, 5)"
            :key="anomaly.metric.id"
            class="anomaly-item bg-white border rounded-lg p-4"
            :class="`border-${getSeverityColor(anomaly.severity)}-200 bg-${getSeverityColor(anomaly.severity)}-50 severity-${anomaly.severity}`"
            :data-testid="`anomaly-severity-${anomaly.severity}`"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div
                  class="w-3 h-3 rounded-full"
                  :class="`bg-${getSeverityColor(anomaly.severity)}-500`"
                ></div>
                <div>
                  <p class="text-sm font-medium text-gray-900">
                    Performance anomaly detected
                  </p>
                  <p class="text-xs text-gray-500">
                    {{ formatMetricValue(anomaly.metric[selectedMetricType]) }}
                    {{ selectedMetricType === 'executionTime' ? 'ms' : 'bytes' }}
                    (Expected: {{ formatMetricValue(anomaly.expectedValue) }})
                  </p>
                </div>
              </div>

              <div class="text-right">
                <p class="text-sm font-medium" :class="`text-${getSeverityColor(anomaly.severity)}-600 severity-${anomaly.severity}`">
                  {{ anomaly.severity.toUpperCase() }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ anomaly.deviationScore.toFixed(1) }}σ deviation
                </p>
              </div>
            </div>
          </div>

          <div v-if="anomalies.length > 5" class="text-center">
            <p class="text-sm text-gray-500">
              {{ anomalies.length - 5 }} more anomalies detected
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import HistoricalTrendChart from './HistoricalTrendChart.vue'
import type { QueryMetric } from '../services/performanceMonitor'
import type { MetricField, TimeWindow } from '../services/performanceAnalytics'
import { PerformanceAnalytics } from '../services/performanceAnalytics'

interface Props {
  metrics: QueryMetric[]
  endpointId: string
  loading?: boolean
  thresholds?: {
    warning: number
    critical: number
  }
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  thresholds: () => ({
    warning: 500, // 500ms for execution time
    critical: 1000 // 1000ms for execution time
  })
})

const emit = defineEmits<{
  'export-analytics': [data: any]
  'anomaly-selected': [anomaly: any]
  'data-point-selected': [data: any]
}>()

// State
const selectedTimeWindow = ref<TimeWindow>('hour')
const selectedMetricType = ref<MetricField>('executionTime')

// Analytics instance
const analytics = new PerformanceAnalytics()

// Computed analytics
const trendAnalysis = computed(() => {
  if (props.metrics.length < 2) return null
  return analytics.calculatePerformanceTrend(props.metrics, selectedMetricType.value)
})

const percentiles = computed(() => {
  if (props.metrics.length === 0) return { p50: 0, p90: 0, p95: 0, p99: 0 }
  return analytics.calculatePercentiles(props.metrics, selectedMetricType.value)
})

const anomalies = computed(() => {
  if (props.metrics.length < 10) return []
  return analytics.detectAnomalies(props.metrics, selectedMetricType.value)
})

// Helper functions
function formatMetricValue(value: number): string {
  if (selectedMetricType.value === 'executionTime') {
    return value.toFixed(1)
  } else {
    // Format bytes with appropriate units
    if (value < 1024) return value.toFixed(0)
    if (value < 1024 * 1024) return (value / 1024).toFixed(1) + 'K'
    return (value / (1024 * 1024)).toFixed(1) + 'M'
  }
}

function getSeverityColor(severity: 'low' | 'medium' | 'high'): string {
  switch (severity) {
    case 'low': return 'yellow'
    case 'medium': return 'orange'
    case 'high': return 'red'
  }
}

function getPercentileClass(value: number): string {
  if (selectedMetricType.value === 'executionTime') {
    if (value > props.thresholds.critical) return 'percentile-critical'
    if (value > props.thresholds.warning) return 'percentile-warning'
  }
  return ''
}

// Event handlers
function exportAnalytics() {
  const exportData = {
    endpointId: props.endpointId,
    metrics: props.metrics,
    trend: trendAnalysis.value,
    percentiles: percentiles.value,
    anomalies: anomalies.value,
    timeWindow: selectedTimeWindow.value,
    metricType: selectedMetricType.value,
    exportedAt: new Date().toISOString()
  }

  emit('export-analytics', exportData)
}

function onDataPointSelected(data: any) {
  emit('data-point-selected', data)
}

// Expose for testing
defineExpose({
  selectedTimeWindow,
  selectedMetricType,
  trendAnalysis,
  percentiles,
  anomalies
})
</script>

<style scoped>
.performance-analytics-panel {
  @apply w-full bg-gray-50 rounded-lg p-6;
}

.trend-analysis-card.trend-improving {
  @apply bg-green-50 border-green-200;
}

.trend-analysis-card.trend-degrading {
  @apply bg-red-50 border-red-200;
}

.trend-analysis-card.trend-stable {
  @apply bg-gray-50 border-gray-200;
}

.percentile-card.percentile-warning {
  @apply bg-yellow-50 border-yellow-200;
}

.percentile-card.percentile-critical {
  @apply bg-red-50 border-red-200;
}

.historical-chart-section {
  @apply bg-white rounded-lg p-4;
}

.anomaly-item:hover {
  @apply shadow-sm;
}
</style>
