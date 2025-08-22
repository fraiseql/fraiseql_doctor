export interface ApiEndpoint {
  id: string
  name: string
  url: string
  environment: 'dev' | 'staging' | 'prod'
  isHealthy: boolean
  responseTime: number
  errorRate?: number
  lastCheck: Date
  authentication?: {
    type: 'none' | 'bearer' | 'api-key' | 'basic'
    token?: string
  }
  monitoring?: {
    enabled: boolean
    interval: number
    thresholds: {
      responseTime: { warning: number; critical: number }
      errorRate: { warning: number; critical: number }
    }
  }
}

export interface ApiConfiguration {
  name: string
  environment: 'dev' | 'staging' | 'prod'
  authentication: {
    type: 'none' | 'bearer' | 'api-key' | 'basic'
    token?: string
  }
  thresholds: {
    responseTime: { warning: number; critical: number }
    errorRate: { warning: number; critical: number }
  }
}

export interface ApiHealthUpdate {
  apiId: string
  isHealthy: boolean
  responseTime: number
  errorRate?: number
  timestamp?: Date
}
