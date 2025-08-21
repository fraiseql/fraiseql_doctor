# Phase 2.5 Cycle 2: TDD Implementation Plan - Endpoint Management Features

**Timeline:** Day 3-5 of Phase 2.5 implementation  
**Goal:** Complete endpoint management system with real-time monitoring following strict TDD methodology  
**Approach:** RED → GREEN → REFACTOR cycle for each feature

---

## 📋 **Cycle 2 Features to Implement**

### **Day 3 Morning - Endpoint Data Layer** 
- ✅ Endpoint types and interfaces
- ✅ Pinia store for endpoint management
- ✅ Mock endpoint service for testing
- ✅ WebSocket integration for real-time updates

### **Day 3 Afternoon - Endpoint CRUD Operations**
- ✅ Endpoint form component (add/edit)
- ✅ Form validation and error handling
- ✅ Authentication configuration UI
- ✅ Custom headers management

### **Day 4 Morning - Endpoint List & Management**
- ✅ Endpoint table component with status indicators
- ✅ Search and filtering functionality
- ✅ Bulk operations (enable/disable)
- ✅ Import/export capabilities

### **Day 4 Afternoon - Health Monitoring**
- ✅ Real-time health status updates
- ✅ Health check execution
- ✅ Performance metrics display
- ✅ Error handling and reporting

### **Day 5 Morning - Testing & Analytics**
- ✅ Endpoint connectivity testing
- ✅ GraphQL introspection
- ✅ Response time analytics
- ✅ Historical data visualization

### **Day 5 Afternoon - Integration & Polish**
- ✅ Navigation updates
- ✅ Route configuration
- ✅ End-to-end testing
- ✅ Performance optimization

---

## 🎯 **Core Endpoint Management Features**

### **1. Endpoint Registration & Configuration**
```typescript
interface Endpoint {
  id: string
  name: string
  url: string
  description?: string
  tags: string[]
  authType: 'none' | 'bearer' | 'api-key' | 'basic'
  authConfig?: {
    token?: string
    apiKey?: string
    username?: string
    password?: string
  }
  headers?: Record<string, string>
  timeout: number
  retryCount: number
  healthCheckInterval: number
  isActive: boolean
  createdAt: Date
  updatedAt: Date
}
```

**Features:**
- ✅ **Add New Endpoints**: Form to register GraphQL endpoints
- ✅ **Edit Endpoint Settings**: Update URL, auth, headers, timeouts
- ✅ **Authentication Methods**: Support Bearer, API Key, Basic Auth
- ✅ **Custom Headers**: Add custom HTTP headers per endpoint
- ✅ **Tagging System**: Organize endpoints with tags (prod, staging, dev)
- ✅ **Active/Inactive Toggle**: Enable/disable monitoring per endpoint

### **2. Endpoint Health Monitoring**
```typescript
interface HealthCheck {
  endpointId: string
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
  responseTime: number
  timestamp: Date
  error?: string
  schemaVersion?: string
  introspectionSuccess: boolean
}
```

**Features:**
- ✅ **Real-time Health Status**: Live monitoring of endpoint availability
- ✅ **Response Time Tracking**: Monitor GraphQL query performance
- ✅ **Schema Introspection**: Detect schema changes automatically  
- ✅ **Uptime Percentage**: Calculate and display uptime stats
- ✅ **Health History**: Track health status over time
- ✅ **Alerting Thresholds**: Configure when to mark as unhealthy

### **3. Endpoint Discovery & Testing**
```typescript
interface EndpointTest {
  endpointId: string
  queryName: string
  query: string
  variables?: Record<string, any>
  expectedStatus: number
  expectedFields?: string[]
  lastRun: Date
  lastResult: 'pass' | 'fail' | 'timeout' | 'error'
  executionTime: number
}
```

**Features:**
- ✅ **Schema Introspection**: Auto-discover available queries/mutations
- ✅ **Quick Test Queries**: Send test queries to validate endpoints
- ✅ **Query Validation**: Validate GraphQL syntax before sending
- ✅ **Response Inspector**: Pretty-printed JSON response viewer
- ✅ **Error Debugging**: Detailed error messages and suggestions
- ✅ **Query History**: Save and recall previous test queries

