<template>
  <div class="min-h-screen bg-gray-50">
    <div class="py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <EndpointList
          @add-endpoint="handleAddEndpoint"
          @select-endpoint="handleSelectEndpoint"
          @edit-endpoint="handleEditEndpoint"
          @delete-endpoint="handleDeleteEndpoint"
          @check-health="handleCheckHealth"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useEndpointsStore } from '../stores/endpoints'
import EndpointList from '../components/EndpointList.vue'

const router = useRouter()
const endpointsStore = useEndpointsStore()

function handleAddEndpoint() {
  router.push('/endpoints/new')
}

function handleSelectEndpoint(id: string) {
  router.push(`/endpoints/${id}`)
}

function handleEditEndpoint(id: string) {
  router.push(`/endpoints/${id}/edit`)
}

async function handleDeleteEndpoint(id: string) {
  const confirmed = confirm('Are you sure you want to delete this endpoint?')
  if (confirmed) {
    await endpointsStore.deleteEndpoint(id)
  }
}

async function handleCheckHealth(id: string) {
  await endpointsStore.performHealthCheck(id)
}
</script>
