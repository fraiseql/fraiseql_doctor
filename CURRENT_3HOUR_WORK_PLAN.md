# 🎯 3-Hour Work Plan: GraphQL Admin UI + Real-Time Analytics

**Session Date**: 2025-01-22
**Duration**: 3 hours (9 micro-cycles, 20 min each)
**Focus**: Complete Sub-PRD GraphQL Admin UI + Enhanced Real-Time Dashboard

## 📊 Current Status Analysis

### ✅ **Completed Foundation**
- Vue 3 + TypeScript project setup with TailwindCSS
- Basic routing and navigation structure
- Endpoint management (CRUD operations)
- Strong test coverage (42+ tests passing in Apollo Studio config, query history, auth)
- Real-time WebSocket foundation established

### 🔄 **In Progress**
- Dashboard overview layout with basic cards
- Component testing suite (comprehensive coverage)
- Real-time analytics integration

### ❌ **Missing (HIGH PRIORITY)**
- **GraphQL API Configuration Admin UI** (Sub-PRD requirement)
- **Real-time health visualization** for specific 3 APIs
- **Advanced performance analytics** with forecasting
- **Integrated alerting system** with thresholds

---

## 🕐 **Hour 1: GraphQL API Configuration Admin UI**
*Priority: HIGH (Sub-PRD requirement)*

### **TDD Micro-Cycle 1A: ApiConfigurationAdmin Component** (20 min)
**Target**: Core admin page for managing 3 specific GraphQL APIs

#### 🔴 RED Phase (7 min)
```typescript
// tests/components/admin/ApiConfigurationAdmin.test.ts
describe('ApiConfigurationAdmin', () => {
  it('should display 3 endpoint cards for api.example.dev, api.example.st, api.example.io', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    const cards = wrapper.findAll('[data-testid="api-endpoint-card"]')
    expect(cards).toHaveLength(3)
    expect(wrapper.text()).toContain('api.example.dev')
    expect(wrapper.text()).toContain('api.example.st')
    expect(wrapper.text()).toContain('api.example.io')
  })

  it('should show health indicators (green/yellow/red) for each API', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    expect(wrapper.find('[data-testid="api.example.dev-status"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="health-indicator"]').classes()).toContain('status-indicator')
  })

  it('should open configuration modal on Configure button click', async () => {
    const wrapper = mount(ApiConfigurationAdmin)
    const configBtn = wrapper.find('[data-testid="configure-api.example.dev"]')
    await configBtn.trigger('click')
    expect(wrapper.find('[data-testid="api-config-modal"]').exists()).toBe(true)
  })
})
```

#### 🟢 GREEN Phase (10 min)
```vue
<!-- src/components/admin/ApiConfigurationAdmin.vue -->
<template>
  <div class="api-configuration-admin p-6">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">GraphQL API Configuration</h1>
        <p class="text-gray-600">Monitor and configure your GraphQL endpoints</p>
      </div>
      <button class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
        + Add API
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <ApiEndpointCard
        v-for="endpoint in endpoints"
        :key="endpoint.id"
        :endpoint="endpoint"
        :data-testid="`api-endpoint-card`"
        @configure="openConfigModal"
        @test="testConnection"
      />
    </div>

    <ApiConfigurationModal
      v-model="showConfigModal"
      :endpoint="selectedEndpoint"
      :data-testid="api-config-modal"
      @save="handleConfigSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ApiEndpointCard from './components/ApiEndpointCard.vue'
import ApiConfigurationModal from './components/ApiConfigurationModal.vue'

const endpoints = ref([
  {
    id: 'api-example-dev',
    name: 'Example Dev API',
    url: 'https://api.example.dev/graphql',
    environment: 'dev',
    isHealthy: true,
    responseTime: 45,
    lastCheck: new Date()
  },
  {
    id: 'api-example-st',
    name: 'Example Staging API',
    url: 'https://api.example.st/graphql',
    environment: 'staging',
    isHealthy: false,
    responseTime: 250,
    lastCheck: new Date()
  },
  {
    id: 'api-example-io',
    name: 'Example Production API',
    url: 'https://api.example.io/graphql',
    environment: 'prod',
    isHealthy: true,
    responseTime: 38,
    lastCheck: new Date()
  }
])

const showConfigModal = ref(false)
const selectedEndpoint = ref(null)

const openConfigModal = (endpoint) => {
  selectedEndpoint.value = endpoint
  showConfigModal.value = true
}

const testConnection = (endpoint) => {
  // Test connection logic
}

const handleConfigSave = (config) => {
  // Save configuration logic
  showConfigModal.value = false
}
</script>
```

