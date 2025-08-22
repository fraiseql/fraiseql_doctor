<template>
  <div class="alert-dashboard" data-testid="alert-dashboard">
    <!-- Alert Overview Statistics -->
    <div class="alert-overview mb-6" data-testid="alert-overview">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat-card bg-white p-4 rounded-lg border border-gray-200">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <span class="text-white text-sm font-bold">{{ alertStats.totalAlerts }}</span>
              </div>
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-500">Total Alerts</p>
              <p class="text-lg font-semibold text-gray-900" data-testid="total-alerts">
                {{ alertStats.totalAlerts }}
              </p>
            </div>
          </div>
        </div>

        <div class="stat-card bg-white p-4 rounded-lg border border-gray-200">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                <span class="text-white text-sm font-bold">{{ alertStats.activeAlerts }}</span>
              </div>
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-500">Active Alerts</p>
              <p class="text-lg font-semibold text-gray-900" data-testid="active-alerts">
                {{ alertStats.activeAlerts }}
              </p>
            </div>
          </div>
        </div>

        <div class="stat-card bg-white p-4 rounded-lg border border-gray-200">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-500">Rules Active</p>
              <p class="text-lg font-semibold text-gray-900">
                {{ alertRules.filter(r => r.enabled).length }}
              </p>
            </div>
          </div>
        </div>

        <div class="stat-card bg-white p-4 rounded-lg border border-gray-200">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-500">High Severity</p>
              <p class="text-lg font-semibold text-gray-900">
                {{ alertStats.alertsBySeverity.high + alertStats.alertsBySeverity.critical }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Alerts Section -->
    <div class="active-alerts-section mb-6" data-testid="active-alerts-section">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-medium text-gray-900">Active Alerts</h2>

          <!-- Filters -->
          <div class="flex items-center space-x-4">
            <select
              v-model="severityFilter"
              class="block w-32 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              data-testid="severity-filter"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>

            <select
              v-model="endpointFilter"
              class="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              data-testid="endpoint-filter"
            >
              <option value="">All Endpoints</option>
              <option v-for="endpointId in uniqueEndpoints" :key="endpointId" :value="endpointId">
                {{ endpointId }}
              </option>
            </select>
          </div>
        </div>

        <!-- Alert List -->
        <div v-if="filteredActiveAlerts.length === 0" class="text-center py-8" data-testid="no-active-alerts">
          <svg class="mx-auto h-12 w-12 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No active alerts</h3>
          <p class="mt-1 text-sm text-gray-500">All systems are operating normally.</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="alert in filteredActiveAlerts"
            :key="alert.id"
            class="alert-item border rounded-lg p-4"
            :class="getAlertClasses(alert)"
:data-testid="`alert-item alert-severity-${alert.severity}`"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div
                  class="w-3 h-3 rounded-full"
                  :class="getSeverityColor(alert.severity)"
                ></div>
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900">
                    {{ alert.message }}
                  </p>
                  <p class="text-xs text-gray-500">
                    Endpoint: {{ alert.endpointId }} •
                    Triggered: {{ formatDate(alert.triggeredAt) }}
                  </p>
                </div>
              </div>

              <div class="flex items-center space-x-2">
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="`severity-${alert.severity}`"
                >
                  {{ alert.severity.toUpperCase() }}
                </span>

                <button
                  @click="acknowledgeAlert(alert.id)"
                  class="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  data-testid="acknowledge-button"
                >
                  Acknowledge
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Alert Rules Section -->
    <div class="alert-rules-section mb-6" data-testid="alert-rules-section">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-medium text-gray-900">Alert Rules</h2>

          <button
            @click="$emit('create-rule')"
            class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <svg class="-ml-1 mr-2 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"></path>
            </svg>
            New Rule
          </button>
        </div>

        <div class="space-y-3">
          <div
            v-for="rule in alertRules"
            :key="rule.id"
            class="rule-item border rounded-lg p-4"
            data-testid="alert-rule-item"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                  <span
                    v-if="rule.enabled"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    data-testid="rule-status-enabled"
                  >
                    Enabled
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                    data-testid="rule-status-disabled"
                  >
                    Disabled
                  </span>
                </div>

                <div>
                  <p class="text-sm font-medium text-gray-900">{{ rule.name }}</p>
                  <p class="text-xs text-gray-500">
                    {{ rule.condition.metric }} {{ rule.condition.operator }} {{ rule.condition.threshold }} •
                    {{ rule.endpointId }}
                  </p>
                </div>
              </div>

              <div class="flex items-center space-x-2">
                <button
                  @click="$emit('edit-rule', rule.id)"
                  class="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                  data-testid="edit-rule-button"
                >
                  Edit
                </button>
                <button
                  @click="confirmDeleteRule(rule.id)"
                  class="text-red-600 hover:text-red-900 text-sm font-medium"
                  data-testid="delete-rule-button"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Alert History Section -->
    <div class="alert-history-section mb-6" data-testid="alert-history-section">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Recent Alert History</h2>

        <div class="space-y-2">
          <div
            v-for="alert in paginatedHistory"
            :key="alert.id"
            class="history-item border-l-4 pl-4 py-2"
            :class="getHistoryBorderClass(alert)"
            data-testid="history-item"
          >
            <p class="text-sm text-gray-900">{{ alert.message }}</p>
            <p class="text-xs text-gray-500">
              {{ formatDate(alert.triggeredAt) }} •
              Status: {{ alert.status }} •
              Endpoint: {{ alert.endpointId }}
            </p>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="alertHistory.length > pageSize" class="mt-4 flex justify-center" data-testid="pagination">
          <nav class="flex items-center space-x-2">
            <button
              @click="currentPage = Math.max(1, currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <span class="px-3 py-2 text-sm text-gray-700">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button
              @click="currentPage = Math.min(totalPages, currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </nav>
        </div>
      </div>
    </div>

    <!-- Export Section -->
    <div class="export-section">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Export Data</h2>

        <div class="flex items-center space-x-4">
          <button
            @click="$emit('export-alerts')"
            class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            data-testid="export-alerts-button"
          >
            Export Alerts
          </button>

          <button
            @click="$emit('export-rules')"
            class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            data-testid="export-rules-button"
          >
            Export Rules
          </button>
        </div>
      </div>
    </div>

    <!-- Acknowledge Dialog -->
    <div
      v-if="showAcknowledgeDialog"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
      data-testid="acknowledge-dialog"
    >
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Acknowledge Alert</h3>
          <p class="text-sm text-gray-500 mb-4">
            Are you sure you want to acknowledge this alert? This will mark it as seen and move it to history.
          </p>

          <div class="flex justify-end space-x-3">
            <button
              @click="showAcknowledgeDialog = false"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              @click="confirmAcknowledge"
              class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700"
            >
              Acknowledge
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <div
      v-if="showDeleteDialog"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
      data-testid="delete-confirmation"
    >
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Delete Alert Rule</h3>
          <p class="text-sm text-gray-500 mb-4">
            Are you sure you want to delete this alert rule? This action cannot be undone.
          </p>

          <div class="flex justify-end space-x-3">
            <button
              @click="showDeleteDialog = false"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              @click="confirmDelete"
              class="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700"
              data-testid="confirm-delete-button"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { AlertingEngine } from '../services/alertingEngine'
import type { Alert, AlertRule, AlertStatistics, AlertSeverity } from '../services/alertingEngine'

// Component state
const alertingEngine = new AlertingEngine()
const activeAlerts = ref<Alert[]>([])
const alertRules = ref<AlertRule[]>([])
const alertHistory = ref<Alert[]>([])
const alertStats = ref<AlertStatistics>({
  totalAlerts: 0,
  activeAlerts: 0,
  alertsByEndpoint: {},
  alertsBySeverity: { low: 0, medium: 0, high: 0, critical: 0 }
})

// Filters
const severityFilter = ref<string>('')
const endpointFilter = ref<string>('')

// Pagination
const currentPage = ref(1)
const pageSize = 10

// Dialogs
const showAcknowledgeDialog = ref(false)
const showDeleteDialog = ref(false)
const selectedAlertId = ref<string>('')
const selectedRuleId = ref<string>('')

// Computed properties
const filteredActiveAlerts = computed(() => {
  return activeAlerts.value.filter(alert => {
    if (severityFilter.value && alert.severity !== severityFilter.value) {
      return false
    }
    if (endpointFilter.value && alert.endpointId !== endpointFilter.value) {
      return false
    }
    return true
  })
})

const uniqueEndpoints = computed(() => {
  const endpoints = new Set<string>()
  activeAlerts.value.forEach(alert => endpoints.add(alert.endpointId))
  alertHistory.value.forEach(alert => endpoints.add(alert.endpointId))
  return Array.from(endpoints).sort()
})

const totalPages = computed(() => {
  return Math.ceil(alertHistory.value.length / pageSize)
})

const paginatedHistory = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return alertHistory.value.slice(start, end)
})

