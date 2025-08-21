<template>
  <div class="max-w-4xl mx-auto">
    <!-- Loading State -->
    <div v-if="!endpoint" data-testid="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Loading endpoint details...</p>
    </div>

    <!-- Endpoint Details -->
    <div v-else class="space-y-6">
      <!-- Header -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <div class="flex items-center space-x-3 mb-2">
              <h1 data-testid="endpoint-name" class="text-2xl font-bold text-gray-900">
                {{ endpoint.name }}
              </h1>

              <!-- Status Badge -->
              <div class="flex items-center space-x-2">
                <div
                  v-if="endpoint.status === EndpointStatus.CHECKING"
                  data-testid="status-checking"
                  class="flex items-center space-x-1"
                >
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-500"></div>
                  <span class="text-sm text-yellow-600">Checking</span>
                </div>
                <div
                  v-else-if="endpoint.isHealthy"
                  data-testid="status-healthy"
                  class="flex items-center space-x-1 bg-green-100 px-2 py-1 rounded-full"
                >
                  <div class="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span class="text-sm text-green-600 font-medium">Healthy</span>
                </div>
                <div
                  v-else
                  data-testid="status-error"
                  class="flex items-center space-x-1 bg-red-100 px-2 py-1 rounded-full"
                >
                  <div class="h-2 w-2 bg-red-500 rounded-full"></div>
                  <span class="text-sm text-red-600 font-medium">Error</span>
                </div>
              </div>
            </div>

            <p data-testid="endpoint-url" class="text-gray-600 break-all mb-2">
              {{ endpoint.url }}
            </p>

            <p v-if="endpoint.description" data-testid="endpoint-description" class="text-gray-500">
              {{ endpoint.description }}
            </p>
          </div>

          <!-- Action Buttons -->
          <div data-testid="action-buttons" class="flex items-center space-x-3 ml-6">
            <button
              @click="$emit('health-check')"
              data-testid="health-check-btn"
              class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <ArrowPathIcon class="h-4 w-4 mr-2" />
              Check Health
            </button>

            <button
              @click="$emit('edit')"
              data-testid="edit-btn"
              class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <PencilIcon class="h-4 w-4 mr-2" />
              Edit
            </button>

            <button
              @click="$emit('delete')"
              data-testid="delete-btn"
              class="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <TrashIcon class="h-4 w-4 mr-2" />
              Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Response Time -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <ClockIcon class="h-8 w-8 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Response Time</dt>
                  <dd data-testid="response-time" class="text-lg font-medium text-gray-900">
                    {{ endpoint.responseTime ? `${endpoint.responseTime}ms` : 'N/A' }}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Last Checked -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <CalendarIcon class="h-8 w-8 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Last Checked</dt>
                  <dd data-testid="last-checked" class="text-lg font-medium text-gray-900">
                    {{ endpoint.lastChecked ? formatDate(endpoint.lastChecked) : 'Never' }}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Introspection -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <DocumentTextIcon class="h-8 w-8 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Introspection</dt>
                  <dd class="text-lg font-medium text-gray-900">
                    <span
                      v-if="endpoint.introspectionEnabled"
                      data-testid="introspection-enabled"
                      class="text-green-600"
                    >
                      Enabled
                    </span>
                    <span
                      v-else
                      data-testid="introspection-disabled"
                      class="text-gray-500"
                    >
                      Disabled
                    </span>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="endpoint.errorMessage" class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex">
          <ExclamationTriangleIcon class="h-5 w-5 text-red-400" />
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error</h3>
            <p data-testid="error-message" class="mt-1 text-sm text-red-700">
              {{ endpoint.errorMessage }}
            </p>
          </div>
        </div>
      </div>

      <!-- Headers -->
      <div v-if="endpoint.headers && Object.keys(endpoint.headers).length > 0" data-testid="headers-section" class="bg-white shadow rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">HTTP Headers</h3>
        <div class="space-y-3">
          <div
            v-for="[key, value] in Object.entries(endpoint.headers)"
            :key="key"
            class="flex items-start justify-between py-2 px-3 bg-gray-50 rounded-md"
          >
            <dt class="text-sm font-medium text-gray-700">{{ key }}</dt>
            <dd class="text-sm text-gray-900 ml-4 break-all">{{ value }}</dd>
          </div>
        </div>
      </div>

      <!-- Schema Introspection -->
      <div v-if="endpoint.introspectionEnabled" class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-medium text-gray-900">GraphQL Schema</h3>

          <button
            v-if="!isLoadingSchema && !schema"
            @click="loadSchema"
            data-testid="load-schema-btn"
            class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <DocumentTextIcon class="h-4 w-4 mr-2" />
            Load Schema
          </button>
        </div>

        <!-- Schema Loading -->
        <div v-if="isLoadingSchema" data-testid="schema-loading" class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p class="mt-2 text-gray-600">Loading schema...</p>
        </div>

        <!-- Schema Content -->
        <div v-else-if="schema" data-testid="schema-content" class="space-y-4">
          <div class="bg-gray-50 rounded-md p-4">
            <pre class="text-sm text-gray-900 whitespace-pre-wrap font-mono">{{ schema }}</pre>
          </div>
        </div>
      </div>

      <!-- Timestamps -->
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Timestamps</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt class="text-sm font-medium text-gray-500">Created</dt>
            <dd data-testid="created-at" class="mt-1 text-sm text-gray-900">
              {{ formatDateTime(endpoint.createdAt) }}
            </dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-gray-500">Last Updated</dt>
            <dd data-testid="updated-at" class="mt-1 text-sm text-gray-900">
              {{ formatDateTime(endpoint.updatedAt) }}
            </dd>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { GraphQLEndpoint } from '../types/endpoint'
import { EndpointStatus } from '../types/endpoint'
import { useGraphQLClient } from '../services/graphql/client'
import {
  ArrowPathIcon,
  PencilIcon,
  TrashIcon,
  ClockIcon,
  CalendarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

// Props
interface Props {
  endpoint?: GraphQLEndpoint
}

const props = defineProps<Props>()

// Emits
defineEmits<{
  'edit': []
  'delete': []
  'health-check': []
}>()

// Services
const { getIntrospectionSchema } = useGraphQLClient()

// State
const isLoadingSchema = ref(false)
const schema = ref<string | null>(null)

// Methods
async function loadSchema() {
  if (!props.endpoint?.url || !props.endpoint.introspectionEnabled) return

  isLoadingSchema.value = true

  try {
    const result = await getIntrospectionSchema(props.endpoint.url)
    schema.value = result
  } catch (error) {
    schema.value = 'Failed to load schema'
    console.error('Failed to load schema:', error)
  } finally {
    isLoadingSchema.value = false
  }
}

function formatDate(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minutes ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours} hours ago`

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays} days ago`

  return date.toLocaleDateString()
}

function formatDateTime(date: Date): string {
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}
</script>
