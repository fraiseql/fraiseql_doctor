<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">
            Export Query History
          </h3>
          <button
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <form @submit.prevent="handleExport" class="px-6 py-4 space-y-4">
        <!-- Format Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Export Format
          </label>
          <div class="space-y-2">
            <label class="flex items-center">
              <input
                type="radio"
                v-model="exportOptions.format"
                value="json"
                class="mr-2"
              >
              <span class="text-sm text-gray-700 dark:text-gray-300">JSON</span>
              <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">(Complete data structure)</span>
            </label>
            <label class="flex items-center">
              <input
                type="radio"
                v-model="exportOptions.format"
                value="csv"
                class="mr-2"
              >
              <span class="text-sm text-gray-700 dark:text-gray-300">CSV</span>
              <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">(Spreadsheet compatible)</span>
            </label>
            <label class="flex items-center">
              <input
                type="radio"
                v-model="exportOptions.format"
                value="graphql"
                class="mr-2"
              >
              <span class="text-sm text-gray-700 dark:text-gray-300">GraphQL</span>
              <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">(Query collection)</span>
            </label>
          </div>
        </div>

        <!-- Data Inclusion Options -->
        <div class="space-y-2">
          <label class="flex items-center">
            <input
              type="checkbox"
              v-model="exportOptions.includeVariables"
              class="mr-2"
            >
            <span class="text-sm text-gray-700 dark:text-gray-300">Include Variables</span>
          </label>
          <label class="flex items-center">
            <input
              type="checkbox"
              v-model="exportOptions.includeResults"
              class="mr-2"
            >
            <span class="text-sm text-gray-700 dark:text-gray-300">Include Results</span>
          </label>
        </div>

        <!-- Export Info -->
        <div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
          <p class="text-sm text-blue-800 dark:text-blue-200">
            <strong>{{ historyCount }}</strong> queries will be exported based on your current filters.
          </p>
        </div>

        <!-- Actions -->
        <div class="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Export
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { QueryHistoryExportOptions } from '../types/queryHistory'

interface Props {
  historyCount: number
}

interface Emits {
  (event: 'export', options: QueryHistoryExportOptions): void
  (event: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const exportOptions = ref<QueryHistoryExportOptions>({
  format: 'json',
  includeResults: true,
  includeVariables: true
})

function handleExport() {
  emit('export', exportOptions.value)
}
</script>