import type {
  QueryHistoryEntry,
  QueryHistoryFilter,
  QueryHistoryStats,
  CreateQueryHistoryInput,
  UpdateQueryHistoryInput,
  QueryHistoryExportOptions,
  QueryHistoryExportResult,
  QueryTemplate,
  CreateQueryTemplateInput,
  QueryHistoryPreferences
} from '../types/queryHistory'

export interface QueryHistoryResult<T> {
  success: boolean
  entry?: T | null
  template?: QueryTemplate | null
  result?: QueryHistoryExportResult | null
  error?: string
  warnings?: string[]
}

const STORAGE_KEYS = {
  HISTORY: 'queryHistory',
  TEMPLATES: 'queryTemplates',
  PREFERENCES: 'queryHistoryPreferences'
} as const

const DEFAULT_PREFERENCES: QueryHistoryPreferences = {
  maxHistoryEntries: 1000,
  autoCapture: true,
  captureResults: true,
  captureVariables: true,
  defaultTags: [],
  exportDefaults: {
    format: 'json',
    includeResults: true,
    includeVariables: true
  }
}

// Each instance maintains its own cache to avoid cross-test contamination
function createQueryHistoryService() {
  let historyCache: QueryHistoryEntry[] = []
  let templatesCache: QueryTemplate[] = []
  let preferencesCache: QueryHistoryPreferences = { ...DEFAULT_PREFERENCES }
  let initialized = false

function generateId(): string {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(key)
    if (!stored) return defaultValue
    
    const parsed = JSON.parse(stored)
    
    // Convert date strings back to Date objects for history entries
    if (key === STORAGE_KEYS.HISTORY && Array.isArray(parsed)) {
      return parsed.map(entry => ({
        ...entry,
        timestamp: new Date(entry.timestamp),
        createdAt: new Date(entry.createdAt),
        updatedAt: new Date(entry.updatedAt),
        ...(entry.lastUsed && { lastUsed: new Date(entry.lastUsed) })
      })) as T
    }
    
    // Convert date strings back to Date objects for templates
    if (key === STORAGE_KEYS.TEMPLATES && Array.isArray(parsed)) {
      return parsed.map(template => ({
        ...template,
        createdAt: new Date(template.createdAt),
        updatedAt: new Date(template.updatedAt),
        ...(template.lastUsed && { lastUsed: new Date(template.lastUsed) })
      })) as T
    }
    
    return parsed
  } catch (error) {
    console.warn(`Failed to load ${key} from localStorage:`, error)
    return defaultValue
  }
}

function saveToStorage<T>(key: string, data: T): void {
  try {
    const serializable = JSON.stringify(data)
    localStorage.setItem(key, serializable)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      throw new Error('Storage quota exceeded. Please clear some history entries.')
    }
    throw new Error(`Failed to save ${key} to localStorage: ${error}`)
  }
}


function validateQueryInput(input: CreateQueryHistoryInput): string[] {
  const errors: string[] = []
  
  if (!input.endpointId || input.endpointId.trim().length === 0) {
    errors.push('Endpoint ID is required')
  }
  
  if (!input.query || input.query.trim().length === 0) {
    errors.push('Query is required')
  }
  
  if (input.executionTime < 0) {
    errors.push('Execution time must be non-negative')
  }
  
  return errors
}

function validateTemplateInput(input: CreateQueryTemplateInput): string[] {
  const errors: string[] = []
  
  if (!input.name || input.name.trim().length === 0) {
    errors.push('Template name is required')
  }
  
  if (!input.query || input.query.trim().length === 0) {
    errors.push('Template query is required')
  }
  
  return errors
}

function maintainHistoryLimit(): void {
  if (historyCache.length > preferencesCache.maxHistoryEntries) {
    // Sort by timestamp descending (newest first) and keep only the newest entries
    historyCache.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    historyCache = historyCache.slice(0, preferencesCache.maxHistoryEntries)
  }
}

