import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

// These imports will fail until we implement them
import DashboardLayout from '@/components/DashboardLayout.vue'
import { useAuth, resetAuthForTesting } from '@/services/auth/useAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } },
    { path: '/endpoints', component: { template: '<div>Endpoints</div>' } }
  ]
})

const mockUser = {
  id: '123',
  name: 'John Doe',
  email: 'john@example.com',
  picture: 'https://example.com/avatar.jpg'
}

describe('Dashboard Layout', () => {
  let wrapper: VueWrapper

  beforeEach(() => {
    setActivePinia(createPinia())
    resetAuthForTesting() // Reset auth state before each test
  })

  it('should render sidebar navigation', () => {
    // This will fail until DashboardLayout component exists
    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    const sidebar = wrapper.find('[data-testid="sidebar"]')
    expect(sidebar.exists()).toBeTruthy()
  })

  it('should toggle sidebar on mobile', async () => {
    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    const toggleButton = wrapper.find('[data-testid="sidebar-toggle"]')
    expect(toggleButton.exists()).toBeTruthy()

    // Should start with sidebar closed on mobile
    expect(wrapper.vm.sidebarOpen).toBe(false)

    // Click toggle
    await toggleButton.trigger('click')
    expect(wrapper.vm.sidebarOpen).toBe(true)
  })

  it('should display user menu when authenticated', async () => {
    // Login first, then mount component
    const { login, isAuthenticated, user } = useAuth()
    await login()

    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    // Check that auth state is correct
    expect(isAuthenticated.value).toBe(true)
    expect(user.value).toBeDefined()

    const userMenu = wrapper.find('[data-testid="user-menu"]')
    expect(userMenu.exists()).toBeTruthy()
  })

  it('should hide user menu when not authenticated', () => {
    // Default state should be unauthenticated
    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    const userMenu = wrapper.find('[data-testid="user-menu"]')
    expect(userMenu.exists()).toBeFalsy()
  })

  it('should have responsive design classes', () => {
    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    // Should have proper responsive classes
    const sidebar = wrapper.find('[data-testid="sidebar"]')
    expect(sidebar.classes()).toContain('w-64') // Desktop width
  })

  it('should render navigation links', () => {
    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    // Should have main navigation links
    const dashboardLink = wrapper.find('[data-testid="nav-dashboard"]')
    expect(dashboardLink.exists()).toBeTruthy()

    const endpointsLink = wrapper.find('[data-testid="nav-endpoints"]')
    expect(endpointsLink.exists()).toBeTruthy()
  })

  it('should handle user logout', async () => {
    wrapper = mount(DashboardLayout, {
      global: {
        plugins: [createPinia(), router]
      }
    })

    // Login first so we can test logout
    const { login, isAuthenticated } = useAuth()
    await login()
    await wrapper.vm.$nextTick()

    // Find and click logout button
    const logoutButton = wrapper.find('[data-testid="logout-button"]')
    expect(logoutButton.exists()).toBeTruthy()

    await logoutButton.trigger('click')

    // Wait a bit for logout to process (MockProvider has a 50ms delay)
    await new Promise(resolve => setTimeout(resolve, 100))
    await wrapper.vm.$nextTick()

    // Should be logged out now
    expect(isAuthenticated.value).toBe(false)
  })
})
