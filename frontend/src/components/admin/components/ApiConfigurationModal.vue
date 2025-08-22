<template>
  <div
    v-if="modelValue"
    data-testid="api-config-modal"
    class="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center p-4"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
      <h2 class="text-lg font-semibold mb-4">
        Configure API: {{ endpoint?.name }}
      </h2>

      <div class="text-sm text-gray-600 mb-4">
        Modal placeholder - configuration form will be implemented in next cycle
      </div>

      <div class="flex justify-end space-x-3">
        <button
          type="button"
          class="px-4 py-2 text-gray-600 hover:text-gray-800"
          @click="$emit('update:modelValue', false)"
        >
          Cancel
        </button>
        <button
          type="button"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          @click="handleSave"
        >
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  endpoint: any
}

defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'save'])

const handleSave = () => {
  emit('save', { test: 'config' })
  emit('update:modelValue', false)
}
</script>