// Methods
function getAlertClasses(alert: Alert): string {
  const baseClasses = 'border-l-4'
  switch (alert.severity) {
    case 'critical': return `${baseClasses} border-red-500 bg-red-50`
    case 'high': return `${baseClasses} border-orange-500 bg-orange-50`
    case 'medium': return `${baseClasses} border-yellow-500 bg-yellow-50`
    case 'low': return `${baseClasses} border-blue-500 bg-blue-50`
    default: return `${baseClasses} border-gray-500 bg-gray-50`
  }
}

function getSeverityColor(severity: AlertSeverity): string {
  switch (severity) {
    case 'critical': return 'bg-red-500'
    case 'high': return 'bg-orange-500'
    case 'medium': return 'bg-yellow-500'
    case 'low': return 'bg-blue-500'
    default: return 'bg-gray-500'
  }
}

function getHistoryBorderClass(alert: Alert): string {
  switch (alert.status) {
    case 'resolved': return 'border-green-400'
    case 'acknowledged': return 'border-yellow-400'
    default: return 'border-gray-400'
  }
}

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

function acknowledgeAlert(alertId: string): void {
  selectedAlertId.value = alertId
  showAcknowledgeDialog.value = true
}

function confirmAcknowledge(): void {
  emit('alert-acknowledged', selectedAlertId.value)
  showAcknowledgeDialog.value = false
  selectedAlertId.value = ''
}

