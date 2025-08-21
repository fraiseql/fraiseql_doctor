import type { EndpointTestResult } from '../../types/endpoint'

// Mock GraphQL client for testing endpoints
export function useGraphQLClient() {
  async function testEndpoint(url: string): Promise<EndpointTestResult> {
    const startTime = Date.now()

    try {
      // Simulate network request
      await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 100))

      const responseTime = Date.now() - startTime

      // Mock different responses based on URL
      if (url.includes('dev.com')) {
        return {
          success: false,
          responseTime,
          statusCode: 0,
          errorMessage: 'Connection timeout'
        }
      }

      if (url.includes('staging.com')) {
        return {
          success: true,
          responseTime,
          statusCode: 200
        }
      }

      // Default successful response
      return {
        success: true,
        responseTime,
        statusCode: 200,
        introspectionSchema: getMockIntrospectionSchema()
      }
    } catch (error) {
      return {
        success: false,
        responseTime: Date.now() - startTime,
        errorMessage: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  async function getIntrospectionSchema(url: string): Promise<string | null> {
    try {
      const result = await testEndpoint(url)
      return result.introspectionSchema || null
    } catch (error) {
      console.error('Failed to get introspection schema:', error)
      return null
    }
  }

  function getMockIntrospectionSchema(): string {
    return `
      type Query {
        user(id: ID!): User
        users(limit: Int, offset: Int): [User!]!
        posts(authorId: ID): [Post!]!
      }

      type Mutation {
        createUser(input: CreateUserInput!): User!
        updateUser(id: ID!, input: UpdateUserInput!): User!
        deleteUser(id: ID!): Boolean!
      }

      type User {
        id: ID!
        name: String!
        email: String!
        posts: [Post!]!
        createdAt: String!
        updatedAt: String!
      }

      type Post {
        id: ID!
        title: String!
        content: String!
        author: User!
        publishedAt: String
        createdAt: String!
        updatedAt: String!
      }

      input CreateUserInput {
        name: String!
        email: String!
      }

      input UpdateUserInput {
        name: String
        email: String
      }
    `.trim()
  }

  return {
    testEndpoint,
    getIntrospectionSchema
  }
}
