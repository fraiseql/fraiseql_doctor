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