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
                <span class="ml-1 text-sm font-medium text-gray-500">{{ endpoint.name }}</span>
              </div>
            </li>
          </ol>
        </nav>

        <EndpointDetails
          v-if="endpoint"
          :endpoint="endpoint"
          @edit="handleEdit"
          @delete="handleDelete"
          @health-check="handleHealthCheck"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEndpointsStore } from '../stores/endpoints'
import EndpointDetails from '../components/EndpointDetails.vue'
import { ServerStackIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

interface Props {
  id: string
}

const props = defineProps<Props>()
const router = useRouter()
const endpointsStore = useEndpointsStore()

const endpoint = computed(() =>
  endpointsStore.endpoints.find(e => e.id === props.id)
)

function handleEdit() {
  router.push(`/endpoints/${props.id}/edit`)
}

async function handleDelete() {
  const confirmed = confirm('Are you sure you want to delete this endpoint?')
  if (confirmed) {
    const success = await endpointsStore.deleteEndpoint(props.id)
    if (success) {
      router.push('/endpoints')
    }
  }
}

async function handleHealthCheck() {
  await endpointsStore.performHealthCheck(props.id)
}

onMounted(() => {
  // Load endpoints if not already loaded
  if (endpointsStore.endpoints.length === 0) {
    endpointsStore.loadEndpoints()
  }
})
</script>
