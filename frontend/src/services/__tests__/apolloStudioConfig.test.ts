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

describe('API Key Authentication', () => {
  it('should handle X-API-Key header format', () => {
    const { formatApiKey } = useApolloStudioConfig()
    
    const apiKey = formatApiKey('my-api-key-123')
    
    expect(apiKey).toBe('my-api-key-123')
  })

  it('should create config with API Key authentication', () => {
    const { createConfigWithAuth } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'API Key API',
      url: 'https://apikey.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'X-API-Key': 'secret-api-key-value'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const config = createConfigWithAuth(endpoint, 'apikey')
    
    expect(config.headers['X-API-Key']).toBe('secret-api-key-value')
  })

  it('should handle custom API Key header names', () => {
    const { createConfigWithAuth } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Custom API Key API',
      url: 'https://custom.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'X-Custom-API-Key': 'custom-key-value'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const config = createConfigWithAuth(endpoint, 'apikey', { headerName: 'X-Custom-API-Key' })
    
    expect(config.headers['X-Custom-API-Key']).toBe('custom-key-value')
  })

  it('should validate API Key format', () => {
    const { validateApiKey } = useApolloStudioConfig()
    
    const validKey = validateApiKey('valid-api-key-123')
    const emptyKey = validateApiKey('')
    const nullKey = validateApiKey(null)
    
    expect(validKey).toBe(true)
    expect(emptyKey).toBe(false)
    expect(nullKey).toBe(false)
  })
})

describe('Basic Authentication', () => {
  it('should encode Basic auth credentials', () => {
    const { encodeBasicAuth } = useApolloStudioConfig()
    
    const encoded = encodeBasicAuth('username', 'password')
    const expected = 'Basic ' + btoa('username:password')
    
    expect(encoded).toBe(expected)
  })

  it('should create config with Basic authentication', () => {
    const { createConfigWithAuth } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Basic Auth API',
      url: 'https://basic.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const config = createConfigWithAuth(endpoint, 'basic')
    
    expect(config.headers.Authorization).toBe('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')
  })

  it('should decode Basic auth credentials', () => {
    const { decodeBasicAuth } = useApolloStudioConfig()
    
    const credentials = decodeBasicAuth('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')
    
    expect(credentials.username).toBe('username')
    expect(credentials.password).toBe('password')
  })

  it('should handle malformed Basic auth headers', () => {
    const { decodeBasicAuth } = useApolloStudioConfig()
    
    const invalidHeader = decodeBasicAuth('InvalidHeader')
    const missingPrefix = decodeBasicAuth('dXNlcm5hbWU6cGFzc3dvcmQ=')
    
    expect(invalidHeader).toBeNull()
    expect(missingPrefix).toBeNull()
  })

  it('should validate Basic auth credentials', () => {
    const { validateBasicAuth } = useApolloStudioConfig()
    
    const validAuth = validateBasicAuth('username', 'password')
    const emptyUsername = validateBasicAuth('', 'password')
    const emptyPassword = validateBasicAuth('username', '')
    
    expect(validAuth).toBe(true)
    expect(emptyUsername).toBe(false)
    expect(emptyPassword).toBe(false)
  })
})

describe('Multi-Authentication Support', () => {
  it('should detect authentication type from headers', () => {
    const { detectAuthType } = useApolloStudioConfig()
    
    const bearerHeaders = { 'Authorization': 'Bearer token123' }
    const basicHeaders = { 'Authorization': 'Basic dXNlcm5hbWU6cGFzc3dvcmQ=' }
    const apiKeyHeaders = { 'X-API-Key': 'api-key-value' }
    const noAuthHeaders = { 'Content-Type': 'application/json' }
    
    expect(detectAuthType(bearerHeaders)).toBe('bearer')
    expect(detectAuthType(basicHeaders)).toBe('basic')
    expect(detectAuthType(apiKeyHeaders)).toBe('apikey')
    expect(detectAuthType(noAuthHeaders)).toBe('none')
  })

  it('should prioritize Bearer over Basic when both present', () => {
    const { detectAuthType } = useApolloStudioConfig()
    
    const mixedHeaders = {
      'Authorization': 'Bearer token123',
      'X-API-Key': 'api-key'
    }
    
    expect(detectAuthType(mixedHeaders)).toBe('bearer')
  })

  it('should handle authentication type switching', () => {
    const { createConfigWithAuth } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Multi Auth API',
      url: 'https://multi.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer original-token'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    // Switch from Bearer to API Key
    const apiKeyConfig = createConfigWithAuth(endpoint, 'apikey', { 
      apiKey: 'new-api-key',
      headerName: 'X-API-Key'
    })
    
    expect(apiKeyConfig.headers['Authorization']).toBeUndefined()
    expect(apiKeyConfig.headers['X-API-Key']).toBe('new-api-key')
    
    // Switch to Basic auth
    const basicConfig = createConfigWithAuth(endpoint, 'basic', {
      username: 'user',
      password: 'pass'
    })
    
    expect(basicConfig.headers['Authorization']).toBe('Basic ' + btoa('user:pass'))
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