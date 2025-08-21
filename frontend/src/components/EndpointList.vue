<template>
  <div class="space-y-6">
    <!-- Header with Add Button -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">GraphQL Endpoints</h1>
        <p class="text-gray-600">Manage your GraphQL endpoint connections</p>
      </div>
      <button
        @click="$emit('add-endpoint')"
        data-testid="add-endpoint-btn"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        <PlusIcon class="h-5 w-5 mr-2" />
        Add Endpoint
      </button>
    </div>

    <!-- Search and Filters -->
    <div class="flex items-center space-x-4">
      <div class="flex-1">
        <input
          v-model="searchQuery"
          data-testid="search-input"
          type="text"
          placeholder="Search endpoints..."
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>
      <div class="flex space-x-2">
        <button
          @click="statusFilter = statusFilter === 'healthy' ? 'all' : 'healthy'"
          data-testid="filter-healthy"
          :class="[
            'px-3 py-2 text-sm font-medium rounded-md',
            statusFilter === 'healthy'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          Healthy Only
        </button>
        <button
          @click="statusFilter = statusFilter === 'unhealthy' ? 'all' : 'unhealthy'"
          data-testid="filter-unhealthy"
          :class="[
            'px-3 py-2 text-sm font-medium rounded-md',
            statusFilter === 'unhealthy'
              ? 'bg-red-100 text-red-800'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          Unhealthy Only
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.isLoading" data-testid="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Loading endpoints...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="text-center py-12">
      <ExclamationTriangleIcon class="h-12 w-12 text-red-400 mx-auto" />
      <p class="mt-4 text-red-600">{{ store.error }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredEndpoints.length === 0 && !searchQuery" class="text-center py-12">
      <ServerStackIcon class="h-12 w-12 text-gray-400 mx-auto" />
      <p class="mt-4 text-gray-600">No endpoints configured yet</p>
      <button
        @click="$emit('add-endpoint')"
        class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200"
      >
        Add your first endpoint
      </button>
    </div>

    <!-- No Search Results -->
    <div v-else-if="filteredEndpoints.length === 0" class="text-center py-12">
      <MagnifyingGlassIcon class="h-12 w-12 text-gray-400 mx-auto" />
      <p class="mt-4 text-gray-600">No endpoints match your search</p>
    </div>

    <!-- Endpoints Grid -->
    <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="endpoint in filteredEndpoints"
        :key="endpoint.id"
        :data-testid="`endpoint-item-${endpoint.id}`"
        @click="$emit('select-endpoint', endpoint.id)"
        class="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:border-gray-300 cursor-pointer transition-colors duration-200"
      >
        <div class="px-6 py-4">
          <!-- Status and Actions Header -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-2">
              <!-- Status Indicator -->
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
                class="flex items-center space-x-1"
              >
                <div class="h-3 w-3 bg-green-500 rounded-full"></div>
                <span class="text-sm text-green-600">Healthy</span>
              </div>
              <div
                v-else
                data-testid="status-error"
                class="flex items-center space-x-1"
              >
                <div class="h-3 w-3 bg-red-500 rounded-full"></div>
                <span class="text-sm text-red-600">Error</span>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center space-x-2" @click.stop>
              <button
                @click="$emit('check-health', endpoint.id)"
                :data-testid="`check-health-${endpoint.id}`"
                class="p-1 text-gray-400 hover:text-gray-600"
                title="Check Health"
              >
                <ArrowPathIcon class="h-4 w-4" />
              </button>
              <button
                @click="$emit('edit-endpoint', endpoint.id)"
                :data-testid="`edit-endpoint-${endpoint.id}`"
                class="p-1 text-gray-400 hover:text-gray-600"
                title="Edit"
              >
                <PencilIcon class="h-4 w-4" />
              </button>
              <button
                @click="$emit('delete-endpoint', endpoint.id)"
                :data-testid="`delete-endpoint-${endpoint.id}`"
                class="p-1 text-gray-400 hover:text-red-600"
                title="Delete"
              >
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </div>

          <!-- Endpoint Info -->
          <div class="space-y-2">
            <h3 class="text-lg font-medium text-gray-900">{{ endpoint.name }}</h3>
            <p class="text-sm text-gray-600 break-all">{{ endpoint.url }}</p>
            <p v-if="endpoint.description" class="text-sm text-gray-500">
              {{ endpoint.description }}
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="endpoint.errorMessage" class="mt-3">
            <p class="text-sm text-red-600">{{ endpoint.errorMessage }}</p>
          </div>

          <!-- Metadata -->
          <div class="mt-4 flex items-center justify-between text-sm text-gray-500">
            <div class="flex items-center space-x-4">
              <span v-if="endpoint.responseTime">
                {{ endpoint.responseTime }}ms
              </span>
              <span v-if="endpoint.introspectionEnabled" class="text-blue-600">
                Introspection
              </span>
            </div>
            <span v-if="endpoint.lastChecked">
              {{ formatLastChecked(endpoint.lastChecked) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEndpointsStore } from '../stores/endpoints'
import { EndpointStatus } from '../types/endpoint'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ArrowPathIcon,
  ServerStackIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon
} from '@heroicons/vue/24/outline'

// Emits
defineEmits<{
  'add-endpoint': []
  'select-endpoint': [id: string]
  'edit-endpoint': [id: string]
  'delete-endpoint': [id: string]
  'check-health': [id: string]
}>()

// Store
const store = useEndpointsStore()

// Local state
const searchQuery = ref('')
const statusFilter = ref<'all' | 'healthy' | 'unhealthy'>('all')

// Computed
const filteredEndpoints = computed(() => {
  let endpoints = store.endpoints

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    endpoints = endpoints.filter(endpoint =>
      endpoint.name.toLowerCase().includes(query) ||
      endpoint.url.toLowerCase().includes(query) ||
      endpoint.description?.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value === 'healthy') {
    endpoints = endpoints.filter(endpoint => endpoint.isHealthy)
  } else if (statusFilter.value === 'unhealthy') {
    endpoints = endpoints.filter(endpoint => !endpoint.isHealthy)
  }

  return endpoints
})

// Methods
function formatLastChecked(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

// Lifecycle
onMounted(() => {
  store.loadEndpoints()
})
</script>