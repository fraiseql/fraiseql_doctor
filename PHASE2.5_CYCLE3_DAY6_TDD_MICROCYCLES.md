# 🧪 **Phase 2.5 Cycle 3 - Day 6: TDD Micro-Cycles**

## **Apollo Studio Integration Foundation**

---

## 📋 **Day 6 Overview**

**Target**: Basic Apollo Studio integration with authentication bridge  
**Duration**: 6 hours (8 micro-cycles)  
**Success Criteria**: Working Apollo Studio iframe with all auth types functional

---

## ⏰ **TDD Micro-Cycle Schedule**

| Cycle | Time | Feature | Duration | Tests | Code |
|-------|------|---------|----------|-------|------|
| **1** | 9:00-9:30 | Basic Component Render | 30 min | 3 tests | Minimal Vue component |
| **2** | 9:30-10:15 | Iframe Integration | 45 min | 4 tests | Iframe element + config |
| **3** | 10:30-11:15 | Auth Configuration Service | 45 min | 6 tests | useApolloStudioConfig |
| **4** | 11:15-12:00 | Bearer Token Auth | 45 min | 4 tests | Bearer auth implementation |
| **5** | 13:00-13:45 | API Key & Basic Auth | 45 min | 5 tests | Multi-auth support |
| **6** | 13:45-14:30 | Endpoint Switching | 45 min | 4 tests | Dynamic config updates |
| **7** | 14:45-15:30 | Error Handling | 45 min | 3 tests | Error boundaries |
| **8** | 15:30-16:00 | Integration Testing | 30 min | 2 tests | E2E scenarios |

---

# 🔄 **TDD Cycle 1: Basic Component Render**

**Time**: 9:00-9:30 (30 minutes)

## ❌ **RED Phase** (10 minutes)

### **Test 1: Component Renders**

```typescript
// src/components/__tests__/ApolloStudioIntegration.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApolloStudioIntegration from '../ApolloStudioIntegration.vue'

describe('Apollo Studio Integration - Cycle 1', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render Apollo Studio container', () => {
    const wrapper = mount(ApolloStudioIntegration)
    
    expect(wrapper.find('[data-testid="apollo-studio-container"]').exists()).toBe(true)
  })

  it('should have correct CSS classes for layout', () => {
    const wrapper = mount(ApolloStudioIntegration)
    const container = wrapper.find('[data-testid="apollo-studio-container"]')
    
    expect(container.classes()).toContain('w-full')
    expect(container.classes()).toContain('h-full')
  })

  it('should render component title', () => {
    const wrapper = mount(ApolloStudioIntegration)
    
    expect(wrapper.find('[data-testid="studio-title"]').text()).toBe('GraphQL Playground')
  })
})
```

