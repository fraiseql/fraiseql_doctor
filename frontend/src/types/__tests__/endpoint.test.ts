import { describe, it, expect } from 'vitest'
import type { GraphQLEndpoint, CreateEndpointInput, UpdateEndpointInput } from '../endpoint'
import { EndpointStatus } from '../endpoint'

describe('Endpoint Types', () => {
  describe('EndpointStatus', () => {
    it('should have correct enum values', () => {
      expect(EndpointStatus.ACTIVE).toBe('active')
      expect(EndpointStatus.INACTIVE).toBe('inactive')
      expect(EndpointStatus.ERROR).toBe('error')
      expect(EndpointStatus.CHECKING).toBe('checking')
    })
  })

  describe('GraphQLEndpoint', () => {
    it('should accept valid endpoint data', () => {
      const endpoint: GraphQLEndpoint = {
        id: 'test-id',
        name: 'Test Endpoint',
        url: 'https://api.example.com/graphql',
        description: 'Test description',
        status: EndpointStatus.ACTIVE,
        introspectionEnabled: true,
        isHealthy: true,
        createdAt: new Date(),
        updatedAt: new Date()
      }

      expect(endpoint.id).toBe('test-id')
      expect(endpoint.name).toBe('Test Endpoint')
      expect(endpoint.status).toBe(EndpointStatus.ACTIVE)
      expect(endpoint.introspectionEnabled).toBe(true)
    })

    it('should accept minimal endpoint data', () => {
      const endpoint: GraphQLEndpoint = {
        id: 'test-id',
        name: 'Test Endpoint',
        url: 'https://api.example.com/graphql',
        status: EndpointStatus.ACTIVE,
        introspectionEnabled: false,
        isHealthy: false,
        createdAt: new Date(),
        updatedAt: new Date()
      }

      expect(endpoint.description).toBeUndefined()
      expect(endpoint.headers).toBeUndefined()
      expect(endpoint.responseTime).toBeUndefined()
    })
  })

  describe('CreateEndpointInput', () => {
    it('should accept valid create input', () => {
      const input: CreateEndpointInput = {
        name: 'New Endpoint',
        url: 'https://api.example.com/graphql',
        description: 'New description',
        headers: { 'Authorization': 'Bearer token' },
        introspectionEnabled: true
      }

      expect(input.name).toBe('New Endpoint')
      expect(input.headers?.Authorization).toBe('Bearer token')
    })

    it('should accept minimal create input', () => {
      const input: CreateEndpointInput = {
        name: 'Minimal Endpoint',
        url: 'https://api.example.com/graphql',
        introspectionEnabled: false
      }

      expect(input.description).toBeUndefined()
      expect(input.headers).toBeUndefined()
    })
  })

  describe('UpdateEndpointInput', () => {
    it('should accept partial update data', () => {
      const input: UpdateEndpointInput = {
        name: 'Updated Name'
      }

      expect(input.name).toBe('Updated Name')
      expect(input.url).toBeUndefined()
    })

    it('should accept full update data', () => {
      const input: UpdateEndpointInput = {
        name: 'Updated Name',
        url: 'https://updated.example.com/graphql',
        description: 'Updated description',
        headers: { 'X-API-Key': 'key123' },
        introspectionEnabled: false
      }

      expect(input.name).toBe('Updated Name')
      expect(input.headers?.['X-API-Key']).toBe('key123')
    })
  })
})
