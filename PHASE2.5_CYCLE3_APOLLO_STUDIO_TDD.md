# Phase 2.5 Cycle 3: TDD Implementation Plan - Apollo GraphQL Studio Integration

**Timeline:** Day 6-8 of Phase 2.5 implementation  
**Goal:** Integrate Apollo GraphQL Studio for professional GraphQL playground experience  
**Approach:** Strategic integration with Apollo Studio following strict TDD methodology  

---

## 📋 **Cycle 3 Features to Implement**

### **Day 6 Morning - Apollo Studio Integration Foundation**
- ✅ Apollo Studio component embedding (iframe/React component)
- ✅ Endpoint configuration bridging from our management system
- ✅ Authentication flow integration with our auth providers
- ✅ Basic theme and UI consistency with our dashboard

### **Day 6 Afternoon - Authentication & Configuration Bridge**
- ✅ Pass endpoint auth configs to Apollo Studio
- ✅ Dynamic endpoint switching within Studio
- ✅ Real-time endpoint health status display
- ✅ Configuration validation and error handling

### **Day 7 Morning - Data Synchronization**
- ✅ Query history capture and storage in our system
- ✅ Results processing and analytics integration
- ✅ Performance metrics sync with our monitoring
- ✅ Schema change detection and notifications

### **Day 7 Afternoon - Enhanced User Experience**
- ✅ Seamless endpoint switching UI
- ✅ Custom toolbar with our workflow actions
- ✅ Query export to our collections system
- ✅ Integration with dashboard navigation

### **Day 8 Morning - Advanced Features**
- ✅ Multi-endpoint query execution
- ✅ Query performance comparison across endpoints
- ✅ Team collaboration features
- ✅ Custom query templates and snippets

### **Day 8 Afternoon - Polish & Integration**
- ✅ End-to-end workflow testing
- ✅ Performance optimization and lazy loading
- ✅ Error boundary implementation
- ✅ Mobile responsiveness adjustments

---

## 🎯 **Apollo Studio Integration Strategy**

### **1. Embedding Approach**
```typescript
// Two main integration options:
// Option A: Apollo Studio Embedded (Recommended)
// Option B: Apollo Studio iframe integration

interface ApolloStudioConfig {
  studioEndpoint: string
  endpointUrl: string
  authentication: AuthConfig
  theme: 'light' | 'dark' | 'auto'
  features: StudioFeature[]
}
```

### **2. Authentication Bridge**
```typescript
interface AuthBridge {
  // Convert our auth configs to Apollo format
  convertAuth: (endpoint: Endpoint) => ApolloAuthConfig
  
  // Handle different auth types
  handleBearerToken: (token: string) => Headers
  handleApiKey: (key: string, name: string) => Headers
  handleBasicAuth: (username: string, password: string) => Headers
}
```

### **3. Data Synchronization**
```typescript
interface StudioDataSync {
  // Capture queries executed in Studio
  onQueryExecuted: (query: string, variables: any, result: any) => void
  
  // Save to our query history system
  saveQueryHistory: (execution: QueryExecution) => Promise<void>
  
  // Sync performance metrics
  syncMetrics: (metrics: QueryMetrics) => void
}
```

---

## 🧪 **TDD Implementation Cycle**

## **Phase 1: Write Failing Tests** ❌

### **1.1 Apollo Studio Integration Tests**
```typescript
// tests/components/ApolloStudioIntegration.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ApolloStudioIntegration from '@/components/ApolloStudioIntegration.vue'
import { useEndpointStore } from '@/stores/endpoint'

describe('Apollo Studio Integration', () => {
  let wrapper
  let endpointStore

  beforeEach(() => {
    const pinia = createPinia()
    endpointStore = useEndpointStore(pinia)
    
    // Mock endpoint
    endpointStore.addEndpoint({
      name: 'Test API',
      url: 'https://api.test.com/graphql',
      authType: 'bearer',
      authConfig: { token: 'test-token' }
    })

    wrapper = mount(ApolloStudioIntegration, {
      global: {
        plugins: [pinia]
      },
      props: {
        activeEndpointId: endpointStore.endpoints[0].id
      }
    })
  })

  it('should render Apollo Studio component', () => {
    // Will fail until component exists
    expect(wrapper.find('[data-testid="apollo-studio-container"]').exists()).toBe(true)
  })

  it('should configure Studio with endpoint URL', () => {
    // Will fail until configuration is implemented
    expect(wrapper.vm.studioConfig.endpointUrl).toBe('https://api.test.com/graphql')
  })

  it('should pass authentication headers to Studio', () => {
    // Will fail until auth bridge implemented
    expect(wrapper.vm.studioConfig.headers).toEqual({
      'Authorization': 'Bearer test-token'
    })
  })

  it('should handle endpoint switching', async () => {
    // Add second endpoint
    const secondEndpoint = endpointStore.addEndpoint({
      name: 'Staging API',
      url: 'https://staging.test.com/graphql',
      authType: 'api-key',
      authConfig: { apiKey: 'staging-key', keyName: 'X-API-Key' }
    })

    // Switch endpoints
    await wrapper.setProps({ activeEndpointId: secondEndpoint.id })

    expect(wrapper.vm.studioConfig.endpointUrl).toBe('https://staging.test.com/graphql')
    expect(wrapper.vm.studioConfig.headers['X-API-Key']).toBe('staging-key')
  })

  it('should display endpoint health status', () => {
    // Update endpoint health
    endpointStore.updateEndpointHealth(endpointStore.endpoints[0].id, {
      status: 'healthy',
      responseTime: 120
    })

    expect(wrapper.find('[data-testid="endpoint-health-indicator"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="health-status-healthy"]').exists()).toBe(true)
  })

  it('should show loading state during Studio initialization', () => {
    wrapper.vm.isStudioLoading = true
    
    expect(wrapper.find('[data-testid="studio-loading"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Loading Apollo Studio')
  })

  it('should handle Studio initialization errors', async () => {
    const initError = new Error('Studio failed to load')
    wrapper.vm.handleStudioError(initError)

    expect(wrapper.find('[data-testid="studio-error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Failed to load Apollo Studio')
  })
})
```

