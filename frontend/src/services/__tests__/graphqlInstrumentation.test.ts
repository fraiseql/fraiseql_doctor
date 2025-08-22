import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { GraphQLInstrumentation, type InstrumentationConfig, type QueryExecution } from '../graphqlInstrumentation'

describe('GraphQLInstrumentation', () => {
  let instrumentation: GraphQLInstrumentation
  let mockGraphQLClient: any
  let mockPerformanceObserver: any

  beforeEach(() => {
    mockGraphQLClient = {
      query: vi.fn(),
      mutate: vi.fn(),
      subscribe: vi.fn()
    }

    mockPerformanceObserver = {
      observe: vi.fn(),
      disconnect: vi.fn(),
      takeRecords: vi.fn().mockReturnValue([])
    }

    const PerformanceObserverMock = vi.fn().mockImplementation((callback) => {
      mockPerformanceObserver.callback = callback
      return mockPerformanceObserver
    })
    ;(PerformanceObserverMock as any).supportedEntryTypes = ['measure', 'navigation']
    global.PerformanceObserver = PerformanceObserverMock as any

    const config: InstrumentationConfig = {
      enableDetailedTracing: true,
      captureVariables: true,
      captureErrors: true,
      samplingRate: 1.0,
      maxTraceDepth: 10,
      excludeIntrospection: true
    }

    instrumentation = new GraphQLInstrumentation(mockGraphQLClient, config)
  })

  afterEach(() => {
    instrumentation?.disable()
    vi.clearAllMocks()
  })

  describe('Query Execution Instrumentation', () => {
    it('should instrument GraphQL query execution with detailed timing', async () => {
      const mockQuery = `
        query GetUserProfile($userId: ID!) {
          user(id: $userId) {
            id
            name
            email
            posts {
              id
              title
              comments {
                id
                content
                author { name }
              }
            }
          }
        }
      `

      const mockResponse = {
        data: {
          user: {
            id: '1',
            name: 'John Doe',
            email: 'john@example.com',
            posts: [
              {
                id: '1',
                title: 'Test Post',
                comments: [
                  { id: '1', content: 'Great post!', author: { name: 'Jane' } }
                ]
              }
            ]
          }
        },
        extensions: {
          tracing: {
            version: 1,
            startTime: '2024-01-15T10:00:00.000Z',
            endTime: '2024-01-15T10:00:00.150Z',
            duration: 150000000, // nanoseconds
            execution: {
              resolvers: [
                {
                  path: ['user'],
                  parentType: 'Query',
                  fieldName: 'user',
                  returnType: 'User',
                  startOffset: 1000000,
                  duration: 50000000
                },
                {
                  path: ['user', 'posts'],
                  parentType: 'User',
                  fieldName: 'posts',
                  returnType: '[Post!]!',
                  startOffset: 60000000,
                  duration: 80000000
                }
              ]
            }
          }
        }
      }

      mockGraphQLClient.query.mockResolvedValueOnce(mockResponse)

      await instrumentation.enable()

      const execution = await instrumentation.executeQuery(mockQuery, {
        userId: '123'
      })

      expect(execution.operationName).toBe('GetUserProfile')
      expect(execution.executionTime).toBe(150)
      expect(execution.variables).toEqual({ userId: '123' })
      expect(execution.responseSize).toBeGreaterThan(0)
      expect(execution.resolverTraces).toHaveLength(2)

      const userResolver = execution.resolverTraces.find(r => r.fieldName === 'user')
      expect(userResolver?.duration).toBe(50)
      expect(userResolver?.path).toEqual(['user'])

      const postsResolver = execution.resolverTraces.find(r => r.fieldName === 'posts')
      expect(postsResolver?.duration).toBe(80)
      expect(postsResolver?.path).toEqual(['user', 'posts'])
    })

    it('should capture and analyze query complexity metrics', async () => {
      const complexQuery = `
        query ComplexQuery {
          users(first: 100) {
            edges {
              node {
                id
                posts(first: 50) {
                  edges {
                    node {
                      comments(first: 20) {
                        edges {
                          node {
                            author {
                              followers {
                                edges {
                                  node { id name }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      `

      const mockResponse = {
        data: { users: { edges: [] } },
        extensions: {
          tracing: { duration: 300000000 }, // 300ms
          complexity: {
            score: 1500,
            maximumAvailable: 10000,
            fieldCount: 25,
            connectionCount: 5,
            depthScore: 120
          }
        }
      }

      mockGraphQLClient.query.mockResolvedValueOnce(mockResponse)

      await instrumentation.enable()

      const execution = await instrumentation.executeQuery(complexQuery)

      expect(execution.complexity).toBeDefined()
      expect(execution.complexity?.score).toBe(1500)
      expect(execution.complexity?.fieldCount).toBe(25)
      expect(execution.complexity?.connectionCount).toBe(5)
      expect(execution.complexity?.depthScore).toBe(120)
      expect(execution.executionTime).toBe(300)
    })

    it('should handle and instrument GraphQL errors', async () => {
      const errorQuery = `
        query GetNonexistentUser($id: ID!) {
          user(id: $id) {
            id
            secretField
          }
        }
      `

      const mockErrorResponse = {
        data: { user: null },
        errors: [
          {
            message: 'User not found',
            locations: [{ line: 3, column: 5 }],
            path: ['user'],
            extensions: {
              code: 'NOT_FOUND',
              timestamp: '2024-01-15T10:00:00.000Z'
            }
          },
          {
            message: 'Field "secretField" is not accessible',
            locations: [{ line: 4, column: 7 }],
            path: ['user', 'secretField'],
            extensions: {
              code: 'FORBIDDEN',
              timestamp: '2024-01-15T10:00:00.050Z'
            }
          }
        ],
        extensions: {
          tracing: { duration: 45000000 } // 45ms
        }
      }

      mockGraphQLClient.query.mockResolvedValueOnce(mockErrorResponse)

      await instrumentation.enable()

      const execution = await instrumentation.executeQuery(errorQuery, { id: '999' })

      expect(execution.status).toBe('error')
      expect(execution.errors).toHaveLength(2)
      expect(execution.errors?.[0].message).toBe('User not found')
      expect(execution.errors?.[0].code).toBe('NOT_FOUND')
      expect(execution.errors?.[1].message).toBe('Field "secretField" is not accessible')
      expect(execution.errors?.[1].code).toBe('FORBIDDEN')
    })
  })

  describe('Performance Monitoring Integration', () => {
    it('should emit performance events for real-time monitoring', async () => {
      const performanceCallback = vi.fn()
      instrumentation.addEventListener('query-executed', performanceCallback)

      const mockQuery = 'query Simple { currentUser { id } }'
      const mockResponse = {
        data: { currentUser: { id: '1' } },
        extensions: { tracing: { duration: 75000000 } }
      }

      mockGraphQLClient.query.mockResolvedValueOnce(mockResponse)

      await instrumentation.enable()
      await instrumentation.executeQuery(mockQuery)

      expect(performanceCallback).toHaveBeenCalledWith({
        operationName: 'Simple',
        executionTime: 75,
        responseSize: expect.any(Number),
        timestamp: expect.any(Date),
        status: 'success',
        complexity: undefined,
        resolverTraces: [],
        cacheInfo: {
          hits: 0,
          misses: 0,
          ratio: 0
        }
      })
    })

    it('should integrate with browser Performance API for client-side metrics', async () => {
      const mockPerformanceEntries = [
        {
          name: 'graphql-query',
          entryType: 'measure',
          startTime: 1000,
          duration: 150,
          detail: {
            operationName: 'GetUser',
            queryId: 'query-123'
          }
        }
      ]

      mockPerformanceObserver.takeRecords.mockReturnValue(mockPerformanceEntries)

      await instrumentation.enable()

      // Simulate performance observer callback
      mockPerformanceObserver.callback({
        getEntries: () => mockPerformanceEntries
      })

      const clientMetrics = instrumentation.getClientSideMetrics()

      expect(clientMetrics.networkLatency).toBeDefined()
      expect(clientMetrics.parseTime).toBeDefined()
      expect(clientMetrics.renderTime).toBeDefined()
      expect(clientMetrics.totalRequestTime).toBe(150)
    })

    it('should implement sampling for high-volume applications', async () => {
      // Set low sampling rate
      const lowSamplingInstrumentation = new GraphQLInstrumentation(mockGraphQLClient, {
        samplingRate: 0.1, // 10% sampling
        enableDetailedTracing: true,
        captureVariables: true,
        captureErrors: true,
        maxTraceDepth: 10,
        excludeIntrospection: true
      })

      const mockQuery = 'query Test { test }'
      const mockResponse = { data: { test: 'value' } }
      mockGraphQLClient.query.mockResolvedValue(mockResponse)

      await lowSamplingInstrumentation.enable()

      const executions: QueryExecution[] = []
      lowSamplingInstrumentation.addEventListener('query-executed', (execution: any) => {
        executions.push(execution)
      })

      // Execute 100 queries
      const promises = Array.from({ length: 100 }, () =>
        lowSamplingInstrumentation.executeQuery(mockQuery)
      )

      await Promise.all(promises)

      // Should have sampled approximately 10% (allowing for randomness)
      expect(executions.length).toBeLessThan(30)
      expect(executions.length).toBeGreaterThan(5)

      lowSamplingInstrumentation.disable()
    })
  })

  describe('Advanced Tracing Features', () => {
    it('should trace nested resolver execution paths', async () => {
      const nestedQuery = `
        query GetUserWithNestedData($id: ID!) {
          user(id: $id) {
            profile {
              avatar {
                url
                metadata {
                  size
                  format
                }
              }
            }
          }
        }
      `

      const mockResponse = {
        data: {
          user: {
            profile: {
              avatar: {
                url: 'https://example.com/avatar.jpg',
                metadata: {
                  size: 1024,
                  format: 'JPEG'
                }
              }
            }
          }
        },
        extensions: {
          tracing: {
            execution: {
              resolvers: [
                {
                  path: ['user'],
                  parentType: 'Query',
                  fieldName: 'user',
                  returnType: 'User',
                  startOffset: 1000000,
                  duration: 20000000
                },
                {
                  path: ['user', 'profile'],
                  parentType: 'User',
                  fieldName: 'profile',
                  returnType: 'Profile',
                  startOffset: 25000000,
                  duration: 15000000
                },
                {
                  path: ['user', 'profile', 'avatar'],
                  parentType: 'Profile',
                  fieldName: 'avatar',
                  returnType: 'Avatar',
                  startOffset: 45000000,
                  duration: 30000000
                },
                {
                  path: ['user', 'profile', 'avatar', 'metadata'],
                  parentType: 'Avatar',
                  fieldName: 'metadata',
                  returnType: 'AvatarMetadata',
                  startOffset: 80000000,
                  duration: 10000000
                }
              ]
            }
          }
        }
      }

      mockGraphQLClient.query.mockResolvedValueOnce(mockResponse)

      await instrumentation.enable()

      const execution = await instrumentation.executeQuery(nestedQuery, { id: '1' })

      expect(execution.resolverTraces).toHaveLength(4)

      // Verify nested path structure
      const profileResolver = execution.resolverTraces.find(r =>
        r.path.join('.') === 'user.profile'
      )
      expect(profileResolver?.parentType).toBe('User')

      const metadataResolver = execution.resolverTraces.find(r =>
        r.path.join('.') === 'user.profile.avatar.metadata'
      )
      expect(metadataResolver?.parentType).toBe('Avatar')
      expect(metadataResolver?.duration).toBe(10)
    })

    it('should provide query optimization recommendations', async () => {
      const inefficientQuery = `
        query InefficientQuery {
          users {
            id
            posts {
              id
              comments {
                id
                author {
                  id
                  posts {
                    id
                    comments { id }
                  }
                }
              }
            }
          }
        }
      `

      const mockResponse = {
        data: { users: [] },
        extensions: {
          tracing: { duration: 2500000000 }, // 2.5 seconds
          complexity: { score: 5000 }
        }
      }

      mockGraphQLClient.query.mockResolvedValueOnce(mockResponse)

      await instrumentation.enable()

      const execution = await instrumentation.executeQuery(inefficientQuery)

      const recommendations = instrumentation.analyzeQueryPerformance(execution)

      expect(recommendations.optimizations).toContain('high_complexity')
      expect(recommendations.optimizations).toContain('slow_execution')
      expect(recommendations.suggestions).toContain('Consider using pagination')
      expect(recommendations.suggestions).toContain('Avoid deep nesting')
      expect(recommendations.severity).toBe('high')
    })
  })
})