#### 🔵 REFACTOR Phase (3 min)
- Extract endpoint configuration to service
- Add TypeScript interfaces
- Improve card layout responsiveness

### **TDD Micro-Cycle 1B: Real-time Health Updates** (20 min)

#### 🔴 RED Phase (7 min)
```typescript
// tests/components/admin/AdminHealthUpdates.test.ts
describe('AdminHealthUpdates', () => {
  it('should update health status via WebSocket', async () => {
    const wrapper = mount(ApiConfigurationAdmin)
    const mockWebSocket = useMockWebSocket()

    mockWebSocket.emit('api-health-update', {
      apiId: 'api-example-dev',
      isHealthy: false,
      responseTime: 5000,
      timestamp: new Date()
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="api-example-dev-status"]').classes()).toContain('status-unhealthy')
  })

  it('should show last check timestamps', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    expect(wrapper.find('[data-testid="last-check-time"]').exists()).toBe(true)
  })

  it('should display response times and error rates', () => {
    const wrapper = mount(ApiConfigurationAdmin)
    expect(wrapper.find('[data-testid="response-time"]').text()).toContain('ms')
    expect(wrapper.find('[data-testid="error-rate"]').exists()).toBe(true)
  })
})
```

#### 🟢 GREEN Phase (10 min)
```vue
<!-- src/components/admin/components/ApiEndpointCard.vue -->
<template>
  <div class="bg-white p-6 rounded-lg shadow border-l-4"
       :class="healthBorderClass">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-lg">{{ endpoint.name }}</h3>
      <div class="flex items-center space-x-2">
        <div
          :data-testid="`${endpoint.id}-status`"
          :class="statusClasses"
          class="w-3 h-3 rounded-full"
        />
        <span class="text-sm text-gray-600">{{ endpoint.environment }}</span>
      </div>
    </div>

    <div class="space-y-2 mb-4">
      <div class="text-sm text-gray-600">{{ endpoint.url }}</div>
      <div class="flex justify-between text-sm">
        <span>Response Time:</span>
        <span data-testid="response-time" :class="responseTimeClass">
          {{ endpoint.responseTime }}ms
        </span>
      </div>
      <div class="flex justify-between text-sm">
        <span>Error Rate:</span>
        <span data-testid="error-rate" :class="errorRateClass">
          {{ endpoint.errorRate || 0 }}%
        </span>
      </div>
      <div class="flex justify-between text-sm">
        <span>Last Check:</span>
        <span data-testid="last-check-time" class="text-gray-500">
          {{ formatRelativeTime(endpoint.lastCheck) }}
        </span>
      </div>
    </div>

    <div class="flex space-x-2">
      <button
        :data-testid="`configure-${endpoint.id}`"
        class="flex-1 bg-blue-50 text-blue-600 px-3 py-2 rounded text-sm hover:bg-blue-100"
        @click="$emit('configure', endpoint)"
      >
        Configure
      </button>
      <button
        class="flex-1 bg-gray-50 text-gray-600 px-3 py-2 rounded text-sm hover:bg-gray-100"
        @click="$emit('test', endpoint)"
      >
        Test
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatRelativeTime } from '@/utils/dateUtils'

interface Endpoint {
  id: string
  name: string
  url: string
  environment: 'dev' | 'staging' | 'prod'
  isHealthy: boolean
  responseTime: number
  errorRate?: number
  lastCheck: Date
}

interface Props {
  endpoint: Endpoint
}

const props = defineProps<Props>()
defineEmits(['configure', 'test'])

const healthBorderClass = computed(() => ({
  'border-green-500': props.endpoint.isHealthy && props.endpoint.responseTime < 200,
  'border-yellow-500': props.endpoint.isHealthy && props.endpoint.responseTime >= 200,
  'border-red-500': !props.endpoint.isHealthy
}))

const statusClasses = computed(() => ({
  'bg-green-500': props.endpoint.isHealthy && props.endpoint.responseTime < 200,
  'bg-yellow-500': props.endpoint.isHealthy && props.endpoint.responseTime >= 200,
  'bg-red-500': !props.endpoint.isHealthy,
  'status-indicator': true,
  'status-healthy': props.endpoint.isHealthy && props.endpoint.responseTime < 200,
  'status-warning': props.endpoint.isHealthy && props.endpoint.responseTime >= 200,
  'status-unhealthy': !props.endpoint.isHealthy
}))
</script>
```