### **4. Endpoint List Management**
**UI Components:**
- ✅ **Endpoints Table**: Sortable, filterable list of all endpoints
- ✅ **Status Indicators**: Visual health status (green/yellow/red)
- ✅ **Search & Filter**: Filter by name, status, tags, URL
- ✅ **Bulk Operations**: Enable/disable multiple endpoints
- ✅ **Import/Export**: JSON import/export for endpoint configurations
- ✅ **Quick Actions**: Test, edit, delete from table rows

### **5. Endpoint Analytics Dashboard**
**Metrics & Visualizations:**
- ✅ **Response Time Charts**: Historical performance graphs
- ✅ **Uptime Statistics**: Percentage uptime over time periods
- ✅ **Error Rate Tracking**: Track and visualize error patterns  
- ✅ **Schema Change Detection**: Alert on schema modifications
- ✅ **Request Volume**: Track query frequency per endpoint
- ✅ **Geographic Distribution**: If endpoints are distributed

---

## 🧪 **TDD Implementation Cycle**

## **Phase 1: Write Failing Tests** ❌

### **1.1 Endpoint Types & Store Tests**
```typescript
// tests/stores/endpoint.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEndpointStore } from '@/stores/endpoint'

describe('Endpoint Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with empty endpoints list', () => {
    const store = useEndpointStore()
    expect(store.endpoints).toEqual([])
    expect(store.isLoading).toBe(false)
  })

  it('should add new endpoint', () => {
    const store = useEndpointStore()
    const newEndpoint = {
      name: 'Test API',
      url: 'https://api.example.com/graphql',
      authType: 'bearer',
      authConfig: { token: 'test-token' },
      isActive: true
    }
    
    store.addEndpoint(newEndpoint)
    expect(store.endpoints).toHaveLength(1)
    expect(store.endpoints[0].name).toBe('Test API')
    expect(store.endpoints[0].id).toBeDefined()
  })

  it('should update endpoint status in real-time', () => {
    const store = useEndpointStore()
    const endpoint = store.addEndpoint({ name: 'Test', url: 'http://test.com' })
    
    store.updateEndpointHealth(endpoint.id, {
      status: 'healthy',
      responseTime: 150,
      timestamp: new Date()
    })
    
    expect(store.endpoints[0].lastHealthCheck?.status).toBe('healthy')
    expect(store.endpoints[0].lastHealthCheck?.responseTime).toBe(150)
  })

  it('should filter endpoints by status', () => {
    const store = useEndpointStore()
    store.addEndpoint({ name: 'Healthy', url: 'http://healthy.com' })
    store.addEndpoint({ name: 'Unhealthy', url: 'http://unhealthy.com' })
    
    store.updateEndpointHealth(store.endpoints[0].id, { status: 'healthy' })
    store.updateEndpointHealth(store.endpoints[1].id, { status: 'unhealthy' })
    
    const healthyEndpoints = store.getEndpointsByStatus('healthy')
    expect(healthyEndpoints).toHaveLength(1)
    expect(healthyEndpoints[0].name).toBe('Healthy')
  })

  it('should search endpoints by name and tags', () => {
    const store = useEndpointStore()
    store.addEndpoint({ 
      name: 'Production API', 
      url: 'http://prod.com',
      tags: ['production', 'v2'] 
    })
    store.addEndpoint({ 
      name: 'Staging API', 
      url: 'http://staging.com',
      tags: ['staging', 'v1'] 
    })
    
    const results = store.searchEndpoints('production')
    expect(results).toHaveLength(1)
    expect(results[0].name).toBe('Production API')
    
    const tagResults = store.searchEndpoints('v2')
    expect(tagResults).toHaveLength(1)
  })
})
```

