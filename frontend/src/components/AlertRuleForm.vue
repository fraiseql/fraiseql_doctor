<template>
  <div class="alert-rule-form" data-testid="alert-rule-form">
    <div class="bg-white shadow rounded-lg p-6">
      <div class="mb-6">
        <h2 class="text-lg font-medium text-gray-900">
          {{ mode === 'create' ? 'Create Alert Rule' : 'Edit Alert Rule' }}
        </h2>
        <p class="mt-1 text-sm text-gray-500">
          Configure alert conditions to monitor your GraphQL endpoints.
        </p>
      </div>

      <form @submit.prevent="submitForm" class="space-y-6">
        <!-- Rule Name -->
        <div>
          <label for="rule-name" class="block text-sm font-medium text-gray-700">
            Rule Name
          </label>
          <div class="mt-1">
            <input
              id="rule-name"
              v-model="formData.name"
              type="text"
              class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              :class="{ 'border-red-500': errors.name }"
              placeholder="Enter a descriptive name for this rule"
              data-testid="rule-name-input"
              :aria-describedby="errors.name ? 'name-error' : ''"
            />
          </div>
          <p v-if="errors.name" id="name-error" class="mt-2 text-sm text-red-600" data-testid="name-error">
            {{ errors.name }}
          </p>
        </div>

        <!-- Endpoint Selection -->
        <div>
          <label for="endpoint-id" class="block text-sm font-medium text-gray-700">
            Endpoint
          </label>
          <div class="mt-1">
            <select
              id="endpoint-id"
              v-model="formData.endpointId"
              class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              :class="{ 'border-red-500': errors.endpointId }"
              data-testid="endpoint-select"
            >
              <option value="">Select an endpoint</option>
              <option value="endpoint-1">Endpoint 1</option>
              <option value="endpoint-2">Endpoint 2</option>
              <option value="endpoint-3">Endpoint 3</option>
            </select>
          </div>
          <p v-if="errors.endpointId" class="mt-2 text-sm text-red-600" data-testid="endpoint-error">
            {{ errors.endpointId }}
          </p>
        </div>

        <!-- Metric Configuration -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Metric Type -->
          <div>
            <label for="metric" class="block text-sm font-medium text-gray-700">
              Metric
            </label>
            <div class="mt-1">
              <select
                id="metric"
                v-model="formData.condition.metric"
                class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                data-testid="metric-select"
                @change="onMetricChange"
              >
                <option value="executionTime">Execution Time</option>
                <option value="responseSize">Response Size</option>
                <option value="errorRate">Error Rate</option>
              </select>
            </div>
          </div>

          <!-- Operator -->
          <div>
            <label for="operator" class="block text-sm font-medium text-gray-700">
              Condition
            </label>
            <div class="mt-1">
              <select
                id="operator"
                v-model="formData.condition.operator"
                class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                data-testid="operator-select"
              >
                <option value="greaterThan" data-testid="operator-option">Greater Than</option>
                <option value="lessThan" data-testid="operator-option">Less Than</option>
                <option value="equals" data-testid="operator-option">Equals</option>
                <option value="notEquals" data-testid="operator-option">Not Equals</option>
              </select>
            </div>
          </div>

          <!-- Threshold -->
          <div>
            <label for="threshold" class="block text-sm font-medium text-gray-700">
              Threshold
            </label>
            <div class="mt-1 relative rounded-md shadow-sm">
              <input
                id="threshold"
                v-model.number="formData.condition.threshold"
                type="number"
                min="0"
                step="any"
                class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full pr-16 sm:text-sm border-gray-300 rounded-md"
                :class="{ 'border-red-500': errors.threshold }"
                placeholder="0"
                data-testid="threshold-input"
              />
              <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <span class="text-gray-500 text-sm" data-testid="threshold-unit">
                  {{ getMetricUnit() }}
                </span>
              </div>
            </div>
            <p v-if="errors.threshold" class="mt-2 text-sm text-red-600" data-testid="threshold-error">
              {{ errors.threshold }}
            </p>
          </div>
        </div>

        <!-- Duration -->
        <div>
          <label for="duration" class="block text-sm font-medium text-gray-700">
            Duration (seconds)
          </label>
          <div class="mt-1">
            <input
              id="duration"
              v-model.number="durationInSeconds"
              type="number"
              min="60"
              class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              :class="{ 'border-red-500': errors.duration }"
              placeholder="300"
              data-testid="duration-input"
            />
          </div>
          <p class="mt-1 text-sm text-gray-500">
            Alert will trigger only if the condition persists for this duration.
          </p>
          <p v-if="errors.duration" class="mt-2 text-sm text-red-600" data-testid="duration-error">
            {{ errors.duration }}
          </p>
        </div>

        <!-- Severity -->
        <div>
          <label for="severity" class="block text-sm font-medium text-gray-700">
            Severity
          </label>
          <div class="mt-1">
            <select
              id="severity"
              v-model="formData.severity"
              class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              data-testid="severity-select"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>

        <!-- Advanced Options Toggle -->
        <div>
          <button
            type="button"
            @click="showAdvanced = !showAdvanced"
            class="flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-500"
            data-testid="show-advanced-toggle"
          >
            <svg
              class="mr-2 h-4 w-4 transform transition-transform"
              :class="{ 'rotate-90': showAdvanced }"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            Advanced Options
          </button>
        </div>

        <!-- Advanced Options -->
        <div v-if="showAdvanced" class="advanced-options bg-gray-50 p-4 rounded-md" data-testid="advanced-options">
          <div class="space-y-4">
            <!-- Notification Settings -->
            <div>
              <h4 class="text-sm font-medium text-gray-900 mb-3">Notification Methods</h4>
              <div class="space-y-2">
                <label class="flex items-center">
                  <input
                    v-model="formData.notifications.email"
                    type="checkbox"
                    class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                    data-testid="email-notifications-checkbox"
                  />
                  <span class="ml-2 text-sm text-gray-700">Email notifications</span>
                </label>

                <label class="flex items-center">
                  <input
                    v-model="formData.notifications.browser"
                    type="checkbox"
                    class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                    data-testid="browser-notifications-checkbox"
                  />
                  <span class="ml-2 text-sm text-gray-700">Browser notifications</span>
                </label>
              </div>
            </div>

            <!-- Webhook URL -->
            <div>
              <label for="webhook-url" class="block text-sm font-medium text-gray-700">
                Webhook URL (optional)
              </label>
              <div class="mt-1">
                <input
                  id="webhook-url"
                  v-model="formData.notifications.webhook"
                  type="url"
                  class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  placeholder="https://api.example.com/webhook"
                  data-testid="webhook-url-input"
                />
              </div>
            </div>

            <!-- Alert Frequency -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label for="alert-frequency" class="block text-sm font-medium text-gray-700">
                  Alert Frequency
                </label>
                <div class="mt-1">
                  <select
                    id="alert-frequency"
                    v-model="formData.alertFrequency"
                    class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    data-testid="alert-frequency-select"
                  >
                    <option value="immediately">Immediately</option>
                    <option value="once">Once per incident</option>
                    <option value="hourly">Hourly reminder</option>
                    <option value="daily">Daily reminder</option>
                  </select>
                </div>
              </div>

              <div>
                <label for="max-alerts" class="block text-sm font-medium text-gray-700">
                  Max Alerts per Hour
                </label>
                <div class="mt-1">
                  <input
                    id="max-alerts"
                    v-model.number="formData.maxAlerts"
                    type="number"
                    min="1"
                    max="100"
                    class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    data-testid="max-alerts-input"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="flex justify-end space-x-3">
          <button
            type="button"
            @click="$emit('cancel')"
            class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            data-testid="cancel-button"
          >
            Cancel
          </button>

          <button
            v-if="mode === 'create'"
            type="submit"
            :disabled="loading || false"
            class="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            data-testid="create-rule-button"
          >
            {{ loading ? 'Creating...' : 'Create Rule' }}
          </button>

          <button
            v-else
            type="submit"
            :disabled="loading || false"
            class="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            data-testid="update-rule-button"
          >
            {{ loading ? 'Updating...' : 'Update Rule' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { AlertRule, AlertCondition, AlertSeverity, MetricField } from '../services/alertingEngine'

interface Props {
  mode: 'create' | 'edit'
  rule?: AlertRule
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'create-rule': [rule: AlertRule]
  'update-rule': [rule: AlertRule]
  'cancel': []
}>()

// Form state
const showAdvanced = ref(false)
const formData = ref({
  name: '',
  endpointId: '',
  condition: {
    metric: 'executionTime' as MetricField,
    operator: 'greaterThan' as const,
    threshold: 500,
    duration: 300000 // 5 minutes in milliseconds
  } as AlertCondition,
  severity: 'medium' as AlertSeverity,
  enabled: true,
  notifications: {
    email: false,
    browser: true,
    webhook: ''
  },
  alertFrequency: 'immediately',
  maxAlerts: 10
})

const errors = ref<Record<string, string>>({})

// Convert duration between seconds (UI) and milliseconds (storage)
const durationInSeconds = computed({
  get: () => Math.round(formData.value.condition.duration / 1000),
  set: (value: number) => {
    formData.value.condition.duration = value * 1000
  }
})

// Methods
function getMetricUnit(): string {
  switch (formData.value.condition.metric) {
    case 'executionTime': return 'ms'
    case 'responseSize': return 'bytes'
    case 'errorRate': return '%'
    default: return ''
  }
}

function onMetricChange(): void {
  // Reset threshold when metric changes
  switch (formData.value.condition.metric) {
    case 'executionTime':
      formData.value.condition.threshold = 500 // 500ms
      break
    case 'responseSize':
      formData.value.condition.threshold = 1024000 // 1MB
      break
    case 'errorRate':
      formData.value.condition.threshold = 5 // 5%
      break
  }
}

function validateForm(): boolean {
  errors.value = {}

  if (!formData.value.name.trim()) {
    errors.value.name = 'Rule name is required'
  }

  if (!formData.value.endpointId) {
    errors.value.endpointId = 'Endpoint selection is required'
  }

  if (formData.value.condition.threshold <= 0) {
    errors.value.threshold = 'Threshold must be a positive number'
  }

  if (formData.value.condition.duration < 60000) { // Less than 60 seconds
    errors.value.duration = 'Duration must be at least 60 seconds'
  }

  return Object.keys(errors.value).length === 0
}

function resetForm(): void {
  formData.value = {
    name: '',
    endpointId: '',
    condition: {
      metric: 'executionTime',
      operator: 'greaterThan',
      threshold: 500,
      duration: 300000
    },
    severity: 'medium',
    enabled: true,
    notifications: {
      email: false,
      browser: true,
      webhook: ''
    },
    alertFrequency: 'immediately',
    maxAlerts: 10
  }
  errors.value = {}
  showAdvanced.value = false
}

function submitForm(): void {
  if (!validateForm()) {
    return
  }

  const ruleData: AlertRule = {
    id: props.mode === 'edit' && props.rule ? props.rule.id : `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    name: formData.value.name,
    endpointId: formData.value.endpointId,
    condition: formData.value.condition,
    severity: formData.value.severity,
    enabled: formData.value.enabled,
    createdAt: props.mode === 'edit' && props.rule ? props.rule.createdAt : new Date(),
    ...(props.mode === 'edit' ? { updatedAt: new Date() } : {}),
    notifications: {
      email: formData.value.notifications.email,
      browser: formData.value.notifications.browser,
      ...(formData.value.notifications.webhook && { webhook: formData.value.notifications.webhook })
    }
  }

  if (props.mode === 'create') {
    emit('create-rule', ruleData)
  } else {
    emit('update-rule', ruleData)
  }
}

// Watch for rule changes in edit mode
watch(() => props.rule, (newRule) => {
  if (newRule && props.mode === 'edit') {
    formData.value = {
      name: newRule.name,
      endpointId: newRule.endpointId,
      condition: { ...newRule.condition },
      severity: newRule.severity,
      enabled: newRule.enabled,
      notifications: {
        email: newRule.notifications?.email || false,
        browser: newRule.notifications?.browser || true,
        webhook: newRule.notifications?.webhook || ''
      },
      alertFrequency: 'immediately', // Default since it's not in the original type
      maxAlerts: 10 // Default since it's not in the original type
    }
  }
}, { immediate: true })

// Watch for field changes to clear errors
watch(() => formData.value.name, () => {
  if (errors.value.name) delete errors.value.name
})

watch(() => formData.value.endpointId, () => {
  if (errors.value.endpointId) delete errors.value.endpointId
})

watch(() => formData.value.condition.threshold, () => {
  if (errors.value.threshold) delete errors.value.threshold
})

watch(() => formData.value.condition.duration, () => {
  if (errors.value.duration) delete errors.value.duration
})

// Initialize form for create mode
onMounted(() => {
  if (props.mode === 'create') {
    resetForm()
  }
})

// Expose methods for testing
defineExpose({
  formData,
  errors,
  resetForm,
  validateForm
})
</script>

<style scoped>
.alert-rule-form {
  @apply max-w-2xl mx-auto;
}

.advanced-options {
  @apply transition-all duration-200;
}
</style>
