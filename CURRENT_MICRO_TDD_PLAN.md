# 🎯 Phase 2.5 Dashboard - Micro TDD Implementation Plan

**Timeline**: 3-5 development sessions (2-3 hours each)
**Focus**: Complete MVP Foundation with real-time features
**Approach**: Short RED-GREEN-REFACTOR cycles (20-30 minutes each)

## 📊 Current Status Assessment

**✅ COMPLETED:**
- Vue 3 + TypeScript project setup
- Basic routing and navigation
- Endpoint management (CRUD operations)
- TypeScript compliance (100%)
- Pre-commit hooks for code quality

**🔄 IN PROGRESS:**
- Dashboard overview layout
- Endpoint detail views
- Component testing suite

**❌ MISSING (HIGH PRIORITY):**
- Real-time WebSocket integration
- Health status visualization
- Query playground functionality

## 🧪 TDD Micro-Cycles Plan

### **CYCLE 1: Real-Time Dashboard Foundation** (Session 1)

#### 🔴 RED Phase 1A (10 min) - WebSocket Service Test
```typescript
// tests/services/websocket.test.ts
describe('WebSocketService', () => {
  it('should connect to WebSocket and emit connection events', async () => {
    const service = new WebSocketService('ws://localhost:8080/health')
    const onConnect = vi.fn()

    service.on('connected', onConnect)
    await service.connect()

    expect(onConnect).toHaveBeenCalled()
  })

  it('should receive real-time endpoint health updates', async () => {
    const service = new WebSocketService('ws://localhost:8080/health')
    const onHealthUpdate = vi.fn()

    service.on('endpoint-health-update', onHealthUpdate)
    // Mock WebSocket message

    expect(onHealthUpdate).toHaveBeenCalledWith({
      endpointId: 'test-endpoint',
      isHealthy: false,
      responseTime: 5000,
      timestamp: expect.any(Date)
    })
  })
})
```

#### 🟢 GREEN Phase 1A (15 min) - Minimal WebSocket Service
```typescript
// src/services/websocket.ts
export class WebSocketService extends EventTarget {
  private ws: WebSocket | null = null

  constructor(private url: string) {
    super()
  }

  async connect(): Promise<void> {
    this.ws = new WebSocket(this.url)
    this.ws.onopen = () => this.dispatchEvent(new CustomEvent('connected'))
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'endpoint-health-update') {
        this.dispatchEvent(new CustomEvent('endpoint-health-update', { detail: data.payload }))
      }
    }
  }
}
```

#### 🔴 RED Phase 1B (10 min) - Dashboard Real-Time Integration Test
```typescript
// src/components/__tests__/Dashboard.test.ts
describe('Dashboard Real-Time Updates', () => {
  it('should update endpoint health when WebSocket message received', async () => {
    const wrapper = mount(Dashboard)
    const mockWebSocket = new MockWebSocketService()

    // Inject mock WebSocket
    wrapper.vm.webSocketService = mockWebSocket

    // Simulate health update
    mockWebSocket.emit('endpoint-health-update', {
      endpointId: 'endpoint-1',
      isHealthy: false,
      responseTime: 5000
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="endpoint-1-status"]').classes()).toContain('status-unhealthy')
  })
})
```

#### 🟢 GREEN Phase 1B (15 min) - Dashboard WebSocket Integration
```typescript
// src/components/Dashboard.vue
export default defineComponent({
  setup() {
    const endpointsStore = useEndpointsStore()
    const webSocketService = new WebSocketService('ws://localhost:8080/health')

    onMounted(async () => {
      await webSocketService.connect()

      webSocketService.addEventListener('endpoint-health-update', (event) => {
        const update = event.detail
        endpointsStore.updateEndpointHealth(update.endpointId, {
          isHealthy: update.isHealthy,
          responseTime: update.responseTime,
          lastChecked: update.timestamp
        })
      })
    })

    return { endpoints: endpointsStore.endpoints }
  }
})
```

#### 🔵 REFACTOR Phase 1 (5 min)
- Extract WebSocket URL to environment config
- Add error handling and reconnection logic
- Optimize event listener cleanup in onUnmounted

---

### **CYCLE 2: Health Status Visualization** (Session 1 continued)

#### 🔴 RED Phase 2A (10 min) - Health Status Card Test
```typescript
// src/components/__tests__/HealthStatusCard.test.ts
describe('HealthStatusCard', () => {
  it('should display healthy endpoint with green indicator', () => {
    const endpoint = {
      id: 'test-1',
      name: 'Test API',
      isHealthy: true,
      responseTime: 150,
      lastChecked: new Date()
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="status-indicator"]').classes()).toContain('bg-green-500')
    expect(wrapper.find('[data-testid="response-time"]').text()).toBe('150ms')
  })

  it('should display unhealthy endpoint with red indicator and error state', () => {
    const endpoint = {
      id: 'test-1',
      name: 'Test API',
      isHealthy: false,
      responseTime: 5000,
      errorMessage: 'Connection timeout',
      lastChecked: new Date()
    }

    const wrapper = mount(HealthStatusCard, { props: { endpoint } })

    expect(wrapper.find('[data-testid="status-indicator"]').classes()).toContain('bg-red-500')
    expect(wrapper.find('[data-testid="error-message"]').text()).toBe('Connection timeout')
  })
})
```