### **1.2 Endpoint Form Component Tests**
```typescript
// tests/components/EndpointForm.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import EndpointForm from '@/components/EndpointForm.vue'

describe('Endpoint Form', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(EndpointForm, {
      global: {
        plugins: [createPinia()]
      },
      props: {
        isOpen: true
      }
    })
  })

  it('should render form fields', () => {
    expect(wrapper.find('[data-testid="endpoint-name"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="endpoint-url"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="auth-type-select"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="save-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="cancel-button"]').exists()).toBe(true)
  })

  it('should validate required fields', async () => {
    const saveButton = wrapper.find('[data-testid="save-button"]')
    await saveButton.trigger('click')
    
    expect(wrapper.find('[data-testid="name-error"]').text()).toContain('Name is required')
    expect(wrapper.find('[data-testid="url-error"]').text()).toContain('URL is required')
  })

  it('should validate URL format', async () => {
    await wrapper.find('[data-testid="endpoint-url"]').setValue('invalid-url')
    await wrapper.find('[data-testid="save-button"]').trigger('click')
    
    expect(wrapper.find('[data-testid="url-error"]').text()).toContain('Invalid URL format')
  })

  it('should show auth fields based on auth type', async () => {
    // Initially no auth fields visible
    expect(wrapper.find('[data-testid="auth-token"]').exists()).toBe(false)
    
    // Select bearer auth
    await wrapper.find('[data-testid="auth-type-select"]').setValue('bearer')
    
    expect(wrapper.find('[data-testid="auth-token"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="auth-token"]').attributes('placeholder')).toContain('Bearer Token')
  })

  it('should show API key field for api-key auth', async () => {
    await wrapper.find('[data-testid="auth-type-select"]').setValue('api-key')
    
    expect(wrapper.find('[data-testid="auth-key"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="auth-key-name"]').exists()).toBe(true)
  })

  it('should show username/password for basic auth', async () => {
    await wrapper.find('[data-testid="auth-type-select"]').setValue('basic')
    
    expect(wrapper.find('[data-testid="auth-username"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="auth-password"]').exists()).toBe(true)
  })

  it('should manage custom headers', async () => {
    const addHeaderBtn = wrapper.find('[data-testid="add-header-button"]')
    await addHeaderBtn.trigger('click')
    
    expect(wrapper.find('[data-testid="header-key-0"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="header-value-0"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="remove-header-0"]').exists()).toBe(true)
  })

  it('should emit save event with form data', async () => {
    await wrapper.find('[data-testid="endpoint-name"]').setValue('Test API')
    await wrapper.find('[data-testid="endpoint-url"]').setValue('https://api.test.com/graphql')
    await wrapper.find('[data-testid="auth-type-select"]').setValue('bearer')
    await wrapper.find('[data-testid="auth-token"]').setValue('test-token')
    
    await wrapper.find('[data-testid="save-button"]').trigger('click')
    
    expect(wrapper.emitted('save')).toBeTruthy()
    const emittedData = wrapper.emitted('save')[0][0]
    expect(emittedData.name).toBe('Test API')
    expect(emittedData.url).toBe('https://api.test.com/graphql')
    expect(emittedData.authType).toBe('bearer')
    expect(emittedData.authConfig.token).toBe('test-token')
  })

  it('should test endpoint connection', async () => {
    await wrapper.find('[data-testid="endpoint-url"]').setValue('https://api.test.com/graphql')
    const testBtn = wrapper.find('[data-testid="test-connection-button"]')
    
    await testBtn.trigger('click')
    
    expect(wrapper.find('[data-testid="connection-testing"]').exists()).toBe(true)
    // Will test actual connection logic once implemented
  })
})
```

