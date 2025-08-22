<template>
  <div
    v-if="modelValue"
    data-testid="api-config-modal"
    class="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center p-4 z-50"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Modal Header -->
      <div class="p-6 border-b">
        <h2 class="text-lg font-semibold">
          Configure API: {{ endpoint?.name }}
        </h2>
      </div>

      <!-- Modal Content -->
      <div class="p-6 space-y-6">
        <!-- Basic Settings -->
        <div>
          <h3 class="font-medium mb-3">Basic Settings</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">Name <span class="text-red-500">*</span></label>
              <input
                v-model="config.name"
                data-testid="endpoint-name-input"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter API name"
              />
              <p v-if="errors.name" data-testid="name-error" class="text-red-500 text-sm mt-1">
                {{ errors.name }}
              </p>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">URL</label>
              <input
                v-model="config.url"
                data-testid="endpoint-url-input"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://api.example.com/graphql"
              />
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm font-medium mb-1">Environment</label>
              <select
                v-model="config.environment"
                data-testid="environment-select"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="dev">Development</option>
                <option value="staging">Staging</option>
                <option value="prod">Production</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Authentication -->
        <div>
          <h3 class="font-medium mb-3">Authentication</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">Type</label>
              <select
                v-model="config.authentication.type"
                data-testid="auth-type-select"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="none">None</option>
                <option value="bearer">Bearer Token</option>
                <option value="api-key">API Key</option>
                <option value="basic">Basic Auth</option>
              </select>
            </div>

            <!-- Bearer Token -->
            <div v-if="config.authentication.type === 'bearer'" class="grid grid-cols-1 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1">Token</label>
                <input
                  v-model="config.authentication.token"
                  type="password"
                  data-testid="auth-token-input"
                  class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter bearer token"
                />
              </div>
            </div>

            <!-- API Key -->
            <div v-if="config.authentication.type === 'api-key'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1">API Key</label>
                <input
                  v-model="config.authentication.apiKey"
                  type="password"
                  data-testid="auth-api-key-input"
                  class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter API key"
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Header Name</label>
                <input
                  v-model="config.authentication.headerName"
                  data-testid="auth-header-name-input"
                  class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="X-API-Key"
                />
              </div>
            </div>

            <!-- Basic Auth -->
            <div v-if="config.authentication.type === 'basic'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1">Username</label>
                <input
                  v-model="config.authentication.username"
                  data-testid="auth-username-input"
                  class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter username"
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Password</label>
                <input
                  v-model="config.authentication.password"
                  type="password"
                  data-testid="auth-password-input"
                  class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter password"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Monitoring Thresholds -->
        <div>
          <h3 class="font-medium mb-3">Monitoring Thresholds</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">Response Time Warning (ms)</label>
              <input
                v-model.number="config.thresholds.responseTime.warning"
                type="number"
                data-testid="response-time-warning"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Response Time Critical (ms)</label>
              <input
                v-model.number="config.thresholds.responseTime.critical"
                type="number"
                data-testid="response-time-critical"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Error Rate Warning (%)</label>
              <input
                v-model.number="config.thresholds.errorRate.warning"
                type="number"
                data-testid="error-rate-warning"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
                max="100"
                step="0.1"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Error Rate Critical (%)</label>
              <input
                v-model.number="config.thresholds.errorRate.critical"
                type="number"
                data-testid="error-rate-critical"
                class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
                max="100"
                step="0.1"
              />
            </div>
          </div>
        </div>

        <!-- Connection Test -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-medium">Connection Test</h3>
            <button
              type="button"
              data-testid="test-connection-btn"
              class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="testing"
              @click="testConnection"
            >
              {{ testing ? 'Testing...' : 'Test Connection' }}
            </button>
          </div>
          <div
            v-if="testResult"
            data-testid="connection-test-result"
            :class="testResult.success ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'"
            class="text-sm p-3 rounded border"
          >
            {{ testResult.message }}
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="flex justify-end space-x-3 p-6 border-t bg-gray-50">
        <button
          type="button"
          data-testid="cancel-btn"
          class="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded hover:bg-gray-50"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="button"
          data-testid="save-config-btn"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!isValid"
          @click="handleSave"
        >
          Save Configuration
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { ApiEndpoint, ApiConfiguration } from '@/types/admin'

interface Props {
  modelValue: boolean
  endpoint: ApiEndpoint | null
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'save'])

// Form configuration
const config = ref<ApiConfiguration>({
  name: '',
  url: '',
  environment: 'dev',
  authentication: {
    type: 'none',
    token: '',
    apiKey: '',
    headerName: 'X-API-Key',
    username: '',
    password: ''
  },
  thresholds: {
    responseTime: {
      warning: 200,
      critical: 500
    },
    errorRate: {
      warning: 1,
      critical: 5
    }
  }
})

// Form validation
const errors = ref({
  name: ''
})

const isValid = computed(() => {
  return config.value.name.trim().length > 0
})

// Connection test
const testing = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

// Watch for endpoint changes to populate form
watch(() => props.endpoint, (endpoint) => {
  if (endpoint) {
    config.value.name = endpoint.name
    config.value.url = endpoint.url
    config.value.environment = endpoint.environment
    
    // Reset other fields to defaults
    config.value.authentication = {
      type: 'none',
      token: '',
      apiKey: '',
      headerName: 'X-API-Key',
      username: '',
      password: ''
    }
    errors.value.name = ''
    testResult.value = null
  }
}, { immediate: true })

// Watch for name changes to clear validation errors
watch(() => config.value.name, (name) => {
  if (name.trim().length > 0) {
    errors.value.name = ''
  }
})

const validateForm = () => {
  errors.value.name = config.value.name.trim().length === 0 ? 'Name is required' : ''
  return isValid.value
}

const testConnection = async () => {
  testing.value = true
  testResult.value = null

  try {
    // Simulate connection test
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Mock success/failure based on URL
    const isValidUrl = config.value.url && config.value.url.includes('api.example')
    
    testResult.value = {
      success: isValidUrl,
      message: isValidUrl 
        ? 'Connection successful! GraphQL endpoint is responding.'
        : 'Connection failed: Unable to reach the GraphQL endpoint.'
    }
  } catch (error) {
    testResult.value = {
      success: false,
      message: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`
    }
  } finally {
    testing.value = false
  }
}

const handleSave = () => {
  if (!validateForm()) {
    return
  }

  // Prepare clean config object for saving
  const configToSave = {
    name: config.value.name,
    url: config.value.url,
    environment: config.value.environment,
    authentication: {
      type: config.value.authentication.type,
      ...(config.value.authentication.type === 'bearer' && { 
        token: config.value.authentication.token 
      }),
      ...(config.value.authentication.type === 'api-key' && { 
        apiKey: config.value.authentication.apiKey,
        headerName: config.value.authentication.headerName
      }),
      ...(config.value.authentication.type === 'basic' && { 
        username: config.value.authentication.username,
        password: config.value.authentication.password
      })
    },
    thresholds: config.value.thresholds
  }

  emit('save', configToSave)
  emit('update:modelValue', false)
}

const handleCancel = () => {
  emit('update:modelValue', false)
}
</script>
