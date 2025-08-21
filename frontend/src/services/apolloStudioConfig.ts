import type { GraphQLEndpoint } from '../types/endpoint'

export interface StudioHeaders {
  [key: string]: string
}

export interface StudioConfig {
  endpoint: string
  headers: StudioHeaders
  theme?: 'light' | 'dark'
  introspection?: boolean
}

export function useApolloStudioConfig() {
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

  return {
    createStudioConfig,
    buildAuthHeaders,
    generateStudioUrl,
    validateEndpointConfig,
    mergeHeaders
  }
}