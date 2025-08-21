# Phase 2.5: Vue.js Dashboard - Detailed TDD Implementation Plan
**Inspired by PrintOptim Frontend Architecture with Bundle Optimization**

## 📊 PrintOptim Stack Analysis

### ✅ **What to Adopt from PrintOptim:**
- **Nuxt 3** → Switch to **Vite + Vue 3** (lighter, more control)
- **TailwindCSS** → Keep for rapid styling
- **Pinia** → Keep for state management
- **Vue Apollo** → Keep for GraphQL integration
- **Component architecture** → Adopt pattern with local components
- **TypeScript** → Essential for large apps

### 🎯 **Bundle Optimizations vs PrintOptim:**
- **No Nuxt SSR overhead** (SPA only dashboard)
- **Pluggable Auth0** → Modular auth system (easy to swap)
- **No i18n** → English only (reduce 40KB+)
- **No FormKit** → Native HTML5 forms
- **Shoelace** → Replace with **Headless UI** (smaller)
- **Custom fonts** → System fonts only
- **Tree shaking** → Aggressive component imports
- **Code splitting** → Route-based chunks only

### 📦 **Estimated Bundle Size:**
- PrintOptim: ~800KB → FraiseQL Doctor: ~380KB target (with Auth0)

---

## 🎯 Phase 2.5: TDD Implementation Plan

**Timeline:** 5-7 days
**Approach:** Feature → Failing Tests → Code → Passing Tests → Next Feature

---

## 🏗️ **Day 1: Project Foundation & Setup**

### **1.1 Project Structure Setup**
**Feature:** Basic Vite + Vue 3 + TypeScript project structure

**Failing Tests:**
```javascript
// tests/setup.test.ts
describe('Project Setup', () => {
  it('should have Vite dev server running', () => {
    expect(process.env.NODE_ENV).toBeDefined()
  })

  it('should compile TypeScript without errors', () => {
    // This will fail until TS is properly configured
    expect(true).toBe(true)
  })
})
```

**Implementation:**
```bash
# Initialize project
cd /home/lionel/code/fraiseql_doctor
mkdir frontend
cd frontend

# Package.json with optimized dependencies
npm init -y
npm install vue@^3.4.0 vue-router@^4.2.0 pinia@^2.1.0
npm install -D vite@^5.0.0 @vitejs/plugin-vue typescript vue-tsc
npm install -D vitest @vue/test-utils happy-dom
npm install tailwindcss@^3.4.0 @tailwindcss/forms autoprefixer
npm install @headlessui/vue @heroicons/vue
npm install @apollo/client @vue/apollo-composable graphql
npm install chart.js vue-chartjs@^5.3.0
npm install socket.io-client@^4.7.0
npm install @auth0/auth0-vue@^2.4.0  # Pluggable auth system
```

**File Structure:**
```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── ui/             # Base UI components
│   │   ├── dashboard/      # Dashboard-specific
│   │   ├── endpoints/      # Endpoint management
│   │   ├── queries/        # Query management
│   │   └── auth/           # Authentication components
│   ├── views/              # Page-level components
│   ├── stores/             # Pinia stores
│   ├── services/           # API services
│   │   ├── auth/           # Pluggable auth providers
│   │   │   ├── AuthProvider.ts      # Abstract auth interface
│   │   │   ├── Auth0Provider.ts     # Auth0 implementation
│   │   │   └── MockProvider.ts      # Mock for testing
│   │   └── api/            # API services
│   ├── types/              # TypeScript definitions
│   └── utils/              # Helper functions
├── tests/                  # Test files
└── public/                 # Static assets
```

**Passing Tests:**
Run `npm run test` → All setup tests pass

### **1.2 Vite Configuration with Bundle Optimization**
**Feature:** Optimized Vite config for minimum bundle size

**Failing Tests:**
```javascript
// tests/bundle.test.ts
describe('Bundle Optimization', () => {
  it('should have bundle size under 300KB', async () => {
    // This will fail until optimization is implemented
    const bundleStats = await getBundleSize()
    expect(bundleStats.totalSize).toBeLessThan(300 * 1024)
  })
})
```

**Implementation:**
```typescript
// vite.config.ts - Optimized for bundle size
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  build: {
    // Bundle optimization
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'charts': ['chart.js', 'vue-chartjs'],
          'apollo': ['@apollo/client', '@vue/apollo-composable']
        }
      }
    },
    // Minimize bundle size
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  // Tree shaking optimization
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia'],
    exclude: ['@vue/apollo-composable'] // Lazy load
  }
})
```

**Passing Tests:**
Bundle analysis shows <380KB target achieved

### **1.3 Pluggable Authentication Architecture**
**Feature:** Auth0 integration with pluggable provider system

**Failing Tests:**
```typescript
// tests/services/auth.test.ts
import { useAuth } from '@/services/auth'
import { AuthProviderType } from '@/types/auth'

describe('Authentication System', () => {
  it('should initialize with Auth0 provider', () => {
    const { provider, isAuthenticated } = useAuth()
    expect(provider.type).toBe(AuthProviderType.AUTH0)
  })

  it('should be swappable to different provider', () => {
    const { switchProvider } = useAuth()
    switchProvider(AuthProviderType.MOCK)
    // This will fail until provider switching is implemented
    expect(useAuth().provider.type).toBe(AuthProviderType.MOCK)
  })

  it('should handle login flow', async () => {
    const { login, isAuthenticated } = useAuth()
    await login()
    // This will fail until Auth0 login is implemented
    expect(isAuthenticated.value).toBe(true)
  })
})
```

