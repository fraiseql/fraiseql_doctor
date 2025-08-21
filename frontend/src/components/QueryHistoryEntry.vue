<template>
  <div class="query-history-entry p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
    <div class="flex items-start justify-between">
      <!-- Main Content -->
      <div class="flex-1 min-w-0">
        <!-- Header -->
        <div class="flex items-center space-x-3 mb-2">
          <!-- Status Indicator -->
          <div class="flex-shrink-0">
            <div
              :class="[
                'w-2 h-2 rounded-full',
                entry.success ? 'bg-green-500' : 'bg-red-500'
              ]"
            />
          </div>

          <!-- Operation Name / Query Preview -->
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ entry.operationName || extractOperationName(entry.query) || 'Unnamed Query' }}
            </h4>
            <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
              {{ queryPreview }}
            </p>
          </div>

          <!-- Timestamp and Execution Time -->
          <div class="flex-shrink-0 text-right">
            <div class="text-xs text-gray-500 dark:text-gray-400" data-testid="timestamp">
              {{ formatTimestamp(entry.timestamp) }}
            </div>
            <div class="text-xs">
              <span :class="executionTimeClass" data-testid="execution-time">
                {{ entry.executionTime }}ms
              </span>
            </div>
          </div>

          <!-- Favorite Button -->
          <button
            @click="$emit('toggle-favorite', entry)"
            class="flex-shrink-0 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            :class="entry.favorite ? 'text-yellow-500' : 'text-gray-400 dark:text-gray-500'"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </button>
        </div>

        <!-- Endpoint Info -->
        <div class="flex items-center space-x-4 mb-2 text-xs">
          <span class="text-gray-600 dark:text-gray-400">
            <strong>Endpoint:</strong> {{ endpoint?.name || 'Unknown' }}
          </span>

          <span v-if="entry.statusCode" class="text-gray-600 dark:text-gray-400">
            <strong>Status:</strong> {{ entry.statusCode }}
          </span>
        </div>

        <!-- Tags -->
        <div v-if="entry.tags.length > 0" class="flex flex-wrap gap-1 mb-2">
          <span
            v-for="tag in entry.tags"
            :key="tag"
            class="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 rounded"
          >
            {{ tag }}
          </span>
        </div>

        <!-- Error Message -->
        <div v-if="!entry.success && entry.error" class="mb-2">
          <div class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            <strong>Error:</strong> {{ entry.error }}
          </div>
        </div>

        <!-- Expandable Sections -->
        <div class="space-y-1">
          <!-- Query -->
          <details class="group">
            <summary class="text-xs text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-800 dark:hover:text-gray-200 flex items-center space-x-1">
              <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
              <span>Query</span>
            </summary>
            <div class="mt-1 ml-4">
              <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto"><code>{{ entry.query }}</code></pre>
            </div>
          </details>

          <!-- Variables -->
          <details v-if="entry.variables" class="group">
            <summary class="text-xs text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-800 dark:hover:text-gray-200 flex items-center space-x-1">
              <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
              <span>Variables</span>
            </summary>
            <div class="mt-1 ml-4">
              <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto"><code>{{ JSON.stringify(entry.variables, null, 2) }}</code></pre>
            </div>
          </details>

          <!-- Result -->
          <details v-if="entry.result" class="group">
            <summary class="text-xs text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-800 dark:hover:text-gray-200 flex items-center space-x-1">
              <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
              <span>Result</span>
            </summary>
            <div class="mt-1 ml-4">
              <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto max-h-40 overflow-y-auto"><code>{{ JSON.stringify(entry.result, null, 2) }}</code></pre>
            </div>
          </details>

          <!-- Headers -->
          <details v-if="entry.headers && Object.keys(entry.headers).length > 0" class="group">
            <summary class="text-xs text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-800 dark:hover:text-gray-200 flex items-center space-x-1">
              <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
              <span>Headers</span>
            </summary>
            <div class="mt-1 ml-4">
              <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto"><code>{{ JSON.stringify(entry.headers, null, 2) }}</code></pre>
            </div>
          </details>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex-shrink-0 ml-4">
        <div class="flex items-center space-x-1">
          <!-- Replay Query -->
          <button
            @click="$emit('replay', entry)"
            class="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            title="Replay this query"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          <!-- Save as Template -->
          <button
            @click="$emit('save-as-template', entry)"
            class="p-1 text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors"
            title="Save as template"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </button>

          <!-- Delete -->
          <button
            @click="$emit('delete', entry)"
            class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            title="Delete from history"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { QueryHistoryEntry } from '../types/queryHistory'
import type { GraphQLEndpoint } from '../types/endpoint'

interface Props {
  entry: QueryHistoryEntry
  endpoint?: GraphQLEndpoint
}

interface Emits {
  (event: 'toggle-favorite', entry: QueryHistoryEntry): void
  (event: 'delete', entry: QueryHistoryEntry): void
  (event: 'replay', entry: QueryHistoryEntry): void
  (event: 'save-as-template', entry: QueryHistoryEntry): void
}

const props = defineProps<Props>()
defineEmits<Emits>()

const queryPreview = computed(() => {
  return props.entry.query.replace(/\s+/g, ' ').trim().substring(0, 100) +
    (props.entry.query.length > 100 ? '...' : '')
})

const executionTimeClass = computed(() => {
  const time = props.entry.executionTime
  if (time > 5000) return 'text-red-600 dark:text-red-400'
  if (time > 2000) return 'text-yellow-600 dark:text-yellow-400'
  if (time > 1000) return 'text-blue-600 dark:text-blue-400'
  return 'text-green-600 dark:text-green-400'
})

function extractOperationName(query: string): string | null {
  const match = query.match(/(?:query|mutation|subscription)\s+(\w+)/i)
  return match ? match[1] : null
}

function formatTimestamp(timestamp: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - timestamp.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return timestamp.toLocaleDateString()
}
</script>
