/**
 * Hybrid Query History Service
 * Automatically switches between API and localStorage based on connectivity
 */

import type {
  QueryHistoryEntry,
  QueryHistoryFilter,
  QueryHistoryStats,
  CreateQueryHistoryInput,
  UpdateQueryHistoryInput,
  QueryHistoryExportOptions,
  QueryHistoryExportResult,
  QueryTemplate
} from '../types/queryHistory'

import { queryHistoryApi } from './api/queryHistoryApi'
import { useQueryHistory as useLocalQueryHistory } from './queryHistory'

export interface QueryHistoryResult<T> {
  success: boolean
  entry?: T | null
  template?: QueryTemplate | null
  result?: QueryHistoryExportResult | null
  error?: string
  warnings?: string[]
  source?: 'api' | 'localStorage'
}

class HybridQueryHistoryService {
  private localService = useLocalQueryHistory()
  private apiConnected = false
  private connectionTestPromise: Promise<boolean> | null = null

  constructor() {
    // Test API connection on initialization
    this.testApiConnection()
  }

  private async testApiConnection(): Promise<boolean> {
    if (this.connectionTestPromise) {
      return this.connectionTestPromise
    }

    this.connectionTestPromise = (async () => {
      try {
        const result = await queryHistoryApi.testConnection()
        this.apiConnected = result.success
        console.log(`🔌 Query History API: ${this.apiConnected ? 'Connected' : 'Offline'}`)
        return this.apiConnected
      } catch (error) {
        console.warn('🔌 Query History API: Connection failed, using localStorage', error)
        this.apiConnected = false
        return false
      }
    })()

    return this.connectionTestPromise
  }

  /**
   * Get query history - tries API first, falls back to localStorage
   */
  async getHistory(): Promise<QueryHistoryEntry[]> {
    await this.testApiConnection()

    if (this.apiConnected) {
      try {
        const result = await queryHistoryApi.getHistory()
        if (result.success && result.data) {
          return result.data.executions
        }
      } catch (error) {
        console.warn('Failed to fetch from API, falling back to localStorage', error)
        this.apiConnected = false
      }
    }

    // Fallback to localStorage
    return this.localService.getHistory()
  }

  /**
   * Search query history with filters
   */
  async searchHistory(filter: QueryHistoryFilter): Promise<QueryHistoryEntry[]> {
    await this.testApiConnection()

    if (this.apiConnected) {
      try {
        const result = await queryHistoryApi.getHistory(filter)
        if (result.success && result.data) {
          return result.data.executions
        }
      } catch (error) {
        console.warn('API search failed, falling back to localStorage', error)
      }
    }

    // Fallback to localStorage
    return this.localService.searchHistory(filter)
  }

  /**
   * Get query history statistics
   */
  async getStats(): Promise<QueryHistoryStats> {
    await this.testApiConnection()

    if (this.apiConnected) {
      try {
        const result = await queryHistoryApi.getStats()
        if (result.success && result.data) {
          return result.data
        }
      } catch (error) {
        console.warn('API stats failed, falling back to localStorage', error)
      }
    }

    // Fallback to localStorage
    return this.localService.getStats()
  }

  /**
   * Add query to history
   */
  async addQuery(input: CreateQueryHistoryInput): Promise<QueryHistoryResult<QueryHistoryEntry>> {
    await this.testApiConnection()

    // Always save to localStorage for offline access
    const localResult = this.localService.addQuery(input)

    if (this.apiConnected) {
      try {
        const apiResult = await queryHistoryApi.addQuery(input)
        if (apiResult.success && apiResult.data) {
          return {
            success: true,
            entry: apiResult.data,
            source: 'api'
          }
        }
      } catch (error) {
        console.warn('Failed to save to API, kept in localStorage', error)
      }
    }

    // Return localStorage result with source indication
    return {
      ...localResult,
      source: 'localStorage'
    }
  }

  /**
   * Update query (e.g., toggle favorite)
   */
  async updateQuery(
    queryId: string, 
    updates: UpdateQueryHistoryInput
  ): Promise<QueryHistoryResult<QueryHistoryEntry>> {
    await this.testApiConnection()

    // Update localStorage first
    const localResult = this.localService.updateQuery(queryId, updates)

    if (this.apiConnected) {
      try {
        const apiResult = await queryHistoryApi.updateQuery(queryId, updates)
        if (apiResult.success && apiResult.data) {
          return {
            success: true,
            entry: apiResult.data,
            source: 'api'
          }
        }
      } catch (error) {
        console.warn('Failed to update via API, kept localStorage change', error)
      }
    }

    return {
      ...localResult,
      source: 'localStorage'
    }
  }

  /**
   * Delete query from history
   */
  async deleteQuery(queryId: string): Promise<QueryHistoryResult<boolean>> {
    await this.testApiConnection()

    // Delete from localStorage
    const localResult = this.localService.deleteQuery(queryId)

    if (this.apiConnected) {
      try {
        const apiResult = await queryHistoryApi.deleteQuery(queryId)
        if (apiResult.success) {
          return {
            success: true,
            entry: true,
            source: 'api'
          }
        }
      } catch (error) {
        console.warn('Failed to delete via API, deleted from localStorage only', error)
      }
    }

    return {
      ...localResult,
      source: 'localStorage'
    }
  }

  /**
   * Clear all history
   */
  async clearHistory(): Promise<QueryHistoryResult<boolean>> {
    await this.testApiConnection()

    // Clear localStorage
    this.localService.clearHistory()

    if (this.apiConnected) {
      try {
        const apiResult = await queryHistoryApi.clearHistory()
        if (apiResult.success) {
          return {
            success: true,
            entry: true,
            source: 'api'
          }
        }
      } catch (error) {
        console.warn('Failed to clear via API, cleared localStorage only', error)
      }
    }

    return {
      success: true,
      source: 'localStorage'
    }
  }

  /**
   * Export history - combines API and localStorage data
   */
  async exportHistory(options: QueryHistoryExportOptions): Promise<QueryHistoryResult<QueryHistoryExportResult>> {
    await this.testApiConnection()

    if (this.apiConnected) {
      try {
        const apiResult = await queryHistoryApi.exportHistory(options)
        if (apiResult.success && apiResult.data) {
          return {
            success: true,
            result: apiResult.data,
            source: 'api'
          }
        }
      } catch (error) {
        console.warn('API export failed, falling back to localStorage', error)
      }
    }

    // Fallback to localStorage export
    const localResult = this.localService.exportHistory(options)
    return {
      ...localResult,
      source: 'localStorage'
    }
  }

  /**
   * Get connection status
   */
  isApiConnected(): boolean {
    return this.apiConnected
  }

  /**
   * Force reconnection test
   */
  async reconnect(): Promise<boolean> {
    this.connectionTestPromise = null
    return await this.testApiConnection()
  }
}

// Export singleton instance
export const useQueryHistoryHybrid = () => new HybridQueryHistoryService()
export default HybridQueryHistoryService