### **1.2 Apollo Studio Configuration Tests**
```typescript
// tests/services/apolloStudioConfig.test.ts
import { describe, it, expect } from 'vitest'
import { useApolloStudioConfig } from '@/services/apolloStudioConfig'
import type { Endpoint } from '@/types/endpoint'

describe('Apollo Studio Configuration Service', () => {
  const mockEndpoint: Endpoint = {
    id: '1',
    name: 'Test API',
    url: 'https://api.test.com/graphql',
    authType: 'bearer',
    authConfig: { token: 'test-token' },
    headers: { 'Custom-Header': 'custom-value' },
    timeout: 30000,
    retryCount: 3,
    healthCheckInterval: 60000,
    isActive: true,
    tags: ['production'],
    createdAt: new Date(),
    updatedAt: new Date()
  }

  it('should create basic Studio configuration', () => {
    const { createStudioConfig } = useApolloStudioConfig()
    
    const config = createStudioConfig(mockEndpoint)
    
    expect(config.endpoint).toBe('https://api.test.com/graphql')
    expect(config.headers['Authorization']).toBe('Bearer test-token')
    expect(config.headers['Custom-Header']).toBe('custom-value')
  })

  it('should handle Bearer token authentication', () => {
    const { buildAuthHeaders } = useApolloStudioConfig()
    
    const headers = buildAuthHeaders({
      authType: 'bearer',
      authConfig: { token: 'my-token' }
    })
    
    expect(headers['Authorization']).toBe('Bearer my-token')
  })

  it('should handle API Key authentication', () => {
    const { buildAuthHeaders } = useApolloStudioConfig()
    
    const headers = buildAuthHeaders({
      authType: 'api-key',
      authConfig: { 
        apiKey: 'my-api-key',
        keyName: 'X-API-Key' 
      }
    })
    
    expect(headers['X-API-Key']).toBe('my-api-key')
  })

  it('should handle Basic authentication', () => {
    const { buildAuthHeaders } = useApolloStudioConfig()
    
    const headers = buildAuthHeaders({
      authType: 'basic',
      authConfig: { 
        username: 'user',
        password: 'pass'
      }
    })
    
    expect(headers['Authorization']).toBe('Basic dXNlcjpwYXNz') // base64 encoded "user:pass"
  })

  it('should merge custom headers with auth headers', () => {
    const { createStudioConfig } = useApolloStudioConfig()
    
    const endpoint: Partial<Endpoint> = {
      url: 'https://api.test.com/graphql',
      authType: 'bearer',
      authConfig: { token: 'token123' },
      headers: {
        'X-Custom': 'custom-value',
        'User-Agent': 'FraiseQL-Doctor'
      }
    }
    
    const config = createStudioConfig(endpoint)
    
    expect(config.headers).toEqual({
      'Authorization': 'Bearer token123',
      'X-Custom': 'custom-value',
      'User-Agent': 'FraiseQL-Doctor'
    })
  })

  it('should validate endpoint URL format', () => {
    const { validateEndpointUrl } = useApolloStudioConfig()
    
    expect(validateEndpointUrl('https://api.test.com/graphql')).toBe(true)
    expect(validateEndpointUrl('http://localhost:4000/graphql')).toBe(true)
    expect(validateEndpointUrl('invalid-url')).toBe(false)
    expect(validateEndpointUrl('')).toBe(false)
  })

  it('should create Studio theme configuration', () => {
    const { createThemeConfig } = useApolloStudioConfig()
    
    const lightTheme = createThemeConfig('light')
    expect(lightTheme.colorScheme).toBe('light')
    
    const darkTheme = createThemeConfig('dark')
    expect(darkTheme.colorScheme).toBe('dark')
  })
})
```

