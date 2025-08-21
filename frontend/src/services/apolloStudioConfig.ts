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

export interface SwitchEndpointOptions {
  preserveAuthType?: boolean
}

export interface UrlParams {
  [key: string]: string | number | boolean | undefined | null
}

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  config: StudioConfig | null
  warnings?: string[]
}

export interface SafeResult<T> {
  success: boolean
  data?: T
  config?: StudioConfig
  error?: string | null
  warnings?: string[]
  fallbackConfig?: StudioConfig
}

export interface RetryOptions {
  maxRetries: number
  retryDelay: number
  retryableErrors: string[]
}

export interface RetryResult {
  config: StudioConfig
  retryCount: number
  canRetry: boolean
  lastError?: string
}

export interface ErrorLogEntry {
  timestamp: Date
  error: string
  context: any
  level: 'error' | 'warning' | 'info'
}

export interface NetworkErrorResult {
  error: string
  retryable: boolean
  fallbackConfig: StudioConfig
}

export interface UrlSafetyResult {
  success: boolean
  url: string
  sanitizedParams: UrlParams
  warnings: string[]
}

export interface IframeConfigOptions {
  enableErrorBoundary?: boolean
  fallbackContent?: string
  retryOnError?: boolean
  maxRetries?: number
}

export interface IframeConfig {
  src: string
  errorBoundary: boolean
  fallbackContent: string
  onError?: (error: Error) => void
  onRetry?: () => void
}

// Global error logging system (shared across instances)
let globalErrorLog: ErrorLogEntry[] = []

function logError(error: string, context: any = {}, level: 'error' | 'warning' | 'info' = 'error'): void {
  globalErrorLog.push({
    timestamp: new Date(),
    error,
    context,
    level
  })
}

function getErrorLog(): ErrorLogEntry[] {
  return [...globalErrorLog]
}

function clearErrorLog(): void {
  globalErrorLog = []
}