**Run Tests**: `npm test -- src/components/__tests__/ApolloStudioIntegration.test.ts`  
**Expected**: ❌ **3 tests fail** (component doesn't exist)

## ✅ **GREEN Phase** (15 minutes)

### **Minimal Implementation**

```vue
<!-- src/components/ApolloStudioIntegration.vue -->
<template>
  <div 
    data-testid="apollo-studio-container"
    class="w-full h-full relative bg-white"
  >
    <h2 data-testid="studio-title" class="text-xl font-semibold p-4">
      GraphQL Playground
    </h2>
  </div>
</template>

<script setup lang="ts">
// Minimal setup - no logic yet
</script>
```

**Run Tests**: `npm test -- src/components/__tests__/ApolloStudioIntegration.test.ts`  
**Expected**: ✅ **3 tests pass**

## 🔧 **REFACTOR Phase** (5 minutes)

### **Clean Up Structure**

```vue
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

<style scoped>
.apollo-studio-integration {
  @apply w-full h-full relative bg-white;
}

.studio-header {
  @apply p-4 border-b border-gray-200;
}
</style>
```

### **Cycle 1 Checkpoint** ✅

- [x] Component renders correctly
- [x] Basic layout structure in place
- [x] CSS classes properly applied
- [x] All tests passing
- [x] Code is clean and maintainable

---

# 🔄 **TDD Cycle 2: Iframe Integration**

**Time**: 9:30-10:15 (45 minutes)

## ❌ **RED Phase** (15 minutes)

### **Add Iframe Tests**

```typescript
// Add to existing test file
describe('Apollo Studio Integration - Cycle 2', () => {
  it('should render iframe when endpoint is provided', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    expect(wrapper.find('[data-testid="apollo-studio-iframe"]').exists()).toBe(true)
  })

  it('should set correct iframe src URL', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    expect(iframe.attributes('src')).toContain('studio.apollographql.com')
  })

  it('should show loading state initially', () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    expect(wrapper.find('[data-testid="studio-loading"]').exists()).toBe(true)
  })

  it('should hide loading state after iframe loads', async () => {
    const wrapper = mount(ApolloStudioIntegration, {
      props: {
        endpointUrl: 'https://api.example.com/graphql'
      }
    })
    
    // Simulate iframe load
    const iframe = wrapper.find('[data-testid="apollo-studio-iframe"]')
    await iframe.trigger('load')
    
    expect(wrapper.find('[data-testid="studio-loading"]').exists()).toBe(false)
  })
})
```

**Run Tests**: `npm test`  
**Expected**: ❌ **4 tests fail** (iframe not implemented)

## ✅ **GREEN Phase** (25 minutes)

### **Add Props and Iframe**

```vue
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
  
  const params = new URLSearchParams({
    endpoint: props.endpointUrl
  })
  
  return `https://studio.apollographql.com/sandbox/explorer?${params.toString()}`
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
```

**Run Tests**: `npm test`  
**Expected**: ✅ **7 tests pass**

## 🔧 **REFACTOR Phase** (5 minutes)

### **Extract URL Building Logic**

```typescript
// src/utils/apolloStudioUrl.ts
export function buildApolloStudioUrl(endpointUrl: string): string {
  const params = new URLSearchParams({
    endpoint: endpointUrl
  })
  
  return `https://studio.apollographql.com/sandbox/explorer?${params.toString()}`
}
```

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { buildApolloStudioUrl } from '../utils/apolloStudioUrl'

// ... rest of component
const studioUrl = computed(() => {
  if (!props.endpointUrl) return ''
  return buildApolloStudioUrl(props.endpointUrl)
})
</script>
```

### **Cycle 2 Checkpoint** ✅

- [x] Iframe integration working
- [x] Loading state implemented
- [x] URL building extracted to utility
- [x] All tests passing
- [x] Clean component structure

---

# 🔄 **TDD Cycle 3: Auth Configuration Service**

**Time**: 10:30-11:15 (45 minutes)

## ❌ **RED Phase** (15 minutes)

### **Create Service Tests**

```typescript
// src/services/__tests__/apolloStudioConfig.test.ts
import { describe, it, expect } from 'vitest'
import { useApolloStudioConfig } from '../apolloStudioConfig'
import type { GraphQLEndpoint } from '../../types/endpoint'
import { EndpointStatus } from '../../types/endpoint'

describe('Apollo Studio Configuration Service', () => {
  const mockEndpoint: GraphQLEndpoint = {
    id: 'test-1',
    name: 'Test API',
    url: 'https://api.example.com/graphql',
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: true,
    isHealthy: true,
    headers: {
      'Authorization': 'Bearer test-token',
      'X-API-Key': 'api-key-value'
    },
    createdAt: new Date(),
    updatedAt: new Date()
  }

  it('should create basic Studio configuration', () => {
    const { createStudioConfig } = useApolloStudioConfig()
    
    const config = createStudioConfig(mockEndpoint)
    
    expect(config.endpoint).toBe('https://api.example.com/graphql')
    expect(config.headers).toEqual(mockEndpoint.headers)
  })

  it('should build Auth0 style configuration', () => {
    const { buildAuthHeaders } = useApolloStudioConfig()
    
    const headers = buildAuthHeaders({
      Authorization: 'Bearer token123',
      'Content-Type': 'application/json'
    })
    
    expect(headers.Authorization).toBe('Bearer token123')
    expect(headers['Content-Type']).toBe('application/json')
  })

  it('should handle missing headers gracefully', () => {
    const endpointWithoutHeaders = { ...mockEndpoint, headers: undefined }
    const { createStudioConfig } = useApolloStudioConfig()
    
    const config = createStudioConfig(endpointWithoutHeaders)
    
    expect(config.headers).toEqual({})
  })

  it('should generate Studio URL with auth parameters', () => {
    const { generateStudioUrl } = useApolloStudioConfig()
    
    const url = generateStudioUrl(mockEndpoint)
    
    expect(url).toContain('studio.apollographql.com')
    expect(url).toContain('endpoint=' + encodeURIComponent(mockEndpoint.url))
  })

  it('should validate endpoint configuration', () => {
    const { validateEndpointConfig } = useApolloStudioConfig()
    
    const isValid = validateEndpointConfig(mockEndpoint)
    const isInvalid = validateEndpointConfig({
      ...mockEndpoint,
      url: 'invalid-url'
    })
    
    expect(isValid).toBe(true)
    expect(isInvalid).toBe(false)
  })

  it('should merge default and custom headers', () => {
    const { mergeHeaders } = useApolloStudioConfig()
    
    const defaultHeaders = { 'Content-Type': 'application/json' }
    const customHeaders = { 'Authorization': 'Bearer token' }
    
    const merged = mergeHeaders(defaultHeaders, customHeaders)
    
    expect(merged).toEqual({
      'Content-Type': 'application/json',
      'Authorization': 'Bearer token'
    })
  })
})
```

**Run Tests**: `npm test -- src/services/__tests__/apolloStudioConfig.test.ts`  
**Expected**: ❌ **6 tests fail** (service doesn't exist)

## ✅ **GREEN Phase** (25 minutes)

### **Implement Service**

```typescript
// src/services/apolloStudioConfig.ts
import type { GraphQLEndpoint } from '../types/endpoint'

export interface StudioConfig {
  endpoint: string
  headers: Record<string, string>
  theme?: 'light' | 'dark'
}

export function useApolloStudioConfig() {
  function createStudioConfig(endpoint: GraphQLEndpoint): StudioConfig {
    return {
      endpoint: endpoint.url,
      headers: endpoint.headers || {}
    }
  }

  function buildAuthHeaders(headers: Record<string, string> = {}): Record<string, string> {
    return { ...headers }
  }

  function generateStudioUrl(endpoint: GraphQLEndpoint): string {
    const params = new URLSearchParams({
      endpoint: endpoint.url
    })
    
    return `https://studio.apollographql.com/sandbox/explorer?${params.toString()}`
  }

  function validateEndpointConfig(endpoint: GraphQLEndpoint): boolean {
    try {
      new URL(endpoint.url)
      return true
    } catch {
      return false
    }
  }

  function mergeHeaders(
    defaultHeaders: Record<string, string>,
    customHeaders: Record<string, string>
  ): Record<string, string> {
    return {
      ...defaultHeaders,
      ...customHeaders
    }
  }

  return {
    createStudioConfig,
    buildAuthHeaders,
    generateStudioUrl,
    validateEndpointConfig,
    mergeHeaders
  }
}
```

**Run Tests**: `npm test -- src/services/__tests__/apolloStudioConfig.test.ts`  
**Expected**: ✅ **6 tests pass**

## 🔧 **REFACTOR Phase** (5 minutes)

### **Add TypeScript Improvements**

```typescript
// Add better type definitions
export interface StudioHeaders {
  [key: string]: string
}