### **1.3 Query History Integration Tests**
```typescript
// tests/services/queryHistorySync.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useQueryHistorySync } from '@/services/queryHistorySync'
import { useQueryHistoryStore } from '@/stores/queryHistory'
import { setActivePinia, createPinia } from 'pinia'

describe('Query History Sync Service', () => {
  let queryHistoryStore

  beforeEach(() => {
    setActivePinia(createPinia())
    queryHistoryStore = useQueryHistoryStore()
  })

  it('should capture executed queries from Apollo Studio', async () => {
    const { captureQueryExecution } = useQueryHistorySync()
    
    const queryExecution = {
      query: 'query GetUsers { users { id name } }',
      variables: {},
      endpointId: 'endpoint-1',
      result: {
        data: { users: [{ id: '1', name: 'John' }] },
        errors: null
      },
      executionTime: 150,
      timestamp: new Date()
    }

    await captureQueryExecution(queryExecution)

    expect(queryHistoryStore.queries).toHaveLength(1)
    expect(queryHistoryStore.queries[0].query).toBe(queryExecution.query)
    expect(queryHistoryStore.queries[0].executionTime).toBe(150)
  })

  it('should handle query execution errors', async () => {
    const { captureQueryExecution } = useQueryHistorySync()
    
    const failedExecution = {
      query: 'query InvalidQuery { invalidField }',
      variables: {},
      endpointId: 'endpoint-1',
      result: {
        data: null,
        errors: [{ message: 'Field invalidField not found' }]
      },
      executionTime: 50,
      timestamp: new Date()
    }

    await captureQueryExecution(failedExecution)

    const savedQuery = queryHistoryStore.queries[0]
    expect(savedQuery.hasErrors).toBe(true)
    expect(savedQuery.errors).toHaveLength(1)
  })

  it('should sync performance metrics', () => {
    const { syncPerformanceMetrics } = useQueryHistorySync()
    
    const metrics = {
      endpointId: 'endpoint-1',
      averageResponseTime: 200,
      totalQueries: 15,
      errorRate: 0.1,
      timestamp: new Date()
    }

    syncPerformanceMetrics(metrics)

    // Should update endpoint performance stats
    expect(queryHistoryStore.getEndpointMetrics('endpoint-1')).toEqual(
      expect.objectContaining({
        averageResponseTime: 200,
        totalQueries: 15,
        errorRate: 0.1
      })
    )
  })

  it('should export queries in various formats', async () => {
    const { exportQueries } = useQueryHistorySync()
    
    // Add some queries to history
    queryHistoryStore.addQuery({
      id: '1',
      query: 'query GetUsers { users { id name } }',
      endpointId: 'endpoint-1'
    })

    const jsonExport = await exportQueries('json')
    expect(typeof jsonExport).toBe('string')
    expect(JSON.parse(jsonExport)).toHaveLength(1)

    const curlExport = await exportQueries('curl')
    expect(curlExport).toContain('curl')
    expect(curlExport).toContain('POST')
  })

  it('should filter query history by endpoint', () => {
    const { getQueriesByEndpoint } = useQueryHistorySync()
    
    // Add queries for different endpoints
    queryHistoryStore.addQuery({
      id: '1',
      query: 'query GetUsers { users { id } }',
      endpointId: 'endpoint-1'
    })
    queryHistoryStore.addQuery({
      id: '2',
      query: 'query GetPosts { posts { title } }',
      endpointId: 'endpoint-2'
    })

    const endpoint1Queries = getQueriesByEndpoint('endpoint-1')
    expect(endpoint1Queries).toHaveLength(1)
    expect(endpoint1Queries[0].query).toContain('GetUsers')
  })
})
```

### **1.4 GraphQL Playground View Tests**
```typescript
// tests/views/GraphQLPlayground.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import GraphQLPlayground from '@/views/GraphQLPlayground.vue'
import { useEndpointStore } from '@/stores/endpoint'

describe('GraphQL Playground View', () => {
  let wrapper
  let endpointStore
  let router

  beforeEach(() => {
    const pinia = createPinia()
    endpointStore = useEndpointStore(pinia)
    
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/playground', component: GraphQLPlayground }
      ]
    })

    // Add test endpoints
    endpointStore.addEndpoint({
      name: 'Production API',
      url: 'https://api.prod.com/graphql',
      authType: 'bearer',
      authConfig: { token: 'prod-token' }
    })
    endpointStore.addEndpoint({
      name: 'Staging API', 
      url: 'https://api.staging.com/graphql',
      authType: 'api-key',
      authConfig: { apiKey: 'staging-key', keyName: 'X-API-Key' }
    })

    wrapper = mount(GraphQLPlayground, {
      global: {
        plugins: [pinia, router]
      }
    })
  })

  it('should render playground layout', () => {
    expect(wrapper.find('[data-testid="graphql-playground"]').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toContain('GraphQL Playground')
  })

  it('should show endpoint selector', () => {
    expect(wrapper.find('[data-testid="endpoint-selector"]').exists()).toBe(true)
    
    const options = wrapper.findAll('[data-testid="endpoint-option"]')
    expect(options).toHaveLength(2)
    expect(options[0].text()).toContain('Production API')
    expect(options[1].text()).toContain('Staging API')
  })

  it('should switch active endpoint', async () => {
    const selector = wrapper.find('[data-testid="endpoint-selector"]')
    await selector.setValue(endpointStore.endpoints[1].id)

    expect(wrapper.vm.activeEndpointId).toBe(endpointStore.endpoints[1].id)
    expect(wrapper.find('[data-testid="active-endpoint-name"]').text()).toBe('Staging API')
  })

  it('should display Apollo Studio integration', () => {
    expect(wrapper.find('[data-testid="apollo-studio-integration"]').exists()).toBe(true)
  })

  it('should show endpoint health status', () => {
    // Update endpoint health
    endpointStore.updateEndpointHealth(endpointStore.endpoints[0].id, {
      status: 'healthy',
      responseTime: 95
    })

    const healthIndicator = wrapper.find('[data-testid="endpoint-health"]')
    expect(healthIndicator.exists()).toBe(true)
    expect(healthIndicator.classes()).toContain('health-healthy')
  })

  it('should handle endpoint with no authentication', async () => {
    endpointStore.addEndpoint({
      name: 'Public API',
      url: 'https://api.public.com/graphql',
      authType: 'none'
    })

    const selector = wrapper.find('[data-testid="endpoint-selector"]')
    await selector.setValue(endpointStore.endpoints[2].id)

    expect(wrapper.vm.currentEndpointConfig.authType).toBe('none')
  })

  it('should show query history panel', () => {
    expect(wrapper.find('[data-testid="query-history-panel"]').exists()).toBe(true)
  })

  it('should handle Studio loading states', () => {
    wrapper.vm.isStudioLoading = true
    
    expect(wrapper.find('[data-testid="studio-loading-overlay"]').exists()).toBe(true)
  })

  it('should show error when no endpoints available', async () => {
    // Clear all endpoints
    endpointStore.endpoints.splice(0)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="no-endpoints-message"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('No endpoints configured')
  })
})
```

