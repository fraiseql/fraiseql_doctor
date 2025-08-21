import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  GraphQLEndpoint, 
  CreateEndpointInput, 
  UpdateEndpointInput, 
  EndpointTestResult 
} from '../types/endpoint'
import { EndpointStatus } from '../types/endpoint'
import { useGraphQLClient } from '../services/graphql/client'

export const useEndpointsStore = defineStore('endpoints', () => {
  // State
  const endpoints = ref<GraphQLEndpoint[]>([])
  const selectedEndpoint = ref<GraphQLEndpoint | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Services
  const { testEndpoint: testEndpointConnectivity, getIntrospectionSchema } = useGraphQLClient()

  // Getters
  const healthyEndpointsCount = computed(() => 
    endpoints.value.filter(endpoint => endpoint.isHealthy).length
  )

  const unhealthyEndpointsCount = computed(() => 
    endpoints.value.filter(endpoint => !endpoint.isHealthy).length
  )

  const activeEndpoints = computed(() => 
    endpoints.value.filter(endpoint => endpoint.status === EndpointStatus.ACTIVE)
  )

  // Actions
  async function loadEndpoints() {
    isLoading.value = true
    error.value = null

    try {
      // In a real app, this would fetch from an API
      // For now, we'll use mock data
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API delay
      
      endpoints.value = generateMockEndpoints()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load endpoints'
    } finally {
      isLoading.value = false
    }
  }

  async function createEndpoint(input: CreateEndpointInput): Promise<GraphQLEndpoint | null> {
    isLoading.value = true
    error.value = null

    try {
      const newEndpoint: GraphQLEndpoint = {
        id: generateId(),
        name: input.name,
        url: input.url,
        description: input.description,
        status: EndpointStatus.ACTIVE,
        headers: input.headers,
        introspectionEnabled: input.introspectionEnabled,
        isHealthy: false, // Will be updated by health check
        createdAt: new Date(),
        updatedAt: new Date()
      }

      endpoints.value.push(newEndpoint)
      
      // Test the endpoint immediately after creation
      await performHealthCheck(newEndpoint.id)
      
      return newEndpoint
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create endpoint'
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function updateEndpoint(id: string, input: UpdateEndpointInput): Promise<boolean> {
    isLoading.value = true
    error.value = null

    try {
      const index = endpoints.value.findIndex(endpoint => endpoint.id === id)
      if (index === -1) {
        error.value = 'Endpoint not found'
        return false
      }

      const updatedEndpoint: GraphQLEndpoint = {
        ...endpoints.value[index],
        ...input,
        updatedAt: new Date()
      }

      endpoints.value[index] = updatedEndpoint

      // If URL changed, retest the endpoint
      if (input.url) {
        await performHealthCheck(id)
      }

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update endpoint'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteEndpoint(id: string): Promise<boolean> {
    try {
      const index = endpoints.value.findIndex(endpoint => endpoint.id === id)
      if (index === -1) {
        return false
      }

      endpoints.value.splice(index, 1)

      // Clear selection if deleted endpoint was selected
      if (selectedEndpoint.value?.id === id) {
        selectedEndpoint.value = null
      }

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete endpoint'
      return false
    }
  }

  async function testEndpoint(url: string): Promise<EndpointTestResult> {
    try {
      return await testEndpointConnectivity(url)
    } catch (err) {
      return {
        success: false,
        responseTime: 0,
        errorMessage: err instanceof Error ? err.message : 'Test failed'
      }
    }
  }

  async function performHealthCheck(endpointId: string): Promise<void> {
    const endpoint = endpoints.value.find(e => e.id === endpointId)
    if (!endpoint) return

    // Set checking status
    endpoint.status = EndpointStatus.CHECKING

    try {
      const result = await testEndpoint(endpoint.url)
      
      endpoint.isHealthy = result.success
      endpoint.responseTime = result.responseTime
      endpoint.lastChecked = new Date()
      endpoint.status = result.success ? EndpointStatus.ACTIVE : EndpointStatus.ERROR
      endpoint.errorMessage = result.errorMessage || undefined
    } catch (err) {
      endpoint.isHealthy = false
      endpoint.status = EndpointStatus.ERROR
      endpoint.errorMessage = err instanceof Error ? err.message : 'Health check failed'
    }
  }

  function selectEndpoint(id: string): void {
    const endpoint = endpoints.value.find(e => e.id === id)
    selectedEndpoint.value = endpoint || null
  }

  function clearSelection(): void {
    selectedEndpoint.value = null
  }

  // Helper functions
  function generateId(): string {
    return `endpoint_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  function generateMockEndpoints(): GraphQLEndpoint[] {
    return [
      {
        id: 'endpoint_1',
        name: 'Production API',
        url: 'https://api.production.com/graphql',
        description: 'Main production GraphQL endpoint',
        status: EndpointStatus.ACTIVE,
        introspectionEnabled: false,
        isHealthy: true,
        responseTime: 150,
        lastChecked: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
        updatedAt: new Date(Date.now() - 5 * 60 * 1000)
      },
      {
        id: 'endpoint_2',
        name: 'Staging API',
        url: 'https://api.staging.com/graphql',
        description: 'Staging environment for testing',
        status: EndpointStatus.ACTIVE,
        introspectionEnabled: true,
        isHealthy: true,
        responseTime: 200,
        lastChecked: new Date(Date.now() - 10 * 60 * 1000), // 10 minutes ago
        headers: {
          'X-API-Key': 'staging-key'
        },
        createdAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), // 15 days ago
        updatedAt: new Date(Date.now() - 10 * 60 * 1000)
      },
      {
        id: 'endpoint_3',
        name: 'Development API',
        url: 'https://api.dev.com/graphql',
        description: 'Local development endpoint',
        status: EndpointStatus.ERROR,
        introspectionEnabled: true,
        isHealthy: false,
        responseTime: 0,
        lastChecked: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
        errorMessage: 'Connection timeout',
        createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
        updatedAt: new Date(Date.now() - 60 * 60 * 1000)
      }
    ]
  }

  return {
    // State
    endpoints,
    selectedEndpoint,
    isLoading,
    error,
    // Getters
    healthyEndpointsCount,
    unhealthyEndpointsCount,
    activeEndpoints,
    // Actions
    loadEndpoints,
    createEndpoint,
    updateEndpoint,
    deleteEndpoint,
    testEndpoint,
    performHealthCheck,
    selectEndpoint,
    clearSelection
  }
})