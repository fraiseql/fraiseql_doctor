import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createFreshQueryHistory } from '../queryHistory'
import type {
  CreateQueryHistoryInput,
  QueryHistoryFilter,
  CreateQueryTemplateInput
} from '../../types/queryHistory'

describe('useQueryHistory', () => {
  let queryHistory: ReturnType<typeof createFreshQueryHistory>

  beforeEach(() => {
    localStorage.clear()
    queryHistory = createFreshQueryHistory()
  })


  describe('Basic Query History Management', () => {
    it('should add a query to history', () => {
      const input: CreateQueryHistoryInput = {
        endpointId: 'endpoint-1',
        query: 'query { users { id name } }',
        variables: { limit: 10 },
        operationName: 'GetUsers',
        executionTime: 150,
        success: true,
        result: { data: { users: [] } },
        statusCode: 200,
        tags: ['test', 'users']
      }

      const result = queryHistory.addQuery(input)

      expect(result.success).toBe(true)
      expect(result.entry).toBeDefined()
      expect(result.entry!.id).toBeDefined()
      expect(result.entry!.query).toBe(input.query)
      expect(result.entry!.endpointId).toBe(input.endpointId)
      expect(result.entry!.executionTime).toBe(input.executionTime)
      expect(result.entry!.success).toBe(true)
      expect(result.entry!.tags).toEqual(['test', 'users'])
      expect(result.entry!.timestamp).toBeInstanceOf(Date)
    })

    it('should handle invalid query input', () => {
      const input = {
        endpointId: '',
        query: '',
        executionTime: -1,
        success: true
      } as CreateQueryHistoryInput

      const result = queryHistory.addQuery(input)

      expect(result.success).toBe(false)
      expect(result.error).toContain('Invalid query input')
      expect(result.entry).toBeNull()
    })

    it('should get all history entries', () => {
      // Add multiple entries
      queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id } }',
        executionTime: 100,
        success: true
      })

      queryHistory.addQuery({
        endpointId: 'endpoint-2',
        query: 'query { posts { id title } }',
        executionTime: 200,
        success: false,
        error: 'Network error'
      })

      const history = queryHistory.getHistory()

      expect(history).toHaveLength(2)
      expect(history[0].query).toContain('posts')
      expect(history[1].query).toContain('users')
    })

    it('should get history entries by endpoint', () => {
      queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id } }',
        executionTime: 100,
        success: true
      })

      queryHistory.addQuery({
        endpointId: 'endpoint-2',
        query: 'query { posts { id } }',
        executionTime: 200,
        success: true
      })

      const endpoint1History = queryHistory.getHistoryByEndpoint('endpoint-1')
      const endpoint2History = queryHistory.getHistoryByEndpoint('endpoint-2')

      expect(endpoint1History).toHaveLength(1)
      expect(endpoint1History[0].query).toContain('users')
      expect(endpoint2History).toHaveLength(1)
      expect(endpoint2History[0].query).toContain('posts')
    })

    it('should delete a query from history', () => {
      const result = queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id } }',
        executionTime: 100,
        success: true
      })

      const queryId = result.entry!.id
      const deleteResult = queryHistory.deleteQuery(queryId)

      expect(deleteResult.success).toBe(true)
      expect(queryHistory.getHistory()).toHaveLength(0)
    })

    it('should handle deleting non-existent query', () => {
      const result = queryHistory.deleteQuery('non-existent-id')

      expect(result.success).toBe(false)
      expect(result.error).toContain('Query not found')
    })

    it('should update query properties', () => {
      const result = queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id } }',
        executionTime: 100,
        success: true,
        tags: ['initial']
      })

      const queryId = result.entry!.id
      const updateResult = queryHistory.updateQuery(queryId, {
        tags: ['updated', 'modified'],
        favorite: true
      })

      expect(updateResult.success).toBe(true)
      expect(updateResult.entry!.tags).toEqual(['updated', 'modified'])
      expect(updateResult.entry!.favorite).toBe(true)
    })

    it('should clear all history', () => {
      // Add some entries
      queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id } }',
        executionTime: 100,
        success: true
      })

      queryHistory.addQuery({
        endpointId: 'endpoint-2',
        query: 'query { posts { id } }',
        executionTime: 200,
        success: true
      })

      queryHistory.clearHistory()

      expect(queryHistory.getHistory()).toHaveLength(0)
    })
  })

  describe('Query History Filtering and Search', () => {
    beforeEach(() => {
      // Setup test data
      const testQueries = [
        {
          endpointId: 'endpoint-1',
          query: 'query GetUsers { users { id name email } }',
          executionTime: 100,
          success: true,
          tags: ['users', 'test'],
          timestamp: new Date('2024-01-01T10:00:00Z')
        },
        {
          endpointId: 'endpoint-1',
          query: 'query GetPosts { posts { id title content } }',
          executionTime: 200,
          success: false,
          error: 'Network timeout',
          tags: ['posts', 'error'],
          timestamp: new Date('2024-01-02T10:00:00Z')
        },
        {
          endpointId: 'endpoint-2',
          query: 'query GetComments { comments { id text } }',
          executionTime: 50,
          success: true,
          tags: ['comments'],
          timestamp: new Date('2024-01-03T10:00:00Z')
        }
      ]

      testQueries.forEach(query => {
        const input = { ...query } as CreateQueryHistoryInput
        delete (input as any).timestamp
        queryHistory.addQuery(input)
        // Manually set timestamp and favorite for testing
        const history = queryHistory.getHistory()
        const addedQuery = history.find(h => h.query === query.query)
        if (addedQuery) {
          addedQuery.timestamp = query.timestamp
          if (query.query.includes('GetComments')) {
            addedQuery.favorite = true
          }
        }
      })
    })

    it('should filter by endpoint', () => {
      const filter: QueryHistoryFilter = { endpointId: 'endpoint-1' }
      const filtered = queryHistory.searchHistory(filter)

      expect(filtered).toHaveLength(2)
      expect(filtered.every(q => q.endpointId === 'endpoint-1')).toBe(true)
    })

    it('should filter by success status', () => {
      const successFilter: QueryHistoryFilter = { success: true }
      const failedFilter: QueryHistoryFilter = { success: false }

      const successful = queryHistory.searchHistory(successFilter)
      const failed = queryHistory.searchHistory(failedFilter)

      expect(successful).toHaveLength(2)
      expect(failed).toHaveLength(1)
      expect(failed[0].success).toBe(false)
    })

    it('should filter by date range', () => {
      const filter: QueryHistoryFilter = {
        fromDate: new Date('2024-01-01T00:00:00Z'),
        toDate: new Date('2024-01-02T23:59:59Z')
      }

      const filtered = queryHistory.searchHistory(filter)

      expect(filtered).toHaveLength(2)
    })

    it('should filter by search term', () => {
      const filter: QueryHistoryFilter = { searchTerm: 'GetUsers' }
      const filtered = queryHistory.searchHistory(filter)

      expect(filtered).toHaveLength(1)
      expect(filtered[0].query).toContain('GetUsers')
    })

    it('should filter by tags', () => {
      const filter: QueryHistoryFilter = { tags: ['users'] }
      const filtered = queryHistory.searchHistory(filter)

      expect(filtered).toHaveLength(1)
      expect(filtered[0].tags).toContain('users')
    })

    it('should filter by favorite status', () => {
      const filter: QueryHistoryFilter = { favorite: true }
      const filtered = queryHistory.searchHistory(filter)

      expect(filtered).toHaveLength(1)
      expect(filtered[0].favorite).toBe(true)
    })

    it('should get recent queries', () => {
      const recent = queryHistory.getRecentQueries(2)

      expect(recent).toHaveLength(2)
      expect(recent[0].timestamp > recent[1].timestamp).toBe(true)
    })
  })

  describe('Query History Statistics', () => {
    beforeEach(() => {
      // Add test data for stats
      const testData = [
        { endpointId: 'endpoint-1', success: true, executionTime: 100, tags: ['users'] },
        { endpointId: 'endpoint-1', success: false, executionTime: 200, tags: ['posts'] },
        { endpointId: 'endpoint-2', success: true, executionTime: 50, tags: ['comments'] },
        { endpointId: 'endpoint-2', success: true, executionTime: 150, tags: ['users'] }
      ]

      testData.forEach((data, index) => {
        queryHistory.addQuery({
          query: `query Test${index} { test }`,
          ...data
        } as CreateQueryHistoryInput)
      })
    })

    it('should calculate query statistics', () => {
      const stats = queryHistory.getStats()

      expect(stats.totalQueries).toBe(4)
      expect(stats.successfulQueries).toBe(3)
      expect(stats.failedQueries).toBe(1)
      expect(stats.averageExecutionTime).toBe(125) // (100 + 200 + 50 + 150) / 4
      expect(stats.mostUsedEndpoints).toHaveLength(2)
      expect(stats.mostUsedEndpoints[0].count).toBe(2)
      expect(stats.recentTags).toContain('users')
      expect(stats.recentTags).toContain('posts')
      expect(stats.recentTags).toContain('comments')
    })

    it('should handle empty history for stats', () => {
      queryHistory.clearHistory()
      const stats = queryHistory.getStats()

      expect(stats.totalQueries).toBe(0)
      expect(stats.successfulQueries).toBe(0)
      expect(stats.failedQueries).toBe(0)
      expect(stats.averageExecutionTime).toBe(0)
      expect(stats.mostUsedEndpoints).toHaveLength(0)
      expect(stats.recentTags).toHaveLength(0)
    })
  })

  describe('Query History Export', () => {
    beforeEach(() => {
      queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id name } }',
        variables: { limit: 10 },
        executionTime: 100,
        success: true,
        result: { data: { users: [] } },
        tags: ['test']
      })
    })

    it('should export history as JSON', () => {
      const exportResult = queryHistory.exportHistory({ format: 'json' })

      expect(exportResult.success).toBe(true)
      expect(exportResult.result!.mimeType).toBe('application/json')
      expect(exportResult.result!.filename).toMatch(/query-history-\d{4}-\d{2}-\d{2}\.json/)

      const data = JSON.parse(exportResult.result!.data)
      expect(Array.isArray(data)).toBe(true)
      expect(data).toHaveLength(1)
      expect(data[0].query).toContain('users')
    })

    it('should export history as CSV', () => {
      const exportResult = queryHistory.exportHistory({ format: 'csv' })

      expect(exportResult.success).toBe(true)
      expect(exportResult.result!.mimeType).toBe('text/csv')
      expect(exportResult.result!.filename).toMatch(/query-history-\d{4}-\d{2}-\d{2}\.csv/)

      const csvData = exportResult.result!.data
      expect(csvData).toContain('id,endpointId,query,operationName,timestamp')
      expect(csvData).toContain('users')
    })

    it('should export filtered history', () => {
      queryHistory.addQuery({
        endpointId: 'endpoint-2',
        query: 'query { posts { id } }',
        executionTime: 200,
        success: false
      })

      const exportResult = queryHistory.exportHistory({
        format: 'json',
        filter: { success: true }
      })

      const data = JSON.parse(exportResult.result!.data)
      expect(data).toHaveLength(1)
      expect(data[0].success).toBe(true)
    })

    it('should handle empty export', () => {
      queryHistory.clearHistory()
      const exportResult = queryHistory.exportHistory({ format: 'json' })

      expect(exportResult.success).toBe(true)
      const data = JSON.parse(exportResult.result!.data)
      expect(data).toHaveLength(0)
    })
  })

  describe('Query Templates', () => {
    it('should add a query template', () => {
      const input: CreateQueryTemplateInput = {
        name: 'Get Users Template',
        description: 'Template for fetching users',
        query: 'query GetUsers($limit: Int) { users(limit: $limit) { id name } }',
        variables: { limit: 10 },
        tags: ['users', 'template'],
        endpointIds: ['endpoint-1', 'endpoint-2']
      }

      const result = queryHistory.addTemplate(input)

      expect(result.success).toBe(true)
      expect(result.template!.name).toBe(input.name)
      expect(result.template!.query).toBe(input.query)
      expect(result.template!.usageCount).toBe(0)
      expect(result.template!.id).toBeDefined()
    })

    it('should get all templates', () => {
      queryHistory.addTemplate({
        name: 'Template 1',
        query: 'query { users { id } }'
      })

      queryHistory.addTemplate({
        name: 'Template 2',
        query: 'query { posts { id } }'
      })

      const templates = queryHistory.getTemplates()

      expect(templates).toHaveLength(2)
      expect(templates.find(t => t.name === 'Template 1')).toBeDefined()
      expect(templates.find(t => t.name === 'Template 2')).toBeDefined()
    })

    it('should delete a template', () => {
      const result = queryHistory.addTemplate({
        name: 'Test Template',
        query: 'query { test }'
      })

      const templateId = result.template!.id
      const deleteResult = queryHistory.deleteTemplate(templateId)

      expect(deleteResult.success).toBe(true)
      expect(queryHistory.getTemplates()).toHaveLength(0)
    })

    it('should update a template', () => {
      const result = queryHistory.addTemplate({
        name: 'Original Template',
        query: 'query { test }',
        tags: ['original']
      })

      const templateId = result.template!.id
      const updateResult = queryHistory.updateTemplate(templateId, {
        name: 'Updated Template',
        tags: ['updated'],
        favorite: true
      })

      expect(updateResult.success).toBe(true)
      expect(updateResult.template!.name).toBe('Updated Template')
      expect(updateResult.template!.tags).toEqual(['updated'])
      expect(updateResult.template!.favorite).toBe(true)
    })

    it('should increment usage count when template is used', () => {
      const result = queryHistory.addTemplate({
        name: 'Usage Template',
        query: 'query { test }'
      })

      const template = result.template!

      // Simulate using the template by adding a query with the same content
      queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: template.query,
        executionTime: 100,
        success: true
      })

      // Template usage should be tracked
      const updatedTemplates = queryHistory.getTemplates()
      const usedTemplate = updatedTemplates.find(t => t.id === template.id)

      expect(usedTemplate!.usageCount).toBe(1)
      expect(usedTemplate!.lastUsed).toBeInstanceOf(Date)
    })
  })

  describe('Local Storage Persistence', () => {
    it('should persist history to localStorage', () => {
      queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { users { id } }',
        executionTime: 100,
        success: true
      })

      // Check localStorage
      const stored = localStorage.getItem('queryHistory')
      expect(stored).toBeDefined()

      const parsed = JSON.parse(stored!)
      expect(parsed).toHaveLength(1)
      expect(parsed[0].query).toContain('users')
    })

    it('should load history from localStorage on init', () => {
      // Manually set localStorage
      const mockHistory = [{
        id: 'test-id',
        endpointId: 'endpoint-1',
        query: 'query { test }',
        executionTime: 100,
        success: true,
        tags: [],
        favorite: false,
        timestamp: new Date().toISOString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }]

      localStorage.setItem('queryHistory', JSON.stringify(mockHistory))

      // Create new instance
      const newQueryHistory = createFreshQueryHistory(); const getNewHistory = newQueryHistory.getHistory
      const loaded = getNewHistory()

      expect(loaded).toHaveLength(1)
      expect(loaded[0].query).toBe('query { test }')
    })

    it('should handle corrupted localStorage gracefully', () => {
      localStorage.setItem('queryHistory', 'invalid-json')

      // Should not throw and should return empty history
      const newQueryHistory = createFreshQueryHistory(); const getNewHistory = newQueryHistory.getHistory
      const loaded = getNewHistory()

      expect(loaded).toHaveLength(0)
    })
  })

  describe('Error Handling', () => {
    it('should handle maximum history size limit', () => {
      // Mock a large number of queries
      vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(
        JSON.stringify(new Array(1001).fill(null).map((_, i) => ({
          id: `query-${i}`,
          endpointId: 'endpoint-1',
          query: `query Query${i} { test }`,
          executionTime: 100,
          success: true,
          tags: [],
          favorite: false,
          timestamp: new Date().toISOString(),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        })))
      )

      const newQueryHistory = createFreshQueryHistory(); const getNewHistory = newQueryHistory.getHistory; const newAddQuery = newQueryHistory.addQuery

      // Adding another query should remove the oldest
      const result = newAddQuery({
        endpointId: 'endpoint-1',
        query: 'query NewQuery { test }',
        executionTime: 100,
        success: true
      })

      expect(result.success).toBe(true)
      const history = getNewHistory()
      expect(history.length).toBeLessThanOrEqual(1000)
    })

    it('should handle localStorage quota exceeded', () => {
      // Mock localStorage to throw quota exceeded error
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem')
      mockSetItem.mockImplementation(() => {
        throw new DOMException('Quota exceeded', 'QuotaExceededError')
      })

      const result = queryHistory.addQuery({
        endpointId: 'endpoint-1',
        query: 'query { test }',
        executionTime: 100,
        success: true
      })

      // Should handle gracefully
      expect(result.success).toBe(false)
      expect(result.error).toContain('Storage quota exceeded')

      mockSetItem.mockRestore()
    })
  })
})