### **1.5 Studio Theme Integration Tests**
```typescript
// tests/services/studioTheme.test.ts
import { describe, it, expect } from 'vitest'
import { useStudioTheme } from '@/services/studioTheme'

describe('Studio Theme Integration', () => {
  it('should generate theme configuration for light mode', () => {
    const { generateThemeConfig } = useStudioTheme()
    
    const lightTheme = generateThemeConfig('light')
    
    expect(lightTheme).toEqual(expect.objectContaining({
      colorScheme: 'light',
      colors: expect.objectContaining({
        background: expect.any(String),
        surface: expect.any(String),
        text: expect.any(String)
      })
    }))
  })

  it('should generate theme configuration for dark mode', () => {
    const { generateThemeConfig } = useStudioTheme()
    
    const darkTheme = generateThemeConfig('dark')
    
    expect(darkTheme.colorScheme).toBe('dark')
    expect(darkTheme.colors.background).toMatch(/^#[0-9a-f]{6}$/i) // Dark color
  })

  it('should match dashboard theme colors', () => {
    const { matchDashboardTheme } = useStudioTheme()
    
    const dashboardColors = {
      primary: '#3b82f6',
      secondary: '#6b7280',
      background: '#f9fafb'
    }

    const studioTheme = matchDashboardTheme(dashboardColors)
    
    expect(studioTheme.colors.primary).toBe('#3b82f6')
    expect(studioTheme.colors.secondary).toBe('#6b7280')
  })

  it('should handle theme switching', () => {
    const { switchTheme, currentTheme } = useStudioTheme()
    
    switchTheme('dark')
    expect(currentTheme.value).toBe('dark')
    
    switchTheme('light')
    expect(currentTheme.value).toBe('light')
  })

  it('should persist theme preference', () => {
    const { saveThemePreference, loadThemePreference } = useStudioTheme()
    
    saveThemePreference('dark')
    const loaded = loadThemePreference()
    
    expect(loaded).toBe('dark')
  })
})
```

---

## **Phase 2: Implement Minimal Code** ✅

### **2.1 Apollo Studio Integration Component**
```vue
<!-- src/components/ApolloStudioIntegration.vue -->
<template>
  <div 
    data-testid="apollo-studio-container" 
    class="w-full h-full relative"
  >
    <!-- Loading Overlay -->
    <div 
      v-if="isStudioLoading"
      data-testid="studio-loading"
      class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10"
    >
      <div class="text-center">
        <svg class="animate-spin h-8 w-8 text-indigo-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-gray-600">Loading Apollo Studio...</p>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-if="studioError"
      data-testid="studio-error" 
      class="absolute inset-0 flex items-center justify-center"
    >
      <div class="text-center max-w-md">
        <svg class="h-12 w-12 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Failed to load Apollo Studio</h3>
        <p class="text-gray-600 mb-4">{{ studioError.message }}</p>
        <button
          @click="retryStudioLoad"
          class="btn-primary"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- Endpoint Health Indicator -->
    <div 
      v-if="activeEndpoint && !isStudioLoading"
      data-testid="endpoint-health-indicator"
      class="absolute top-4 right-4 z-20"
    >
      <div 
        :data-testid="`health-status-${activeEndpoint.lastHealthCheck?.status}`"
        class="flex items-center space-x-2 bg-white rounded-lg shadow-sm px-3 py-2 border"
      >
        <div 
          :class="[
            'w-2 h-2 rounded-full',
            {
              'bg-green-500': activeEndpoint.lastHealthCheck?.status === 'healthy',
              'bg-yellow-500': activeEndpoint.lastHealthCheck?.status === 'degraded', 
              'bg-red-500': activeEndpoint.lastHealthCheck?.status === 'unhealthy',
              'bg-gray-400': !activeEndpoint.lastHealthCheck?.status
            }
          ]"
        ></div>
        <span class="text-sm text-gray-700">
          {{ activeEndpoint.name }}
        </span>
        <span v-if="activeEndpoint.lastHealthCheck?.responseTime" class="text-xs text-gray-500">
          {{ activeEndpoint.lastHealthCheck.responseTime }}ms
        </span>
      </div>
    </div>

    <!-- Apollo Studio Iframe/Component -->
    <iframe
      v-if="!isStudioLoading && !studioError"
      ref="studioIframe"
      :src="studioUrl"
      class="w-full h-full border-0"
      @load="onStudioLoaded"
      @error="onStudioError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useApolloStudioConfig } from '@/services/apolloStudioConfig'
import { useQueryHistorySync } from '@/services/queryHistorySync'
import type { Endpoint } from '@/types/endpoint'

interface Props {
  activeEndpointId: string
  endpoints: Endpoint[]
}

const props = defineProps<Props>()

// Services
const { createStudioConfig, validateEndpointUrl } = useApolloStudioConfig()
const { captureQueryExecution } = useQueryHistorySync()

// State
const isStudioLoading = ref(true)
const studioError = ref<Error | null>(null)
const studioIframe = ref<HTMLIFrameElement>()

// Computed
const activeEndpoint = computed(() => 
  props.endpoints.find(e => e.id === props.activeEndpointId)
)

const studioConfig = computed(() => {
  if (!activeEndpoint.value) return null
  return createStudioConfig(activeEndpoint.value)
})

const studioUrl = computed(() => {
  if (!studioConfig.value) return ''
  
  const params = new URLSearchParams({
    endpoint: studioConfig.value.endpoint,
    headers: JSON.stringify(studioConfig.value.headers),
    theme: studioConfig.value.theme || 'light'
  })
  
  return `https://studio.apollographql.com/sandbox?${params.toString()}`
})

