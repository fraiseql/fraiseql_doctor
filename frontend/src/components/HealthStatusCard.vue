<template>
  <div class="health-status-card p-4 border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold text-gray-900">{{ endpoint.name }}</h3>
      <div
        :class="statusClasses"
        class="w-3 h-3 rounded-full"
        data-testid="status-indicator"
      />
    </div>

    <div class="text-sm text-gray-600 mb-2">
      <span data-testid="response-time" class="font-medium">{{ endpoint.responseTime || 0 }}ms</span>
      <span class="mx-2">•</span>
      <span data-testid="last-checked">{{ formattedLastChecked }}</span>
    </div>

    <div v-if="!endpoint.isHealthy && endpoint.errorMessage" class="text-red-600 text-sm" data-testid="error-message">
      {{ endpoint.errorMessage }}
    </div>

    <div class="mt-3 text-xs text-gray-500">
      {{ endpoint.url }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { GraphQLEndpoint } from '../types/endpoint'

interface Props {
  endpoint: GraphQLEndpoint
}

const props = defineProps<Props>()

const statusClasses = computed(() => ({
  'bg-green-500': props.endpoint.isHealthy,
  'bg-red-500': !props.endpoint.isHealthy,
  'bg-yellow-500': props.endpoint.status === 'checking'
}))

const formattedLastChecked = computed(() => {
  if (!props.endpoint.lastChecked) return 'Never'

  const now = new Date()
  const checked = new Date(props.endpoint.lastChecked)
  const diffMs = now.getTime() - checked.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
})
</script>
