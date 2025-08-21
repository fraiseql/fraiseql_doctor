<template>
  <div 
    data-testid="apollo-studio-container"
    :class="containerClasses"
    :role="ariaLabel ? 'application' : undefined"
    :aria-label="ariaLabel"
    :style="containerStyles"
  >
    <header class="studio-header">
      <div class="flex items-center justify-between">
        <div>
          <h2 data-testid="studio-title" class="text-xl font-semibold">
            GraphQL Playground
          </h2>
          
          <!-- Configuration Summary -->
          <div v-if="configMode === 'advanced'" data-testid="config-summary" class="text-sm text-gray-600 mt-2">
            <span v-if="authSummary">{{ authSummary }}</span>
            <span v-if="endpoint?.introspectionEnabled"> • Introspection enabled</span>
          </div>
        </div>

        <!-- Query History Toggle -->
        <div class="flex items-center space-x-2">
          <button
            @click="showQueryHistory = !showQueryHistory"
            :class="[
              'px-3 py-2 text-sm rounded transition-colors',
              showQueryHistory 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            ]"
            title="Toggle Query History"
          >
            <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            History
          </button>
        </div>
      </div>
    </header>

    <!-- Error Boundary -->
    <div 
      v-if="showErrorState"
      data-testid="error-boundary" 
      class="error-boundary"
    >
      <div class="error-content">
        <div class="text-red-600 mb-4">
          <svg class="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.96-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
          <h3 data-testid="error-message" class="text-lg font-semibold">Configuration Error</h3>
        </div>
        
        <div v-if="debugMode" data-testid="debug-panel" class="mt-4 p-4 bg-gray-100 rounded">
          <div v-if="hasSecurityWarning" data-testid="security-warning" class="text-red-600 font-semibold mb-2">
            ⚠️ Security Warning
          </div>
          <div data-testid="error-details" class="text-sm text-gray-700">
            {{ errorDetails }}
          </div>
        </div>
        
        <button 
          v-if="enableRetry && canRetry"
          data-testid="retry-button"
          @click="handleRetry"
          class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          Retry Connection
        </button>
      </div>
    </div>

    <!-- Error State for Network Issues -->
    <div 
      v-if="showNetworkError"
      data-testid="error-state" 
      class="network-error"
    >
      <p class="text-orange-600">Connection failed. Retrying...</p>
      <div data-testid="retry-counter" class="text-sm text-gray-600 mt-2">
        Attempt {{ retryCount }} of {{ maxRetries }}
      </div>
      
      <button 
        data-testid="retry-button"
        @click="handleRetry"
        class="mt-4 px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
      >
        Retry Now
      </button>
    </div>

    <!-- Loading State -->
    <div 
      v-if="isLoading && !showErrorState"
      data-testid="studio-loading"
      class="studio-loading"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading Apollo Studio...</p>
    </div>

    <!-- Main Content Area -->
    <div class="studio-content flex-1 flex" v-if="!showErrorState && !showNetworkError">
      <!-- Apollo Studio Iframe -->
      <div class="studio-main flex-1">
        <iframe
          v-if="showIframe"
          data-testid="apollo-studio-iframe"
          :src="finalStudioUrl"
          :title="iframeTitle"
          :aria-label="iframeAriaLabel"
          :style="iframeStyles"
          class="studio-iframe"
          @load="handleIframeLoad"
          @error="handleIframeError"
        />
      </div>

      <!-- Query History Sidebar -->
      <div 
        v-if="showQueryHistory"
        class="studio-history w-96 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
      >
        <QueryHistory
          :endpoints="availableEndpoints"
          :current-endpoint="endpoint"
          @replay-query="handleReplayQuery"
          @save-template="handleSaveTemplate"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { buildApolloStudioUrl } from '../utils/apolloStudioUrl'
import { useApolloStudioConfig } from '../services/apolloStudioConfig'
import { useQueryHistoryHybrid } from '../services/queryHistoryHybrid'
import QueryHistory from './QueryHistory.vue'
import type { AuthType, StudioConfig, UrlParams } from '../services/apolloStudioConfig'
import type { GraphQLEndpoint } from '../types/endpoint'
import type { QueryHistoryEntry } from '../types/queryHistory'

// Props
interface Props {
  endpointUrl?: string
  endpoint?: GraphQLEndpoint
  availableEndpoints?: GraphQLEndpoint[]
  authType?: AuthType
  customParams?: UrlParams
  studioConfig?: StudioConfig
  theme?: 'light' | 'dark'
  height?: string
  responsive?: boolean
  ariaLabel?: string
  configMode?: 'simple' | 'advanced'
  showErrorBoundary?: boolean
  debugMode?: boolean
  enableRetry?: boolean
  maxRetries?: number
  enableQueryHistory?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'light',
  height: 'auto',
  responsive: false,
  configMode: 'simple',
  showErrorBoundary: false,
  debugMode: false,
  enableRetry: true,
  maxRetries: 3,
  enableQueryHistory: true,
  availableEndpoints: () => []
})

