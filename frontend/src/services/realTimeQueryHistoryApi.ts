export interface QueryHistoryFilters {
  endpointId: string
  startTime: Date
  endTime: Date
  operationName?: string
  minExecutionTime?: number
  maxExecutionTime?: number
  status?: 'success' | 'error'
}

export interface HistoricalQueryData {
  id: string
  endpointId: string
  operationName: string
  query: string
  variables: Record<string, any>
  executionTime: number
  responseSize: number
  timestamp: Date
  status: 'success' | 'error'
  errors: any[] | null
  clientInfo: {
    userAgent: string
    ipAddress: string
    userId: string
  }
  serverInfo: {
    resolverExecutionTimes: Record<string, number>
    cacheHits: string[]
    cacheMisses: string[]
    databaseQueries: number
  }
}

export interface PerformanceTrend {
  period: string
  endpointId: string
  metrics: {
    totalQueries: number
    averageExecutionTime: number
    medianExecutionTime: number
    p95ExecutionTime: number
    p99ExecutionTime: number
    errorRate: number
    throughput: number
    slowestQueries: Array<{
      operationName: string
      executionTime: number
      count: number
    }>
  }
  comparisonToPrevious: {
    executionTimeChange: number
    throughputChange: number
    errorRateChange: number
  }
}

export interface PaginationOptions {
  limit: number
  cursor: string | null
}

export interface QueryHistoryResult {
  queries: HistoricalQueryData[]
  totalCount: number
  hasNextPage: boolean
  cursor?: string
}

export interface ApiConfig {
  baseUrl: string
  apiKey: string
  timeout: number
}

export interface LiveQueryStream {
  id: string
  status: 'active' | 'closed' | 'error'
}

export interface LiveQueryStreamOptions {
  endpointId: string
  callback: (query: HistoricalQueryData) => void
  onReconnect?: () => void
}