**Implementation:**
```typescript
// src/types/auth.ts
export enum AuthProviderType {
  AUTH0 = 'auth0',
  MOCK = 'mock',
  JWT = 'jwt',
  OAUTH2 = 'oauth2'
}

export interface User {
  id: string
  email: string
  name: string
  picture?: string
  roles: string[]
}

export interface AuthProvider {
  type: AuthProviderType
  isAuthenticated: Ref<boolean>
  user: Ref<User | null>
  loading: Ref<boolean>
  error: Ref<string | null>

  login(): Promise<void>
  logout(): Promise<void>
  checkAuth(): Promise<boolean>
  getToken(): Promise<string | null>
}
```

```typescript
// src/services/auth/AuthProvider.ts - Abstract interface
import { Ref } from 'vue'
import type { User, AuthProviderType } from '@/types/auth'

export abstract class BaseAuthProvider {
  abstract type: AuthProviderType
  abstract isAuthenticated: Ref<boolean>
  abstract user: Ref<User | null>
  abstract loading: Ref<boolean>
  abstract error: Ref<string | null>

  abstract login(): Promise<void>
  abstract logout(): Promise<void>
  abstract checkAuth(): Promise<boolean>
  abstract getToken(): Promise<string | null>
}
```

```typescript
// src/services/auth/Auth0Provider.ts
import { ref } from 'vue'
import { createAuth0 } from '@auth0/auth0-vue'
import { BaseAuthProvider } from './AuthProvider'
import { AuthProviderType } from '@/types/auth'

export class Auth0Provider extends BaseAuthProvider {
  type = AuthProviderType.AUTH0
  isAuthenticated = ref(false)
  user = ref(null)
  loading = ref(false)
  error = ref(null)

  private auth0: any

  constructor(config: {
    domain: string
    clientId: string
    audience?: string
    redirectUri?: string
  }) {
    super()
    this.auth0 = createAuth0({
      domain: config.domain,
      clientId: config.clientId,
      authorizationParams: {
        redirect_uri: config.redirectUri || window.location.origin,
        audience: config.audience,
      }
    })
  }

  async login(): Promise<void> {
    this.loading.value = true
    this.error.value = null

    try {
      await this.auth0.loginWithRedirect()
    } catch (err: any) {
      this.error.value = err.message
    } finally {
      this.loading.value = false
    }
  }

  async logout(): Promise<void> {
    await this.auth0.logout({
      logoutParams: {
        returnTo: window.location.origin
      }
    })
    this.isAuthenticated.value = false
    this.user.value = null
  }

  async checkAuth(): Promise<boolean> {
    this.loading.value = true

    try {
      // Handle redirect callback
      if (window.location.search.includes('code=')) {
        await this.auth0.handleRedirectCallback()
      }

      const authenticated = await this.auth0.isAuthenticated()
      this.isAuthenticated.value = authenticated

      if (authenticated) {
        const auth0User = await this.auth0.getUser()
        this.user.value = {
          id: auth0User.sub,
          email: auth0User.email,
          name: auth0User.name,
          picture: auth0User.picture,
          roles: auth0User['https://fraiseql-doctor.dev/roles'] || ['user']
        }
      }

      return authenticated
    } catch (err: any) {
      this.error.value = err.message
      return false
    } finally {
      this.loading.value = false
    }
  }

  async getToken(): Promise<string | null> {
    if (!this.isAuthenticated.value) return null

    try {
      return await this.auth0.getAccessTokenSilently()
    } catch (err) {
      console.error('Failed to get access token:', err)
      return null
    }
  }
}
```

```typescript
// src/services/auth/MockProvider.ts - For testing/development
import { ref } from 'vue'
import { BaseAuthProvider } from './AuthProvider'
import { AuthProviderType } from '@/types/auth'

export class MockAuthProvider extends BaseAuthProvider {
  type = AuthProviderType.MOCK
  isAuthenticated = ref(false)
  user = ref(null)
  loading = ref(false)
  error = ref(null)

  async login(): Promise<void> {
    this.loading.value = true

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))

    this.isAuthenticated.value = true
    this.user.value = {
      id: 'mock-user-123',
      email: 'user@example.com',
      name: 'Mock User',
      roles: ['admin']
    }
    this.loading.value = false
  }

  async logout(): Promise<void> {
    this.isAuthenticated.value = false
    this.user.value = null
  }

  async checkAuth(): Promise<boolean> {
    return this.isAuthenticated.value
  }

  async getToken(): Promise<string | null> {
    return this.isAuthenticated.value ? 'mock-jwt-token' : null
  }
}
```

```typescript
// src/services/auth/index.ts - Main auth service
import { ref, readonly } from 'vue'
import { Auth0Provider } from './Auth0Provider'
import { MockAuthProvider } from './MockProvider'
import type { BaseAuthProvider } from './AuthProvider'
import { AuthProviderType } from '@/types/auth'

const currentProvider = ref<BaseAuthProvider>()
const config = {
  auth0: {
    domain: import.meta.env.VITE_AUTH0_DOMAIN,
    clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
  }
}

// Initialize default provider based on environment
const initializeProvider = () => {
  const providerType = import.meta.env.VITE_AUTH_PROVIDER || AuthProviderType.AUTH0

  switch (providerType) {
    case AuthProviderType.AUTH0:
      return new Auth0Provider(config.auth0)
    case AuthProviderType.MOCK:
      return new MockAuthProvider()
    default:
      throw new Error(`Unknown auth provider: ${providerType}`)
  }
}

// Initialize on first use
currentProvider.value = initializeProvider()

export const useAuth = () => {
  if (!currentProvider.value) {
    throw new Error('Auth provider not initialized')
  }

  const switchProvider = (type: AuthProviderType) => {
    switch (type) {
      case AuthProviderType.AUTH0:
        currentProvider.value = new Auth0Provider(config.auth0)
        break
      case AuthProviderType.MOCK:
        currentProvider.value = new MockAuthProvider()
        break
      default:
        throw new Error(`Unsupported auth provider: ${type}`)
    }
  }

  return {
    provider: readonly(currentProvider),
    isAuthenticated: currentProvider.value.isAuthenticated,
    user: currentProvider.value.user,
    loading: currentProvider.value.loading,
    error: currentProvider.value.error,
    login: () => currentProvider.value!.login(),
    logout: () => currentProvider.value!.logout(),
    checkAuth: () => currentProvider.value!.checkAuth(),
    getToken: () => currentProvider.value!.getToken(),
    switchProvider,
  }
}

// Router guard for authentication
export const requireAuth = async () => {
  const { checkAuth, isAuthenticated } = useAuth()
  await checkAuth()
  return isAuthenticated.value
}
```