#### 🟢 GREEN Phase 2A (15 min) - Health Status Card Component
```vue
<!-- src/components/HealthStatusCard.vue -->
<template>
  <div class="health-status-card p-4 border rounded-lg">
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold">{{ endpoint.name }}</h3>
      <div
        :class="statusClasses"
        class="w-3 h-3 rounded-full"
        data-testid="status-indicator"
      />
    </div>

    <div class="text-sm text-gray-600 mb-2">
      <span data-testid="response-time">{{ endpoint.responseTime }}ms</span>
      <span class="mx-2">•</span>
      <span>{{ formattedLastChecked }}</span>
    </div>

    <div v-if="!endpoint.isHealthy" class="text-red-600 text-sm" data-testid="error-message">
      {{ endpoint.errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GraphQLEndpoint } from '../types/endpoint'

interface Props {
  endpoint: GraphQLEndpoint
}

const props = defineProps<Props>()

const statusClasses = computed(() => ({
  'bg-green-500': props.endpoint.isHealthy,
  'bg-red-500': !props.endpoint.isHealthy
}))
</script>
```

#### 🔴 RED Phase 2B (10 min) - Dashboard Grid Layout Test
```typescript
// src/components/__tests__/Dashboard.test.ts (additional test)
describe('Dashboard Grid Layout', () => {
  it('should display endpoints in responsive grid layout', () => {
    const mockEndpoints = [
      { id: '1', name: 'API 1', isHealthy: true },
      { id: '2', name: 'API 2', isHealthy: false },
      { id: '3', name: 'API 3', isHealthy: true }
    ]

    const wrapper = mount(Dashboard, {
      global: {
        stubs: { HealthStatusCard: true }
      }
    })

    // Mock store data
    wrapper.vm.endpoints = mockEndpoints

    const grid = wrapper.find('[data-testid="endpoints-grid"]')
    expect(grid.classes()).toContain('grid')
    expect(wrapper.findAllComponents({ name: 'HealthStatusCard' })).toHaveLength(3)
  })

  it('should show quick stats summary', () => {
    const wrapper = mount(Dashboard)
    wrapper.vm.endpoints = [
      { isHealthy: true }, { isHealthy: false }, { isHealthy: true }
    ]

    expect(wrapper.find('[data-testid="total-endpoints"]').text()).toBe('3')
    expect(wrapper.find('[data-testid="healthy-count"]').text()).toBe('2')
    expect(wrapper.find('[data-testid="unhealthy-count"]').text()).toBe('1')
  })
})
```

#### 🟢 GREEN Phase 2B (15 min) - Dashboard Grid Implementation
```vue
<!-- src/components/Dashboard.vue -->
<template>
  <div class="dashboard p-6">
    <!-- Quick Stats -->
    <div class="stats-grid grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-2xl font-bold" data-testid="total-endpoints">{{ endpoints.length }}</div>
        <div class="text-gray-600">Total Endpoints</div>
      </div>
      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-2xl font-bold text-green-600" data-testid="healthy-count">{{ healthyCount }}</div>
        <div class="text-gray-600">Healthy</div>
      </div>
      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-2xl font-bold text-red-600" data-testid="unhealthy-count">{{ unhealthyCount }}</div>
        <div class="text-gray-600">Unhealthy</div>
      </div>
      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-2xl font-bold" data-testid="avg-response-time">{{ avgResponseTime }}ms</div>
        <div class="text-gray-600">Avg Response Time</div>
      </div>
    </div>

    <!-- Endpoints Grid -->
    <div
      class="endpoints-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="endpoints-grid"
    >
      <HealthStatusCard
        v-for="endpoint in endpoints"
        :key="endpoint.id"
        :endpoint="endpoint"
        @click="viewEndpointDetails(endpoint)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const endpointsStore = useEndpointsStore()
const { endpoints } = storeToRefs(endpointsStore)

const healthyCount = computed(() => endpoints.value.filter(e => e.isHealthy).length)
const unhealthyCount = computed(() => endpoints.value.filter(e => !e.isHealthy).length)
const avgResponseTime = computed(() => {
  if (endpoints.value.length === 0) return 0
  const total = endpoints.value.reduce((sum, e) => sum + (e.responseTime || 0), 0)
  return Math.round(total / endpoints.value.length)
})
</script>
```

