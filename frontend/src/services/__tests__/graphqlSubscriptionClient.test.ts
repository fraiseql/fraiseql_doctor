import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { GraphQLSubscriptionClient, type QueryPerformanceData } from '../graphqlSubscriptionClient'

describe('GraphQLSubscriptionClient', () => {
  let subscriptionClient: GraphQLSubscriptionClient
  let mockWebSocket: any

  beforeEach(() => {
    // Mock WebSocket
    mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.OPEN,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    }

    const WebSocketMock = vi.fn().mockImplementation(() => mockWebSocket)
    ;(WebSocketMock as any).CONNECTING = 0
    ;(WebSocketMock as any).OPEN = 1
    ;(WebSocketMock as any).CLOSING = 2
    ;(WebSocketMock as any).CLOSED = 3
    global.WebSocket = WebSocketMock as any

    subscriptionClient = new GraphQLSubscriptionClient({
      endpoint: 'ws://localhost:4000/graphql',
      reconnectAttempts: 3,
      heartbeatInterval: 30000
    })
  })

  afterEach(() => {
    subscriptionClient?.disconnect()
    vi.clearAllMocks()
  })

  describe('Real-time Performance Monitoring', () => {
    it('should establish GraphQL subscription for query performance metrics', async () => {
      const performanceData: QueryPerformanceData[] = []

      const subscription = await subscriptionClient.subscribeToPerformanceMetrics({
        endpointId: 'test-endpoint-1',
        callback: (data) => performanceData.push(data)
      })

      expect(subscription.id).toBeDefined()
      expect(subscription.status).toBe('active')
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        expect.stringContaining('subscription queryPerformanceUpdates')
      )
    })

    it('should receive real-time query execution data via subscription', async () => {
      const receivedData: QueryPerformanceData[] = []

      await subscriptionClient.subscribeToPerformanceMetrics({
        endpointId: 'endpoint-1',
        callback: (data) => receivedData.push(data)
      })

      // Simulate incoming subscription data
      const mockPerformanceData: QueryPerformanceData = {
        id: 'query-123',
        endpointId: 'endpoint-1',
        operationName: 'GetUsers',
        query: 'query GetUsers { users { id name } }',
        variables: { limit: 10 },
        executionTime: 150,
        responseSize: 2048,
        timestamp: new Date(),
        status: 'success',
        errors: null,
        fieldExecutionTimes: {
          'users': 120,
          'users.id': 5,
          'users.name': 25
        }
      }

      // Trigger WebSocket message event
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'data',
          payload: {
            data: {
              queryPerformanceUpdates: mockPerformanceData
            }
          }
        })
      })

      mockWebSocket.addEventListener.mock.calls
        .find((call: any) => call[0] === 'message')[1](messageEvent)

      expect(receivedData).toHaveLength(1)
      expect(receivedData[0]).toEqual(mockPerformanceData)
      expect(receivedData[0].executionTime).toBe(150)
      expect(receivedData[0].operationName).toBe('GetUsers')
    })

    it('should handle subscription errors gracefully', async () => {
      const errorCallback = vi.fn()

      const subscription = await subscriptionClient.subscribeToPerformanceMetrics({
        endpointId: 'endpoint-1',
        callback: vi.fn(),
        onError: errorCallback
      })

      // Simulate subscription error
      const errorEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'error',
          payload: {
            message: 'Subscription failed: Invalid endpoint ID',
            code: 'SUBSCRIPTION_ERROR'
          }
        })
      })

      mockWebSocket.addEventListener.mock.calls
        .find((call: any) => call[0] === 'message')[1](errorEvent)

      expect(errorCallback).toHaveBeenCalledWith({
        message: 'Subscription failed: Invalid endpoint ID',
        code: 'SUBSCRIPTION_ERROR'
      })
      expect(subscription.status).toBe('error')
    })
  })

  describe('Advanced Query Analytics Subscriptions', () => {
    it('should subscribe to aggregated performance metrics by time windows', async () => {
      const aggregatedData: any[] = []

      await subscriptionClient.subscribeToAggregatedMetrics({
        endpointId: 'endpoint-1',
        timeWindow: '1m', // 1 minute aggregation
        callback: (data) => aggregatedData.push(data)
      })

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        expect.stringContaining('subscription aggregatedPerformanceMetrics')
      )

      // Simulate aggregated data
      const mockAggregatedData = {
        endpointId: 'endpoint-1',
        timeWindow: '1m',
        windowStart: new Date(),
        windowEnd: new Date(),
        metrics: {
          totalQueries: 150,
          averageExecutionTime: 180,
          p95ExecutionTime: 350,
          p99ExecutionTime: 500,
          errorRate: 0.02,
          throughput: 2.5
        }
      }

      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'data',
          payload: {
            data: {
              aggregatedPerformanceMetrics: mockAggregatedData
            }
          }
        })
      })

      mockWebSocket.addEventListener.mock.calls
        .find((call: any) => call[0] === 'message')[1](messageEvent)

      expect(aggregatedData).toHaveLength(1)
      expect(aggregatedData[0].metrics.totalQueries).toBe(150)
      expect(aggregatedData[0].metrics.p95ExecutionTime).toBe(350)
    })

    it('should subscribe to schema introspection changes', async () => {
      const schemaChanges: any[] = []

      await subscriptionClient.subscribeToSchemaChanges({
        endpointId: 'endpoint-1',
        callback: (change) => schemaChanges.push(change)
      })

      // Simulate schema change notification
      const schemaChangeData = {
        endpointId: 'endpoint-1',
        changeType: 'field_added',
        fieldPath: 'User.profilePicture',
        timestamp: new Date(),
        schemaVersion: '1.2.3',
        impactAnalysis: {
          breakingChange: false,
          affectedQueries: ['GetUserProfile', 'SearchUsers'],
          deprecationWarnings: []
        }
      }

      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'data',
          payload: {
            data: {
              schemaChanges: schemaChangeData
            }
          }
        })
      })

      mockWebSocket.addEventListener.mock.calls
        .find((call: any) => call[0] === 'message')[1](messageEvent)

      expect(schemaChanges).toHaveLength(1)
      expect(schemaChanges[0].changeType).toBe('field_added')
      expect(schemaChanges[0].impactAnalysis.breakingChange).toBe(false)
    })
  })

  describe('Connection Management', () => {
    it('should automatically reconnect on connection loss', async () => {
      const reconnectCallback = vi.fn()
      subscriptionClient.on('reconnected', reconnectCallback)

      await subscriptionClient.connect()

      // Simulate connection loss
      const closeEvent = new CloseEvent('close', { code: 1006, reason: 'Connection lost' })
      mockWebSocket.addEventListener.mock.calls
        .find((call: any) => call[0] === 'close')[1](closeEvent)

      // Wait for reconnection attempt
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(global.WebSocket).toHaveBeenCalledTimes(2) // Initial + reconnection
      expect(reconnectCallback).toHaveBeenCalled()
    })

    it('should implement subscription heartbeat to maintain connection', async () => {
      vi.useFakeTimers()

      await subscriptionClient.connect()

      // Fast-forward heartbeat interval
      vi.advanceTimersByTime(30000)

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"heartbeat"')
      )

      vi.useRealTimers()
    })

    it('should handle subscription cleanup on disconnect', async () => {
      await subscriptionClient.subscribeToPerformanceMetrics({
        endpointId: 'endpoint-1',
        callback: vi.fn()
      })

      await subscriptionClient.subscribeToAggregatedMetrics({
        endpointId: 'endpoint-2',
        timeWindow: '5m',
        callback: vi.fn()
      })

      expect(subscriptionClient.getActiveSubscriptions()).toHaveLength(2)

      subscriptionClient.disconnect()

      expect(subscriptionClient.getActiveSubscriptions()).toHaveLength(0)
      expect(mockWebSocket.close).toHaveBeenCalled()
    })
  })

  describe('Error Handling and Resilience', () => {
    it('should handle malformed subscription messages', async () => {
      const errorCallback = vi.fn()
      subscriptionClient.on('error', errorCallback)

      await subscriptionClient.connect()

      // Send malformed JSON
      const malformedEvent = new MessageEvent('message', {
        data: '{ invalid json'
      })

      mockWebSocket.addEventListener.mock.calls
        .find((call: any) => call[0] === 'message')[1](malformedEvent)

      expect(errorCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'parse_error',
          message: expect.stringContaining('Failed to parse')
        })
      )
    })

    it('should implement exponential backoff for reconnection attempts', async () => {
      vi.useFakeTimers()

      const reconnectDelays: number[] = []
      const originalSetTimeout = global.setTimeout

      // Mock setTimeout to track delays
      const mockSetTimeout = vi.fn().mockImplementation((callback: any, delay: number) => {
        reconnectDelays.push(delay)
        return originalSetTimeout(callback, 0) // Execute immediately for testing
      })
      Object.assign(mockSetTimeout, { __promisify__: vi.fn() })
      global.setTimeout = mockSetTimeout as any

      // Trigger multiple connection failures
      for (let i = 0; i < 3; i++) {
        const closeEvent = new CloseEvent('close', { code: 1006 })
        mockWebSocket.addEventListener.mock.calls
          .find((call: any) => call[0] === 'close')[1](closeEvent)

        await new Promise(resolve => setTimeout(resolve, 10))
      }

      // Verify exponential backoff: 1000ms, 2000ms, 4000ms
      expect(reconnectDelays).toEqual([1000, 2000, 4000])

      vi.useRealTimers()
    })
  })
})
