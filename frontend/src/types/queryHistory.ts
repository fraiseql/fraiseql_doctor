export interface QueryHistoryEntry {
  id: string
  endpointId: string
  query: string
  variables?: Record<string, any>
  operationName?: string
  timestamp: Date
  executionTime: number
  success: boolean
  result?: any
  error?: string
  statusCode?: number
  headers?: Record<string, string>
  tags: string[]
  favorite: boolean
  createdAt: Date
  updatedAt: Date
}

export interface QueryHistoryFilter {
  endpointId?: string
  success?: boolean
  fromDate?: Date
  toDate?: Date
  searchTerm?: string
  tags?: string[]
  favorite?: boolean
}

export interface QueryHistorySortOptions {
  field: 'timestamp' | 'executionTime' | 'createdAt'
  direction: 'asc' | 'desc'
}

export interface QueryHistoryStats {
  totalQueries: number
  successfulQueries: number
  failedQueries: number
  averageExecutionTime: number
  mostUsedEndpoints: Array<{
    endpointId: string
    count: number
  }>
  recentTags: string[]
}

export interface CreateQueryHistoryInput {
  endpointId: string
  query: string
  variables?: Record<string, any>
  operationName?: string
  executionTime: number
  success: boolean
  result?: any
  error?: string
  statusCode?: number
  headers?: Record<string, string>
  tags?: string[]
}

export interface UpdateQueryHistoryInput {
  tags?: string[]
  favorite?: boolean
}

export interface QueryHistoryExportOptions {
  format: 'json' | 'csv' | 'graphql'
  filter?: QueryHistoryFilter
  includeResults?: boolean
  includeVariables?: boolean
}

export interface QueryHistoryExportResult {
  data: string
  filename: string
  mimeType: string
}

export interface QueryTemplate {
  id: string
  name: string
  description?: string
  query: string
  variables?: Record<string, any>
  tags: string[]
  endpointIds: string[]
  favorite: boolean
  usageCount: number
  lastUsed?: Date
  createdAt: Date
  updatedAt: Date
}

export interface CreateQueryTemplateInput {
  name: string
  description?: string
  query: string
  variables?: Record<string, any>
  tags?: string[]
  endpointIds?: string[]
}

export interface QueryHistoryPreferences {
  maxHistoryEntries: number
  autoCapture: boolean
  captureResults: boolean
  captureVariables: boolean
  defaultTags: string[]
  exportDefaults: QueryHistoryExportOptions
}