### **1.3 Endpoint Table Component Tests**
```typescript
// tests/components/EndpointTable.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import EndpointTable from '@/components/EndpointTable.vue'
import { useEndpointStore } from '@/stores/endpoint'

const mockEndpoints = [
  {
    id: '1',
    name: 'Production API',
    url: 'https://api.prod.com/graphql',
    status: 'healthy',
    responseTime: 120,
    isActive: true,
    tags: ['production', 'v2'],
    lastHealthCheck: {
      status: 'healthy',
      responseTime: 120,
      timestamp: new Date()
    }
  },
  {
    id: '2', 
    name: 'Staging API',
    url: 'https://api.staging.com/graphql',
    status: 'unhealthy',
    responseTime: 0,
    isActive: false,
    tags: ['staging'],
    lastHealthCheck: {
      status: 'unhealthy',
      responseTime: 0,
      timestamp: new Date(),
      error: 'Connection timeout'
    }
  }
]

describe('Endpoint Table', () => {
  let wrapper
  let store

  beforeEach(() => {
    const pinia = createPinia()
    store = useEndpointStore(pinia)
    
    // Mock store with test data
    store.endpoints = mockEndpoints
    
    wrapper = mount(EndpointTable, {
      global: {
        plugins: [pinia]
      }
    })
  })

  it('should render endpoint table with data', () => {
    expect(wrapper.find('[data-testid="endpoints-table"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-testid^="endpoint-row-"]')).toHaveLength(2)
  })

  it('should display endpoint status indicators', () => {
    const healthyRow = wrapper.find('[data-testid="endpoint-row-1"]')
    const unhealthyRow = wrapper.find('[data-testid="endpoint-row-2"]')
    
    expect(healthyRow.find('[data-testid="status-healthy"]').exists()).toBe(true)
    expect(unhealthyRow.find('[data-testid="status-unhealthy"]').exists()).toBe(true)
  })

  it('should show response times', () => {
    const healthyRow = wrapper.find('[data-testid="endpoint-row-1"]')
    expect(healthyRow.find('[data-testid="response-time"]').text()).toContain('120ms')
  })

  it('should filter endpoints by search term', async () => {
    const searchInput = wrapper.find('[data-testid="search-input"]')
    await searchInput.setValue('Production')
    
    expect(wrapper.findAll('[data-testid^="endpoint-row-"]')).toHaveLength(1)
    expect(wrapper.find('[data-testid="endpoint-row-1"]').exists()).toBe(true)
  })

  it('should filter by status', async () => {
    const statusFilter = wrapper.find('[data-testid="status-filter"]')
    await statusFilter.setValue('healthy')
    
    expect(wrapper.findAll('[data-testid^="endpoint-row-"]')).toHaveLength(1)
    expect(wrapper.find('[data-testid="endpoint-row-1"]').exists()).toBe(true)
  })

  it('should show action buttons for each endpoint', () => {
    const firstRow = wrapper.find('[data-testid="endpoint-row-1"]')
    
    expect(firstRow.find('[data-testid="test-button"]').exists()).toBe(true)
    expect(firstRow.find('[data-testid="edit-button"]').exists()).toBe(true)
    expect(firstRow.find('[data-testid="delete-button"]').exists()).toBe(true)
    expect(firstRow.find('[data-testid="toggle-button"]').exists()).toBe(true)
  })

  it('should emit test event when test button clicked', async () => {
    const testBtn = wrapper.find('[data-testid="endpoint-row-1"] [data-testid="test-button"]')
    await testBtn.trigger('click')
    
    expect(wrapper.emitted('test')).toBeTruthy()
    expect(wrapper.emitted('test')[0][0]).toBe('1')
  })

  it('should emit edit event when edit button clicked', async () => {
    const editBtn = wrapper.find('[data-testid="endpoint-row-1"] [data-testid="edit-button"]')
    await editBtn.trigger('click')
    
    expect(wrapper.emitted('edit')).toBeTruthy()
    expect(wrapper.emitted('edit')[0][0]).toBe('1')
  })

  it('should handle bulk operations', async () => {
    // Select multiple endpoints
    await wrapper.find('[data-testid="select-endpoint-1"]').setChecked(true)
    await wrapper.find('[data-testid="select-endpoint-2"]').setChecked(true)
    
    const bulkDisable = wrapper.find('[data-testid="bulk-disable"]')
    await bulkDisable.trigger('click')
    
    expect(wrapper.emitted('bulk-update')).toBeTruthy()
  })

  it('should sort by columns', async () => {
    const nameHeader = wrapper.find('[data-testid="sort-name"]')
    await nameHeader.trigger('click')
    
    // Should sort endpoints by name
    expect(wrapper.vm.sortBy).toBe('name')
    expect(wrapper.vm.sortDirection).toBe('asc')
  })
})
```