function confirmDeleteRule(ruleId: string): void {
  selectedRuleId.value = ruleId
  showDeleteDialog.value = true
}

function confirmDelete(): void {
  emit('delete-rule', selectedRuleId.value)
  showDeleteDialog.value = false
  selectedRuleId.value = ''
}

function handleNewAlert(alert: Alert): void {
  activeAlerts.value.push(alert)
  updateStatistics()
}

function handleAlertResolved(alert: Alert): void {
  const index = activeAlerts.value.findIndex(a => a.id === alert.id)
  if (index !== -1) {
    activeAlerts.value.splice(index, 1)
    alertHistory.value.unshift(alert)
    updateStatistics()
  }
}

function updateStatistics(): void {
  alertStats.value = alertingEngine.getAlertStatistics()
}

// Event emitters
const emit = defineEmits<{
  'alert-acknowledged': [alertId: string]
  'edit-rule': [ruleId: string]
  'delete-rule': [ruleId: string]
  'create-rule': []
  'export-alerts': []
  'export-rules': []
}>()

// Lifecycle
onMounted(() => {
  // Load initial data
  activeAlerts.value = alertingEngine.getActiveAlerts()
  alertRules.value = alertingEngine.getRules()
  alertHistory.value = alertingEngine.getAlertHistory()
  updateStatistics()

  // Set up event listeners
  alertingEngine.addEventListener('alert-triggered', ((event: Event) => {
    handleNewAlert((event as CustomEvent).detail)
  }) as EventListener)

  alertingEngine.addEventListener('alert-resolved', ((event: Event) => {
    handleAlertResolved((event as CustomEvent).detail)
  }) as EventListener)
})

onUnmounted(() => {
  // Clean up event listeners
  alertingEngine.removeEventListener('alert-triggered', ((event: Event) => {
    handleNewAlert((event as CustomEvent).detail)
  }) as EventListener)
  alertingEngine.removeEventListener('alert-resolved', ((event: Event) => {
    handleAlertResolved((event as CustomEvent).detail)
  }) as EventListener)
})

// Expose methods for testing
defineExpose({
  activeAlerts,
  alertRules,
  alertHistory,
  alertStats,
  handleNewAlert,
  handleAlertResolved,
  updateStatistics
})
</script>

<style scoped>
.alert-dashboard {
  @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8;
}

.stat-card {
  @apply transition-shadow duration-200 hover:shadow-md;
}

.alert-item {
  @apply transition-all duration-200 hover:shadow-sm;
}

.rule-item {
  @apply transition-all duration-200 hover:bg-gray-50;
}

.severity-critical {
  @apply bg-red-100 text-red-800;
}

.severity-high {
  @apply bg-orange-100 text-orange-800;
}

.severity-medium {
  @apply bg-yellow-100 text-yellow-800;
}

.severity-low {
  @apply bg-blue-100 text-blue-800;
}
</style>
