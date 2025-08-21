<template>
  <div class="query-history bg-white dark:bg-gray-800 rounded-lg shadow">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          Query History
        </h3>
        <div class="flex items-center space-x-2">
          <!-- Connection Status -->
          <div class="flex items-center space-x-1">
            <div 
              class="w-2 h-2 rounded-full"
              :class="connectionStatus.connected ? 'bg-green-500' : 'bg-orange-500'"
            ></div>
            <span class="text-xs text-gray-500 dark:text-gray-400">
              {{ connectionStatus.connected ? 'API' : 'Offline' }}
            </span>
          </div>

          <!-- Stats Display -->
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{ stats.totalQueries }} queries, {{ stats.successfulQueries }} successful
          </div>
          
          <!-- Actions -->
          <button
            @click="exportHistory"
            class="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            :disabled="!hasHistory"
          >
            Export
          </button>
          <button
            @click="clearAllHistory"
            class="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            :disabled="!hasHistory"
          >
            Clear All
          </button>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Endpoint Filter -->
        <select
          v-model="filters.endpointId"
          class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="">All Endpoints</option>
          <option v-for="endpoint in endpoints" :key="endpoint.id" :value="endpoint.id">
            {{ endpoint.name }}
          </option>
        </select>

        <!-- Success Filter -->
        <select
          v-model="filters.success"
          class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option :value="undefined">All Status</option>
          <option :value="true">Successful</option>
          <option :value="false">Failed</option>
        </select>

        <!-- Favorites Filter -->
        <label class="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            v-model="filters.onlyFavorites"
            class="rounded border-gray-300 dark:border-gray-600"
          >
          <span class="text-gray-700 dark:text-gray-300">Favorites only</span>
        </label>

        <!-- Search -->
        <input
          v-model="filters.searchTerm"
          type="text"
          placeholder="Search queries, operations, tags..."
          class="flex-1 min-w-0 px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        >

        <!-- Clear Filters -->
        <button
          @click="clearFilters"
          v-if="hasActiveFilters"
          class="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
        >
          Clear Filters
        </button>
      </div>

      <!-- Date Range -->
      <div class="flex items-center space-x-3">
        <label class="text-sm text-gray-700 dark:text-gray-300">From:</label>
        <input
          v-model="filters.fromDate"
          type="datetime-local"
          class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
        <label class="text-sm text-gray-700 dark:text-gray-300">To:</label>
        <input
          v-model="filters.toDate"
          type="datetime-local"
          class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
      </div>
    </div>

    <!-- History List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="p-8 text-center text-gray-500 dark:text-gray-400">
        Loading history...
      </div>
      
      <div v-else-if="!hasHistory" class="p-8 text-center text-gray-500 dark:text-gray-400">
        No query history found.
      </div>
      
      <div v-else-if="filteredHistory.length === 0" class="p-8 text-center text-gray-500 dark:text-gray-400">
        No queries match your current filters.
      </div>

      <div v-else class="divide-y divide-gray-200 dark:divide-gray-700">
        <QueryHistoryEntry
          v-for="entry in paginatedHistory"
          :key="entry.id"
          :entry="entry"
          :endpoint="getEndpoint(entry.endpointId)"
          @toggle-favorite="toggleFavorite"
          @delete="deleteEntry"
          @replay="replayQuery"
          @save-as-template="saveAsTemplate"
        />
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="p-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Showing {{ startIndex + 1 }}-{{ endIndex }} of {{ filteredHistory.length }} queries
          </div>
          <div class="flex items-center space-x-2">
            <button
              @click="currentPage = Math.max(1, currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span class="text-sm text-gray-700 dark:text-gray-300">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button
              @click="currentPage = Math.min(totalPages, currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Export Modal -->
    <ExportModal
      v-if="showExportModal"
      :history-count="filteredHistory.length"
      @export="handleExport"
      @close="showExportModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useQueryHistoryHybrid } from '../services/queryHistoryHybrid'
import type { 
  QueryHistoryEntry as HistoryEntry,
  QueryHistoryFilter,
  QueryHistoryExportOptions
} from '../types/queryHistory'
import type { GraphQLEndpoint } from '../types/endpoint'
import QueryHistoryEntry from './QueryHistoryEntry.vue'
import ExportModal from './ExportModal.vue'

interface Props {
  endpoints: GraphQLEndpoint[]
  currentEndpoint?: GraphQLEndpoint
}

