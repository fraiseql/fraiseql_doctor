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

describe('Endpoint Switching & URL Management', () => {
  it('should switch endpoint configuration dynamically', () => {
    const { switchEndpoint } = useApolloStudioConfig()
    
    const oldEndpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Old API',
      url: 'https://old.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer old-token'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const newEndpoint: GraphQLEndpoint = {
      id: '2',
      name: 'New API',
      url: 'https://new.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: false,
      isHealthy: true,
      headers: {
        'X-API-Key': 'new-api-key'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const result = switchEndpoint(oldEndpoint, newEndpoint)
    
    expect(result.endpoint).toBe('https://new.api.com/graphql')
    expect(result.headers['Authorization']).toBeUndefined()
    expect(result.headers['X-API-Key']).toBe('new-api-key')
    expect(result.introspection).toBe(false)
  })

  it('should preserve auth type when switching endpoints', () => {
    const { switchEndpoint } = useApolloStudioConfig()
    
    const endpoint1: GraphQLEndpoint = {
      id: '1',
      name: 'API 1',
      url: 'https://api1.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer token-1'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const endpoint2: GraphQLEndpoint = {
      id: '2',
      name: 'API 2',
      url: 'https://api2.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer token-2'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const result = switchEndpoint(endpoint1, endpoint2, { preserveAuthType: true })
    
    expect(result.endpoint).toBe('https://api2.com/graphql')
    expect(result.headers['Authorization']).toBe('Bearer token-2')
  })

  it('should generate studio URLs with custom parameters', () => {
    const { generateStudioUrlWithParams } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Test API',
      url: 'https://api.example.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const customParams = {
      theme: 'dark',
      showDocs: 'true',
      operation: 'query'
    }
    
    const url = generateStudioUrlWithParams(endpoint, customParams)
    
    expect(url).toContain('theme=dark')
    expect(url).toContain('showDocs=true')
    expect(url).toContain('operation=query')
    expect(url).toContain('endpoint=' + encodeURIComponent(endpoint.url))
  })

  it('should sanitize URL parameters', () => {
    const { sanitizeUrlParams } = useApolloStudioConfig()
    
    const unsafeParams = {
      'safe-param': 'value',
      '<script>alert("xss")</script>': 'malicious',
      'normal_param': 'normal-value',
      'javascript:alert()': 'another-malicious'
    }
    
    const sanitized = sanitizeUrlParams(unsafeParams)
    
    expect(sanitized['safe-param']).toBe('value')
    expect(sanitized['normal_param']).toBe('normal-value')
    expect(sanitized['<script>alert("xss")</script>']).toBeUndefined()
    expect(sanitized['javascript:alert()']).toBeUndefined()
  })

  it('should validate endpoint URLs before switching', () => {
    const { validateEndpointUrl } = useApolloStudioConfig()
    
    expect(validateEndpointUrl('https://valid.api.com/graphql')).toBe(true)
    expect(validateEndpointUrl('http://localhost:4000/graphql')).toBe(true)
    expect(validateEndpointUrl('invalid-url')).toBe(false)
    expect(validateEndpointUrl('javascript:alert()')).toBe(false)
    expect(validateEndpointUrl('')).toBe(false)
    expect(validateEndpointUrl('ftp://not-http.com')).toBe(false)
  })

  it('should build URL query string from parameters', () => {
    const { buildQueryString } = useApolloStudioConfig()
    
    const params = {
      endpoint: 'https://api.example.com/graphql',
      introspection: 'true',
      theme: 'dark',
      empty: '',
      undefined: undefined,
      null: null
    }
    
    const queryString = buildQueryString(params)
    
    expect(queryString).toContain('endpoint=' + encodeURIComponent('https://api.example.com/graphql'))
    expect(queryString).toContain('introspection=true')
    expect(queryString).toContain('theme=dark')
    expect(queryString).not.toContain('empty=')
    expect(queryString).not.toContain('undefined')
    expect(queryString).not.toContain('null')
  })

  it('should handle endpoint switching with different auth types', () => {
    const { switchEndpointWithAuth } = useApolloStudioConfig()
    
    const bearerEndpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Bearer API',
      url: 'https://bearer.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer bearer-token'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const apiKeyEndpoint: GraphQLEndpoint = {
      id: '2',
      name: 'API Key API',
      url: 'https://apikey.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'X-API-Key': 'api-key-value'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const result = switchEndpointWithAuth(bearerEndpoint, apiKeyEndpoint, 'apikey')
    
    expect(result.endpoint).toBe('https://apikey.api.com/graphql')
    expect(result.headers['Authorization']).toBeUndefined()
    expect(result.headers['X-API-Key']).toBe('api-key-value')
  })

  it('should generate Studio URLs with authentication parameters', () => {
    const { generateAuthenticatedStudioUrl } = useApolloStudioConfig()
    
    const endpoint: GraphQLEndpoint = {
      id: '1',
      name: 'Auth API',
      url: 'https://auth.api.com/graphql',
      status: EndpointStatus.ACTIVE,
      introspectionEnabled: true,
      isHealthy: true,
      headers: {
        'Authorization': 'Bearer secret-token'
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    const url = generateAuthenticatedStudioUrl(endpoint)
    
    expect(url).toContain('studio.apollographql.com')
    expect(url).toContain('endpoint=' + encodeURIComponent(endpoint.url))
    // Note: Should NOT contain actual auth tokens in URL for security
    expect(url).not.toContain('secret-token')
  })
})