export interface GraphQLEndpoint {
  id: string
  name: string
  url: string
  description?: string
  status: EndpointStatus
  lastChecked?: Date
  responseTime?: number
  headers?: Record<string, string>
  introspectionEnabled: boolean
  isHealthy: boolean
  errorMessage?: string
  createdAt: Date
  updatedAt: Date
}

export enum EndpointStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ERROR = 'error',
  CHECKING = 'checking'
}

export interface EndpointHealthCheck {
  id: string
  endpointId: string
  timestamp: Date
  isHealthy: boolean
  responseTime: number
  statusCode?: number
  errorMessage?: string
}

export interface CreateEndpointInput {
  name: string
  url: string
  description?: string
  headers?: Record<string, string>
  introspectionEnabled: boolean
}

export interface UpdateEndpointInput {
  name?: string
  url?: string
  description?: string
  headers?: Record<string, string>
  introspectionEnabled?: boolean
}

export interface EndpointTestResult {
  success: boolean
  responseTime: number
  statusCode?: number
  errorMessage?: string
  introspectionSchema?: string
}