### **1.4 Endpoint Management View Tests**
```typescript
// tests/views/EndpointManagement.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import EndpointManagement from '@/views/EndpointManagement.vue'

describe('Endpoint Management View', () => {
  let wrapper
  let router

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/endpoints', component: EndpointManagement }
      ]
    })

    wrapper = mount(EndpointManagement, {
      global: {
        plugins: [createPinia(), router]
      }
    })
  })

  it('should render page title and add button', () => {
    expect(wrapper.find('h1').text()).toContain('Endpoint Management')
    expect(wrapper.find('[data-testid="add-endpoint-button"]').exists()).toBe(true)
  })

  it('should show endpoint table', () => {
    expect(wrapper.find('[data-testid="endpoint-table"]').exists()).toBe(true)
  })

  it('should open add endpoint form', async () => {
    const addBtn = wrapper.find('[data-testid="add-endpoint-button"]')
    await addBtn.trigger('click')
    
    expect(wrapper.find('[data-testid="endpoint-form"]').exists()).toBe(true)
  })

  it('should handle real-time endpoint status updates', async () => {
    // Mock WebSocket message
    const mockWebSocketUpdate = {
      type: 'endpoint-health',
      endpointId: '1',
      health: {
        status: 'healthy',
        responseTime: 95,
        timestamp: new Date().toISOString()
      }
    }
    
    // Simulate WebSocket message
    wrapper.vm.handleWebSocketMessage(mockWebSocketUpdate)
    
    // Should update endpoint status in store
    expect(wrapper.vm.endpointStore.endpoints[0]?.lastHealthCheck?.status).toBe('healthy')
  })

  it('should handle endpoint testing', async () => {
    const testSpy = vi.spyOn(wrapper.vm, 'testEndpoint')
    
    // Simulate test action from table
    await wrapper.vm.testEndpoint('endpoint-id-123')
    
    expect(testSpy).toHaveBeenCalledWith('endpoint-id-123')
  })

  it('should show loading state during operations', () => {
    wrapper.vm.isLoading = true
    
    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true)
  })

  it('should show error messages', () => {
    wrapper.vm.error = 'Failed to load endpoints'
    
    expect(wrapper.find('[data-testid="error-message"]').text()).toContain('Failed to load endpoints')
  })
})
```

### **1.5 Endpoint Testing Service Tests**
```typescript
// tests/services/endpointTesting.test.ts
import { describe, it, expect, vi } from 'vitest'
import { useEndpointTesting } from '@/services/endpointTesting'

describe('Endpoint Testing Service', () => {
  it('should test basic connectivity', async () => {
    const { testConnection } = useEndpointTesting()
    
    // Mock successful connection
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Map([['content-type', 'application/json']]),
      json: () => Promise.resolve({ data: null })
    })
    
    const result = await testConnection({
      url: 'https://api.test.com/graphql',
      authType: 'none'
    })
    
    expect(result.success).toBe(true)
    expect(result.responseTime).toBeGreaterThan(0)
    expect(result.status).toBe(200)
  })

  it('should perform GraphQL introspection', async () => {
    const { introspectSchema } = useEndpointTesting()
    
    const mockIntrospectionResponse = {
      data: {
        __schema: {
          queryType: { name: 'Query' },
          types: [
            { name: 'User', kind: 'OBJECT' },
            { name: 'Post', kind: 'OBJECT' }
          ]
        }
      }
    }
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockIntrospectionResponse)
    })
    
    const result = await introspectSchema({
      url: 'https://api.test.com/graphql'
    })
    
    expect(result.success).toBe(true)
    expect(result.schema).toBeDefined()
    expect(result.types).toContain('User')
    expect(result.types).toContain('Post')
  })

  it('should execute test queries', async () => {
    const { executeQuery } = useEndpointTesting()
    
    const mockQueryResponse = {
      data: {
        users: [
          { id: '1', name: 'John Doe' }
        ]
      }
    }
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockQueryResponse)
    })
    
    const result = await executeQuery({
      url: 'https://api.test.com/graphql',
      query: 'query { users { id name } }'
    })
    
    expect(result.success).toBe(true)
    expect(result.data.users).toHaveLength(1)
    expect(result.data.users[0].name).toBe('John Doe')
  })

  it('should handle authentication headers', async () => {
    const { testConnection } = useEndpointTesting()
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: null })
    })
    
    await testConnection({
      url: 'https://api.test.com/graphql',
      authType: 'bearer',
      authConfig: { token: 'test-token' }
    })
    
    expect(fetch).toHaveBeenCalledWith(
      'https://api.test.com/graphql',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token'
        })
      })
    )
  })

  it('should handle connection errors gracefully', async () => {
    const { testConnection } = useEndpointTesting()
    
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
    
    const result = await testConnection({
      url: 'https://api.unreachable.com/graphql'
    })
    
    expect(result.success).toBe(false)
    expect(result.error).toContain('Network error')
  })
})
```

---

## **Phase 2: Implement Minimal Code** ✅

