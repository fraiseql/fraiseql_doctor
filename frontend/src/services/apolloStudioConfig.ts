import type { GraphQLEndpoint } from '../types/endpoint'
import { isBearerToken, sanitizeToken } from '../utils/authHelpers'

export interface StudioHeaders {
  [key: string]: string
}

export interface StudioConfig {
  endpoint: string
  headers: StudioHeaders
  theme?: 'light' | 'dark'
  introspection?: boolean
}

export type AuthType = 'bearer' | 'apikey' | 'basic' | 'none'

export interface AuthOptions {
  headerName?: string
  apiKey?: string
  username?: string
  password?: string
}

export interface BasicAuthCredentials {
  username: string
  password: string
}

export function useApolloStudioConfig() {
  // Helper function to remove API key headers
  const API_KEY_HEADERS = ['X-API-Key', 'X-Api-Key', 'API-Key', 'Api-Key']
  
  function clearApiKeyHeaders(headers: StudioHeaders): void {
    API_KEY_HEADERS.forEach(header => delete headers[header])
  }
  
  function createStudioConfig(endpoint: GraphQLEndpoint): StudioConfig {
    return {
      endpoint: endpoint.url,
      headers: endpoint.headers || {},
      introspection: endpoint.introspectionEnabled
    }
  }

  function buildAuthHeaders(headers: StudioHeaders = {}): StudioHeaders {
    return { ...headers }
  }

  function generateStudioUrl(endpoint: GraphQLEndpoint): string {
    const baseUrl = 'https://studio.apollographql.com/sandbox/explorer'
    const params = new URLSearchParams({
      endpoint: endpoint.url,
      ...(endpoint.introspectionEnabled && { introspection: 'true' })
    })
    
    return `${baseUrl}?${params.toString()}`
  }

  function validateEndpointConfig(endpoint: GraphQLEndpoint): boolean {
    try {
      new URL(endpoint.url)
      return true
    } catch {
      return false
    }
  }

  function mergeHeaders(
    defaultHeaders: StudioHeaders,
    customHeaders: StudioHeaders
  ): StudioHeaders {
    return {
      ...defaultHeaders,
      ...customHeaders
    }
  }

  function formatBearerToken(token: string): string {
    const clean = sanitizeToken(token)
    return isBearerToken(clean) ? clean : `Bearer ${clean}`
  }

  function extractBearerToken(authHeader: string): string {
    return authHeader.replace(/^Bearer\s+/, '')
  }

  // API Key Authentication Functions
  function formatApiKey(apiKey: string): string {
    return apiKey
  }

  function validateApiKey(apiKey: string | null): boolean {
    return Boolean(apiKey && apiKey.trim().length > 0)
  }

  // Basic Authentication Functions
  function encodeBasicAuth(username: string, password: string): string {
    return 'Basic ' + btoa(`${username}:${password}`)
  }

  function decodeBasicAuth(authHeader: string): BasicAuthCredentials | null {
    try {
      if (!authHeader.startsWith('Basic ')) {
        return null
      }
      
      const base64 = authHeader.replace('Basic ', '')
      const decoded = atob(base64)
      const [username, password] = decoded.split(':')
      
      if (!username || !password) {
        return null
      }
      
      return { username, password }
    } catch {
      return null
    }
  }

  function validateBasicAuth(username: string, password: string): boolean {
    return Boolean(username && username.trim().length > 0 && 
                   password && password.trim().length > 0)
  }

  // Multi-Authentication Support
  function detectAuthType(headers: StudioHeaders): AuthType {
    const authHeader = headers.Authorization
    
    if (authHeader) {
      if (authHeader.startsWith('Bearer ')) {
        return 'bearer'
      }
      if (authHeader.startsWith('Basic ')) {
        return 'basic'
      }
    }
    
    // Check for common API key headers
    for (const header of API_KEY_HEADERS) {
      if (headers[header]) {
        return 'apikey'
      }
    }
    
    return 'none'
  }

  function createConfigWithAuth(
    endpoint: GraphQLEndpoint, 
    authType: AuthType,
    options?: AuthOptions
  ): StudioConfig {
    const config = createStudioConfig(endpoint)
    
    switch (authType) {
      case 'bearer':
        if (config.headers.Authorization) {
          config.headers.Authorization = formatBearerToken(config.headers.Authorization)
        }
        // Clear non-bearer auth headers
        clearApiKeyHeaders(config.headers)
        break
        
      case 'apikey':
        // Clear auth header for API key auth
        delete config.headers.Authorization
        
        if (options?.apiKey && options?.headerName) {
          config.headers[options.headerName] = options.apiKey
        } else if (endpoint.headers) {
          // Use existing API key from endpoint headers
          for (const header of API_KEY_HEADERS) {
            if (endpoint.headers[header]) {
              config.headers[header] = endpoint.headers[header]
              break
            }
          }
        }
        break
        
      case 'basic':
        // Clear API key headers for Basic auth
        clearApiKeyHeaders(config.headers)
        
        if (options?.username && options?.password) {
          config.headers.Authorization = encodeBasicAuth(options.username, options.password)
        } else if (config.headers.Authorization?.startsWith('Basic ')) {
          // Keep existing Basic auth header
        }
        break
        
      case 'none':
        delete config.headers.Authorization
        clearApiKeyHeaders(config.headers)
        break
    }
    
    return config
  }

  return {
    createStudioConfig,
    buildAuthHeaders,
    generateStudioUrl,
    validateEndpointConfig,
    mergeHeaders,
    formatBearerToken,
    extractBearerToken,
    createConfigWithAuth,
    // API Key functions
    formatApiKey,
    validateApiKey,
    // Basic Auth functions
    encodeBasicAuth,
    decodeBasicAuth,
    validateBasicAuth,
    // Multi-auth functions
    detectAuthType
  }
}