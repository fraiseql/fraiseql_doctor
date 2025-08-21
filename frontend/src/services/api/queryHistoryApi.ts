/**
 * API service for Query History - connects to backend FastAPI
 */

import type {
  QueryHistoryEntry,
  QueryHistoryFilter,
  QueryHistoryStats,
  CreateQueryHistoryInput,
  UpdateQueryHistoryInput,
  QueryHistoryExportOptions,
  QueryHistoryExportResult
} from '../../types/queryHistory'

export interface QueryHistoryApiResult<T> {
  success: boolean
  data?: T
  error?: string
  warnings?: string[]
}

export interface QueryHistoryListResponse {
  executions: QueryHistoryEntry[]
  total: number
  limit: number
  offset: number
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

class QueryHistoryApiService {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Get query history with filtering and pagination
   */
  async getHistory(
    filter?: QueryHistoryFilter,
    limit: number = 100,
    offset: number = 0
  ): Promise<QueryHistoryApiResult<QueryHistoryListResponse>> {
    try {
      const params = new URLSearchParams()
      
      if (filter?.endpointId) params.append('endpoint_id', filter.endpointId)
      if (filter?.success !== undefined) params.append('success', filter.success.toString())
      if (filter?.searchTerm) params.append('search', filter.searchTerm)
      if (filter?.favorite) params.append('favorite', filter.favorite.toString())
      if (filter?.fromDate) params.append('from_date', filter.fromDate.toISOString())
      if (filter?.toDate) params.append('to_date', filter.toDate.toISOString())
      
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await fetch(`${this.baseUrl}/api/v1/executions/?${params}`)
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`)
      }

      const data = await response.json() as QueryHistoryListResponse
      
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown API error'
      }
    }
  }

  /**
   * Get query history statistics
   */
  async getStats(filter?: QueryHistoryFilter): Promise<QueryHistoryApiResult<QueryHistoryStats>> {
    try {
      const params = new URLSearchParams()
      
      if (filter?.endpointId) params.append('endpoint_id', filter.endpointId)
      if (filter?.fromDate) params.append('from_date', filter.fromDate.toISOString())
      if (filter?.toDate) params.append('to_date', filter.toDate.toISOString())

      const response = await fetch(`${this.baseUrl}/api/v1/executions/stats?${params}`)
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`)
      }

      const data = await response.json()
      
      // Map backend response to frontend format
      const stats: QueryHistoryStats = {
        totalQueries: data.total_queries,
        successfulQueries: data.successful_queries,
        failedQueries: data.failed_queries,
        averageResponseTime: data.average_response_time
      }
      
      return {
        success: true,
        data: stats
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch stats'
      }
    }
  }

  /**
   * Add a new query execution to history
   */
  async addQuery(input: CreateQueryHistoryInput): Promise<QueryHistoryApiResult<QueryHistoryEntry>> {
    try {
      // For now, this would need to be implemented on the backend
      // The backend would create both a Query and an Execution record
      
      const response = await fetch(`${this.baseUrl}/api/v1/executions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          endpoint_id: input.endpointId,
          query: input.query,
          variables: input.variables,
          execution_time: input.executionTime,
          success: input.success,
          result: input.result,
          status_code: input.statusCode,
          error: input.error
        })
      })
      
      if (!response.ok) {
        throw new Error(`Failed to add query: ${response.status}`)
      }

      const data = await response.json() as QueryHistoryEntry
      
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to add query'
      }
    }
  }

  /**
   * Update query execution (e.g., toggle favorite)
   */
  async updateQuery(
    queryId: string, 
    updates: UpdateQueryHistoryInput
  ): Promise<QueryHistoryApiResult<QueryHistoryEntry>> {
    try {
      if (updates.favorite !== undefined) {
        // Toggle favorite via specific endpoint
        const response = await fetch(`${this.baseUrl}/api/v1/executions/${queryId}/favorite`, {
          method: 'POST'
        })
        
        if (!response.ok) {
          throw new Error(`Failed to toggle favorite: ${response.status}`)
        }

        // Get updated execution
        const execResponse = await fetch(`${this.baseUrl}/api/v1/executions/${queryId}`)
        const data = await execResponse.json() as QueryHistoryEntry
        
        return {
          success: true,
          data
        }
      }

      // For other updates, implement as needed
      throw new Error('Update type not implemented')
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update query'
      }
    }
  }

  /**
   * Delete query from history
   */
  async deleteQuery(queryId: string): Promise<QueryHistoryApiResult<boolean>> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/executions/${queryId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        throw new Error(`Failed to delete query: ${response.status}`)
      }

      return {
        success: true,
        data: true
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete query'
      }
    }
  }

  /**
   * Clear all query history
   */
  async clearHistory(endpointId?: string): Promise<QueryHistoryApiResult<boolean>> {
    try {
      const params = endpointId ? `?endpoint_id=${endpointId}` : ''
      const response = await fetch(`${this.baseUrl}/api/v1/executions/clear${params}`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error(`Failed to clear history: ${response.status}`)
      }

      return {
        success: true,
        data: true
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to clear history'
      }
    }
  }

  /**
   * Export query history
   */
  async exportHistory(options: QueryHistoryExportOptions): Promise<QueryHistoryApiResult<QueryHistoryExportResult>> {
    try {
      // For now, get the data and export client-side
      // In the future, this could be a backend endpoint
      
      const historyResult = await this.getHistory(options.filter, 10000, 0)  // Get all data
      
      if (!historyResult.success || !historyResult.data) {
        throw new Error('Failed to fetch history for export')
      }

      const { executions } = historyResult.data
      
      let exportData: string
      let mimeType: string
      let filename: string

      const timestamp = new Date().toISOString().split('T')[0]

      switch (options.format) {
        case 'json':
          exportData = JSON.stringify(executions, null, 2)
          mimeType = 'application/json'
          filename = `query-history-${timestamp}.json`
          break
          
        case 'csv':
          const csvHeaders = ['Timestamp', 'Endpoint', 'Query', 'Success', 'Response Time', 'Error']
          const csvRows = executions.map(entry => [
            entry.timestamp.toISOString(),
            entry.endpoint?.name || 'Unknown',
            entry.query.replace(/"/g, '""'), // Escape quotes
            entry.success ? 'Yes' : 'No',
            entry.executionTime?.toString() || '',
            entry.error || ''
          ])
          
          exportData = [
            csvHeaders.join(','),
            ...csvRows.map(row => row.map(cell => `"${cell}"`).join(','))
          ].join('\n')
          
          mimeType = 'text/csv'
          filename = `query-history-${timestamp}.csv`
          break
          
        case 'graphql':
          const queries = executions.map(entry => entry.query).join('\n\n# ---\n\n')
          exportData = `# Query History Export - ${timestamp}\n\n${queries}`
          mimeType = 'text/plain'
          filename = `queries-${timestamp}.graphql`
          break
          
        default:
          throw new Error(`Unsupported export format: ${options.format}`)
      }

      return {
        success: true,
        data: {
          data: exportData,
          filename,
          mimeType
        }
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Export failed'
      }
    }
  }

  /**
   * Test API connectivity
   */
  async testConnection(): Promise<QueryHistoryApiResult<boolean>> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      
      if (!response.ok) {
        throw new Error(`API health check failed: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.status !== 'healthy') {
        throw new Error('API reported unhealthy status')
      }

      return {
        success: true,
        data: true
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Connection test failed'
      }
    }
  }
}

// Export singleton instance
export const queryHistoryApi = new QueryHistoryApiService()
export default QueryHistoryApiService