interface Emits {
  (event: 'replay-query', entry: HistoryEntry): void
  (event: 'save-template', entry: HistoryEntry): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Query History Service (Hybrid API/localStorage)
const queryHistoryService = useQueryHistoryHybrid()

// State
const loading = ref(true)
const history = ref<HistoryEntry[]>([])
const stats = ref({ totalQueries: 0, successfulQueries: 0, failedQueries: 0, averageResponseTime: 0 })
const connectionStatus = ref({ connected: false, source: 'localStorage' })
const currentPage = ref(1)
const pageSize = ref(20)
const showExportModal = ref(false)

// Filters
const filters = ref<{
  endpointId?: string
  success?: boolean
  searchTerm?: string
  onlyFavorites: boolean
  fromDate?: string
  toDate?: string
}>({
  endpointId: props.currentEndpoint?.id || '',
  success: undefined,
  searchTerm: '',
  onlyFavorites: false,
  fromDate: '',
  toDate: ''
})

// Computed
const hasHistory = computed(() => history.value.length > 0)

const hasActiveFilters = computed(() => {
  return filters.value.endpointId ||
         filters.value.success !== undefined ||
         filters.value.searchTerm ||
         filters.value.onlyFavorites ||
         filters.value.fromDate ||
         filters.value.toDate
})

const filteredHistory = computed(() => {
  // Client-side filtering since we already have the data loaded
  let filtered = history.value
  
  if (filters.value.endpointId) {
    filtered = filtered.filter(entry => entry.endpointId === filters.value.endpointId)
  }
  
  if (filters.value.success !== undefined) {
    filtered = filtered.filter(entry => entry.success === filters.value.success)
  }
  
  if (filters.value.searchTerm) {
    const searchTerm = filters.value.searchTerm.toLowerCase()
    filtered = filtered.filter(entry => 
      entry.query.toLowerCase().includes(searchTerm) ||
      entry.operationName?.toLowerCase().includes(searchTerm) ||
      entry.tags?.some(tag => tag.toLowerCase().includes(searchTerm))
    )
  }
  
  if (filters.value.onlyFavorites) {
    filtered = filtered.filter(entry => entry.favorite)
  }
  
  if (filters.value.fromDate) {
    const fromDate = new Date(filters.value.fromDate)
    filtered = filtered.filter(entry => entry.timestamp >= fromDate)
  }
  
  if (filters.value.toDate) {
    const toDate = new Date(filters.value.toDate)
    filtered = filtered.filter(entry => entry.timestamp <= toDate)
  }
  
  return filtered
})

const totalPages = computed(() => Math.ceil(filteredHistory.value.length / pageSize.value))

const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
const endIndex = computed(() => Math.min(startIndex.value + pageSize.value, filteredHistory.value.length))

const paginatedHistory = computed(() => {
  return filteredHistory.value.slice(startIndex.value, endIndex.value)
})

// Methods
function getEndpoint(endpointId: string): GraphQLEndpoint | undefined {
  return props.endpoints.find(e => e.id === endpointId)
}

async function loadHistory() {
  loading.value = true
  try {
    // Load history and stats in parallel
    const [historyData, statsData] = await Promise.all([
      queryHistoryService.getHistory(),
      queryHistoryService.getStats()
    ])
    
    history.value = historyData
    stats.value = statsData
    connectionStatus.value = {
      connected: queryHistoryService.isApiConnected(),
      source: queryHistoryService.isApiConnected() ? 'api' : 'localStorage'
    }
  } catch (error) {
    console.error('Failed to load history:', error)
    history.value = []
  } finally {
    loading.value = false
  }
}

function clearFilters() {
  filters.value = {
    endpointId: '',
    success: undefined,
    searchTerm: '',
    onlyFavorites: false,
    fromDate: '',
    toDate: ''
  }
  currentPage.value = 1
}

async function toggleFavorite(entry: HistoryEntry) {
  try {
    const result = await queryHistoryService.updateQuery(entry.id, {
      favorite: !entry.favorite
    })
    
    if (result.success && result.entry) {
      // Update local copy
      const index = history.value.findIndex(h => h.id === entry.id)
      if (index >= 0) {
        history.value[index] = result.entry
      }
    }
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
  }
}

async function deleteEntry(entry: HistoryEntry) {
  if (confirm('Are you sure you want to delete this query from history?')) {
    try {
      const result = await queryHistoryService.deleteQuery(entry.id)
      
      if (result.success) {
        await loadHistory()
      }
    } catch (error) {
      console.error('Failed to delete entry:', error)
    }
  }
}

function replayQuery(entry: HistoryEntry) {
  emit('replay-query', entry)
}

function saveAsTemplate(entry: HistoryEntry) {
  emit('save-template', entry)
}

function exportHistory() {
  showExportModal.value = true
}

async function handleExport(options: QueryHistoryExportOptions) {
  try {
    const filter: QueryHistoryFilter = {
      endpointId: filters.value.endpointId || undefined,
      success: filters.value.success,
      searchTerm: filters.value.searchTerm || undefined,
      favorite: filters.value.onlyFavorites ? true : undefined,
      fromDate: filters.value.fromDate ? new Date(filters.value.fromDate) : undefined,
      toDate: filters.value.toDate ? new Date(filters.value.toDate) : undefined
    }
    
    const result = await queryHistoryService.exportHistory({
      ...options,
      filter
    })
    
    if (result.success && result.result) {
      const blob = new Blob([result.result.data], { type: result.result.mimeType })
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = result.result.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      
      URL.revokeObjectURL(url)
    }
  } catch (error) {
    console.error('Failed to export history:', error)
  }
  
  showExportModal.value = false
}

async function clearAllHistory() {
  if (confirm('Are you sure you want to clear all query history? This action cannot be undone.')) {
    try {
      await queryHistoryService.clearHistory()
      await loadHistory()
    } catch (error) {
      console.error('Failed to clear history:', error)
    }
  }
}

// Watch for filter changes to reset pagination
watch(filters, () => {
  currentPage.value = 1
}, { deep: true })

// Watch for endpoint changes
watch(() => props.currentEndpoint, (newEndpoint) => {
  if (newEndpoint && !filters.value.endpointId) {
    filters.value.endpointId = newEndpoint.id
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.query-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 500px;
}
</style>