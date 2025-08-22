<template>
  <div class="bg-white p-6 rounded-lg shadow border-l-4" :class="healthBorderClass">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-lg">{{ endpoint.name }}</h3>
      <div class="flex items-center space-x-2">
        <div
          :data-testid="`${endpoint.id}-status`"
          :class="statusClasses"
          class="w-3 h-3 rounded-full"
        />
        <span class="text-sm text-gray-600">{{ endpoint.environment }}</span>
      </div>
    </div>

    <div class="space-y-2 mb-4">
      <div class="text-sm text-gray-600">{{ endpoint.url }}</div>
      <div class="flex justify-between text-sm">
        <span>Response Time:</span>
        <span data-testid="response-time" :class="responseTimeClass">
          {{ endpoint.responseTime }}ms
        </span>
      </div>
      <div class="flex justify-between text-sm">
        <span>Error Rate:</span>
        <span data-testid="error-rate" :class="errorRateClass">
          {{ endpoint.errorRate || 0 }}%
        </span>
      </div>
      <div class="flex justify-between text-sm">
        <span>Last Check:</span>
        <span data-testid="last-check-time" class="text-gray-500">
          {{ formatRelativeTime(endpoint.lastCheck) }}
        </span>
      </div>
    </div>

    <div class="flex space-x-2">
      <button
        :data-testid="`configure-${endpoint.id}`"
        class="flex-1 bg-blue-50 text-blue-600 px-3 py-2 rounded text-sm hover:bg-blue-100"
        @click="$emit('configure', endpoint)"
      >
        Configure
      </button>
      <button
        class="flex-1 bg-gray-50 text-gray-600 px-3 py-2 rounded text-sm hover:bg-gray-100"
        @click="$emit('test', endpoint)"
      >
        Test
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiEndpoint } from '@/types/admin'

interface Props {
  endpoint: ApiEndpoint
}

const props = defineProps<Props>()
defineEmits(['configure', 'test'])

const healthBorderClass = computed(() => ({
  'border-green-500': props.endpoint.isHealthy && props.endpoint.responseTime < 200,
  'border-yellow-500': props.endpoint.isHealthy && props.endpoint.responseTime >= 200,
  'border-red-500': !props.endpoint.isHealthy
}))

const statusClasses = computed(() => ({
  'bg-green-500': props.endpoint.isHealthy && props.endpoint.responseTime < 200,
  'bg-yellow-500': props.endpoint.isHealthy && props.endpoint.responseTime >= 200,
  'bg-red-500': !props.endpoint.isHealthy,
  'status-indicator': true,
  'status-healthy': props.endpoint.isHealthy && props.endpoint.responseTime < 200,
  'status-warning': props.endpoint.isHealthy && props.endpoint.responseTime >= 200,
  'status-unhealthy': !props.endpoint.isHealthy
}))

const responseTimeClass = computed(() => ({
  'text-green-600': props.endpoint.responseTime < 200,
  'text-yellow-600': props.endpoint.responseTime >= 200 && props.endpoint.responseTime < 500,
  'text-red-600': props.endpoint.responseTime >= 500
}))

const errorRateClass = computed(() => ({
  'text-green-600': (props.endpoint.errorRate || 0) < 1,
  'text-yellow-600': (props.endpoint.errorRate || 0) >= 1 && (props.endpoint.errorRate || 0) < 5,
  'text-red-600': (props.endpoint.errorRate || 0) >= 5
}))

const formatRelativeTime = (date: Date): string => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}min ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}
</script>