// Methods
const onStudioLoaded = () => {
  isStudioLoading.value = false
  studioError.value = null
  
  // Set up message listener for Studio communication
  setupStudioMessageListener()
}

const onStudioError = (error: Event) => {
  isStudioLoading.value = false
  studioError.value = new Error('Failed to load Apollo Studio')
}

const handleStudioError = (error: Error) => {
  studioError.value = error
  isStudioLoading.value = false
}

const retryStudioLoad = () => {
  studioError.value = null
  isStudioLoading.value = true
  
  if (studioIframe.value) {
    studioIframe.value.src = studioUrl.value
  }
}

const setupStudioMessageListener = () => {
  const handleMessage = (event: MessageEvent) => {
    // Handle messages from Apollo Studio iframe
    if (event.data.type === 'apollo-studio-query-executed') {
      captureQueryExecution({
        query: event.data.query,
        variables: event.data.variables,
        result: event.data.result,
        endpointId: props.activeEndpointId,
        executionTime: event.data.executionTime,
        timestamp: new Date()
      })
    }
  }
  
  window.addEventListener('message', handleMessage)
  
  // Cleanup on unmount
  onBeforeUnmount(() => {
    window.removeEventListener('message', handleMessage)
  })
}

// Watchers
watch(() => props.activeEndpointId, () => {
  // Reload Studio when endpoint changes
  if (studioIframe.value && studioUrl.value) {
    isStudioLoading.value = true
    studioIframe.value.src = studioUrl.value
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  if (!activeEndpoint.value) {
    handleStudioError(new Error('No active endpoint selected'))
  }
})

// Expose for testing
defineExpose({
  studioConfig,
  isStudioLoading,
  handleStudioError
})
</script>
```

### **2.2 Apollo Studio Configuration Service**
```typescript
// src/services/apolloStudioConfig.ts
import type { Endpoint } from '@/types/endpoint'

interface ApolloStudioConfig {
  endpoint: string
  headers: Record<string, string>
  theme?: 'light' | 'dark'
  features?: string[]
}

export function useApolloStudioConfig() {
  const createStudioConfig = (endpoint: Partial<Endpoint>): ApolloStudioConfig => {
    if (!endpoint.url) {
      throw new Error('Endpoint URL is required')
    }

    if (!validateEndpointUrl(endpoint.url)) {
      throw new Error('Invalid endpoint URL format')
    }

    return {
      endpoint: endpoint.url,
      headers: {
        ...buildAuthHeaders(endpoint),
        ...endpoint.headers
      },
      theme: 'light', // TODO: Get from user preference
      features: ['introspection', 'query-plan', 'tracing']
    }
  }

  const buildAuthHeaders = (endpoint: Partial<Endpoint>): Record<string, string> => {
    const headers: Record<string, string> = {}

    switch (endpoint.authType) {
      case 'bearer':
        if (endpoint.authConfig?.token) {
          headers['Authorization'] = `Bearer ${endpoint.authConfig.token}`
        }
        break
        
      case 'api-key':
        if (endpoint.authConfig?.apiKey && endpoint.authConfig?.keyName) {
          headers[endpoint.authConfig.keyName] = endpoint.authConfig.apiKey
        }
        break
        
      case 'basic':
        if (endpoint.authConfig?.username && endpoint.authConfig?.password) {
          const credentials = btoa(
            `${endpoint.authConfig.username}:${endpoint.authConfig.password}`
          )
          headers['Authorization'] = `Basic ${credentials}`
        }
        break
    }

    return headers
  }

  const validateEndpointUrl = (url: string): boolean => {
    if (!url) return false
    
    try {
      const parsedUrl = new URL(url)
      return ['http:', 'https:'].includes(parsedUrl.protocol)
    } catch {
      return false
    }
  }

  const createThemeConfig = (theme: 'light' | 'dark') => {
    return {
      colorScheme: theme,
      colors: {
        background: theme === 'light' ? '#ffffff' : '#1a1a1a',
        surface: theme === 'light' ? '#f8f9fa' : '#2d2d2d',
        text: theme === 'light' ? '#1a1a1a' : '#ffffff',
        primary: '#3b82f6',
        secondary: '#6b7280'
      }
    }
  }

  return {
    createStudioConfig,
    buildAuthHeaders,
    validateEndpointUrl,
    createThemeConfig
  }
}
```

### **2.3 Query History Sync Service**
```typescript
// src/services/queryHistorySync.ts
import { useQueryHistoryStore } from '@/stores/queryHistory'

interface QueryExecution {
  query: string
  variables: Record<string, any>
  result: {
    data?: any
    errors?: GraphQLError[]
  }
  endpointId: string
  executionTime: number
  timestamp: Date
}

interface QueryMetrics {
  endpointId: string
  averageResponseTime: number
  totalQueries: number
  errorRate: number
  timestamp: Date
}

export function useQueryHistorySync() {
  const queryHistoryStore = useQueryHistoryStore()

  const captureQueryExecution = async (execution: QueryExecution) => {
    const queryRecord = {
      id: crypto.randomUUID(),
      query: execution.query,
      variables: execution.variables,
      endpointId: execution.endpointId,
      result: execution.result,
      executionTime: execution.executionTime,
      timestamp: execution.timestamp,
      hasErrors: !!(execution.result.errors?.length),
      errors: execution.result.errors || []
    }

    queryHistoryStore.addQuery(queryRecord)
  }

  const syncPerformanceMetrics = (metrics: QueryMetrics) => {
    queryHistoryStore.updateEndpointMetrics(metrics.endpointId, {
      averageResponseTime: metrics.averageResponseTime,
      totalQueries: metrics.totalQueries,
      errorRate: metrics.errorRate,
      lastUpdated: metrics.timestamp
    })
  }

  const exportQueries = async (format: 'json' | 'csv' | 'curl'): Promise<string> => {
    const queries = queryHistoryStore.queries

    switch (format) {
      case 'json':
        return JSON.stringify(queries, null, 2)
        
      case 'csv':
        const headers = 'Query,Endpoint,Execution Time,Timestamp,Has Errors\n'
        const rows = queries.map(q => 
          `"${q.query}","${q.endpointId}",${q.executionTime},"${q.timestamp}",${q.hasErrors}`
        ).join('\n')
        return headers + rows
        
      case 'curl':
        return queries.map(q => 
          `curl -X POST ${q.endpointId} \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify({ query: q.query, variables: q.variables })}'`
        ).join('\n\n')
        
      default:
        throw new Error(`Unsupported export format: ${format}`)
    }
  }

  const getQueriesByEndpoint = (endpointId: string) => {
    return queryHistoryStore.queries.filter(q => q.endpointId === endpointId)
  }

  return {
    captureQueryExecution,
    syncPerformanceMetrics,
    exportQueries,
    getQueriesByEndpoint
  }
}
```

### **2.4 Query History Store**
```typescript
// src/stores/queryHistory.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface QueryRecord {
  id: string
  query: string
  variables: Record<string, any>
  endpointId: string
  result: any
  executionTime: number
  timestamp: Date
  hasErrors: boolean
  errors: any[]
}