// Emits
const emit = defineEmits<{
  'studio-loaded': [payload: { url: string; timestamp: Date }]
  'studio-error': [error: Error]
  'config-changed': [config: StudioConfig]
  'query-replayed': [entry: QueryHistoryEntry]
  'template-requested': [entry: QueryHistoryEntry]
}>()

// Composables
const {
  generateStudioUrlWithParams,
  validateConfigurationSafely,
  createConfigWithAuthSafely,
  detectAuthType
} = useApolloStudioConfig()

const queryHistoryService = useQueryHistoryHybrid()

// State
const isLoading = ref(true)
const hasError = ref(false)
const retryCount = ref(0)
const errorMessage = ref('')
const networkError = ref(false)
const showQueryHistory = ref(false)

// Computed Properties
const containerClasses = computed(() => {
  const classes = ['apollo-studio-integration']
  if (props.responsive) classes.push('responsive-layout')
  if (props.theme === 'dark') classes.push('dark-theme')
  return classes
})

const containerStyles = computed(() => {
  const styles: Record<string, string> = {}
  if (props.height && props.height !== 'auto') {
    styles.height = props.height
  }
  return styles
})

const iframeStyles = computed(() => {
  const styles: Record<string, string> = {}
  if (props.height && props.height !== 'auto') {
    styles.height = `calc(${props.height} - 73px)` // Account for header
  }
  return styles
})

const showErrorState = computed(() => {
  return hasError.value && props.showErrorBoundary
})

const showNetworkError = computed(() => {
  return networkError.value && props.enableRetry
})

const showIframe = computed(() => {
  const hasValidUrl = finalStudioUrl.value && finalStudioUrl.value.length > 0
  return hasValidUrl && 
         (props.endpointUrl || props.endpoint || props.studioConfig) && 
         !showErrorState.value && 
         !showNetworkError.value
})

const canRetry = computed(() => {
  return retryCount.value < props.maxRetries
})

const authSummary = computed(() => {
  if (!props.endpoint?.headers) return ''
  
  const authType = detectAuthType(props.endpoint.headers)
  
  switch (authType) {
    case 'bearer': return 'Bearer authentication'
    case 'apikey': return 'API Key authentication'
    case 'basic': return 'Basic authentication'
    default: return 'No authentication'
  }
})

const errorDetails = computed(() => {
  if (hasSecurityWarning.value) {
    return 'Dangerous URL pattern detected. Please use a valid HTTPS endpoint.'
  }
  return errorMessage.value
})

const hasSecurityWarning = computed(() => {
  const url = props.endpointUrl || props.endpoint?.url || ''
  return url.includes('javascript:') || url.includes('<script')
})

const finalStudioUrl = computed(() => {
  try {
    // Priority 1: Studio config
    if (props.studioConfig) {
      const mockEndpoint = { 
        id: '1',
        name: 'Configured API',
        url: props.studioConfig.endpoint,
        status: 'ACTIVE' as const,
        introspectionEnabled: true,
        isHealthy: true,
        createdAt: new Date(),
        updatedAt: new Date()
      } as GraphQLEndpoint
      return generateStudioUrlWithParams(mockEndpoint, props.customParams || {})
    }
    
    // Priority 2: Endpoint with auth type
    if (props.endpoint && props.authType) {
      const result = createConfigWithAuthSafely(props.endpoint, props.authType)
      if (result.success && result.config) {
        return generateStudioUrlWithParams(props.endpoint, props.customParams || {})
      }
    }
    
    // Priority 3: Endpoint without auth type
    if (props.endpoint) {
      return generateStudioUrlWithParams(props.endpoint, props.customParams || {})
    }
    
    // Priority 4: Simple endpoint URL
    if (props.endpointUrl) {
      const customParamsWithTheme = {
        ...(props.customParams || {}),
        ...(props.theme !== 'light' ? { theme: props.theme } : {})
      }
      
      // Always use advanced function for consistency
      const mockEndpoint = {
        id: '1',
        name: 'Simple API',
        url: props.endpointUrl,
        status: 'ACTIVE' as const,
        introspectionEnabled: true,
        isHealthy: true,
        createdAt: new Date(),
        updatedAt: new Date()
      } as GraphQLEndpoint
      
      return generateStudioUrlWithParams(mockEndpoint, customParamsWithTheme)
    }
    
    return ''
  } catch (error) {
    console.error('Error generating studio URL:', error)
    // Ultimate fallback
    if (props.endpointUrl) {
      try {
        return buildApolloStudioUrl(props.endpointUrl)
      } catch (fallbackError) {
        console.error('Fallback URL generation failed:', fallbackError)
        return `https://studio.apollographql.com/sandbox/explorer?endpoint=${encodeURIComponent(props.endpointUrl)}`
      }
    }
    return ''
  }
})

const iframeTitle = computed(() => 'Apollo GraphQL Studio')

const iframeAriaLabel = computed(() => {
  return props.ariaLabel ? `${props.ariaLabel} Interface` : 'GraphQL API Explorer Interface'
})

// Methods
function handleIframeLoad() {
  isLoading.value = false
  networkError.value = false
  retryCount.value = 0
  
  emit('studio-loaded', {
    url: finalStudioUrl.value,
    timestamp: new Date()
  })
}