export interface StudioConfig {
  endpoint: string
  headers: StudioHeaders
  theme?: 'light' | 'dark'
  introspection?: boolean
}

// Improve URL generation
function generateStudioUrl(endpoint: GraphQLEndpoint): string {
  const baseUrl = 'https://studio.apollographql.com/sandbox/explorer'
  const params = new URLSearchParams({
    endpoint: endpoint.url,
    ...(endpoint.introspectionEnabled && { introspection: 'true' })
  })
  
  return `${baseUrl}?${params.toString()}`
}
```

### **Cycle 3 Checkpoint** ✅

- [x] Configuration service implemented
- [x] All auth header handling working
- [x] URL generation with parameters
- [x] Validation logic in place
- [x] TypeScript types properly defined
- [x] All tests passing

---

# 🔄 **TDD Cycle 4: Bearer Token Auth**

**Time**: 11:15-12:00 (45 minutes)

## ❌ **RED Phase** (15 minutes)

### **Bearer Auth Tests**

```typescript
// Add to apolloStudioConfig.test.ts
describe('Bearer Token Authentication', () => {
  it('should handle Bearer token format correctly', () => {
    const { formatBearerToken } = useApolloStudioConfig()
    
    const token = formatBearerToken('my-secret-token')
    
    expect(token).toBe('Bearer my-secret-token')
  })

  it('should not double-prefix Bearer tokens', () => {
    const { formatBearerToken } = useApolloStudioConfig()
    
    const alreadyPrefixed = formatBearerToken('Bearer existing-token')
    
    expect(alreadyPrefixed).toBe('Bearer existing-token')
    expect(alreadyPrefixed).not.toBe('Bearer Bearer existing-token')
  })

  it('should create config with Bearer authentication', () => {
    const { createConfigWithAuth } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Auth API',
      url: 'https://auth.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'my-token-123'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const config = createConfigWithAuth(endpoint, 'bearer')
    
    expect(config.headers.Authorization).toBe('Bearer my-token-123')
  })

  it('should extract token from Bearer header', () => {
    const { extractBearerToken } = useApolloStudioConfig()
    
    const token = extractBearerToken('Bearer secret-token-value')
    
    expect(token).toBe('secret-token-value')
  })
})
```

**Run Tests**: `npm test`  
**Expected**: ❌ **4 tests fail** (Bearer functions not implemented)

## ✅ **GREEN Phase** (25 minutes)

### **Implement Bearer Auth Logic**

```typescript
// Add to apolloStudioConfig.ts
export type AuthType = 'bearer' | 'api-key' | 'basic' | 'none'