function updateTemplateUsage(query: string): void {
  const matchingTemplate = templatesCache.find(template => 
    template.query.trim() === query.trim()
  )
  
  if (matchingTemplate) {
    matchingTemplate.usageCount += 1
    matchingTemplate.lastUsed = new Date()
    matchingTemplate.updatedAt = new Date()
    
    try {
      saveToStorage(STORAGE_KEYS.TEMPLATES, templatesCache)
    } catch (error) {
      console.warn('Failed to update template usage:', error)
    }
  }
}

  function initializeStorage(): void {
    if (initialized) return
    
    historyCache = loadFromStorage(STORAGE_KEYS.HISTORY, [])
    templatesCache = loadFromStorage(STORAGE_KEYS.TEMPLATES, [])
    preferencesCache = { ...DEFAULT_PREFERENCES, ...loadFromStorage(STORAGE_KEYS.PREFERENCES, {}) }
    
    initialized = true
  }

  // Initialize storage on first use
  initializeStorage()

  function addQuery(input: CreateQueryHistoryInput): QueryHistoryResult<QueryHistoryEntry> {
    try {
      const validationErrors = validateQueryInput(input)
      
      if (validationErrors.length > 0) {
        return {
          success: false,
          entry: null,
          error: `Invalid query input: ${validationErrors.join(', ')}`
        }
      }

      const now = new Date()
      const entry: QueryHistoryEntry = {
        id: generateId(),
        endpointId: input.endpointId,
        query: input.query,
        ...(input.variables && { variables: input.variables }),
        ...(input.operationName && { operationName: input.operationName }),
        timestamp: now,
        executionTime: input.executionTime,
        success: input.success,
        ...(input.result && { result: input.result }),
        ...(input.error && { error: input.error }),
        ...(input.statusCode && { statusCode: input.statusCode }),
        ...(input.headers && { headers: input.headers }),
        tags: input.tags || [],
        favorite: false,
        createdAt: now,
        updatedAt: now
      }

      historyCache.unshift(entry) // Add to beginning for newest-first
      maintainHistoryLimit()
      
      // Update template usage if query matches a template
      updateTemplateUsage(input.query)
      
      saveToStorage(STORAGE_KEYS.HISTORY, historyCache)
      
      return {
        success: true,
        entry
      }
    } catch (error) {
      return {
        success: false,
        entry: null,
        error: error instanceof Error ? error.message : 'Failed to add query to history'
      }
    }
  }

  function getHistory(): QueryHistoryEntry[] {
    return [...historyCache].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  }

  function getHistoryByEndpoint(endpointId: string): QueryHistoryEntry[] {
    return historyCache
      .filter(entry => entry.endpointId === endpointId)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  }

  function deleteQuery(id: string): QueryHistoryResult<null> {
    try {
      const index = historyCache.findIndex(entry => entry.id === id)
      
      if (index === -1) {
        return {
          success: false,
          error: 'Query not found in history'
        }
      }
      
      historyCache.splice(index, 1)
      saveToStorage(STORAGE_KEYS.HISTORY, historyCache)
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete query'
      }
    }
  }

  function updateQuery(id: string, updates: UpdateQueryHistoryInput): QueryHistoryResult<QueryHistoryEntry> {
    try {
      const entry = historyCache.find(entry => entry.id === id)
      
      if (!entry) {
        return {
          success: false,
          entry: null,
          error: 'Query not found in history'
        }
      }
      
      Object.assign(entry, updates, { updatedAt: new Date() })
      saveToStorage(STORAGE_KEYS.HISTORY, historyCache)
      
      return {
        success: true,
        entry
      }
    } catch (error) {
      return {
        success: false,
        entry: null,
        error: error instanceof Error ? error.message : 'Failed to update query'
      }
    }
  }

  function clearHistory(): void {
    historyCache = []
    saveToStorage(STORAGE_KEYS.HISTORY, historyCache)
  }

  function searchHistory(filter: QueryHistoryFilter = {}): QueryHistoryEntry[] {
    let filtered = [...historyCache]
    
    if (filter.endpointId) {
      filtered = filtered.filter(entry => entry.endpointId === filter.endpointId)
    }
    
    if (filter.success !== undefined) {
      filtered = filtered.filter(entry => entry.success === filter.success)
    }
    
    if (filter.fromDate) {
      filtered = filtered.filter(entry => entry.timestamp >= filter.fromDate!)
    }
    
    if (filter.toDate) {
      filtered = filtered.filter(entry => entry.timestamp <= filter.toDate!)
    }
    
    if (filter.searchTerm) {
      const searchTerm = filter.searchTerm.toLowerCase()
      filtered = filtered.filter(entry =>
        entry.query.toLowerCase().includes(searchTerm) ||
        entry.operationName?.toLowerCase().includes(searchTerm) ||
        entry.tags.some(tag => tag.toLowerCase().includes(searchTerm))
      )
    }
    
    if (filter.tags && filter.tags.length > 0) {
      filtered = filtered.filter(entry =>
        filter.tags!.some(tag => entry.tags.includes(tag))
      )
    }
    
    if (filter.favorite !== undefined) {
      filtered = filtered.filter(entry => entry.favorite === filter.favorite)
    }
    
    return filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  }

  function getRecentQueries(limit: number = 10): QueryHistoryEntry[] {
    return getHistory().slice(0, limit)
  }

  function getStats(): QueryHistoryStats {
    const total = historyCache.length
    const successful = historyCache.filter(entry => entry.success).length
    const failed = total - successful
    
    const totalExecutionTime = historyCache.reduce((sum, entry) => sum + entry.executionTime, 0)
    const averageExecutionTime = total > 0 ? Math.round(totalExecutionTime / total) : 0
    
    // Count endpoint usage
    const endpointCounts = historyCache.reduce((acc, entry) => {
      acc[entry.endpointId] = (acc[entry.endpointId] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const mostUsedEndpoints = Object.entries(endpointCounts)
      .map(([endpointId, count]) => ({ endpointId, count }))
      .sort((a, b) => b.count - a.count)
    
    // Get recent tags (from last 50 entries)
    const recentEntries = getHistory().slice(0, 50)
    const tagCounts = recentEntries.reduce((acc, entry) => {
      entry.tags.forEach(tag => {
        acc[tag] = (acc[tag] || 0) + 1
      })
      return acc
    }, {} as Record<string, number>)
    
    const recentTags = Object.keys(tagCounts).sort((a, b) => tagCounts[b] - tagCounts[a])
    
    return {
      totalQueries: total,
      successfulQueries: successful,
      failedQueries: failed,
      averageExecutionTime,
      mostUsedEndpoints,
      recentTags
    }
  }

  function exportHistory(options: QueryHistoryExportOptions): QueryHistoryResult<QueryHistoryExportResult> {
    try {
      const { format, filter, includeResults = true, includeVariables = true } = options
      
      let dataToExport = filter ? searchHistory(filter) : getHistory()
      
      // Remove sensitive data if requested
      if (!includeResults) {
        dataToExport = dataToExport.map(entry => {
          const { result, ...entryWithoutResult } = entry
          return entryWithoutResult
        })
      }
      
      if (!includeVariables) {
        dataToExport = dataToExport.map(entry => {
          const { variables, ...entryWithoutVariables } = entry
          return entryWithoutVariables
        })
      }
      
      const timestamp = new Date().toISOString().split('T')[0]
      let exportResult: QueryHistoryExportResult
      
      switch (format) {
        case 'json':
          exportResult = {
            data: JSON.stringify(dataToExport, null, 2),
            filename: `query-history-${timestamp}.json`,
            mimeType: 'application/json'
          }
          break
          
        case 'csv':
          const headers = [
            'id', 'endpointId', 'query', 'operationName', 'timestamp',
            'executionTime', 'success', 'error', 'statusCode', 'tags', 'favorite'
          ]
          
          if (includeVariables) headers.splice(-2, 0, 'variables')
          if (includeResults) headers.splice(-2, 0, 'result')
          
          const csvRows = [headers.join(',')]
          
          dataToExport.forEach(entry => {
            const row = [
              `"${entry.id}"`,
              `"${entry.endpointId}"`,
              `"${entry.query.replace(/"/g, '""')}"`,
              `"${entry.operationName || ''}"`,
              `"${entry.timestamp.toISOString()}"`,
              entry.executionTime.toString(),
              entry.success.toString(),
              `"${entry.error || ''}"`,
              (entry.statusCode || '').toString(),
              `"${entry.tags.join(';')}"`,
              entry.favorite.toString()
            ]
            
            if (includeVariables) {
              row.splice(-2, 0, `"${JSON.stringify(entry.variables || {}).replace(/"/g, '""')}"`)
            }
            
            if (includeResults) {
              row.splice(-2, 0, `"${JSON.stringify(entry.result || {}).replace(/"/g, '""')}"`)
            }
            
            csvRows.push(row.join(','))
          })
          
          exportResult = {
            data: csvRows.join('\n'),
            filename: `query-history-${timestamp}.csv`,
            mimeType: 'text/csv'
          }
          break
          
        case 'graphql':
          const graphqlQueries = dataToExport
            .map(entry => {
              const comment = `# ${entry.operationName || 'Query'} - ${entry.timestamp.toISOString()}\n# Endpoint: ${entry.endpointId}\n# Success: ${entry.success}, Time: ${entry.executionTime}ms\n`
              const variables = entry.variables ? `\n# Variables: ${JSON.stringify(entry.variables)}\n` : '\n'
              return comment + variables + entry.query
            })
            .join('\n\n# ---\n\n')
          
          exportResult = {
            data: graphqlQueries,
            filename: `query-history-${timestamp}.graphql`,
            mimeType: 'application/graphql'
          }
          break
          
        default:
          throw new Error(`Unsupported export format: ${format}`)
      }
      
      return {
        success: true,
        result: exportResult
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Export failed'
      }
    }
  }

  // Template management functions
  function addTemplate(input: CreateQueryTemplateInput): QueryHistoryResult<QueryTemplate> {
    try {
      const validationErrors = validateTemplateInput(input)
      
      if (validationErrors.length > 0) {
        return {
          success: false,
          template: null,
          error: `Invalid template input: ${validationErrors.join(', ')}`
        }
      }

      const now = new Date()
      const template: QueryTemplate = {
        id: generateId(),
        name: input.name,
        ...(input.description && { description: input.description }),
        query: input.query,
        ...(input.variables && { variables: input.variables }),
        tags: input.tags || [],
        endpointIds: input.endpointIds || [],
        favorite: false,
        usageCount: 0,
        createdAt: now,
        updatedAt: now
      }

      templatesCache.push(template)
      saveToStorage(STORAGE_KEYS.TEMPLATES, templatesCache)
      
      return {
        success: true,
        template
      }
    } catch (error) {
      return {
        success: false,
        template: null,
        error: error instanceof Error ? error.message : 'Failed to add template'
      }
    }
  }

  function getTemplates(): QueryTemplate[] {
    return [...templatesCache].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
  }

  function deleteTemplate(id: string): QueryHistoryResult<null> {
    try {
      const index = templatesCache.findIndex(template => template.id === id)
      
      if (index === -1) {
        return {
          success: false,
          error: 'Template not found'
        }
      }
      
      templatesCache.splice(index, 1)
      saveToStorage(STORAGE_KEYS.TEMPLATES, templatesCache)
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete template'
      }
    }
  }

  function updateTemplate(id: string, updates: Partial<QueryTemplate>): QueryHistoryResult<QueryTemplate> {
    try {
      const template = templatesCache.find(template => template.id === id)
      
      if (!template) {
        return {
          success: false,
          template: null,
          error: 'Template not found'
        }
      }
      
      Object.assign(template, updates, { updatedAt: new Date() })
      saveToStorage(STORAGE_KEYS.TEMPLATES, templatesCache)
      
      return {
        success: true,
        template
      }
    } catch (error) {
      return {
        success: false,
        template: null,
        error: error instanceof Error ? error.message : 'Failed to update template'
      }
    }
  }

  return {
    // History management
    addQuery,
    getHistory,
    getHistoryByEndpoint,
    deleteQuery,
    updateQuery,
    clearHistory,
    
    // Search and filtering
    searchHistory,
    getRecentQueries,
    getStats,
    
    // Export
    exportHistory,
    
    // Template management
    addTemplate,
    getTemplates,
    deleteTemplate,
    updateTemplate
  }
}

// Create a singleton instance
let serviceInstance: ReturnType<typeof createQueryHistoryService> | null = null

export function useQueryHistory() {
  if (!serviceInstance) {
    serviceInstance = createQueryHistoryService()
  }
  return serviceInstance
}

// For testing - create a fresh instance
export function createFreshQueryHistory() {
  return createQueryHistoryService()
}