function handleIframeError() {
  networkError.value = true
  isLoading.value = false
  retryCount.value++
  
  const error = new Error(`Iframe loading failed (attempt ${retryCount.value})`)
  emit('studio-error', error)
}

function handleRetry() {
  if (!canRetry.value) return
  
  retryCount.value++
  isLoading.value = true
  // Keep networkError.value = true to show retry counter
  hasError.value = false
  
  // Force iframe reload by updating the src
  const iframe = document.querySelector('[data-testid="apollo-studio-iframe"]') as HTMLIFrameElement
  if (iframe) {
    iframe.src = finalStudioUrl.value
  }
}

function validateConfiguration() {
  // Reset errors first
  hasError.value = false
  errorMessage.value = ''
  
  // Check for security warnings first
  if (hasSecurityWarning.value) {
    hasError.value = true
    errorMessage.value = 'Dangerous URL pattern detected'
    return false
  }
  
  // Validate endpoint if provided
  if (props.endpoint) {
    const validation = validateConfigurationSafely(props.endpoint)
    if (!validation.isValid) {
      hasError.value = true
      errorMessage.value = validation.errors.join(', ')
      return false
    }
  }
  
  // Validate simple endpoint URL
  if (props.endpointUrl && !props.endpoint) {
    const mockEndpoint = {
      id: '1',
      name: 'Simple API',
      url: props.endpointUrl,
      status: 'ACTIVE' as const,
      introspectionEnabled: true,
      isHealthy: true,
      createdAt: new Date(),
      updatedAt: new Date()
    } as GraphQLEndpoint
    
    const validation = validateConfigurationSafely(mockEndpoint)
    if (!validation.isValid) {
      hasError.value = true
      errorMessage.value = validation.errors.join(', ')
      return false
    }
  }
  
  return true
}

// Query History Methods
function handleReplayQuery(entry: QueryHistoryEntry) {
  emit('query-replayed', entry)
}

function handleSaveTemplate(entry: QueryHistoryEntry) {
  emit('template-requested', entry)
}

// Method to manually add a query to history (for iframe integration)
async function addQueryToHistory(query: string, variables?: Record<string, any>, result?: any, success: boolean = true, executionTime: number = 0) {
  if (!props.endpoint || !props.enableQueryHistory) return

  try {
    await queryHistoryService.addQuery({
      endpointId: props.endpoint.id,
      query,
      ...(variables && { variables }),
      executionTime,
      success,
      result,
      statusCode: success ? 200 : 500
    })
  } catch (error) {
    console.error('Failed to add query to history:', error)
  }
}

// Watchers
watch([() => props.endpoint, () => props.authType, () => props.endpointUrl], () => {
  validateConfiguration()
  
  if (props.endpoint && props.authType) {
    const result = createConfigWithAuthSafely(props.endpoint, props.authType)
    if (result.success && result.config) {
      emit('config-changed', result.config)
    }
  }
}, { deep: true, immediate: true })

// Lifecycle
onMounted(() => {
  validateConfiguration()
})

onUnmounted(() => {
  // Cleanup any pending timers or event listeners
})

// Expose methods for external access (e.g., from parent components)
defineExpose({
  addQueryToHistory
})
</script>

<style scoped>
.apollo-studio-integration {
  @apply w-full h-full relative bg-white;
}

.apollo-studio-integration.responsive-layout {
  @apply max-w-full;
}

.apollo-studio-integration.dark-theme {
  @apply bg-gray-900 text-white;
}

.studio-header {
  @apply p-4 border-b border-gray-200;
}

.dark-theme .studio-header {
  @apply border-gray-700;
}

.studio-loading {
  @apply absolute inset-0 flex flex-col items-center justify-center bg-white;
}

.dark-theme .studio-loading {
  @apply bg-gray-900;
}

.studio-iframe {
  @apply w-full border-0;
  height: 100%;
}

.studio-content {
  height: calc(100% - 73px); /* Account for header */
}

.studio-main {
  min-width: 0; /* Allows iframe to shrink */
}

.studio-history {
  min-width: 384px; /* w-96 = 384px */
  max-width: 384px;
}

.error-boundary {
  @apply absolute inset-0 flex items-center justify-center bg-white p-8;
}

.dark-theme .error-boundary {
  @apply bg-gray-900;
}

.error-content {
  @apply text-center max-w-md;
}

.network-error {
  @apply absolute inset-0 flex flex-col items-center justify-center bg-orange-50 p-8;
}

.dark-theme .network-error {
  @apply bg-orange-900;
}

/* Responsive styles */
@media (max-width: 1200px) {
  .studio-history {
    min-width: 320px;
    max-width: 320px;
  }
}

@media (max-width: 768px) {
  .responsive-layout .studio-header {
    @apply p-2;
  }
  
  .responsive-layout .studio-content {
    @apply flex-col;
  }
  
  .responsive-layout .studio-history {
    @apply w-full;
    min-width: unset;
    max-width: unset;
    height: 300px;
  }
}
</style>