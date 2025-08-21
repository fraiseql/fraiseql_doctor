<template>
  <div 
    data-testid="apollo-studio-container"
    class="apollo-studio-integration"
  >
    <header class="studio-header">
      <h2 data-testid="studio-title" class="text-xl font-semibold">
        GraphQL Playground
      </h2>
    </header>

    <!-- Loading State -->
    <div 
      v-if="isLoading"
      data-testid="studio-loading"
      class="studio-loading"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading Apollo Studio...</p>
    </div>

    <!-- Apollo Studio Iframe -->
    <iframe
      v-if="endpointUrl"
      data-testid="apollo-studio-iframe"
      :src="studioUrl"
      class="studio-iframe"
      @load="handleIframeLoad"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { buildApolloStudioUrl } from '../utils/apolloStudioUrl'

// Props
interface Props {
  endpointUrl?: string
}

const props = defineProps<Props>()

// State
const isLoading = ref(true)

// Computed
const studioUrl = computed(() => {
  if (!props.endpointUrl) return ''
  return buildApolloStudioUrl(props.endpointUrl)
})

// Methods
function handleIframeLoad() {
  isLoading.value = false
}
</script>

<style scoped>
.apollo-studio-integration {
  @apply w-full h-full relative bg-white;
}

.studio-header {
  @apply p-4 border-b border-gray-200;
}

.studio-loading {
  @apply absolute inset-0 flex flex-col items-center justify-center bg-white;
}

.studio-iframe {
  @apply w-full border-0;
  height: calc(100% - 73px); /* Account for header */
}
</style>