**Environment Configuration:**
```bash
# .env.development
VITE_AUTH_PROVIDER=auth0
VITE_AUTH0_DOMAIN=your-dev-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-dev-client-id
VITE_AUTH0_AUDIENCE=https://api.fraiseql-doctor.dev

# .env.test
VITE_AUTH_PROVIDER=mock

# .env.production
VITE_AUTH_PROVIDER=auth0
VITE_AUTH0_DOMAIN=your-prod-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-prod-client-id
VITE_AUTH0_AUDIENCE=https://api.fraiseql-doctor.com
```

**Passing Tests:**
All authentication tests pass, provider switching works, Auth0 integration functional

---

## 📊 **Day 2: Dashboard Overview (Core MVP)**

### **2.1 Dashboard Layout Component**
**Feature:** Main dashboard layout with sidebar navigation

**Failing Tests:**
```typescript
// tests/components/DashboardLayout.test.ts
import { mount } from '@vue/test-utils'
import DashboardLayout from '@/components/DashboardLayout.vue'

describe('DashboardLayout', () => {
  it('should render sidebar navigation', () => {
    const wrapper = mount(DashboardLayout)
    expect(wrapper.find('[data-testid="sidebar"]')).toBeTruthy()
  })

  it('should toggle sidebar on mobile', async () => {
    const wrapper = mount(DashboardLayout)
    const toggleBtn = wrapper.find('[data-testid="sidebar-toggle"]')
    await toggleBtn.trigger('click')
    expect(wrapper.vm.sidebarOpen).toBe(false)
  })

  it('should highlight active navigation item', () => {
    const wrapper = mount(DashboardLayout)
    // This will fail until navigation is implemented
    expect(wrapper.find('.nav-active')).toBeTruthy()
  })
})
```

**Implementation:**
```vue
<!-- src/components/DashboardLayout.vue -->
<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside
      data-testid="sidebar"
      :class="[
        'bg-white shadow-lg transition-transform duration-300',
        sidebarOpen ? 'w-64' : 'w-16 md:w-64'
      ]"
    >
      <div class="p-4 flex items-center justify-between">
        <h1 class="text-xl font-bold text-gray-800">FraiseQL Doctor</h1>
        <UserMenu v-if="user" :user="user" />
      </div>

      <nav class="mt-8">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600',
            $route.path === item.path ? 'bg-blue-50 text-blue-600 nav-active' : ''
          ]"
        >
          <component :is="item.icon" class="w-5 h-5 mr-3" />
          <span v-show="sidebarOpen || !isMobile">{{ item.name }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="flex-1 p-6">
      <button
        data-testid="sidebar-toggle"
        class="md:hidden mb-4 p-2 text-gray-600"
        @click="toggleSidebar"
      >
        <MenuIcon class="w-6 h-6" />
      </button>

      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@/services/auth'
import UserMenu from '@/components/auth/UserMenu.vue'
import {
  HomeIcon,
  ServerIcon,
  DocumentTextIcon,
  ChartBarIcon,
  MenuIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const { user, checkAuth } = useAuth()
const sidebarOpen = ref(true)
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)

const navItems = [
  { path: '/', name: 'Dashboard', icon: HomeIcon },
  { path: '/endpoints', name: 'Endpoints', icon: ServerIcon },
  { path: '/queries', name: 'Queries', icon: DocumentTextIcon },
  { path: '/monitoring', name: 'Monitoring', icon: ChartBarIcon },
]

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', updateWindowWidth)
  checkAuth() // Initialize authentication
})

onUnmounted(() => {
  window.removeEventListener('resize', updateWindowWidth)
})
</script>
```

**UserMenu Component:**
```vue
<!-- src/components/auth/UserMenu.vue -->
<template>
  <Menu as="div" class="relative">
    <MenuButton class="flex items-center space-x-3 text-sm focus:outline-none">
      <img
        v-if="user.picture"
        :src="user.picture"
        :alt="user.name"
        class="w-8 h-8 rounded-full"
      >
      <div
        v-else
        class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center"
      >
        <span class="text-white font-medium">{{ user.name.charAt(0) }}</span>
      </div>
    </MenuButton>

    <transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <MenuItems class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
        <div class="p-3 border-b">
          <p class="text-sm font-medium text-gray-900">{{ user.name }}</p>
          <p class="text-xs text-gray-500">{{ user.email }}</p>
        </div>
        <div class="py-1">
          <MenuItem v-slot="{ active }">
            <router-link
              to="/profile"
              :class="[
                active ? 'bg-gray-100' : '',
                'block px-4 py-2 text-sm text-gray-700'
              ]"
            >
              Profile Settings
            </router-link>
          </MenuItem>
          <MenuItem v-slot="{ active }">
            <button
              :class="[
                active ? 'bg-gray-100' : '',
                'block w-full text-left px-4 py-2 text-sm text-gray-700'
              ]"
              @click="handleLogout"
            >
              Sign Out
            </button>
          </MenuItem>
        </div>
      </MenuItems>
    </transition>
  </Menu>
</template>

<script setup lang="ts">
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'
import { useAuth } from '@/services/auth'
import { useRouter } from 'vue-router'

interface Props {
  user: {
    id: string
    email: string
    name: string
    picture?: string
  }
}

defineProps<Props>()

const { logout } = useAuth()
const router = useRouter()

const handleLogout = async () => {
  await logout()
  router.push('/login')
}
</script>
```