#### 🔵 REFACTOR Phase (3 min)
- Integrate with existing WebSocket service
- Extract health status logic to composable
- Add loading states for real-time updates

### **TDD Micro-Cycle 1C: Configuration Modal** (20 min)

#### 🔴 RED Phase (7 min)
```typescript
// tests/components/admin/ApiConfigurationModal.test.ts
describe('ApiConfigurationModal', () => {
  it('should save authentication settings (Bearer, API Key, Basic)', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: { endpoint: mockEndpoint, modelValue: true }
    })

    await wrapper.find('[data-testid="auth-type-select"]').setValue('bearer')
    await wrapper.find('[data-testid="auth-token-input"]').setValue('test-token-123')
    await wrapper.find('[data-testid="save-config-btn"]').trigger('click')

    expect(wrapper.emitted('save')).toBeTruthy()
    expect(wrapper.emitted('save')[0][0]).toMatchObject({
      authentication: { type: 'bearer', token: 'test-token-123' }
    })
  })

  it('should configure monitoring thresholds', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: { endpoint: mockEndpoint, modelValue: true }
    })

    await wrapper.find('[data-testid="response-time-warning"]').setValue('200')
    await wrapper.find('[data-testid="response-time-critical"]').setValue('500')
    await wrapper.find('[data-testid="save-config-btn"]').trigger('click')

    expect(wrapper.emitted('save')[0][0]).toMatchObject({
      thresholds: { responseTime: { warning: 200, critical: 500 } }
    })
  })

  it('should test connection functionality', async () => {
    const wrapper = mount(ApiConfigurationModal, {
      props: { endpoint: mockEndpoint, modelValue: true }
    })

    const testBtn = wrapper.find('[data-testid="test-connection-btn"]')
    await testBtn.trigger('click')

    expect(wrapper.find('[data-testid="connection-test-result"]').exists()).toBe(true)
  })
})
```