### **2.1 Endpoint Types & Interfaces**
```typescript
// src/types/endpoint.ts
export interface Endpoint {
  id: string
  name: string
  url: string
  description?: string
  tags: string[]
  authType: 'none' | 'bearer' | 'api-key' | 'basic'
  authConfig?: {
    token?: string
    apiKey?: string
    keyName?: string
    username?: string
    password?: string
  }
  headers?: Record<string, string>
  timeout: number
  retryCount: number
  healthCheckInterval: number
  isActive: boolean
  createdAt: Date
  updatedAt: Date
  lastHealthCheck?: HealthCheck
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
  responseTime: number
  timestamp: Date
  error?: string
  schemaVersion?: string
  introspectionSuccess: boolean
}

export interface EndpointTest {
  success: boolean
  responseTime: number
  status?: number
  error?: string
  data?: any
  schema?: SchemaInfo
}

export interface SchemaInfo {
  queryType?: string
  mutationType?: string
  subscriptionType?: string
  types: string[]
}

export interface EndpointFormData {
  name: string
  url: string
  description: string
  tags: string[]
  authType: Endpoint['authType']
  authConfig: Endpoint['authConfig']
  headers: Record<string, string>
  timeout: number
  retryCount: number
  healthCheckInterval: number
  isActive: boolean
}
```

### **2.2 Endpoint Store (Pinia) - Key Methods**
```typescript
// src/stores/endpoint.ts - Excerpt of key methods
export const useEndpointStore = defineStore('endpoint', () => {
  const endpoints = ref<Endpoint[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const addEndpoint = (data: Partial<EndpointFormData>): Endpoint => {
    const endpoint: Endpoint = {
      id: uuidv4(),
      name: data.name || '',
      url: data.url || '',
      // ... other fields with defaults
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    endpoints.value.push(endpoint)
    return endpoint
  }

  const updateEndpointHealth = (id: string, health: Partial<HealthCheck>) => {
    const endpoint = endpoints.value.find(e => e.id === id)
    if (endpoint) {
      endpoint.lastHealthCheck = {
        status: health.status || 'unknown',
        responseTime: health.responseTime || 0,
        timestamp: health.timestamp || new Date(),
        error: health.error,
        schemaVersion: health.schemaVersion,
        introspectionSuccess: health.introspectionSuccess || false
      }
    }
  }

  const searchEndpoints = (query: string) => {
    const lowercaseQuery = query.toLowerCase()
    return endpoints.value.filter(endpoint =>
      endpoint.name.toLowerCase().includes(lowercaseQuery) ||
      endpoint.url.toLowerCase().includes(lowercaseQuery) ||
      endpoint.tags.some(tag => tag.toLowerCase().includes(lowercaseQuery))
    )
  }

  // ... other methods
})
```

### **2.3 Endpoint Testing Service - Core Methods**
```typescript
// src/services/endpointTesting.ts - Key methods
export function useEndpointTesting() {
  const buildHeaders = (endpoint: Partial<Endpoint>) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...endpoint.headers
    }

    // Add authentication headers
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
          const credentials = btoa(`${endpoint.authConfig.username}:${endpoint.authConfig.password}`)
          headers['Authorization'] = `Basic ${credentials}`
        }
        break
    }

    return headers
  }

  const testConnection = async (endpoint: Partial<Endpoint>): Promise<EndpointTest> => {
    const startTime = performance.now()
    
    try {
      const response = await fetch(endpoint.url!, {
        method: 'POST',
        headers: buildHeaders(endpoint),
        body: JSON.stringify({
          query: '{ __schema { queryType { name } } }'
        }),
        signal: AbortSignal.timeout(endpoint.timeout || 30000)
      })

      const responseTime = performance.now() - startTime

      if (response.ok) {
        const data = await response.json()
        return {
          success: true,
          responseTime,
          status: response.status,
          data
        }
      } else {
        return {
          success: false,
          responseTime,
          status: response.status,
          error: `HTTP ${response.status}: ${response.statusText}`
        }
      }
    } catch (error) {
      const responseTime = performance.now() - startTime
      return {
        success: false,
        responseTime,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  const introspectSchema = async (endpoint: Partial<Endpoint>): Promise<EndpointTest> => {
    // GraphQL introspection implementation
    // Returns schema information and types
  }

  return {
    testConnection,
    introspectSchema,
    executeQuery
  }
}
```

---

## **Phase 3: Run Tests & Verify** ✅

After implementing each component, run the specific test suite:

```bash
# Test individual components as they're implemented
npm run test tests/stores/endpoint.test.ts -- --run
npm run test tests/components/EndpointForm.test.ts -- --run
npm run test tests/components/EndpointTable.test.ts -- --run
npm run test tests/views/EndpointManagement.test.ts -- --run
npm run test tests/services/endpointTesting.test.ts -- --run

# Run all endpoint management tests
npm run test tests/ -t "endpoint" -- --run

# Verify bundle size still under 380KB
npm run build
```