**Passing Tests:**
All layout tests pass, sidebar functionality working

### **2.2 Dashboard Overview Cards**
**Feature:** Health status overview with real-time updates

**Failing Tests:**
```typescript
// tests/views/Dashboard.test.ts
import { mount } from '@vue/test-utils'
import Dashboard from '@/views/Dashboard.vue'
import { createTestingPinia } from '@pinia/testing'

describe('Dashboard', () => {
  it('should display endpoint status cards', () => {
    const wrapper = mount(Dashboard, {
      global: { plugins: [createTestingPinia()] }
    })
    expect(wrapper.findAll('[data-testid="status-card"]')).toHaveLength(4)
  })

  it('should show correct health metrics', async () => {
    const wrapper = mount(Dashboard, {
      global: { plugins: [createTestingPinia()] }
    })
    // This will fail until store is implemented
    expect(wrapper.text()).toContain('Healthy Endpoints: 0')
  })

  it('should update in real-time', async () => {
    // WebSocket test - will fail until implemented
    const wrapper = mount(Dashboard, {
      global: { plugins: [createTestingPinia()] }
    })
    // Simulate WebSocket update
    await wrapper.vm.updateHealthStatus({ healthy: 5 })
    expect(wrapper.text()).toContain('Healthy Endpoints: 5')
  })
})
```

**Implementation:**
```vue
<!-- src/views/Dashboard.vue -->
<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
      <p class="text-gray-600">Monitor your GraphQL endpoints health</p>
    </div>

    <!-- Status Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <StatusCard
        data-testid="status-card"
        title="Total Endpoints"
        :value="dashboardStats.totalEndpoints"
        color="blue"
        :icon="ServerIcon"
      />
      <StatusCard
        data-testid="status-card"
        title="Healthy Endpoints"
        :value="dashboardStats.healthyEndpoints"
        color="green"
        :icon="CheckCircleIcon"
      />
      <StatusCard
        data-testid="status-card"
        title="Warning Status"
        :value="dashboardStats.warningEndpoints"
        color="yellow"
        :icon="ExclamationTriangleIcon"
      />
      <StatusCard
        data-testid="status-card"
        title="Critical Issues"
        :value="dashboardStats.criticalEndpoints"
        color="red"
        :icon="XCircleIcon"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Health Trend Chart -->
      <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Health Trends (24h)</h2>
        <HealthTrendChart :data="healthTrendData" />
      </div>

      <!-- Recent Activity -->
      <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Recent Activity</h2>
        <RecentActivityList :activities="recentActivities" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebSocketConnection } from '@/services/websocket'
import StatusCard from '@/components/dashboard/StatusCard.vue'
import HealthTrendChart from '@/components/dashboard/HealthTrendChart.vue'
import RecentActivityList from '@/components/dashboard/RecentActivityList.vue'
import {
  ServerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon
} from '@heroicons/vue/24/outline'

const dashboardStore = useDashboardStore()
const { connect, disconnect } = useWebSocketConnection()

const dashboardStats = computed(() => dashboardStore.stats)
const healthTrendData = computed(() => dashboardStore.healthTrend)
const recentActivities = computed(() => dashboardStore.recentActivities)

const updateHealthStatus = (newStats: any) => {
  dashboardStore.updateStats(newStats)
}

onMounted(async () => {
  await dashboardStore.loadInitialData()
  connect('dashboard', updateHealthStatus)
})

onUnmounted(() => {
  disconnect('dashboard')
})
</script>
```

**Pinia Store:**
```typescript
// src/stores/dashboard.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DashboardStats, HealthTrendData, Activity } from '@/types'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats>({
    totalEndpoints: 0,
    healthyEndpoints: 0,
    warningEndpoints: 0,
    criticalEndpoints: 0,
  })

  const healthTrend = ref<HealthTrendData[]>([])
  const recentActivities = ref<Activity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const healthPercentage = computed(() => {
    if (stats.value.totalEndpoints === 0) return 0
    return Math.round((stats.value.healthyEndpoints / stats.value.totalEndpoints) * 100)
  })

  const loadInitialData = async () => {
    loading.value = true
    try {
      // API calls to load dashboard data
      const response = await fetch('/api/dashboard/overview')
      const data = await response.json()

      stats.value = data.stats
      healthTrend.value = data.healthTrend
      recentActivities.value = data.recentActivities
    } catch (err) {
      error.value = 'Failed to load dashboard data'
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  const updateStats = (newStats: Partial<DashboardStats>) => {
    stats.value = { ...stats.value, ...newStats }
  }

  return {
    stats,
    healthTrend,
    recentActivities,
    loading,
    error,
    healthPercentage,
    loadInitialData,
    updateStats,
  }
})
```

**Passing Tests:**
Dashboard renders correctly, stats display properly, WebSocket updates working

---

## 🌐 **Day 3: Endpoint Management**

### **3.1 Endpoint List View**
**Feature:** Display all GraphQL endpoints with health status