export function useApolloStudioConfig() {
  // ... existing functions

  function formatBearerToken(token: string): string {
    if (token.startsWith('Bearer ')) {
      return token
    }
    return `Bearer ${token}`
  }

  function extractBearerToken(authHeader: string): string {
    return authHeader.replace(/^Bearer\s+/, '')
  }

  function createConfigWithAuth(
    endpoint: GraphQLEndpoint, 
    authType: AuthType
  ): StudioConfig {
    const config = createStudioConfig(endpoint)
    
    if (authType === 'bearer' && config.headers.Authorization) {
      config.headers.Authorization = formatBearerToken(config.headers.Authorization)
    }
    
    return config
  }

  return {
    // ... existing exports
    formatBearerToken,
    extractBearerToken,
    createConfigWithAuth
  }
}
```

**Run Tests**: `npm test`  
**Expected**: ✅ **10 tests pass**

## 🔧 **REFACTOR Phase** (5 minutes)

### **Extract Auth Utilities**

```typescript
// src/utils/authHelpers.ts
export function isBearerToken(token: string): boolean {
  return token.startsWith('Bearer ')
}

export function sanitizeToken(token: string): string {
  return token.trim()
}

// Update service to use utilities
import { isBearerToken, sanitizeToken } from '../utils/authHelpers'

function formatBearerToken(token: string): string {
  const clean = sanitizeToken(token)
  return isBearerToken(clean) ? clean : `Bearer ${clean}`
}
```

### **Cycle 4 Checkpoint** ✅

- [x] Bearer token formatting working
- [x] Double-prefix prevention
- [x] Token extraction logic
- [x] Auth type configuration
- [x] Utility functions extracted
- [x] All tests passing

---

# 🔄 **TDD Cycles 5-8 Summary**

## **Cycle 5: API Key & Basic Auth** (13:00-13:45)

- **Tests**: API key header formatting, basic auth encoding, multi-auth support
- **Implementation**: Support for X-API-Key, custom header names, base64 basic auth
- **Refactor**: Auth strategy pattern

## **Cycle 6: Endpoint Switching** (13:45-14:30)

- **Tests**: Dynamic config updates, iframe refresh, state management
- **Implementation**: Reactive configuration, endpoint change detection
- **Refactor**: Configuration caching

## **Cycle 7: Error Handling** (14:45-15:30)

- **Tests**: Network errors, invalid URLs, auth failures
- **Implementation**: Error boundaries, user feedback, retry logic
- **Refactor**: Error state management

## **Cycle 8: Integration Testing** (15:30-16:00)

- **Tests**: End-to-end scenarios, real iframe interaction
- **Implementation**: Component integration, message passing
- **Refactor**: Final cleanup and optimization

---

# 📊 **Day 6 Success Metrics**

## **Completion Checklist**

- [ ] All 31 tests passing
- [ ] Apollo Studio iframe functional
- [ ] All authentication types working
- [ ] Endpoint switching smooth
- [ ] Error handling robust
- [ ] Bundle size impact <50KB
- [ ] No TypeScript errors
- [ ] Clean, maintainable code

## **Performance Targets**

- [ ] Iframe load time <3 seconds
- [ ] Endpoint switch time <1 second
- [ ] No memory leaks
- [ ] Responsive design works

## **Code Quality Metrics**

- [ ] Test coverage >90%
- [ ] No console errors
- [ ] Proper TypeScript typing
- [ ] Clean component structure
- [ ] Reusable utilities extracted

---

## 🎯 **Next Steps for Day 7**

With Day 6 foundation complete, Day 7 will focus on:

1. **Query History Capture** (TDD Cycles 9-12)
2. **Theme Integration** (TDD Cycles 13-15)
3. **Performance Optimization** (TDD Cycles 16-17)

The micro-cycle approach ensures steady progress with clear checkpoints and maintains the high-quality TDD methodology established in previous cycles.