export class RealTimeQueryHistoryApi {
  private config: ApiConfig
  private requestCache: Map<string, { data: any; timestamp: number }> = new Map()
  private cacheTimeoutMs: number = 30000 // 30 seconds cache
  private retryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 8000
  }

  constructor(config: ApiConfig) {
    this.config = config
  }

  async getQueryHistory(
    filters: QueryHistoryFilters,
    pagination: PaginationOptions = { limit: 50, cursor: null }
  ): Promise<QueryHistoryResult> {
    const query = `
      query getQueryHistory(
        $endpointId: String!
        $startTime: DateTime!
        $endTime: DateTime!
        $operationName: String
        $minExecutionTime: Int
        $maxExecutionTime: Int
        $status: QueryStatus
        $limit: Int!
        $cursor: String
      ) {
        queryHistory(
          endpointId: $endpointId
          startTime: $startTime
          endTime: $endTime
          operationName: $operationName
          minExecutionTime: $minExecutionTime
          maxExecutionTime: $maxExecutionTime
          status: $status
          limit: $limit
          cursor: $cursor
        ) {
          queries {
            id
            endpointId
            operationName
            query
            variables
            executionTime
            responseSize
            timestamp
            status
            errors
            clientInfo {
              userAgent
              ipAddress
              userId
            }
            serverInfo {
              resolverExecutionTimes
              cacheHits
              cacheMisses
              databaseQueries
            }
          }
          totalCount
          hasNextPage
          cursor
        }
      }
    `

    const response = await this.makeRequest(query, {
      ...filters,
      ...pagination
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.errors?.[0]?.message || 'Failed to fetch query history')
    }

    const data = await response.json()
    return data.data.queryHistory
  }

  async getPerformanceTrends(options: {
    endpointId: string
    startTime: Date
    endTime: Date
    aggregationPeriod: string
  }): Promise<PerformanceTrend[]> {
    const query = `
      query getPerformanceTrends(
        $endpointId: String!
        $startTime: DateTime!
        $endTime: DateTime!
        $aggregationPeriod: String!
      ) {
        performanceTrends(
          endpointId: $endpointId
          startTime: $startTime
          endTime: $endTime
          aggregationPeriod: $aggregationPeriod
        ) {
          period
          endpointId
          metrics {
            totalQueries
            averageExecutionTime
            medianExecutionTime
            p95ExecutionTime
            p99ExecutionTime
            errorRate
            throughput
            slowestQueries {
              operationName
              executionTime
              count
            }
          }
          comparisonToPrevious {
            executionTimeChange
            throughputChange
            errorRateChange
          }
        }
      }
    `

    const response = await this.makeRequest(query, options)
    const data = await response.json()
    return data.data.performanceTrends
  }

  async detectPerformanceAnomalies(options: {
    endpointId: string
    startTime: Date
    endTime: Date
    sensitivityLevel: string
  }): Promise<any> {
    const query = `
      query detectPerformanceAnomalies(
        $endpointId: String!
        $startTime: DateTime!
        $endTime: DateTime!
        $sensitivityLevel: String!
      ) {
        performanceAnomalies(
          endpointId: $endpointId
          startTime: $startTime
          endTime: $endTime
          sensitivityLevel: $sensitivityLevel
        ) {
          anomalies {
            id
            timestamp
            type
            severity
            description
            metrics {
              actualValue
              expectedValue
              deviationScore
            }
            affectedQueries
            suggestedActions
          }
          totalAnomalies
          timeRange {
            start
            end
          }
        }
      }
    `

    const response = await this.makeRequest(query, options)
    const data = await response.json()
    return data.data.performanceAnomalies
  }

  async streamLiveQueries(options: LiveQueryStreamOptions): Promise<LiveQueryStream> {
    const streamId = this.generateId()
    const url = `${this.config.baseUrl.replace('http', 'ws')}/stream/queries/${options.endpointId}`

    const eventSource = new EventSource(url, {
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`
      }
    } as any)

    const stream: LiveQueryStream = {
      id: streamId,
      status: 'active'
    }

    eventSource.addEventListener('message', (event) => {
      try {
        const queryData = JSON.parse(event.data)
        options.callback(queryData)
      } catch (error) {
        console.error('Failed to parse live query data:', error)
      }
    })

    eventSource.addEventListener('error', () => {
      stream.status = 'error'

      // Attempt reconnection
      setTimeout(() => {
        if (options.onReconnect) {
          options.onReconnect()
        }
        this.streamLiveQueries(options)
      }, 1000)
    })

    ;(stream as any).eventSource = eventSource

    return stream
  }

  async analyzeQueryComplexity(options: {
    endpointId: string
    startTime: Date
    endTime: Date
    includeOptimizationSuggestions: boolean
  }): Promise<any> {
    const query = `
      query analyzeQueryComplexity(
        $endpointId: String!
        $startTime: DateTime!
        $endTime: DateTime!
        $includeOptimizationSuggestions: Boolean!
      ) {
        queryComplexityAnalysis(
          endpointId: $endpointId
          startTime: $startTime
          endTime: $endTime
          includeOptimizationSuggestions: $includeOptimizationSuggestions
        ) {
          queries {
            operationName
            complexityScore
            averageExecutionTime
            fieldAnalysis {
              totalFields
              nestedLevels
              connectionFields
              expensiveResolvers
            }
            performanceCorrelation {
              complexityToTimeCorrelation
              predictedExecutionTime
              performanceRating
            }
          }
          aggregateMetrics {
            averageComplexity
            complexityExecutionTimeCorrelation
            highComplexityQueries
            optimizationOpportunities
          }
        }
      }
    `

    const response = await this.makeRequest(query, options)
    const data = await response.json()
    return data.data.queryComplexityAnalysis
  }

  private async makeRequest(query: string, variables: Record<string, any>): Promise<Response> {
    // Check cache first
    const cacheKey = this.generateCacheKey(query, variables)
    const cached = this.getFromCache(cacheKey)
    if (cached) {
      return {
        ok: true,
        json: async () => cached
      } as Response
    }

    let lastError: Error | null = null

    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout)

      try {
        const response = await fetch(`${this.config.baseUrl}/graphql`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.config.apiKey}`
          },
          body: JSON.stringify({ query, variables }),
          signal: controller.signal
        })

        clearTimeout(timeoutId)

        // Cache successful responses
        if (response.ok) {
          const responseData = await response.clone().json()
          this.setCache(cacheKey, responseData)
        }

        return response
      } catch (error) {
        clearTimeout(timeoutId)
        lastError = error instanceof Error ? error : new Error(String(error))

        if (error instanceof Error && error.name === 'AbortError') {
          lastError = new Error('Request timeout')
        }

        // Don't retry on timeout or last attempt
        if (lastError.message === 'Request timeout' || attempt === this.retryConfig.maxRetries) {
          break
        }

        // Exponential backoff
        const delay = Math.min(
          this.retryConfig.baseDelay * Math.pow(2, attempt),
          this.retryConfig.maxDelay
        )
        await this.sleep(delay)
      }
    }

    throw lastError || new Error('Unknown error occurred')
  }

  private generateCacheKey(query: string, variables: Record<string, any>): string {
    return `${query.slice(0, 50)}_${JSON.stringify(variables)}`
  }

  private getFromCache(key: string): any | null {
    const cached = this.requestCache.get(key)
    if (cached && Date.now() - cached.timestamp < this.cacheTimeoutMs) {
      return cached.data
    }
    this.requestCache.delete(key)
    return null
  }

  private setCache(key: string, data: any): void {
    this.requestCache.set(key, {
      data,
      timestamp: Date.now()
    })

    // Cleanup old cache entries
    if (this.requestCache.size > 100) {
      const oldestKey = this.requestCache.keys().next().value
      this.requestCache.delete(oldestKey)
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private generateId(): string {
    return `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}