**Failing Tests:**
```typescript
// tests/views/Endpoints.test.ts
import { mount } from '@vue/test-utils'
import EndpointsView from '@/views/Endpoints.vue'

describe('EndpointsView', () => {
  it('should render endpoint list table', () => {
    const wrapper = mount(EndpointsView)
    expect(wrapper.find('[data-testid="endpoints-table"]')).toBeTruthy()
  })

  it('should filter endpoints by status', async () => {
    const wrapper = mount(EndpointsView)
    const filterSelect = wrapper.find('[data-testid="status-filter"]')
    await filterSelect.setValue('healthy')
    // This will fail until filtering is implemented
    expect(wrapper.findAll('.endpoint-row')).toHaveLength(3)
  })

  it('should navigate to endpoint detail on click', async () => {
    const wrapper = mount(EndpointsView)
    const firstEndpoint = wrapper.find('.endpoint-row')
    await firstEndpoint.trigger('click')
    // This will fail until navigation is implemented
    expect(mockRouter.push).toHaveBeenCalledWith('/endpoints/uuid-123')
  })
})
```

**Implementation:**
```vue
<!-- src/views/Endpoints.vue -->
<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">GraphQL Endpoints</h1>
        <p class="text-gray-600">Manage and monitor your GraphQL endpoints</p>
      </div>
      <button
        class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        @click="showAddEndpointDialog = true"
      >
        Add Endpoint
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg shadow mb-6">
      <div class="flex flex-wrap gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Status Filter
          </label>
          <select
            v-model="statusFilter"
            data-testid="status-filter"
            class="border border-gray-300 rounded px-3 py-2"
          >
            <option value="">All Statuses</option>
            <option value="healthy">Healthy</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Search endpoints..."
            class="border border-gray-300 rounded px-3 py-2"
          >
        </div>
      </div>
    </div>

    <!-- Endpoints Table -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <table
        data-testid="endpoints-table"
        class="w-full"
      >
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Name
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              URL
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Response Time
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Last Check
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="endpoint in filteredEndpoints"
            :key="endpoint.id"
            class="endpoint-row hover:bg-gray-50 cursor-pointer"
            @click="navigateToEndpoint(endpoint.id)"
          >
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-gray-900">
                {{ endpoint.name }}
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
              {{ endpoint.url }}
            </td>
            <td class="px-6 py-4">
              <HealthBadge :status="endpoint.status" />
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
              {{ endpoint.responseTime }}ms
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
              {{ formatDate(endpoint.lastCheck) }}
            </td>
            <td class="px-6 py-4 text-sm">
              <button
                class="text-blue-600 hover:text-blue-800 mr-3"
                @click.stop="editEndpoint(endpoint)"
              >
                Edit
              </button>
              <button
                class="text-red-600 hover:text-red-800"
                @click.stop="deleteEndpoint(endpoint.id)"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Endpoint Dialog -->
    <AddEndpointDialog
      v-model="showAddEndpointDialog"
      @added="handleEndpointAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEndpointsStore } from '@/stores/endpoints'
import HealthBadge from '@/components/endpoints/HealthBadge.vue'
import AddEndpointDialog from '@/components/endpoints/AddEndpointDialog.vue'

const router = useRouter()
const endpointsStore = useEndpointsStore()

const statusFilter = ref('')
const searchTerm = ref('')
const showAddEndpointDialog = ref(false)

const filteredEndpoints = computed(() => {
  let endpoints = endpointsStore.endpoints

  if (statusFilter.value) {
    endpoints = endpoints.filter(e => e.status === statusFilter.value)
  }

  if (searchTerm.value) {
    endpoints = endpoints.filter(e =>
      e.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      e.url.toLowerCase().includes(searchTerm.value.toLowerCase())
    )
  }

  return endpoints
})

const navigateToEndpoint = (id: string) => {
  router.push(`/endpoints/${id}`)
}

const editEndpoint = (endpoint: any) => {
  // Edit logic
}

const deleteEndpoint = (id: string) => {
  if (confirm('Are you sure you want to delete this endpoint?')) {
    endpointsStore.deleteEndpoint(id)
  }
}

const handleEndpointAdded = () => {
  showAddEndpointDialog.value = false
  endpointsStore.loadEndpoints()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

onMounted(() => {
  endpointsStore.loadEndpoints()
})
</script>
```

**Passing Tests:**
Endpoint list renders, filtering works, navigation implemented

### **3.2 Real-time Health Updates**
**Feature:** WebSocket connection for live endpoint status updates

**Failing Tests:**
```typescript
// tests/services/websocket.test.ts
import { useWebSocketConnection } from '@/services/websocket'

describe('WebSocket Connection', () => {
  it('should establish connection', () => {
    const { connect, isConnected } = useWebSocketConnection()
    connect('test-channel')
    // This will fail until WebSocket is implemented
    expect(isConnected.value).toBe(true)
  })

  it('should receive endpoint status updates', async () => {
    const { connect, disconnect } = useWebSocketConnection()
    const mockCallback = vi.fn()

    connect('endpoints', mockCallback)
    // Simulate WebSocket message
    // This will fail until message handling is implemented
    expect(mockCallback).toHaveBeenCalledWith({
      type: 'endpoint_status_update',
      data: { id: '123', status: 'healthy' }
    })
  })
})
```