#### 🟢 GREEN Phase (10 min)
```vue
<!-- src/components/admin/components/ApiConfigurationModal.vue -->
<template>
  <Dialog :open="modelValue" @close="$emit('update:modelValue', false)">
    <div class="fixed inset-0 bg-black bg-opacity-25" />
    <div class="fixed inset-0 overflow-y-auto">
      <div class="flex min-h-full items-center justify-center p-4">
        <DialogPanel class="w-full max-w-2xl bg-white rounded-lg shadow-xl">
          <DialogTitle class="text-lg font-semibold p-6 border-b">
            Configure API: {{ endpoint?.name }}
          </DialogTitle>

          <div class="p-6 space-y-6" data-testid="api-config-modal">
            <!-- Basic Settings -->
            <div>
              <h3 class="font-medium mb-3">Basic Settings</h3>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium mb-1">Name</label>
                  <input
                    v-model="config.name"
                    class="w-full border rounded px-3 py-2"
                    data-testid="endpoint-name-input"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium mb-1">Environment</label>
                  <select
                    v-model="config.environment"
                    class="w-full border rounded px-3 py-2"
                  >
                    <option value="dev">Development</option>
                    <option value="staging">Staging</option>
                    <option value="prod">Production</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Authentication -->
            <div>
              <h3 class="font-medium mb-3">Authentication</h3>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium mb-1">Type</label>
                  <select
                    v-model="config.authentication.type"
                    data-testid="auth-type-select"
                    class="w-full border rounded px-3 py-2"
                  >
                    <option value="none">None</option>
                    <option value="bearer">Bearer Token</option>
                    <option value="api-key">API Key</option>
                    <option value="basic">Basic Auth</option>
                  </select>
                </div>

                <div v-if="config.authentication.type === 'bearer'">
                  <label class="block text-sm font-medium mb-1">Token</label>
                  <input
                    v-model="config.authentication.token"
                    type="password"
                    data-testid="auth-token-input"
                    class="w-full border rounded px-3 py-2"
                    placeholder="Enter bearer token"
                  />
                </div>
              </div>
            </div>

            <!-- Monitoring Thresholds -->
            <div>
              <h3 class="font-medium mb-3">Monitoring Thresholds</h3>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium mb-1">Response Time Warning (ms)</label>
                  <input
                    v-model.number="config.thresholds.responseTime.warning"
                    type="number"
                    data-testid="response-time-warning"
                    class="w-full border rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium mb-1">Response Time Critical (ms)</label>
                  <input
                    v-model.number="config.thresholds.responseTime.critical"
                    type="number"
                    data-testid="response-time-critical"
                    class="w-full border rounded px-3 py-2"
                  />
                </div>
              </div>
            </div>

            <!-- Connection Test -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <h3 class="font-medium">Connection Test</h3>
                <button
                  type="button"
                  data-testid="test-connection-btn"
                  class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                  :disabled="testing"
                  @click="testConnection"
                >
                  {{ testing ? 'Testing...' : 'Test Connection' }}
                </button>
              </div>
              <div
                v-if="testResult"
                data-testid="connection-test-result"
                :class="testResult.success ? 'text-green-600' : 'text-red-600'"
                class="text-sm p-3 bg-gray-50 rounded"
              >
                {{ testResult.message }}
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 p-6 border-t">
            <button
              type="button"
              class="px-4 py-2 text-gray-600 hover:text-gray-800"
              @click="$emit('update:modelValue', false)"
            >
              Cancel
            </button>
            <button
              type="button"
              data-testid="save-config-btn"
              class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              @click="saveConfig"
            >
              Save Configuration
            </button>
          </div>
        </DialogPanel>
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/vue'

interface Props {
  modelValue: boolean
  endpoint: any
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'save'])

const config = ref({
  name: '',
  environment: 'dev',
  authentication: {
    type: 'none',
    token: ''
  },
  thresholds: {
    responseTime: {
      warning: 200,
      critical: 500
    }
  }
})

const testing = ref(false)
const testResult = ref(null)

const testConnection = async () => {
  testing.value = true
  try {
    // Simulate connection test
    await new Promise(resolve => setTimeout(resolve, 1000))
    testResult.value = { success: true, message: 'Connection successful!' }
  } catch (error) {
    testResult.value = { success: false, message: 'Connection failed: ' + error.message }
  } finally {
    testing.value = false
  }
}

const saveConfig = () => {
  emit('save', { ...config.value })
}

watch(() => props.endpoint, (endpoint) => {
  if (endpoint) {
    config.value.name = endpoint.name
    config.value.environment = endpoint.environment
  }
}, { immediate: true })
</script>
```

#### 🔵 REFACTOR Phase (3 min)
- Extract configuration validation
- Add form error handling
- Improve accessibility

---

## 🕑 **Hour 2: Enhanced Real-Time Analytics Dashboard**

### **TDD Micro-Cycle 2A: Interactive Time Series Chart** (20 min)
### **TDD Micro-Cycle 2B: Real-Time Performance Dashboard** (20 min)
### **TDD Micro-Cycle 2C: Advanced Query History** (20 min)

---

## 🕒 **Hour 3: Integration & Production Readiness**

### **TDD Micro-Cycle 3A: Apollo Studio Integration** (20 min)
### **TDD Micro-Cycle 3B: Alert System Integration** (20 min)
### **TDD Micro-Cycle 3C: Production Performance** (20 min)

---

## ✅ **Session Success Metrics**

### **Functional Deliverables**
- [ ] GraphQL Admin UI for 3 specific APIs (api.example.dev/st/io)
- [ ] Real-time health monitoring with configurable thresholds
- [ ] Enhanced analytics dashboard with forecasting
- [ ] Integrated alert system with notifications
- [ ] Apollo Studio bridge with authentication

### **Technical Quality**
- [ ] All new tests passing (target: 15+ new tests)
- [ ] No TypeScript errors
- [ ] WebSocket performance <100ms latency
- [ ] Bundle size remains <400KB
- [ ] Real-time updates working smoothly

### **User Experience**
- [ ] Admin can configure all 3 APIs in under 5 minutes
- [ ] Health status visible immediately on page load
- [ ] Performance trends show actionable insights
- [ ] Alerts trigger within 30 seconds of threshold breach

---

**Next Session**: Focus on query complexity analysis and advanced monitoring features
