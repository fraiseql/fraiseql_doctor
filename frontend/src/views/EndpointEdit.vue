<template>
  <div class="min-h-screen bg-gray-50">
    <div class="py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Breadcrumbs -->
        <nav class="flex mb-8" aria-label="Breadcrumb">
          <ol class="inline-flex items-center space-x-1 md:space-x-3">
            <li class="inline-flex items-center">
              <router-link
                to="/endpoints"
                class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-blue-600"
              >
                <ServerStackIcon class="h-4 w-4 mr-2" />
                Endpoints
              </router-link>
            </li>
            <li v-if="endpoint">
              <div class="flex items-center">
                <ChevronRightIcon class="h-5 w-5 text-gray-400" />
                <router-link
                  :to="`/endpoints/${endpoint.id}`"
                  class="ml-1 text-sm font-medium text-gray-700 hover:text-blue-600"
                >
                  {{ endpoint.name }}
                </router-link>
              </div>
            </li>
            <li>
              <div class="flex items-center">
                <ChevronRightIcon class="h-5 w-5 text-gray-400" />
                <span class="ml-1 text-sm font-medium text-gray-500">Edit</span>
              </div>
            </li>
          </ol>
        </nav>

        <EndpointForm
          v-if="endpoint"
          mode="edit"
          :endpoint="endpoint"
          :loading="isLoading"
          @update="handleUpdate"
          @cancel="handleCancel"
        />

        <!-- Loading state while fetching endpoint -->
        <div v-else class="text-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p class="mt-4 text-gray-600">Loading endpoint...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEndpointsStore } from '../stores/endpoints'
import EndpointForm from '../components/EndpointForm.vue'
import type { UpdateEndpointInput } from '../types/endpoint'
import { ServerStackIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

interface Props {
  id: string
}

const props = defineProps<Props>()
const router = useRouter()
const endpointsStore = useEndpointsStore()

const isLoading = ref(false)

const endpoint = computed(() => 
  endpointsStore.endpoints.find(e => e.id === props.id)
)

async function handleUpdate(data: UpdateEndpointInput) {
  isLoading.value = true
  
  try {
    const success = await endpointsStore.updateEndpoint(props.id, data)
    if (success) {
      router.push(`/endpoints/${props.id}`)
    }
  } catch (error) {
    console.error('Failed to update endpoint:', error)
  } finally {
    isLoading.value = false
  }
}

function handleCancel() {
  router.push(`/endpoints/${props.id}`)
}

onMounted(() => {
  // Load endpoints if not already loaded
  if (endpointsStore.endpoints.length === 0) {
    endpointsStore.loadEndpoints()
  }
})
</script>