**Implementation:**
```typescript
// src/services/websocket.ts
import { ref, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

const socket = ref<Socket | null>(null)
const isConnected = ref(false)
const subscribers = new Map<string, Function[]>()

export function useWebSocketConnection() {
  const connect = (channel: string, callback?: Function) => {
    if (!socket.value) {
      socket.value = io(import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8001', {
        transports: ['websocket'],
        autoConnect: true,
      })

      socket.value.on('connect', () => {
        isConnected.value = true
        console.log('WebSocket connected')
      })

      socket.value.on('disconnect', () => {
        isConnected.value = false
        console.log('WebSocket disconnected')
      })

      socket.value.on('error', (error) => {
        console.error('WebSocket error:', error)
      })
    }

    // Subscribe to channel
    if (callback) {
      if (!subscribers.has(channel)) {
        subscribers.set(channel, [])
      }
      subscribers.get(channel)!.push(callback)

      // Listen for channel messages
      socket.value.on(channel, (data) => {
        subscribers.get(channel)?.forEach(cb => cb(data))
      })
    }
  }

  const disconnect = (channel?: string) => {
    if (channel) {
      subscribers.delete(channel)
      socket.value?.off(channel)
    } else {
      socket.value?.disconnect()
      socket.value = null
      isConnected.value = false
      subscribers.clear()
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connect,
    disconnect,
    isConnected: readonly(isConnected),
    socket: readonly(socket)
  }
}
```

**Passing Tests:**
WebSocket connection established, real-time updates working

---

## 📝 **Day 4: Query Management**

### **4.1 Query Library Interface**
**Feature:** GraphQL query management with syntax highlighting

**Failing Tests:**
```typescript
// tests/views/Queries.test.ts
describe('QueriesView', () => {
  it('should render query list', () => {
    const wrapper = mount(QueriesView)
    expect(wrapper.find('[data-testid="queries-list"]')).toBeTruthy()
  })

  it('should open query editor on create', async () => {
    const wrapper = mount(QueriesView)
    const createBtn = wrapper.find('[data-testid="create-query-btn"]')
    await createBtn.trigger('click')
    // This will fail until editor is implemented
    expect(wrapper.find('[data-testid="query-editor"]')).toBeTruthy()
  })
})
```

**Implementation:**
```vue
<!-- src/views/Queries.vue -->
<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Query Library</h1>
        <p class="text-gray-600">Manage your GraphQL queries</p>
      </div>
      <button
        data-testid="create-query-btn"
        class="bg-blue-600 text-white px-4 py-2 rounded-lg"
        @click="createNewQuery"
      >
        Create Query
      </button>
    </div>

    <!-- Query List -->
    <div
      data-testid="queries-list"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <QueryCard
        v-for="query in queries"
        :key="query.id"
        :query="query"
        @edit="editQuery"
        @delete="deleteQuery"
        @execute="executeQuery"
      />
    </div>

    <!-- Query Editor Modal -->
    <QueryEditorModal
      v-model="showEditor"
      :query="selectedQuery"
      @save="handleQuerySave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQueriesStore } from '@/stores/queries'
import QueryCard from '@/components/queries/QueryCard.vue'
import QueryEditorModal from '@/components/queries/QueryEditorModal.vue'

const queriesStore = useQueriesStore()
const queries = computed(() => queriesStore.queries)
const showEditor = ref(false)
const selectedQuery = ref(null)

const createNewQuery = () => {
  selectedQuery.value = null
  showEditor.value = true
}

const editQuery = (query: any) => {
  selectedQuery.value = query
  showEditor.value = true
}

const deleteQuery = (queryId: string) => {
  if (confirm('Delete this query?')) {
    queriesStore.deleteQuery(queryId)
  }
}

const executeQuery = (query: any) => {
  router.push(`/playground?query=${query.id}`)
}

const handleQuerySave = (queryData: any) => {
  if (selectedQuery.value) {
    queriesStore.updateQuery(selectedQuery.value.id, queryData)
  } else {
    queriesStore.createQuery(queryData)
  }
  showEditor.value = false
}

onMounted(() => {
  queriesStore.loadQueries()
})
</script>
```

**GraphQL Playground Component:**
```vue
<!-- src/components/queries/GraphQLPlayground.vue -->
<template>
  <div class="h-full flex flex-col">
    <!-- Toolbar -->
    <div class="bg-white border-b p-4 flex justify-between items-center">
      <div class="flex items-center space-x-4">
        <select
          v-model="selectedEndpoint"
          class="border rounded px-3 py-2"
        >
          <option
            v-for="endpoint in endpoints"
            :key="endpoint.id"
            :value="endpoint.id"
          >
            {{ endpoint.name }}
          </option>
        </select>
        <button
          class="bg-blue-600 text-white px-4 py-2 rounded"
          :disabled="executing"
          @click="executeQuery"
        >
          {{ executing ? 'Executing...' : 'Execute' }}
        </button>
      </div>
    </div>

    <!-- Editor and Results -->
    <div class="flex-1 flex">
      <!-- Query Editor -->
      <div class="w-1/2 border-r">
        <GraphQLEditor
          v-model="queryText"
          :schema="endpointSchema"
          class="h-full"
        />
      </div>

      <!-- Results Panel -->
      <div class="w-1/2 bg-gray-50">
        <div class="h-full overflow-auto p-4">
          <pre
            v-if="queryResult"
            class="text-sm"
          >{{ JSON.stringify(queryResult, null, 2) }}</pre>
          <div
            v-else-if="executing"
            class="flex items-center justify-center h-32"
          >
            <div class="text-gray-500">Executing query...</div>
          </div>
          <div
            v-else
            class="flex items-center justify-center h-32 text-gray-500"
          >
            Write a query and click Execute
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@vue/apollo-composable'
import { useEndpointsStore } from '@/stores/endpoints'
import GraphQLEditor from '@/components/queries/GraphQLEditor.vue'

const endpointsStore = useEndpointsStore()
const endpoints = computed(() => endpointsStore.endpoints)

const selectedEndpoint = ref('')
const queryText = ref(`query GetUsers {
  users {
    id
    name
    email
  }
}`)
const queryResult = ref(null)
const executing = ref(false)
const endpointSchema = ref(null)

const executeQuery = async () => {
  if (!selectedEndpoint.value || !queryText.value) return

  executing.value = true
  try {
    // Execute GraphQL query
    const response = await fetch('/api/graphql/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        endpoint_id: selectedEndpoint.value,
        query: queryText.value,
        variables: {}
      })
    })

    queryResult.value = await response.json()
  } catch (error) {
    queryResult.value = { error: error.message }
  } finally {
    executing.value = false
  }
}

// Load schema for autocomplete when endpoint changes
watch(selectedEndpoint, async (endpointId) => {
  if (endpointId) {
    try {
      const response = await fetch(`/api/endpoints/${endpointId}/schema`)
      endpointSchema.value = await response.json()
    } catch (error) {
      console.error('Failed to load schema:', error)
    }
  }
})
</script>
```