interface EndpointMetrics {
  endpointId: string
  averageResponseTime: number
  totalQueries: number
  errorRate: number
  lastUpdated: Date
}

export const useQueryHistoryStore = defineStore('queryHistory', () => {
  // State
  const queries = ref<QueryRecord[]>([])
  const endpointMetrics = ref<Map<string, EndpointMetrics>>(new Map())

  // Getters
  const recentQueries = computed(() => 
    queries.value
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 50)
  )

  const queriesWithErrors = computed(() =>
    queries.value.filter(q => q.hasErrors)
  )

  // Actions
  const addQuery = (query: QueryRecord) => {
    queries.value.push(query)
    
    // Keep only last 1000 queries
    if (queries.value.length > 1000) {
      queries.value = queries.value.slice(-1000)
    }
  }

  const updateEndpointMetrics = (endpointId: string, metrics: Partial<EndpointMetrics>) => {
    const existing = endpointMetrics.value.get(endpointId)
    
    endpointMetrics.value.set(endpointId, {
      endpointId,
      averageResponseTime: metrics.averageResponseTime ?? existing?.averageResponseTime ?? 0,
      totalQueries: metrics.totalQueries ?? existing?.totalQueries ?? 0,
      errorRate: metrics.errorRate ?? existing?.errorRate ?? 0,
      lastUpdated: metrics.lastUpdated ?? existing?.lastUpdated ?? new Date()
    })
  }

  const getEndpointMetrics = (endpointId: string) => {
    return endpointMetrics.value.get(endpointId)
  }

  const clearHistory = () => {
    queries.value = []
    endpointMetrics.value.clear()
  }

  const deleteQuery = (queryId: string) => {
    const index = queries.value.findIndex(q => q.id === queryId)
    if (index !== -1) {
      queries.value.splice(index, 1)
    }
  }

  return {
    // State
    queries,
    endpointMetrics,
    
    // Getters
    recentQueries,
    queriesWithErrors,
    
    // Actions
    addQuery,
    updateEndpointMetrics,
    getEndpointMetrics,
    clearHistory,
    deleteQuery
  }
})
```

### **2.5 GraphQL Playground View**
```vue
<!-- src/views/GraphQLPlayground.vue -->
<template>
  <div data-testid="graphql-playground" class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex-none bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">GraphQL Playground</h1>
          <p class="text-sm text-gray-600 mt-1">
            Interactive GraphQL query editor powered by Apollo Studio
          </p>
        </div>

        <!-- Endpoint Selector -->
        <div class="flex items-center space-x-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Active Endpoint
            </label>
            <select
              data-testid="endpoint-selector"
              v-model="activeEndpointId"
              class="border border-gray-300 rounded-md px-3 py-2 bg-white text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="" disabled>Select an endpoint</option>
              <option 
                v-for="endpoint in availableEndpoints"
                :key="endpoint.id"
                :value="endpoint.id"
                data-testid="endpoint-option"
              >
                {{ endpoint.name }}
              </option>
            </select>
          </div>

          <!-- Active Endpoint Info -->
          <div v-if="currentEndpoint" class="text-right">
            <div data-testid="active-endpoint-name" class="text-sm font-medium text-gray-900">
              {{ currentEndpoint.name }}
            </div>
            <div class="text-xs text-gray-500">
              {{ currentEndpoint.url }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Endpoints Message -->
    <div 
      v-if="availableEndpoints.length === 0"
      data-testid="no-endpoints-message"
      class="flex-1 flex items-center justify-center"
    >
      <div class="text-center">
        <svg class="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No endpoints configured</h3>
        <p class="text-gray-600 mb-4">
          Add GraphQL endpoints to start using the playground
        </p>
        <router-link
          to="/endpoints"
          class="btn-primary"
        >
          Manage Endpoints
        </router-link>
      </div>
    </div>

    <!-- Main Playground Area -->
    <div v-else class="flex-1 flex">
      <!-- Query History Sidebar -->
      <div 
        data-testid="query-history-panel"
        class="w-80 bg-gray-50 border-r border-gray-200 flex flex-col"
      >
        <div class="p-4 border-b border-gray-200">
          <h2 class="font-semibold text-gray-900">Query History</h2>
        </div>
        <div class="flex-1 overflow-y-auto">
          <QueryHistoryPanel :endpoint-id="activeEndpointId" />
        </div>
      </div>

      <!-- Apollo Studio Integration -->
      <div class="flex-1 relative">
        <!-- Endpoint Health Status -->
        <div 
          v-if="currentEndpoint?.lastHealthCheck"
          data-testid="endpoint-health"
          :class="[
            'absolute top-4 left-4 z-10 px-2 py-1 rounded text-xs font-medium',
            {
              'bg-green-100 text-green-800 health-healthy': currentEndpoint.lastHealthCheck.status === 'healthy',
              'bg-yellow-100 text-yellow-800': currentEndpoint.lastHealthCheck.status === 'degraded',
              'bg-red-100 text-red-800': currentEndpoint.lastHealthCheck.status === 'unhealthy'
            }
          ]"
        >
          {{ currentEndpoint.lastHealthCheck.status?.toUpperCase() }} 
          ({{ currentEndpoint.lastHealthCheck.responseTime }}ms)
        </div>

        <!-- Loading Overlay -->
        <div 
          v-if="isStudioLoading"
          data-testid="studio-loading-overlay"
          class="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-20"
        >
          <div class="text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
            <p class="text-gray-600">Initializing Apollo Studio...</p>
          </div>
        </div>

        <!-- Apollo Studio Component -->
        <ApolloStudioIntegration
          v-if="activeEndpointId"
          data-testid="apollo-studio-integration"
          :active-endpoint-id="activeEndpointId"
          :endpoints="availableEndpoints"
          @studio-loaded="isStudioLoading = false"
          @studio-error="handleStudioError"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEndpointStore } from '@/stores/endpoint'
