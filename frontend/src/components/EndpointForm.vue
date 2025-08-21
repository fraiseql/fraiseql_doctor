<template>
  <div class="max-w-2xl mx-auto">
    <!-- Form Header -->
    <div class="mb-8">
      <h2 data-testid="form-title" class="text-2xl font-bold text-gray-900">
        {{ mode === 'create' ? 'Add New Endpoint' : 'Edit Endpoint' }}
      </h2>
      <p class="text-gray-600 mt-2">
        {{ mode === 'create' ? 'Configure a new GraphQL endpoint' : 'Update endpoint configuration' }}
      </p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Basic Information -->
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>

        <div class="grid grid-cols-1 gap-6">
          <!-- Name -->
          <div>
            <label for="name" class="block text-sm font-medium text-gray-700">
              Name <span class="text-red-500">*</span>
            </label>
            <input
              id="name"
              v-model="formData.name"
              data-testid="name-input"
              type="text"
              class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              :class="{ 'border-red-300': errors.name }"
            />
            <p v-if="errors.name" data-testid="name-error" class="mt-1 text-sm text-red-600">
              {{ errors.name }}
            </p>
          </div>

          <!-- URL -->
          <div>
            <label for="url" class="block text-sm font-medium text-gray-700">
              GraphQL URL <span class="text-red-500">*</span>
            </label>
            <div class="mt-1 flex rounded-md shadow-sm">
              <input
                id="url"
                v-model="formData.url"
                data-testid="url-input"
                type="url"
                placeholder="https://api.example.com/graphql"
                class="flex-1 border-gray-300 rounded-l-md focus:ring-indigo-500 focus:border-indigo-500"
                :class="{ 'border-red-300': errors.url }"
              />
              <button
                type="button"
                @click="testEndpoint"
                data-testid="test-btn"
                :disabled="!formData.url || isTestingEndpoint"
                class="inline-flex items-center px-4 py-2 border border-l-0 border-gray-300 bg-gray-50 text-sm font-medium text-gray-700 rounded-r-md hover:bg-gray-100 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span v-if="isTestingEndpoint" data-testid="test-loading">
                  <ArrowPathIcon class="h-4 w-4 animate-spin" />
                </span>
                <span v-else>Test</span>
              </button>
            </div>
            <p v-if="errors.url" data-testid="url-error" class="mt-1 text-sm text-red-600">
              {{ errors.url }}
            </p>

            <!-- Test Result -->
            <div v-if="testResult" data-testid="test-result" class="mt-2">
              <div v-if="testResult.success" class="text-sm text-green-600 flex items-center">
                <CheckCircleIcon class="h-4 w-4 mr-1" />
                Connection successful ({{ testResult.responseTime }}ms)
              </div>
              <div v-else class="text-sm text-red-600 flex items-center">
                <XCircleIcon class="h-4 w-4 mr-1" />
                {{ testResult.errorMessage || 'Connection failed' }}
              </div>
            </div>
          </div>

          <!-- Description -->
          <div>
            <label for="description" class="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              v-model="formData.description"
              data-testid="description-input"
              rows="3"
              class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Optional description for this endpoint..."
            />
          </div>

          <!-- Introspection -->
          <div class="flex items-center">
            <input
              id="introspection"
              v-model="formData.introspectionEnabled"
              data-testid="introspection-checkbox"
              type="checkbox"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label for="introspection" class="ml-2 block text-sm text-gray-900">
              Enable introspection
            </label>
            <InformationCircleIcon
              class="h-4 w-4 text-gray-400 ml-2"
              title="Allows fetching the GraphQL schema for better tooling support"
            />
          </div>
        </div>
      </div>

      <!-- Headers Configuration -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-medium text-gray-900">HTTP Headers</h3>
          <button
            type="button"
            @click="addHeader"
            data-testid="add-header-btn"
            class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <PlusIcon class="h-4 w-4 mr-1" />
            Add Header
          </button>
        </div>

        <div v-if="headers.length === 0" class="text-sm text-gray-500 text-center py-4">
          No headers configured. Click "Add Header" to add authentication or other headers.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="(header, index) in headers"
            :key="index"
            :data-testid="`header-row-${index}`"
            class="flex items-center space-x-3"
          >
            <input
              v-model="header.key"
              :data-testid="`header-key-${index}`"
              type="text"
              placeholder="Header name"
              class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
            <input
              v-model="header.value"
              :data-testid="`header-value-${index}`"
              type="text"
              placeholder="Header value"
              class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              type="button"
              @click="removeHeader(index)"
              :data-testid="`remove-header-${index}`"
              class="p-2 text-gray-400 hover:text-red-600"
            >
              <TrashIcon class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="flex items-center justify-end space-x-3">
        <button
          type="button"
          @click="handleCancel"
          data-testid="cancel-btn"
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          data-testid="submit-btn"
          :disabled="!!loading"
          class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">
            {{ mode === 'create' ? 'Adding...' : 'Updating...' }}
          </span>
          <span v-else>
            {{ mode === 'create' ? 'Add Endpoint' : 'Update Endpoint' }}
          </span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import type { GraphQLEndpoint, CreateEndpointInput, UpdateEndpointInput, EndpointTestResult } from '../types/endpoint'