#### 🔵 REFACTOR Phase 2 (5 min)
- Extract stats calculations to composable
- Add loading states for endpoints
- Improve responsive breakpoints

---

### **CYCLE 3: Query Playground Foundation** (Session 2)

#### 🔴 RED Phase 3A (15 min) - GraphQL Editor Test
```typescript
// src/components/__tests__/GraphQLPlayground.test.ts
describe('GraphQLPlayground', () => {
  it('should render query editor with syntax highlighting', () => {
    const wrapper = mount(GraphQLPlayground, {
      props: { endpointUrl: 'https://api.test.com/graphql' }
    })

    expect(wrapper.find('[data-testid="query-editor"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="variables-editor"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="execute-button"]').exists()).toBe(true)
  })

  it('should execute query and display results', async () => {
    const mockExecuteQuery = vi.fn().mockResolvedValue({
      data: { users: [{ id: '1', name: 'John' }] },
      extensions: { tracing: { duration: 120 } }
    })

    const wrapper = mount(GraphQLPlayground, {
      props: { endpointUrl: 'https://api.test.com/graphql' },
      global: {
        provide: { executeQuery: mockExecuteQuery }
      }
    })

    await wrapper.find('[data-testid="execute-button"]').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="query-results"]').text()).toContain('John')
    expect(wrapper.find('[data-testid="execution-time"]').text()).toBe('120ms')
  })
})
```

#### 🟢 GREEN Phase 3A (20 min) - GraphQL Playground Component
```vue
<!-- src/components/GraphQLPlayground.vue -->
<template>
  <div class="graphql-playground flex h-full">
    <!-- Left Panel: Query + Variables -->
    <div class="left-panel w-1/2 p-4 border-r">
      <div class="mb-4">
        <label class="block text-sm font-medium mb-2">GraphQL Query</label>
        <textarea
          v-model="query"
          data-testid="query-editor"
          class="w-full h-64 p-3 border rounded font-mono text-sm"
          placeholder="Enter your GraphQL query..."
        />
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium mb-2">Query Variables (JSON)</label>
        <textarea
          v-model="variables"
          data-testid="variables-editor"
          class="w-full h-32 p-3 border rounded font-mono text-sm"
          placeholder='{ "limit": 10 }'
        />
      </div>

      <button
        @click="executeQuery"
        :disabled="loading"
        data-testid="execute-button"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Executing...' : 'Execute Query' }}
      </button>
    </div>

    <!-- Right Panel: Results -->
    <div class="right-panel w-1/2 p-4">
      <div v-if="loading" class="text-center py-8 text-gray-500">
        Executing query...
      </div>

      <div v-else-if="results" class="results">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-semibold">Results</h3>
          <span v-if="executionTime" data-testid="execution-time" class="text-sm text-gray-500">
            {{ executionTime }}ms
          </span>
        </div>

        <pre
          data-testid="query-results"
          class="bg-gray-50 p-3 rounded text-sm overflow-auto max-h-96"
        >{{ JSON.stringify(results, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  endpointUrl: string
}

const props = defineProps<Props>()

const query = ref('')
const variables = ref('')
const results = ref(null)
const loading = ref(false)
const executionTime = ref<number | null>(null)

const executeQuery = async () => {
  loading.value = true
  try {
    const startTime = Date.now()
    const result = await graphqlClient.execute(props.endpointUrl, {
      query: query.value,
      variables: variables.value ? JSON.parse(variables.value) : undefined
    })
    executionTime.value = Date.now() - startTime
    results.value = result
  } catch (error) {
    results.value = { error: error.message }
  } finally {
    loading.value = false
  }
}
</script>
```

#### 🔵 REFACTOR Phase 3A (5 min)
- Add syntax highlighting with Prism.js or CodeMirror
- Improve error handling and validation
- Add query history dropdown

---

### **CYCLE 4: Performance Monitoring Integration** (Session 3)

#### 🔴 RED Phase 4A (10 min) - Performance Metrics Test
```typescript
// src/services/__tests__/performanceMonitor.test.ts
describe('PerformanceMonitor', () => {
  it('should track query execution metrics', async () => {
    const monitor = new PerformanceMonitor()
    const onMetric = vi.fn()

    monitor.on('metric-recorded', onMetric)

    await monitor.trackQuery('test-endpoint', 'query { users }', {
      executionTime: 250,
      complexity: 15,
      success: true
    })

    expect(onMetric).toHaveBeenCalledWith({
      endpointId: 'test-endpoint',
      query: 'query { users }',
      metrics: expect.objectContaining({
        executionTime: 250,
        complexity: 15,
        success: true,
        timestamp: expect.any(Date)
      })
    })
  })
})
```