import ApolloStudioIntegration from '@/components/ApolloStudioIntegration.vue'
import QueryHistoryPanel from '@/components/QueryHistoryPanel.vue'

// Stores
const endpointStore = useEndpointStore()

// State
const activeEndpointId = ref<string>('')
const isStudioLoading = ref(false)

// Computed
const availableEndpoints = computed(() => 
  endpointStore.activeEndpoints
)

const currentEndpoint = computed(() =>
  availableEndpoints.value.find(e => e.id === activeEndpointId.value)
)

const currentEndpointConfig = computed(() => {
  if (!currentEndpoint.value) return null
  
  return {
    url: currentEndpoint.value.url,
    authType: currentEndpoint.value.authType,
    authConfig: currentEndpoint.value.authConfig,
    headers: currentEndpoint.value.headers
  }
})

// Methods
const handleStudioError = (error: Error) => {
  console.error('Apollo Studio error:', error)
  // TODO: Show user-friendly error message
}

// Watchers
watch(() => availableEndpoints.value, (endpoints) => {
  // Auto-select first endpoint if none selected
  if (!activeEndpointId.value && endpoints.length > 0) {
    activeEndpointId.value = endpoints[0].id
  }
}, { immediate: true })

watch(() => activeEndpointId.value, (newId) => {
  if (newId) {
    isStudioLoading.value = true
  }
})