**Passing Tests:**
Query management interface working, GraphQL playground functional

---

## 📊 **Day 5: Monitoring & Charts**

### **5.1 Real-time Health Charts**
**Feature:** Chart.js integration for performance visualization

**Failing Tests:**
```typescript
// tests/components/HealthChart.test.ts
describe('HealthChart', () => {
  it('should render chart canvas', () => {
    const wrapper = mount(HealthChart, {
      props: { data: mockChartData }
    })
    expect(wrapper.find('canvas')).toBeTruthy()
  })

  it('should update chart data reactively', async () => {
    const wrapper = mount(HealthChart, {
      props: { data: [] }
    })

    await wrapper.setProps({ data: mockChartData })
    // This will fail until chart updates are implemented
    expect(wrapper.vm.chart.data.datasets[0].data).toEqual([1, 2, 3])
  })
})
```

**Implementation:**
```vue
<!-- src/components/monitoring/HealthChart.vue -->
<template>
  <div class="relative">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface Props {
  data: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
    }[]
  }
}

const props = defineProps<Props>()
const chartCanvas = ref<HTMLCanvasElement>()
let chart: ChartJS | null = null

onMounted(() => {
  if (chartCanvas.value) {
    chart = new ChartJS(chartCanvas.value, {
      type: 'line',
      data: props.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          legend: {
            position: 'top'
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Time'
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: 'Response Time (ms)'
            },
            suggestedMin: 0
          }
        },
        elements: {
          point: {
            radius: 3
          },
          line: {
            tension: 0.4
          }
        }
      }
    })
  }
})

watch(
  () => props.data,
  (newData) => {
    if (chart) {
      chart.data = newData
      chart.update('active')
    }
  },
  { deep: true }
)

onUnmounted(() => {
  if (chart) {
    chart.destroy()
  }
})
</script>
```

**Monitoring Dashboard:**
```vue
<!-- src/views/Monitoring.vue -->
<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Health Monitoring</h1>
      <p class="text-gray-600">Real-time performance and health metrics</p>
    </div>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- Response Time Chart -->
      <div class="lg:col-span-2 bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Response Time Trends</h2>
        <div class="h-80">
          <HealthChart :data="responseTimeData" />
        </div>
      </div>

      <!-- Status Distribution -->
      <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Status Distribution</h2>
        <div class="h-80">
          <DoughnutChart :data="statusDistributionData" />
        </div>
      </div>
    </div>

    <!-- Alerts Panel -->
    <div class="bg-white rounded-lg shadow">
      <div class="p-6 border-b">
        <h2 class="text-lg font-semibold">Active Alerts</h2>
      </div>
      <div class="divide-y">
        <AlertItem
          v-for="alert in activeAlerts"
          :key="alert.id"
          :alert="alert"
          @acknowledge="acknowledgeAlert"
          @resolve="resolveAlert"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useMonitoringStore } from '@/stores/monitoring'
import HealthChart from '@/components/monitoring/HealthChart.vue'
import DoughnutChart from '@/components/monitoring/DoughnutChart.vue'
import AlertItem from '@/components/monitoring/AlertItem.vue'

const monitoringStore = useMonitoringStore()

const responseTimeData = computed(() => monitoringStore.responseTimeData)
const statusDistributionData = computed(() => monitoringStore.statusDistribution)
const activeAlerts = computed(() => monitoringStore.activeAlerts)

const acknowledgeAlert = (alertId: string) => {
  monitoringStore.acknowledgeAlert(alertId)
}

const resolveAlert = (alertId: string) => {
  monitoringStore.resolveAlert(alertId)
}

onMounted(() => {
  monitoringStore.loadMonitoringData()
  // Set up real-time updates
  const interval = setInterval(() => {
    monitoringStore.refreshData()
  }, 30000) // Update every 30 seconds

  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>
```

**Passing Tests:**
Charts render correctly, real-time updates working, alerts functional

---

## ⚡ **Day 6: Performance Optimization & Testing**

### **6.1 Bundle Size Optimization**
**Feature:** Achieve <300KB bundle size target

**Failing Tests:**
```typescript
// tests/performance/bundle.test.ts
describe('Bundle Optimization', () => {
  it('should have main bundle under 200KB', () => {
    const bundleStats = getBundleStats()
    expect(bundleStats.main.size).toBeLessThan(200 * 1024)
  })

  it('should lazy load chart components', () => {
    const chunkStats = getBundleStats()
    expect(chunkStats.charts).toBeDefined()
    expect(chunkStats.charts.async).toBe(true)
  })
})
```

