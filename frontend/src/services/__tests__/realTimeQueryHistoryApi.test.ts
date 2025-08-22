import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { RealTimeQueryHistoryApi, type QueryHistoryFilters, type HistoricalQueryData, type PerformanceTrend } from '../realTimeQueryHistoryApi'

describe('RealTimeQueryHistoryApi', () => {
  let queryHistoryApi: RealTimeQueryHistoryApi
  let mockFetch: any

  beforeEach(() => {
    mockFetch = vi.fn()
    global.fetch = mockFetch

    queryHistoryApi = new RealTimeQueryHistoryApi({
      baseUrl: 'https://api.example.com/graphql',
      apiKey: 'test-api-key',
      timeout: 5000
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Historical Query Data Retrieval', () => {
    it('should fetch historical query performance data with pagination', async () => {
      const mockHistoricalData: HistoricalQueryData[] = [
        {
          id: 'query-001',
          endpointId: 'endpoint-1',
          operationName: 'GetUsers',
          query: 'query GetUsers($limit: Int!) { users(limit: $limit) { id name email } }',
          variables: { limit: 20 },
          executionTime: 145,
          responseSize: 4096,
          timestamp: new Date('2024-01-15T10:30:00Z'),
          status: 'success',
          errors: null,
          clientInfo: {
            userAgent: 'GraphQL Client 1.0',
            ipAddress: '192.168.1.100',
            userId: 'user-123'
          },
          serverInfo: {
            resolverExecutionTimes: {
              'Query.users': 120,
              'User.id': 5,
              'User.name': 10,
              'User.email': 10
            },
            cacheHits: ['User:1', 'User:2'],
            cacheMisses: ['User:3', 'User:4'],
            databaseQueries: 2
          }
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            queryHistory: {
              queries: mockHistoricalData,
              totalCount: 150,
              hasNextPage: true,
              cursor: 'cursor-abc123'
            }
          }
        })
      })

      const filters: QueryHistoryFilters = {
        endpointId: 'endpoint-1',
        startTime: new Date('2024-01-15T00:00:00Z'),
        endTime: new Date('2024-01-15T23:59:59Z'),
        operationName: 'GetUsers',
        minExecutionTime: 100,
        maxExecutionTime: 1000,
        status: 'success'
      }

      const result = await queryHistoryApi.getQueryHistory(filters, {
        limit: 50,
        cursor: null
      })

      expect(result.queries).toHaveLength(1)
      expect(result.queries[0].operationName).toBe('GetUsers')
      expect(result.queries[0].executionTime).toBe(145)
      expect(result.queries[0].serverInfo.resolverExecutionTimes['Query.users']).toBe(120)
      expect(result.totalCount).toBe(150)
      expect(result.hasNextPage).toBe(true)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/graphql'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-api-key',
            'Content-Type': 'application/json'
          }),
          body: expect.stringContaining('query getQueryHistory')
        })
      )
    })

    it('should handle query history API errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          errors: [{
            message: 'Internal server error',
            code: 'INTERNAL_ERROR'
          }]
        })
      })

      await expect(queryHistoryApi.getQueryHistory({
        endpointId: 'endpoint-1',
        startTime: new Date(),
        endTime: new Date()
      })).rejects.toThrow('Internal server error')
    })

    it('should implement request timeout handling', async () => {
      vi.useFakeTimers()

      mockFetch.mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 10000))
      )

      const queryPromise = queryHistoryApi.getQueryHistory({
        endpointId: 'endpoint-1',
        startTime: new Date(),
        endTime: new Date()
      })

      vi.advanceTimersByTime(5000)

      await expect(queryPromise).rejects.toThrow('Request timeout')

      vi.useRealTimers()
    })
  })

  describe('Performance Trend Analysis', () => {
    it('should calculate performance trends over time periods', async () => {
      const mockTrendData: PerformanceTrend[] = [
        {
          period: '2024-01-15T10:00:00Z',
          endpointId: 'endpoint-1',
          metrics: {
            totalQueries: 120,
            averageExecutionTime: 180,
            medianExecutionTime: 150,
            p95ExecutionTime: 350,
            p99ExecutionTime: 500,
            errorRate: 0.025,
            throughput: 2.0,
            slowestQueries: [
              {
                operationName: 'GetUserPosts',
                executionTime: 500,
                count: 3
              }
            ]
          },
          comparisonToPrevious: {
            executionTimeChange: 15.5, // 15.5% increase
            throughputChange: -5.2,    // 5.2% decrease
            errorRateChange: 0.8       // 0.8% increase
          }
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            performanceTrends: mockTrendData
          }
        })
      })

      const trends = await queryHistoryApi.getPerformanceTrends({
        endpointId: 'endpoint-1',
        startTime: new Date('2024-01-15T00:00:00Z'),
        endTime: new Date('2024-01-15T23:59:59Z'),
        aggregationPeriod: '1h'
      })

      expect(trends).toHaveLength(1)
      expect(trends[0].metrics.averageExecutionTime).toBe(180)
      expect(trends[0].metrics.p95ExecutionTime).toBe(350)
      expect(trends[0].comparisonToPrevious.executionTimeChange).toBe(15.5)
      expect(trends[0].metrics.slowestQueries[0].operationName).toBe('GetUserPosts')
    })

    it('should identify performance anomalies in historical data', async () => {
      const mockAnomalies = {
        anomalies: [
          {
            id: 'anomaly-001',
            timestamp: new Date('2024-01-15T14:23:15Z'),
            type: 'execution_time_spike',
            severity: 'high',
            description: 'Execution time exceeded 3 standard deviations from baseline',
            metrics: {
              actualValue: 2500,
              expectedValue: 180,
              deviationScore: 3.8
            },
            affectedQueries: ['GetUserPosts', 'GetComments'],
            suggestedActions: [
              'Check database connection pool',
              'Review query complexity',
              'Examine server resource usage'
            ]
          }
        ],
        totalAnomalies: 1,
        timeRange: {
          start: new Date('2024-01-15T00:00:00Z'),
          end: new Date('2024-01-15T23:59:59Z')
        }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            performanceAnomalies: mockAnomalies
          }
        })
      })

      const anomalies = await queryHistoryApi.detectPerformanceAnomalies({
        endpointId: 'endpoint-1',
        startTime: new Date('2024-01-15T00:00:00Z'),
        endTime: new Date('2024-01-15T23:59:59Z'),
        sensitivityLevel: 'medium'
      })

      expect(anomalies.anomalies).toHaveLength(1)
      expect(anomalies.anomalies[0].type).toBe('execution_time_spike')
      expect(anomalies.anomalies[0].metrics.actualValue).toBe(2500)
      expect(anomalies.anomalies[0].suggestedActions).toContain('Check database connection pool')
    })
  })

  describe('Real-time Data Streaming', () => {
    it('should establish real-time query stream for live monitoring', async () => {
      const streamedQueries: HistoricalQueryData[] = []

      const mockEventSource = {
        addEventListener: vi.fn(),
        close: vi.fn(),
        readyState: 1 // EventSource.OPEN
      }

      const EventSourceMock = vi.fn().mockImplementation(() => mockEventSource)
      ;(EventSourceMock as any).CONNECTING = 0
      ;(EventSourceMock as any).OPEN = 1
      ;(EventSourceMock as any).CLOSED = 2
      global.EventSource = EventSourceMock as any

      const stream = await queryHistoryApi.streamLiveQueries({
        endpointId: 'endpoint-1',
        callback: (query) => streamedQueries.push(query)
      })

      expect(stream.id).toBeDefined()
      expect(stream.status).toBe('active')
      expect(global.EventSource).toHaveBeenCalledWith(
        expect.stringContaining('/stream/queries/endpoint-1')
      )

      // Simulate incoming real-time query data
      const mockQueryData: HistoricalQueryData = {
        id: 'query-live-001',
        endpointId: 'endpoint-1',
        operationName: 'GetRecentPosts',
        query: 'query GetRecentPosts { posts(limit: 10) { id title author } }',
        variables: { limit: 10 },
        executionTime: 95,
        responseSize: 1024,
        timestamp: new Date(),
        status: 'success',
        errors: null,
        clientInfo: {
          userAgent: 'Mobile App 2.1',
          ipAddress: '10.0.0.50',
          userId: 'user-456'
        },
        serverInfo: {
          resolverExecutionTimes: {
            'Query.posts': 80,
            'Post.id': 3,
            'Post.title': 6,
            'Post.author': 6
          },
          cacheHits: ['Post:1'],
          cacheMisses: ['Post:2', 'Post:3'],
          databaseQueries: 1
        }
      }

      // Trigger EventSource message
      const messageCallback = mockEventSource.addEventListener.mock.calls
        .find(call => call[0] === 'message')[1]

      messageCallback({
        data: JSON.stringify(mockQueryData)
      })

      expect(streamedQueries).toHaveLength(1)
      expect(streamedQueries[0].operationName).toBe('GetRecentPosts')
      expect(streamedQueries[0].executionTime).toBe(95)
    })

    it('should handle stream reconnection on connection loss', async () => {
      const reconnectCallback = vi.fn()

      const mockEventSource = {
        addEventListener: vi.fn(),
        close: vi.fn(),
        readyState: 0 // EventSource.CONNECTING
      }

      const EventSourceMock = vi.fn().mockImplementation(() => mockEventSource)
      ;(EventSourceMock as any).CONNECTING = 0
      ;(EventSourceMock as any).OPEN = 1
      ;(EventSourceMock as any).CLOSED = 2
      global.EventSource = EventSourceMock as any

      await queryHistoryApi.streamLiveQueries({
        endpointId: 'endpoint-1',
        callback: vi.fn(),
        onReconnect: reconnectCallback
      })

      // Simulate connection error
      const errorCallback = mockEventSource.addEventListener.mock.calls
        .find(call => call[0] === 'error')[1]

      errorCallback({ type: 'error' })

      // Wait for reconnection
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(global.EventSource).toHaveBeenCalledTimes(2) // Initial + reconnection
      expect(reconnectCallback).toHaveBeenCalled()
    })
  })

  describe('Advanced Query Analytics', () => {
    it('should analyze query complexity and performance correlation', async () => {
      const mockComplexityAnalysis = {
        queries: [
          {
            operationName: 'GetUserWithPosts',
            complexityScore: 25,
            averageExecutionTime: 180,
            fieldAnalysis: {
              totalFields: 15,
              nestedLevels: 3,
              connectionFields: 2,
              expensiveResolvers: ['User.posts', 'Post.comments']
            },
            performanceCorrelation: {
              complexityToTimeCorrelation: 0.85,
              predictedExecutionTime: 175,
              performanceRating: 'acceptable'
            }
          }
        ],
        aggregateMetrics: {
          averageComplexity: 18.5,
          complexityExecutionTimeCorrelation: 0.78,
          highComplexityQueries: 12,
          optimizationOpportunities: 3
        }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            queryComplexityAnalysis: mockComplexityAnalysis
          }
        })
      })

      const analysis = await queryHistoryApi.analyzeQueryComplexity({
        endpointId: 'endpoint-1',
        startTime: new Date('2024-01-15T00:00:00Z'),
        endTime: new Date('2024-01-15T23:59:59Z'),
        includeOptimizationSuggestions: true
      })

      expect(analysis.queries).toHaveLength(1)
      expect(analysis.queries[0].complexityScore).toBe(25)
      expect(analysis.queries[0].performanceCorrelation.complexityToTimeCorrelation).toBe(0.85)
      expect(analysis.aggregateMetrics.complexityExecutionTimeCorrelation).toBe(0.78)
      expect(analysis.aggregateMetrics.optimizationOpportunities).toBe(3)
    })
  })
})