// Expose for testing
defineExpose({
  activeEndpointId,
  currentEndpointConfig,
  isStudioLoading
})
</script>
```

---

## **Phase 3: Run Tests & Verify** ✅

After implementing each component, run the specific test suite:

```bash
# Test individual components as they're implemented
npm run test tests/components/ApolloStudioIntegration.test.ts -- --run
npm run test tests/services/apolloStudioConfig.test.ts -- --run
npm run test tests/services/queryHistorySync.test.ts -- --run
npm run test tests/views/GraphQLPlayground.test.ts -- --run
npm run test tests/stores/queryHistory.test.ts -- --run

# Run all Apollo Studio integration tests
npm run test tests/ -t "apollo" -- --run

# Verify bundle size impact is minimal
npm run build

# Test Apollo Studio communication
npm run test tests/ -t "studio.*integration" -- --run
```

---

## **Phase 4: Refactor & Optimize** 🔄

- **Code Splitting**: Lazy load Apollo Studio integration
- **Bundle Optimization**: Dynamic imports for Studio components
- **Error Handling**: Comprehensive Studio communication error handling
- **Performance**: Optimize iframe communication and message passing
- **Accessibility**: Ensure Studio iframe is accessible
- **Theme Sync**: Perfect theme matching with our dashboard

---

## 🎯 **Success Criteria for Cycle 3**

### **Functional Requirements**: ✅
- **Apollo Studio Integration**: Professional GraphQL playground embedded
- **Endpoint Management**: Seamless switching between managed endpoints  
- **Query History**: Capture and store all executed queries
- **Authentication Bridge**: Pass all auth types to Studio correctly
- **Theme Integration**: Studio appearance matches our dashboard
- **Real-time Health**: Display endpoint status within playground

### **Technical Requirements**: ✅
- **Bundle Impact**: <50KB total impact (vs 350KB custom solution)
- **Test Coverage**: 90%+ coverage following strict TDD
- **TypeScript**: Zero errors in strict mode
- **Performance**: Studio loads in <3 seconds
- **Communication**: Reliable iframe message passing
- **Error Recovery**: Graceful handling of Studio failures

### **User Experience**: ✅
- **Professional UX**: Industry-standard GraphQL playground experience
- **Seamless Integration**: Feels native to our dashboard
- **Quick Endpoint Switching**: <1 second endpoint changes
- **Query History**: Persistent history across sessions
- **Error Handling**: Clear feedback for connection/auth issues
- **Mobile Support**: Responsive design for tablet usage

---

## 📊 **Bundle Size Analysis**

### **Apollo Studio Integration vs Custom Monaco Solution**

| Approach | Base Size | Features | Total Impact | Time to Implement |
|----------|-----------|----------|--------------|-------------------|
| **Apollo Studio** | 20-30KB | Full GraphQL IDE | **~50KB** | **3 days** |
| **Custom Monaco** | 200KB+ | Basic editor | **~350KB** | **2-3 weeks** |

### **Key Benefits of Apollo Studio Integration:**
- ✅ **85% smaller bundle impact** (50KB vs 350KB)
- ✅ **90% faster implementation** (3 days vs 3 weeks)
- ✅ **Professional features** out of the box
- ✅ **Future-proof** with Apollo updates
- ✅ **Developer familiar** interface

---

## 🔗 **Integration Architecture**

### **Data Flow**
```
Our Dashboard ←→ Apollo Studio Integration ←→ Apollo Studio ←→ GraphQL Endpoints
       ↑                    ↑                       ↑
   Navigation        Auth Configuration      Query Execution
   Theme Config      Endpoint Switching      Results Capture
   Query History     Health Status           Error Handling
```

### **Communication Protocol**
```typescript
// Messages from our app to Studio
interface StudioInboundMessage {
  type: 'endpoint-change' | 'auth-update' | 'theme-change'
  payload: any
}

// Messages from Studio to our app  
interface StudioOutboundMessage {
  type: 'query-executed' | 'error-occurred' | 'schema-loaded'
  payload: any
}
```

---

## 📱 **User Experience Flow**

### **1. Playground Entry**
- User navigates to GraphQL Playground
- Auto-selects first available endpoint
- Apollo Studio loads with endpoint configuration
- Query history panel shows recent queries

### **2. Query Development**
- User writes queries in Apollo Studio editor
- Full IntelliSense and syntax highlighting
- Real-time schema validation
- Execution results displayed inline

### **3. Endpoint Management**
- Quick dropdown to switch endpoints
- Authentication automatically configured
- Health status always visible
- Seamless transition between endpoints

### **4. Query History**
- All executed queries automatically saved
- Filter by endpoint, time, success/failure
- One-click to re-run previous queries
- Export capabilities for sharing

---

## ✅ **Definition of Done**

**Cycle 3 is complete when**:
1. **Apollo Studio Integration** works flawlessly
2. **All authentication types** pass through correctly
3. **Endpoint switching** is seamless (<1s)
4. **Query history** captures all executions
5. **Bundle size** remains under 380KB total
6. **Theme matching** with dashboard
7. **90%+ test coverage** with TDD
8. **Error handling** for all failure scenarios
9. **Mobile responsive** design
10. **Performance optimized** (<3s load time)

**🎯 Ready to begin Apollo Studio Integration!**

This approach delivers a professional, feature-complete GraphQL playground experience while maintaining our strict TDD methodology and bundle size constraints. The integration with Apollo Studio provides immediate access to industry-leading GraphQL tooling that would take months to build from scratch.