#### 🟢 GREEN Phase 4A (15 min) - Performance Monitor Service
```typescript
// src/services/performanceMonitor.ts
export class PerformanceMonitor extends EventTarget {
  private metrics: QueryMetric[] = []

  async trackQuery(endpointId: string, query: string, metrics: QueryMetrics): Promise<void> {
    const metric: QueryMetric = {
      id: generateId(),
      endpointId,
      query,
      ...metrics,
      timestamp: new Date()
    }

    this.metrics.push(metric)
    this.dispatchEvent(new CustomEvent('metric-recorded', { detail: metric }))

    // Send to backend analytics
    await this.sendToAnalytics(metric)
  }

  getMetricsForEndpoint(endpointId: string): QueryMetric[] {
    return this.metrics.filter(m => m.endpointId === endpointId)
  }
}
```

#### 🔴 RED Phase 4B (10 min) - Performance Chart Test
```typescript
// src/components/__tests__/PerformanceChart.test.ts
describe('PerformanceChart', () => {
  it('should render response time trend chart', () => {
    const metrics = [
      { timestamp: new Date('2025-01-21T10:00:00Z'), executionTime: 120 },
      { timestamp: new Date('2025-01-21T11:00:00Z'), executionTime: 150 },
      { timestamp: new Date('2025-01-21T12:00:00Z'), executionTime: 200 }
    ]

    const wrapper = mount(PerformanceChart, {
      props: { metrics, type: 'response-time' }
    })

    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(wrapper.vm.chartData.datasets[0].data).toEqual([120, 150, 200])
  })
})
```

#### 🟢 GREEN Phase 4B (15 min) - Performance Chart Component
```vue
<!-- src/components/PerformanceChart.vue -->
<template>
  <div class="performance-chart">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { Chart } from 'chart.js/auto'

interface Props {
  metrics: QueryMetric[]
  type: 'response-time' | 'complexity' | 'success-rate'
}

const props = defineProps<Props>()
const chartCanvas = ref<HTMLCanvasElement>()
let chart: Chart | null = null

const chartData = computed(() => {
  const labels = props.metrics.map(m => m.timestamp.toLocaleTimeString())
  const data = props.metrics.map(m => {
    switch (props.type) {
      case 'response-time': return m.executionTime
      case 'complexity': return m.complexity
      case 'success-rate': return m.success ? 1 : 0
      default: return 0
    }
  })

  return {
    labels,
    datasets: [{
      label: props.type === 'response-time' ? 'Response Time (ms)' :
             props.type === 'complexity' ? 'Query Complexity' : 'Success Rate',
      data,
      borderColor: '#3B82F6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.3
    }]
  }
})

onMounted(() => {
  if (chartCanvas.value) {
    chart = new Chart(chartCanvas.value, {
      type: 'line',
      data: chartData.value,
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    })
  }
})

watch(() => chartData.value, (newData) => {
  if (chart) {
    chart.data = newData
    chart.update()
  }
}, { deep: true })
</script>
```

#### 🔵 REFACTOR Phase 4 (5 min)
- Optimize chart updates for real-time data
- Add chart type switching
- Implement data aggregation for large datasets

---

## 🎯 **Session-by-Session Breakdown**

### **Session 1** (2-3 hours): Real-Time Foundation
- **Cycle 1**: WebSocket service + Dashboard integration
- **Cycle 2**: Health status visualization + Grid layout
- **Deliverable**: Live dashboard with real-time endpoint health updates

### **Session 2** (2-3 hours): Query Playground
- **Cycle 3**: GraphQL editor + Query execution
- **Deliverable**: Functional query playground for testing endpoints

### **Session 3** (2-3 hours): Performance Integration
- **Cycle 4**: Performance monitoring + Analytics charts
- **Deliverable**: Complete MVP with performance insights

## ✅ **Success Criteria**

**After Session 1:**
- [ ] Dashboard shows real-time endpoint health updates
- [ ] WebSocket connection established and stable
- [ ] Health status cards display correctly

**After Session 2:**
- [ ] Users can write and execute GraphQL queries
- [ ] Query results displayed with execution time
- [ ] Basic syntax highlighting working

**After Session 3:**
- [ ] Performance metrics tracked and visualized
- [ ] Charts show response time trends
- [ ] Complete MVP ready for user testing

## 📋 **Technical Debt & Future Cycles**

**Identified for future refinement:**
- Advanced query editor (CodeMirror integration)
- Query complexity analysis
- Advanced alerting system
- Export functionality
- Mobile responsive optimization

**Architecture decisions made:**
- WebSocket for real-time updates (vs polling)
- Chart.js for visualization (vs D3.js complexity)
- In-memory metrics storage (vs immediate persistence)
- Component-based testing approach

---

**🎯 Goal**: Deliver a functional MVP dashboard that provides real-time GraphQL endpoint monitoring with query testing capabilities, following strict TDD principles throughout development.
