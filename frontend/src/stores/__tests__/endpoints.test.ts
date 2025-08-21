import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useEndpointsStore } from '../endpoints'
import type { GraphQLEndpoint, CreateEndpointInput, UpdateEndpointInput } from '../../types/endpoint'
import { EndpointStatus } from '../../types/endpoint'

// Mock the GraphQL client service
vi.mock('../../services/graphql/client', () => ({
  useGraphQLClient: () => ({
    testEndpoint: vi.fn().mockResolvedValue({
      success: true,
      responseTime: 100,
      statusCode: 200
    }),
    getIntrospectionSchema: vi.fn().mockResolvedValue('schema')
  })
}))

describe('Endpoints Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const store = useEndpointsStore()

      expect(store.endpoints).toEqual([])
      expect(store.selectedEndpoint).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('getters', () => {
    it('should calculate healthy endpoints count correctly', () => {
      const store = useEndpointsStore()

      store.endpoints = [
        createMockEndpoint('1', { isHealthy: true }),
        createMockEndpoint('2', { isHealthy: false }),
        createMockEndpoint('3', { isHealthy: true })
      ]

      expect(store.healthyEndpointsCount).toBe(2)
    })

    it('should calculate unhealthy endpoints count correctly', () => {
      const store = useEndpointsStore()

      store.endpoints = [
        createMockEndpoint('1', { isHealthy: true }),
        createMockEndpoint('2', { isHealthy: false }),
        createMockEndpoint('3', { isHealthy: false })
      ]

      expect(store.unhealthyEndpointsCount).toBe(2)
    })

    it('should get active endpoints correctly', () => {
      const store = useEndpointsStore()

      store.endpoints = [
        createMockEndpoint('1', { status: EndpointStatus.ACTIVE }),
        createMockEndpoint('2', { status: EndpointStatus.INACTIVE }),
        createMockEndpoint('3', { status: EndpointStatus.ACTIVE })
      ]

      expect(store.activeEndpoints).toHaveLength(2)
      expect(store.activeEndpoints.every(e => e.status === EndpointStatus.ACTIVE)).toBe(true)
    })
  })

  describe('actions', () => {
    describe('loadEndpoints', () => {
      it('should set loading state while fetching', async () => {
        const store = useEndpointsStore()

        // Mock a delayed promise
        const loadPromise = store.loadEndpoints()

        expect(store.isLoading).toBe(true)

        await loadPromise

        expect(store.isLoading).toBe(false)
      })

      it('should load mock endpoints', async () => {
        const store = useEndpointsStore()

        await store.loadEndpoints()

        expect(store.endpoints.length).toBeGreaterThan(0)
        expect(store.error).toBeNull()
      })
    })

    describe('createEndpoint', () => {
      it('should add new endpoint with generated ID', async () => {
        const store = useEndpointsStore()

        const input: CreateEndpointInput = {
          name: 'Test Endpoint',
          url: 'https://api.example.com/graphql',
          introspectionEnabled: true
        }

        const result = await store.createEndpoint(input)

        expect(result).toBeTruthy()
        expect(store.endpoints).toHaveLength(1)
        expect(store.endpoints[0].name).toBe(input.name)
        expect(store.endpoints[0].url).toBe(input.url)
        expect(store.endpoints[0].id).toBeTruthy()
      })
    })

    describe('updateEndpoint', () => {
      it('should update existing endpoint', async () => {
        const store = useEndpointsStore()

        // First create an endpoint
        const createInput: CreateEndpointInput = {
          name: 'Original Name',
          url: 'https://original.com/graphql',
          introspectionEnabled: true
        }

        await store.createEndpoint(createInput)
        const endpointId = store.endpoints[0].id

        // Then update it
        const updateInput: UpdateEndpointInput = {
          name: 'Updated Name'
        }

        const result = await store.updateEndpoint(endpointId, updateInput)

        expect(result).toBeTruthy()
        expect(store.endpoints[0].name).toBe('Updated Name')
        expect(store.endpoints[0].url).toBe('https://original.com/graphql') // unchanged
      })

      it('should return false for non-existent endpoint', async () => {
        const store = useEndpointsStore()

        const result = await store.updateEndpoint('non-existent-id', { name: 'Test' })

        expect(result).toBe(false)
      })
    })

    describe('deleteEndpoint', () => {
      it('should remove endpoint from store', async () => {
        const store = useEndpointsStore()

        // First create an endpoint
        const input: CreateEndpointInput = {
          name: 'Test Endpoint',
          url: 'https://api.example.com/graphql',
          introspectionEnabled: true
        }

        await store.createEndpoint(input)
        const endpointId = store.endpoints[0].id

        // Then delete it
        const result = await store.deleteEndpoint(endpointId)

        expect(result).toBe(true)
        expect(store.endpoints).toHaveLength(0)
      })

      it('should return false for non-existent endpoint', async () => {
        const store = useEndpointsStore()

        const result = await store.deleteEndpoint('non-existent-id')

        expect(result).toBe(false)
      })
    })

    describe('testEndpoint', () => {
      it('should test endpoint connectivity', async () => {
        const store = useEndpointsStore()

        const result = await store.testEndpoint('https://api.example.com/graphql')

        expect(result).toHaveProperty('success')
        expect(result).toHaveProperty('responseTime')
      })
    })

    describe('selectEndpoint', () => {
      it('should set selected endpoint', () => {
        const store = useEndpointsStore()

        const endpoint = createMockEndpoint('test-id')
        store.endpoints = [endpoint]

        store.selectEndpoint('test-id')

        expect(store.selectedEndpoint).toEqual(endpoint)
      })

      it('should clear selected endpoint if not found', () => {
        const store = useEndpointsStore()

        store.selectEndpoint('non-existent-id')

        expect(store.selectedEndpoint).toBeNull()
      })
    })
  })
})

function createMockEndpoint(id: string, overrides?: Partial<GraphQLEndpoint>): GraphQLEndpoint {
  return {
    id,
    name: `Endpoint ${id}`,
    url: `https://api${id}.example.com/graphql`,
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: true,
    isHealthy: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides
  }
}