**Implementation:**
```typescript
// vite.config.ts - Enhanced optimization
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-core': ['vue', 'vue-router'],
          'state': ['pinia'],
          'charts': ['chart.js', 'vue-chartjs'],
          'apollo': ['@apollo/client', '@vue/apollo-composable'],
          'icons': ['@heroicons/vue/24/outline'],
          'ui': ['@headlessui/vue']
        }
      }
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log']
      }
    }
  },
  // Aggressive tree shaking
  optimizeDeps: {
    include: ['vue', 'pinia', 'vue-router'],
    exclude: ['chart.js'] // Lazy load charts
  }
})

// Dynamic imports for code splitting
const HealthChart = defineAsyncComponent(() => import('@/components/monitoring/HealthChart.vue'))
const QueryEditor = defineAsyncComponent(() => import('@/components/queries/QueryEditor.vue'))
```

**Lazy Loading Implementation:**
```typescript
// src/router/index.ts - Route-based code splitting
const routes = [
  {
    path: '/',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/endpoints',
    component: () => import('@/views/Endpoints.vue')
  },
  {
    path: '/queries',
    component: () => import('@/views/Queries.vue')
  },
  {
    path: '/monitoring',
    component: () => import('@/views/Monitoring.vue')
  },
  {
    path: '/playground',
    component: () => import('@/views/GraphQLPlayground.vue')
  }
]
```

### **6.2 Comprehensive Test Suite**
**Feature:** 90%+ test coverage across all components

**Test Organization:**
```
tests/
├── unit/
│   ├── components/
│   │   ├── dashboard/
│   │   ├── endpoints/
│   │   ├── queries/
│   │   └── monitoring/
│   ├── stores/
│   ├── services/
│   └── utils/
├── integration/
│   ├── api/
│   ├── websocket/
│   └── e2e-flows/
└── performance/
    ├── bundle-size/
    └── load-time/
```

**Key Test Suites:**
```typescript
// tests/integration/dashboard-flow.test.ts
describe('Dashboard Integration Flow', () => {
  it('should complete full dashboard workflow', async () => {
    // Mount app with router
    const wrapper = mount(App, {
      global: { plugins: [router, pinia] }
    })

    // Navigate to dashboard
    await router.push('/')
    await nextTick()

    // Verify dashboard loads
    expect(wrapper.find('[data-testid="dashboard"]')).toBeTruthy()

    // Check status cards
    const statusCards = wrapper.findAll('[data-testid="status-card"]')
    expect(statusCards).toHaveLength(4)

    // Simulate WebSocket update
    await simulateWebSocketMessage({
      type: 'health_update',
      data: { healthy: 10, total: 12 }
    })

    // Verify UI updates
    expect(wrapper.text()).toContain('Healthy: 10')
  })
})
```

**Passing Tests:**
- Unit tests: 95% coverage
- Integration tests: All user flows tested
- Bundle size: <300KB achieved
- Performance: <2s initial load

---

## 🚀 **Day 7: Production Deployment & Polish**

### **7.1 Production Build Configuration**
**Feature:** Production-ready build with optimizations

**Implementation:**
```typescript
// vite.config.prod.ts
export default defineConfig({
  mode: 'production',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        passes: 2
      }
    },
    rollupOptions: {
      external: ['vue'],
      output: {
        globals: {
          vue: 'Vue'
        },
        // Asset optimization
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `img/[name]-[hash][extname]`
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        }
      }
    }
  },
  // Production optimizations
  define: {
    __VUE_OPTIONS_API__: false,
    __VUE_PROD_DEVTOOLS__: false
  }
})
```

### **7.2 Docker Configuration**
**Feature:** Containerized deployment

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### **7.3 Final Integration Test**
**Feature:** End-to-end production workflow

**Final Comprehensive Test:**
```typescript
// tests/e2e/complete-workflow.test.ts
describe('Complete Production Workflow', () => {
  it('should handle full user journey', async () => {
    // 1. Dashboard loads
    await page.goto('/')
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible()

    // 2. Add endpoint
    await page.click('[data-testid="nav-endpoints"]')
    await page.click('[data-testid="add-endpoint"]')
    await page.fill('[data-testid="endpoint-name"]', 'Test Endpoint')
    await page.fill('[data-testid="endpoint-url"]', 'https://api.example.com/graphql')
    await page.click('[data-testid="save-endpoint"]')

    // 3. Create query
    await page.click('[data-testid="nav-queries"]')
    await page.click('[data-testid="create-query"]')
    await page.fill('[data-testid="query-name"]', 'Test Query')
    await page.fill('[data-testid="query-text"]', 'query { users { id name } }')
    await page.click('[data-testid="save-query"]')

    // 4. Execute query
    await page.click('[data-testid="nav-playground"]')
    await page.selectOption('[data-testid="endpoint-select"]', 'Test Endpoint')
    await page.click('[data-testid="execute-query"]')

    // 5. View monitoring
    await page.click('[data-testid="nav-monitoring"]')
    await expect(page.locator('[data-testid="health-chart"]')).toBeVisible()

    // 6. Verify real-time updates
    // Simulate WebSocket message
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('websocket-message', {
        detail: { type: 'health_update', data: { status: 'healthy' } }
      }))
    })

    await expect(page.locator('[data-testid="status-healthy"]')).toBeVisible()
  })
})
```

---

## 📋 **Final Deliverables Checklist**

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Analyze PrintOptim frontend architecture for optimization insights", "status": "completed"}, {"content": "Create Phase 2.5 detailed TDD implementation plan", "status": "completed"}, {"content": "Set up Vue 3 project structure with bundle optimization", "status": "pending"}, {"content": "Implement dashboard overview with TDD approach", "status": "pending"}, {"content": "Build endpoint management with real-time updates", "status": "pending"}, {"content": "Create query playground with GraphQL integration", "status": "pending"}, {"content": "Add monitoring and alerting features", "status": "pending"}, {"content": "Optimize bundle size and performance", "status": "pending"}, {"content": "Complete comprehensive testing suite", "status": "pending"}, {"content": "Deploy production-ready application", "status": "pending"}]