export function useApolloStudioConfig() {
  // Constants
  const API_KEY_HEADERS = ['X-API-Key', 'X-Api-Key', 'API-Key', 'Api-Key']
  const APOLLO_STUDIO_BASE_URL = 'https://studio.apollographql.com/sandbox/explorer'
  const DANGEROUS_URL_PATTERNS = ['<script', 'javascript:', 'data:']

  // Helper functions
  function clearApiKeyHeaders(headers: StudioHeaders): void {
    API_KEY_HEADERS.forEach(header => delete headers[header])
  }

  function isValidValue(value: any): boolean {
    return value !== undefined && value !== null && value !== ''
  }

  function createFallbackConfig(endpoint?: GraphQLEndpoint): StudioConfig {
    return {
      endpoint: endpoint?.url || 'https://api.example.com/graphql',
      headers: {},
      introspection: false
    }
  }

  // Common error handling patterns
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  function handleError<T>(
    operation: () => T,
    fallback: T,
    context: string,
    logContext: any = {}
  ): SafeResult<T> {
    try {
      const result = operation()
      return {
        success: true,
        data: result,
        error: null,
        warnings: []
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      logError(`${context} failed`, { ...logContext, error: errorMessage })

      return {
        success: false,
        data: fallback,
        error: errorMessage,
        warnings: ['Using fallback due to error']
      }
    }
  }

  function validateEndpointStructure(endpoint: GraphQLEndpoint): string[] {
    const errors: string[] = []

    // Check URL first (most critical)
    if (!validateEndpointUrl(endpoint.url)) {
      errors.push('Invalid URL format')
    }

    if (DANGEROUS_URL_PATTERNS.some(pattern => endpoint.url.includes(pattern))) {
      errors.push('Dangerous URL pattern detected')
    }

    // Then check required fields
    if (!endpoint.id || !endpoint.name) {
      errors.push('Missing required endpoint fields')
    }

    return errors
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

  // URL Generation Helper Functions (defined early for use by other functions)
  function sanitizeUrlParams(params: UrlParams): UrlParams {
    const sanitized: UrlParams = {}

    for (const [key, value] of Object.entries(params)) {
      // Skip dangerous keys that could contain scripts
      const isDangerous = DANGEROUS_URL_PATTERNS.some(pattern => key.includes(pattern))
      if (isDangerous) {
        continue
      }

      // Only include valid values
      if (isValidValue(value)) {
        sanitized[key] = value
      }
    }

    return sanitized
  }

  function buildQueryString(params: UrlParams): string {
    const sanitized = sanitizeUrlParams(params)
    const searchParams = new URLSearchParams()

    for (const [key, value] of Object.entries(sanitized)) {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    }

    return searchParams.toString()
  }

  function generateStudioUrl(endpoint: GraphQLEndpoint): string {
    const params = {
      endpoint: endpoint.url,
      ...(endpoint.introspectionEnabled && { introspection: 'true' })
    }

    const queryString = buildQueryString(params)
    return `${APOLLO_STUDIO_BASE_URL}?${queryString}`
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

  // Endpoint Switching Functions
  function switchEndpoint(
    fromEndpoint: GraphQLEndpoint,
    toEndpoint: GraphQLEndpoint,
    options?: SwitchEndpointOptions
  ): StudioConfig {
    const config = createStudioConfig(toEndpoint)

    if (options?.preserveAuthType) {
      // Keep the same auth type but use new endpoint's credentials
      const fromAuthType = detectAuthType(fromEndpoint.headers || {})
      return createConfigWithAuth(toEndpoint, fromAuthType)
    }

    // Use the target endpoint's natural auth configuration
    const targetAuthType = detectAuthType(config.headers)
    return createConfigWithAuth(toEndpoint, targetAuthType)
  }

  function switchEndpointWithAuth(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    fromEndpoint: GraphQLEndpoint,
    toEndpoint: GraphQLEndpoint,
    forceAuthType: AuthType
  ): StudioConfig {
    return createConfigWithAuth(toEndpoint, forceAuthType)
  }

  // URL Generation Functions
  function validateEndpointUrl(url: string): boolean {
    if (!url || typeof url !== 'string' || url.trim().length === 0) {
      return false
    }

    try {
      const parsed = new URL(url)
      // Only allow http and https protocols
      return parsed.protocol === 'http:' || parsed.protocol === 'https:'
    } catch {
      return false
    }
  }

  function generateStudioUrlWithParams(
    endpoint: GraphQLEndpoint,
    customParams: UrlParams = {}
  ): string {
    const params: UrlParams = {
      endpoint: endpoint.url,
      ...(endpoint.introspectionEnabled && { introspection: 'true' }),
      ...customParams
    }

    const queryString = buildQueryString(params)
    return `${APOLLO_STUDIO_BASE_URL}?${queryString}`
  }

  function generateAuthenticatedStudioUrl(endpoint: GraphQLEndpoint): string {
    // For security, we don't pass auth tokens in the URL
    // The iframe will handle authentication through headers
    return generateStudioUrlWithParams(endpoint, {
      // Add any safe, non-sensitive parameters here
      hasAuth: 'true' // Indicates auth is configured but don't expose tokens
    })
  }

  // Error Handling and Resilience Functions
  function validateConfigurationSafely(endpoint: GraphQLEndpoint): ValidationResult {
    const warnings: string[] = []

    try {
      const errors = validateEndpointStructure(endpoint)

      if (errors.length > 0) {
        errors.forEach(error => logError(error, { endpoint: endpoint.url }))
        return {
          isValid: false,
          errors,
          config: null,
          warnings
        }
      }

      const config = createStudioConfig(endpoint)
      return {
        isValid: true,
        errors: [],
        config,
        warnings
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown validation error'
      logError('Configuration validation failed', { endpoint, error: errorMessage })
      return {
        isValid: false,
        errors: [errorMessage],
        config: null,
        warnings
      }
    }
  }

  function createStudioConfigSafely(endpoint: GraphQLEndpoint): SafeResult<StudioConfig> {
    try {
      // Handle corrupt or missing headers
      const safeEndpoint = {
        ...endpoint,
        headers: endpoint.headers || {}
      }

      const config = createStudioConfig(safeEndpoint)

      return {
        success: true,
        config,
        error: null,
        warnings: endpoint.headers === null ? ['Headers were null, using empty object'] : []
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      logError('Safe config creation failed', { endpoint, error: errorMessage })

      return {
        success: false,
        config: createFallbackConfig(endpoint),
        error: errorMessage,
        warnings: ['Using fallback configuration']
      }
    }
  }

  function createConfigWithAuthSafely(
    endpoint: GraphQLEndpoint,
    authType: AuthType
  ): SafeResult<StudioConfig> {
    try {
      const warnings: string[] = []

      // Handle invalid token formats with fallback
      if (authType === 'bearer' && endpoint.headers?.Authorization) {
        const authHeader = endpoint.headers.Authorization
        if (!authHeader.startsWith('Bearer ') && !isBearerToken(authHeader)) {
          warnings.push('Invalid token format, applied fallback')
        }
      }

      const config = createConfigWithAuth(endpoint, authType)

      return {
        success: true,
        config,
        error: null,
        warnings
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown auth error'
      logError('Safe auth config creation failed', { endpoint, authType, error: errorMessage })

      return {
        success: false,
        config: createFallbackConfig(endpoint),
        error: errorMessage,
        warnings: ['Using fallback configuration without authentication']
      }
    }
  }

  function simulateNetworkError(
    endpoint: GraphQLEndpoint,
    errorType: 'timeout' | 'network' | 'cors' | 'auth'
  ): NetworkErrorResult {
    const fallbackConfig = createFallbackConfig(endpoint)

    const errorMap = {
      timeout: { retryable: true, message: 'Request timeout' },
      network: { retryable: true, message: 'Network error' },
      cors: { retryable: false, message: 'CORS policy error' },
      auth: { retryable: false, message: 'Authentication failed' }
    }

    const errorInfo = errorMap[errorType]
    logError(`Simulated ${errorType} error`, { endpoint: endpoint.url }, 'warning')

    return {
      error: errorType,
      retryable: errorInfo.retryable,
      fallbackConfig
    }
  }

  function createConfigWithRetry(
    endpoint: GraphQLEndpoint,
    options: RetryOptions
  ): RetryResult {
    try {
      const config = createStudioConfig(endpoint)

      return {
        config,
        retryCount: 0,
        canRetry: true
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      logError('Config creation failed, retry available', { endpoint, options, error: errorMessage })

      return {
        config: createFallbackConfig(endpoint),
        retryCount: 0,
        canRetry: options.retryableErrors.includes('config_creation'),
        lastError: errorMessage
      }
    }
  }

  function generateStudioUrlSafely(
    endpoint: GraphQLEndpoint,
    customParams: UrlParams = {}
  ): UrlSafetyResult {
    const warnings: string[] = []

    try {
      // Check for dangerous parameters
      const dangerousKeys = Object.keys(customParams).filter(key =>
        DANGEROUS_URL_PATTERNS.some(pattern => key.includes(pattern))
      )

      if (dangerousKeys.length > 0) {
        warnings.push('Dangerous parameters removed')
        logError('Dangerous URL parameters detected', { dangerousKeys }, 'warning')
      }

      // Check for function parameters (not serializable)
      const functionParams = Object.entries(customParams).filter(([_, value]) =>
        typeof value === 'function'
      )

      if (functionParams.length > 0) {
        warnings.push('Non-serializable parameters removed')
      }

      const sanitizedParams = sanitizeUrlParams(customParams)
      const url = generateStudioUrlWithParams(endpoint, sanitizedParams)

      return {
        success: true,
        url,
        sanitizedParams,
        warnings
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'URL generation failed'
      logError('Safe URL generation failed', { endpoint, customParams, error: errorMessage })

      return {
        success: false,
        url: generateStudioUrl(endpoint), // Fallback to basic URL
        sanitizedParams: {},
        warnings: ['Using fallback URL generation', ...warnings]
      }
    }
  }

  function switchEndpointSafely(
    fromEndpoint: GraphQLEndpoint,
    toEndpoint: GraphQLEndpoint,
    options?: SwitchEndpointOptions
  ): SafeResult<StudioConfig> {
    try {
      // Validate target endpoint first
      const validation = validateConfigurationSafely(toEndpoint)

      if (!validation.isValid) {
        return {
          success: false,
          error: `Invalid target endpoint: ${validation.errors.join(', ')}`,
          fallbackConfig: createStudioConfig(fromEndpoint),
          warnings: ['Using original endpoint as fallback']
        }
      }

      const config = switchEndpoint(fromEndpoint, toEndpoint, options)

      return {
        success: true,
        config,
        error: null
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Endpoint switching failed'
      logError('Safe endpoint switching failed', { fromEndpoint, toEndpoint, options, error: errorMessage })

      return {
        success: false,
        error: errorMessage,
        fallbackConfig: createStudioConfig(fromEndpoint),
        warnings: ['Using original endpoint as fallback']
      }
    }
  }

  function createIframeConfig(
    endpoint: GraphQLEndpoint,
    options: IframeConfigOptions = {}
  ): IframeConfig {
    const {
      enableErrorBoundary = true,
      fallbackContent = '<div>Apollo Studio is temporarily unavailable</div>',
      retryOnError = true,
      maxRetries = 3
    } = options

    let retryCount = 0

    const handleError = (error: Error) => {
      logError('Iframe loading error', { endpoint: endpoint.url, error: error.message })

      if (retryOnError && retryCount < maxRetries) {
        retryCount++
        logError(`Retrying iframe load (attempt ${retryCount}/${maxRetries})`, { endpoint: endpoint.url }, 'info')
      }
    }

    const handleRetry = () => {
      if (retryCount < maxRetries) {
        retryCount++
        logError(`Manual retry triggered (attempt ${retryCount}/${maxRetries})`, { endpoint: endpoint.url }, 'info')
      }
    }

    return {
      src: generateStudioUrl(endpoint),
      errorBoundary: enableErrorBoundary,
      fallbackContent,
      onError: handleError,
      onRetry: handleRetry
    }
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
    detectAuthType,
    // Endpoint switching functions
    switchEndpoint,
    switchEndpointWithAuth,
    // URL management functions
    validateEndpointUrl,
    sanitizeUrlParams,
    buildQueryString,
    generateStudioUrlWithParams,
    generateAuthenticatedStudioUrl,
    // Error handling functions
    validateConfigurationSafely,
    createStudioConfigSafely,
    createConfigWithAuthSafely,
    simulateNetworkError,
    createConfigWithRetry,
    generateStudioUrlSafely,
    switchEndpointSafely,
    createIframeConfig,
    // Error logging functions
    getErrorLog,
    clearErrorLog
  }
}