import { useGraphQLClient } from '../services/graphql/client'
import {
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'

// Props
interface Props {
  mode: 'create' | 'edit'
  endpoint?: GraphQLEndpoint
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'create': [data: CreateEndpointInput]
  'update': [data: UpdateEndpointInput]
  'cancel': []
}>()

// Services
const { testEndpoint: testEndpointConnectivity } = useGraphQLClient()

// Form data
const formData = reactive({
  name: '',
  url: '',
  description: '',
  introspectionEnabled: false
})

// Headers management
interface HeaderPair {
  key: string
  value: string
}

const headers = ref<HeaderPair[]>([])

// Form state
const errors = reactive({
  name: '',
  url: ''
})

const isTestingEndpoint = ref(false)
const testResult = ref<EndpointTestResult | null>(null)

// Computed
const isFormValid = computed(() => {
  return formData.name.trim() && formData.url.trim() && !errors.name && !errors.url
})

// Methods
function validateForm(): boolean {
  let isValid = true

  // Reset errors
  errors.name = ''
  errors.url = ''

  // Validate name
  if (!formData.name.trim()) {
    errors.name = 'Name is required'
    isValid = false
  }

  // Validate URL
  if (!formData.url.trim()) {
    errors.url = 'URL is required'
    isValid = false
  } else {
    try {
      new URL(formData.url)
    } catch {
      errors.url = 'Please enter a valid URL'
      isValid = false
    }
  }

  return isValid
}

function addHeader() {
  headers.value.push({ key: '', value: '' })
}

function removeHeader(index: number) {
  headers.value.splice(index, 1)
}

function buildHeaders(): Record<string, string> {
  const headersObj: Record<string, string> = {}

  headers.value.forEach(header => {
    if (header.key.trim() && header.value.trim()) {
      headersObj[header.key.trim()] = header.value.trim()
    }
  })

  return headersObj
}

async function testEndpoint() {
  if (!formData.url.trim()) return

  isTestingEndpoint.value = true
  testResult.value = null

  try {
    // Add a small delay to show loading state in tests
    await new Promise(resolve => setTimeout(resolve, 10))
    const result = await testEndpointConnectivity(formData.url)
    testResult.value = result
  } catch (error) {
    testResult.value = {
      success: false,
      responseTime: 0,
      errorMessage: 'Test failed'
    }
  } finally {
    isTestingEndpoint.value = false
  }
}

function handleSubmit() {
  validateForm()

  if (!isFormValid.value) return

  const headersData = buildHeaders()

  if (props.mode === 'create') {
    const createData: CreateEndpointInput = {
      name: formData.name.trim(),
      url: formData.url.trim(),
      introspectionEnabled: formData.introspectionEnabled,
      ...(formData.description.trim() && { description: formData.description.trim() }),
      ...(Object.keys(headersData).length > 0 && { headers: headersData })
    }

    emit('create', createData)
  } else {
    const updateData: UpdateEndpointInput = {
      name: formData.name.trim(),
      url: formData.url.trim(),
      introspectionEnabled: formData.introspectionEnabled,
      ...(formData.description.trim() && { description: formData.description.trim() }),
      ...(Object.keys(headersData).length > 0 && { headers: headersData })
    }

    emit('update', updateData)
  }
}

function handleCancel() {
  // Reset form
  resetForm()
  emit('cancel')
}

function resetForm() {
  formData.name = ''
  formData.url = ''
  formData.description = ''
  formData.introspectionEnabled = false
  headers.value = []
  errors.name = ''
  errors.url = ''
  testResult.value = null
}

function populateForm(endpoint: GraphQLEndpoint) {
  formData.name = endpoint.name
  formData.url = endpoint.url
  formData.description = endpoint.description || ''
  formData.introspectionEnabled = endpoint.introspectionEnabled

  // Populate headers
  headers.value = []
  if (endpoint.headers) {
    Object.entries(endpoint.headers).forEach(([key, value]) => {
      headers.value.push({ key, value })
    })
  }
}

// Watchers
watch(() => props.endpoint, (newEndpoint) => {
  if (newEndpoint && props.mode === 'edit') {
    populateForm(newEndpoint)
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  if (props.endpoint && props.mode === 'edit') {
    populateForm(props.endpoint)
  }
})
</script>
