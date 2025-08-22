<template>
  <div class="real-time-analytics-dashboard">
    <!-- Connection Status -->
    <div class="connection-status mb-4 flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <div
          class="status-indicator w-3 h-3 rounded-full"
          :class="{
            'bg-green-500': connectionStatus === 'connected',
            'bg-yellow-500': connectionStatus === 'reconnecting',
            'bg-red-500': connectionStatus === 'disconnected'
          }"
          data-testid="connection-status"
        ></div>
        <span class="text-sm font-medium">
          {{ connectionStatus === 'connected' ? 'Connected' :
             connectionStatus === 'reconnecting' ? 'Reconnecting...' : 'Disconnected' }}
        </span>
        <span v-if="reconnectAttempts > 0" class="text-xs text-gray-500">
          (Attempt {{ reconnectAttempts }})
        </span>
      </div>

      <!-- Real-time Toggle -->
      <div class="flex items-center space-x-2">
        <label class="flex items-center">
          <input
            v-model="realTimeEnabled"
            type="checkbox"
            class="form-checkbox h-4 w-4"
          >
          <span class="ml-2 text-sm">Real-time Updates</span>
        </label>
      </div>
    </div>

    <!-- KPI Dashboard -->
    <div class="kpi-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <!-- Throughput KPI -->
      <div
        class="kpi-card p-4 bg-white rounded-lg border-2"
        :class="getKpiStatusClass('throughput')"
        data-testid="throughput-kpi"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-500">Throughput</p>
            <p class="text-2xl font-bold text-gray-900">
              {{ kpiData.currentThroughput?.toFixed(1) || '0.0' }}
              <span class="text-sm text-gray-500">req/min</span>
            </p>
          </div>
          <div
            class="trend-indicator"
            :class="getTrendClass('throughput')"
            data-testid="throughput-trend"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              :data-icon="getTrendIcon('throughput')"
            >
              <path
                v-if="getTrendIcon('throughput') === 'arrow-up'"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 17L17 7M17 7H7M17 7v10"
              />
              <path
                v-else-if="getTrendIcon('throughput') === 'arrow-down'"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 7L7 17M7 17h10M7 17V7"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- Latency KPI -->
      <div
        class="kpi-card p-4 bg-white rounded-lg border-2"
        :class="getKpiStatusClass('latency')"
        data-testid="latency-kpi"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-500">Avg Latency</p>
            <p class="text-2xl font-bold text-gray-900">
              {{ kpiData.averageLatency?.toFixed(1) || '0.0' }}
              <span class="text-sm text-gray-500">ms</span>
            </p>
          </div>
          <div
            class="trend-indicator"
            :class="getTrendClass('latency')"
            data-testid="latency-trend"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                v-if="getTrendIcon('latency') === 'arrow-down'"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 7L7 17M7 17h10M7 17V7"
              />
              <path
                v-else-if="getTrendIcon('latency') === 'arrow-up'"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 17L17 7M17 7H7M17 7v10"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- Error Rate KPI -->
      <div
        class="kpi-card p-4 bg-white rounded-lg border-2"
        :class="getKpiStatusClass('errorRate')"
        data-testid="error-rate-kpi"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-500">Error Rate</p>
            <p class="text-2xl font-bold text-gray-900">
              {{ ((kpiData.errorRate || 0) * 100).toFixed(1) }}%
            </p>
          </div>
          <div
            class="trend-indicator"
            :class="getTrendClass('errorRate')"
            data-testid="error-rate-trend"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- P95 Latency KPI -->
      <div
        class="kpi-card p-4 bg-white rounded-lg border-2"
        data-testid="p95-latency-kpi"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-500">P95 Latency</p>
            <p class="text-2xl font-bold text-gray-900">
              {{ kpiData.p95Latency?.toFixed(1) || '0.0' }}
              <span class="text-sm text-gray-500">ms</span>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Multi-Chart Layout -->
    <div class="charts-container grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-6">
      <div
        v-for="metric in displayMetrics"
        :key="metric"
        class="chart-panel bg-white p-4 rounded-lg shadow"
        :data-testid="`metric-chart-${metric}`"
      >
        <h3 class="text-lg font-medium mb-4">{{ getMetricLabel(metric) }}</h3>
        <div class="h-64">
          <!-- Chart placeholder - would integrate with InteractiveTimeSeriesChart -->
          <div class="w-full h-full bg-gray-100 rounded flex items-center justify-center">
            <span class="text-gray-500">Chart: {{ metric }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Chart Overlay Controls -->
    <div class="overlay-controls mb-6 p-4 bg-gray-50 rounded-lg">
      <h4 class="font-medium mb-3">Chart Overlays</h4>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <label class="flex items-center">
          <input
            v-model="chartOverlays.movingAverage.enabled"
            type="checkbox"
            class="form-checkbox h-4 w-4"
          >
          <span
            class="ml-2 text-sm px-2 py-1 rounded"
            :class="chartOverlays.movingAverage.enabled ? 'bg-blue-100' : ''"
            data-testid="overlay-moving-average"
          >
            Moving Average
          </span>
        </label>

        <label class="flex items-center">
          <input
            v-model="chartOverlays.percentileBands.enabled"
            type="checkbox"
            class="form-checkbox h-4 w-4"
          >
          <span
            class="ml-2 text-sm px-2 py-1 rounded"
            :class="chartOverlays.percentileBands.enabled ? 'bg-blue-100' : ''"
            data-testid="overlay-percentile-bands"
          >
            Percentile Bands
          </span>
        </label>

        <label class="flex items-center">
          <input
            v-model="chartOverlays.anomalyHighlights.enabled"
            type="checkbox"
            class="form-checkbox h-4 w-4"
          >
          <span class="ml-2 text-sm px-2 py-1 rounded">Anomaly Highlights</span>
        </label>

        <label class="flex items-center">
          <input
            v-model="chartOverlays.trendLine.enabled"
            type="checkbox"
            class="form-checkbox h-4 w-4"
          >
          <span class="ml-2 text-sm px-2 py-1 rounded">Trend Line</span>
        </label>
      </div>
    </div>

    <!-- Forecast Display -->
    <div v-if="forecastData.predictions.length > 0" class="forecast-panel mb-6 p-4 bg-blue-50 rounded-lg">
      <div class="flex items-center justify-between mb-4">
        <h4 class="font-medium">Predictive Forecast</h4>
        <div class="flex items-center space-x-4">
          <span class="text-sm" data-testid="forecast-accuracy">
            Accuracy: {{ (forecastData.modelAccuracy.confidence * 100).toFixed(0) }}%
          </span>
          <div
            v-if="forecastAlerts.length > 0"
            class="px-2 py-1 bg-orange-100 text-orange-800 rounded text-sm"
            data-testid="forecast-alert-badge"
          >
            {{ forecastAlerts.length }} Alert{{ forecastAlerts.length > 1 ? 's' : '' }}
          </div>
        </div>
      </div>
      <div class="h-32 bg-white rounded" data-testid="forecast-display">
        <!-- Forecast chart placeholder -->
        <div class="w-full h-full flex items-center justify-center text-gray-500">
          Forecast Chart ({{ forecastData.predictions.length }} points)
        </div>
      </div>
    </div>

    <!-- Model Performance Metrics -->
    <div v-if="modelMetrics.accuracy" class="model-metrics mb-6 p-4 bg-gray-50 rounded-lg">
      <div class="flex items-center justify-between mb-4">
        <h4 class="font-medium">Model Performance</h4>
        <div
          v-if="modelMetrics.recommendRetraining"
          class="flex items-center space-x-2 text-orange-500"
          data-testid="retrain-recommendation"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 6.5c-.77.833-.192 2.5 1.732 2.5z" />
          </svg>
          <span class="text-sm">Retraining Recommended</span>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p class="text-sm text-gray-500">Model Accuracy</p>
          <p class="text-lg font-semibold" data-testid="model-accuracy">
            {{ (modelMetrics.accuracy * 100).toFixed(0) }}%
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-500">Model Age</p>
          <p class="text-lg font-semibold" data-testid="model-age">
            {{ modelMetrics.modelAge }}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-500">Training Data</p>
          <p class="text-lg font-semibold">
            {{ modelMetrics.trainingDataPoints?.toLocaleString() }}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-500">Last Retrained</p>
          <p class="text-lg font-semibold">
            {{ modelMetrics.lastRetrained ? formatDate(modelMetrics.lastRetrained) : 'Never' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Anomaly Alerts -->
    <div v-if="currentAnomalies.length > 0" class="anomaly-alerts mb-6">
      <h4 class="font-medium mb-3">Active Anomalies</h4>
      <div class="space-y-2">
        <div
          v-for="anomaly in currentAnomalies"
          :key="anomaly.timestamp"
          class="anomaly-alert p-3 bg-red-50 border border-red-200 rounded-lg"
          data-testid="anomaly-alert"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div
                class="w-3 h-3 rounded-full"
                :class="{
                  'bg-red-500': anomaly.severity === 'high',
                  'bg-orange-500': anomaly.severity === 'medium',
                  'bg-yellow-500': anomaly.severity === 'low'
                }"
                data-testid="anomaly-severity"
              ></div>
              <div>
                <p class="font-medium">{{ anomaly.explanation }}</p>
                <p class="text-sm text-gray-600">
                  {{ anomaly.metric }}: {{ anomaly.value }}
                  (Score: {{ anomaly.anomalyScore.toFixed(2) }})
                </p>
              </div>
            </div>
            <button
              @click="() => {}"
              class="text-sm text-blue-600 hover:text-blue-800"
            >
              Investigate
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Investigation Panel -->
    <div v-if="activeInvestigation" class="investigation-panel p-4 bg-gray-50 rounded-lg" data-testid="investigation-panel">
      <h4 class="font-medium mb-3">Anomaly Investigation</h4>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h5 class="text-sm font-medium mb-2">Affected Queries</h5>
          <ul class="text-sm text-gray-600" data-testid="affected-queries">
            <li v-for="query in activeInvestigation.affectedQueries" :key="query">
              {{ query }}
            </li>
          </ul>
        </div>

        <div>
          <h5 class="text-sm font-medium mb-2">Root Cause Hypotheses</h5>
          <ul class="text-sm text-gray-600" data-testid="root-cause-hypotheses">
            <li v-for="hypothesis in activeInvestigation.rootCauseHypotheses" :key="hypothesis">
              • {{ hypothesis }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Performance Monitoring -->
    <div class="performance-monitoring mt-6 p-4 bg-gray-50 rounded-lg">
      <h4 class="font-medium mb-3">System Performance</h4>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p class="text-sm text-gray-500">Data Points</p>
          <p class="text-lg font-semibold">{{ totalDataPoints }}</p>
        </div>
        <div>
          <p class="text-sm text-gray-500">Memory Usage</p>
          <p class="text-lg font-semibold">{{ (memoryUsage.dataPoints / 1024).toFixed(1) }}KB</p>
        </div>
        <div>
          <p class="text-sm text-gray-500">Update Rate</p>
          <p class="text-lg font-semibold">{{ updateRate }}/sec</p>
        </div>
        <div>
          <p class="text-sm text-gray-500">Buffer Size</p>
          <p class="text-lg font-semibold">{{ dataBuffer.length }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { QueryPerformanceData } from '../services/graphqlSubscriptionClient'

interface Props {
  endpointId: string
  autoRefresh?: boolean
  refreshInterval?: number
  metrics?: string[]
  chartLayout?: 'grid' | 'stack'
  theme?: 'light' | 'dark'
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 1000,
  metrics: () => ['executionTime', 'responseSize', 'errorRate'],
  chartLayout: 'grid',
  theme: 'light'
})

// Removed unused emit defineEmits

// Connection state
const wsConnection = ref<WebSocket>()
const connectionStatus = ref<'connected' | 'reconnecting' | 'disconnected'>('connected')
const reconnectAttempts = ref(0)
const realTimeEnabled = ref(true)

// Data state
// Removed unused realtimeBuffer
// Removed unused offlineBuffer
const dataBuffer = ref<QueryPerformanceData[]>([])
const totalDataPoints = ref(0)
const updateQueue = ref<any[]>([])
// Removed unused pendingUpdates

// KPI state
const kpiData = ref({
  currentThroughput: 0,
  averageLatency: 0,
  errorRate: 0,
  p95Latency: 0
})

const trendData = ref({
  throughput: { current: 0, previous: 0, trend: 'stable' },
  latency: { current: 0, previous: 0, trend: 'stable' },
  errorRate: { current: 0, previous: 0, trend: 'stable' }
})

const alertingMetrics = ref({
  latency: { value: 0, threshold: 200, status: 'normal' },
  errorRate: { value: 0, threshold: 0.05, status: 'normal' },
  throughput: { value: 0, threshold: 100, status: 'normal' }
})

// Chart state
const displayMetrics = computed(() => props.metrics)
// Removed unused globalTimeRange
const chartOverlays = ref({
  movingAverage: { enabled: false, window: 20 },
  percentileBands: { enabled: false, percentiles: [25, 75, 95] },
  anomalyHighlights: { enabled: false, threshold: 2.5 },
  trendLine: { enabled: false, method: 'linear' }
})

// Forecast state
const forecastData = ref({
  predictions: [] as any[],
  modelAccuracy: { confidence: 0.85 }
})
const forecastAlerts = ref<any[]>([])

// Model state
const modelMetrics = ref({
  accuracy: 0.78,
  lastRetrained: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
  trainingDataPoints: 10000,
  modelAge: '2 days',
  recommendRetraining: true
})

// Anomaly state
const currentAnomalies = ref<any[]>([])
const activeInvestigation = ref<any>(null)
// Removed unused anomaly tracking variables

// Performance state
const memoryUsage = ref({ dataPoints: 0 })
const updateRate = ref(0)

// User preferences
const userPreferences = ref({
  defaultTimeRange: '1hour',
  preferredMetrics: ['executionTime', 'errorRate'],
  chartColors: { executionTime: '#3b82f6', errorRate: '#ef4444' },
  alertThresholds: { latency: 200, errorRate: 0.05 },
  refreshInterval: 5000
})

// Removed unused dashboardLayout

// Methods
// Removed unused functions

// Removed unused updateKPIs

function loadPreferences() {
  const saved = localStorage.getItem('dashboard-preferences')
  if (saved) {
    userPreferences.value = JSON.parse(saved)
  }
}

function performMemoryCleanup() {
  if (totalDataPoints.value > 1000) {
    dataBuffer.value = dataBuffer.value.slice(-500)
    totalDataPoints.value = dataBuffer.value.length
  }

  memoryUsage.value.dataPoints = totalDataPoints.value * 100 // Rough estimate
}

// Helper functions
function getKpiStatusClass(metric: string) {
  const status = alertingMetrics.value[metric as keyof typeof alertingMetrics.value]?.status
  return {
    'border-gray-300': status === 'normal',
    'border-yellow-400': status === 'warning',
    'border-red-500': status === 'critical'
  }
}

function getTrendClass(metric: string) {
  const trend = trendData.value[metric as keyof typeof trendData.value]?.trend
  return {
    'text-green-500': (metric === 'throughput' && trend === 'increasing') ||
                     (metric !== 'throughput' && trend === 'decreasing'),
    'text-red-500': (metric === 'throughput' && trend === 'decreasing') ||
                    (metric !== 'throughput' && trend === 'increasing'),
    'text-gray-500': trend === 'stable'
  }
}

function getTrendIcon(metric: string) {
  const trend = trendData.value[metric as keyof typeof trendData.value]?.trend
  if (metric === 'throughput') {
    return trend === 'increasing' ? 'arrow-up' : trend === 'decreasing' ? 'arrow-down' : 'stable'
  } else {
    return trend === 'decreasing' ? 'arrow-down' : trend === 'increasing' ? 'arrow-up' : 'stable'
  }
}

function getMetricLabel(metric: string): string {
  const labels = {
    executionTime: 'Execution Time',
    responseSize: 'Response Size',
    errorRate: 'Error Rate'
  }
  return labels[metric as keyof typeof labels] || metric
}

// Removed unused calculatePercentile

function formatDate(date: Date): string {
  return new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
    .format(Math.round((date.getTime() - Date.now()) / (1000 * 60 * 60 * 24)), 'day')
}

// Lifecycle
onMounted(() => {
  loadPreferences()

  // Simulate WebSocket connection
  wsConnection.value = {} as WebSocket

  // Start performance monitoring
  const perfInterval = setInterval(() => {
    updateRate.value = updateQueue.value.length
    updateQueue.value = []
    performMemoryCleanup()
  }, 1000)

  // Cleanup on unmount
  onUnmounted(() => {
    clearInterval(perfInterval)
  })
})
</script>

<style scoped>
.form-checkbox {
  @apply rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50;
}

.kpi-card {
  transition: border-color 0.3s ease;
}

.trend-indicator {
  transition: color 0.3s ease;
}

.dashboard-container.dark-theme {
  @apply bg-gray-900 text-white;
}

.dashboard-container.light-theme {
  @apply bg-white text-gray-900;
}
</style>