---

## **Phase 4: Refactor & Optimize** 🔄

- **Component extraction**: Create reusable UI components
- **Performance optimization**: Implement virtual scrolling for large endpoint lists
- **Error handling**: Add comprehensive error boundaries
- **Accessibility**: Ensure WCAG 2.1 AA compliance
- **Bundle optimization**: Code splitting for endpoint management features

---

## 🎯 **Success Criteria for Cycle 2**

### **Functional Requirements**: ✅
- **CRUD Operations**: Users can add, edit, delete GraphQL endpoints
- **Real-time Monitoring**: Live health status updates with WebSocket
- **Connection Testing**: Test endpoint connectivity and introspect schemas
- **Search & Filter**: Find endpoints by name, status, tags
- **Bulk Operations**: Enable/disable multiple endpoints
- **Import/Export**: JSON configuration management

### **Technical Requirements**: ✅
- **Test Coverage**: 90%+ coverage following strict TDD
- **Bundle Size**: Total bundle remains <380KB
- **TypeScript**: Zero errors in strict mode
- **Performance**: Handles 100+ endpoints smoothly
- **Responsive**: Works on mobile, tablet, desktop
- **Real-time**: WebSocket updates within 100ms

### **User Experience**: ✅
- **Intuitive UI**: Clear visual hierarchy and navigation
- **Immediate Feedback**: Loading states, success/error messages
- **Accessibility**: Screen reader compatible, keyboard navigation
- **Error Recovery**: Graceful handling of network failures
- **Data Persistence**: Form state preserved during navigation

---

## 📈 **Implementation Timeline**

| Day | Morning (4h) | Afternoon (4h) | Key Deliverable |
|-----|--------------|----------------|-----------------|
| **Day 3** | Data layer + Store | Endpoint Form Component | ✅ Core CRUD operations |
| **Day 4** | Endpoint Table + List | Health Monitoring | ✅ Real-time dashboard |
| **Day 5** | Testing + Analytics | Integration + Polish | ✅ Complete feature set |

**Total Effort**: ~24 hours over 3 days
**Expected Bundle Impact**: +50-80KB (still well under 380KB limit)
**Test Coverage Target**: 90%+ with full TDD approach

---

## 🔗 **Integration Points**

### **Backend Integration**
```python
# Existing backend has these related models:
class Endpoint(Base):
    id: UUID
    name: str
    url: str
    # ... other fields

class HealthCheck(Base): 
    endpoint_id: UUID
    status: str
    response_time: float
    # ... other fields
```

### **WebSocket Integration**  
```typescript
// Real-time endpoint status updates
const { connect } = useWebSocket()
connect('endpoints', (data) => {
  // Update endpoint status in real-time
  endpointStore.updateEndpointStatus(data)
})
```

---

## 📱 **User Experience Flow**

### **1. Endpoint List View**
- User sees table of all registered endpoints
- Status indicators show health (green/yellow/red dots)
- Response times displayed per endpoint
- Filter/search to find specific endpoints

### **2. Add New Endpoint**  
- Click "Add Endpoint" button
- Form opens with URL, auth, and configuration options
- Test connection before saving
- Validation ensures URL is reachable

### **3. Test Endpoint**
- Click test icon next to any endpoint  
- Quick introspection query runs
- Results show success/failure with details
- Schema information displayed if successful

### **4. Monitor Health**
- Real-time status updates via WebSocket
- Visual indicators change based on health
- Click endpoint to see detailed health history
- Alerts for degraded performance

---

## ✅ **Definition of Done**

**Cycle 2 is complete when**:
1. **All tests pass** (90%+ of written tests)
2. **Bundle size achieved** (Total <380KB)
3. **Endpoint CRUD works** (Add, edit, delete endpoints)
4. **Real-time monitoring** (WebSocket health updates)
5. **Testing functional** (Connection and schema introspection)
6. **Search & filter** (Find endpoints by various criteria)
7. **TypeScript strict** (Zero TS errors)
8. **Manual testing successful** (Full user workflow)

**🎯 Ready to begin TDD Cycle 2 implementation!**

This establishes comprehensive endpoint management capabilities as the foundation for Phase 2.5, after which Cycle 3 will add the GraphQL playground, and subsequent cycles will complete the advanced dashboard functionality.