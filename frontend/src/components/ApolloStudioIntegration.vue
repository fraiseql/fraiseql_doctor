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
  </div>
</template>

<script setup lang="ts">
// Minimal setup - no logic yet
</script>

<style scoped>
.apollo-studio-integration {
  @apply w-full h-full relative bg-white;
}

.studio-header {
  @apply p-4 border-b border-gray-200;
}
</style>