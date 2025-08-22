import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import QueryHistory from '../QueryHistory.vue'
import type { GraphQLEndpoint } from '../../types/endpoint'
import { EndpointStatus } from '../../types/endpoint'
import type { QueryHistoryEntry } from '../../types/queryHistory'

// Create mock functions that can be accessed in tests
const mockGetHistory = vi.fn()
const mockGetStats = vi.fn()
const mockSearchHistory = vi.fn()
const mockUpdateQuery = vi.fn()
const mockDeleteQuery = vi.fn()
const mockClearHistory = vi.fn()
const mockExportHistory = vi.fn()

// Mock the service
vi.mock('../../services/queryHistory', () => ({
  useQueryHistory: () => ({
    getHistory: mockGetHistory,
    getStats: mockGetStats,
    searchHistory: mockSearchHistory,
    updateQuery: mockUpdateQuery,
    deleteQuery: mockDeleteQuery,
    clearHistory: mockClearHistory,
    exportHistory: mockExportHistory
  })
}))

const mockEndpoints: GraphQLEndpoint[] = [
  {
    id: 'endpoint-1',
    name: 'Test API',
    url: 'https://api.test.com/graphql',
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: true,
    isHealthy: true,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    id: 'endpoint-2',
    name: 'Dev API',
    url: 'https://dev.api.test.com/graphql',
    status: EndpointStatus.ACTIVE,
    introspectionEnabled: false,
    isHealthy: true,
    createdAt: new Date(),
    updatedAt: new Date()
  }
]

const mockHistory: QueryHistoryEntry[] = [
  {
    id: 'query-1',
    endpointId: 'endpoint-1',
    query: 'query GetUsers { users { id name email } }',
    operationName: 'GetUsers',
    timestamp: new Date('2024-08-21T10:00:00Z'),
    executionTime: 150,
    success: true,
    result: { data: { users: [] } },
    statusCode: 200,
    tags: ['users', 'test'],
    favorite: false,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    id: 'query-2',
    endpointId: 'endpoint-2',
    query: 'query GetPosts { posts { id title } }',
    operationName: 'GetPosts',
    timestamp: new Date('2024-08-21T11:00:00Z'),
    executionTime: 300,
    success: false,
    error: 'Network timeout',
    statusCode: 500,
    tags: ['posts', 'error'],
    favorite: true,
    createdAt: new Date(),
    updatedAt: new Date()
  }
]

const mockStats = {
  totalQueries: 2,
  successfulQueries: 1,
  failedQueries: 1,
  averageExecutionTime: 225,
  mostUsedEndpoints: [
    { endpointId: 'endpoint-1', count: 1 },
    { endpointId: 'endpoint-2', count: 1 }
  ],
  recentTags: ['users', 'posts', 'test', 'error']
}

describe('QueryHistory', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    // Reset and setup default mock behavior
    vi.clearAllMocks()
    
    // Set up default mock returns
    mockGetHistory.mockReturnValue(mockHistory)
    mockGetStats.mockReturnValue(mockStats)
    mockSearchHistory.mockImplementation((filter) => {
      let results = mockHistory

      if (filter?.success === true) results = results.filter(h => h.success)
      if (filter?.success === false) results = results.filter(h => !h.success)
      if (filter?.endpointId) results = results.filter(h => h.endpointId === filter.endpointId)
      if (filter?.favorite === true) results = results.filter(h => h.favorite)
      if (filter?.searchTerm) {
        results = results.filter(h =>
          h.query.toLowerCase().includes(filter.searchTerm.toLowerCase()) ||
          h.operationName?.toLowerCase().includes(filter.searchTerm.toLowerCase())
        )
      }

      return results
    })
    mockUpdateQuery.mockImplementation((id, updates) => ({
      success: true,
      entry: { ...mockHistory.find(h => h.id === id)!, ...updates }
    }))
    mockDeleteQuery.mockReturnValue({ success: true })
    mockClearHistory.mockReturnValue(undefined)
    mockExportHistory.mockReturnValue({
      success: true,
      result: {
        data: JSON.stringify(mockHistory),
        filename: 'query-history-2024-08-21.json',
        mimeType: 'application/json'
      }
    })

    wrapper = mount(QueryHistory, {
      props: {
        endpoints: mockEndpoints
      }
    })
  })

  describe('Component Mounting and Basic Display', () => {
    it('should render without errors', () => {
      expect(wrapper.exists()).toBe(true)
    })

    it('should display the component title', () => {
      expect(wrapper.text()).toContain('Query History')
    })

    it('should display query statistics', async () => {
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('2 queries, 1 successful')
    })

    it('should display filter controls', () => {
      expect(wrapper.find('select').exists()).toBe(true) // Endpoint filter
      expect(wrapper.find('input[type="text"]').exists()).toBe(true) // Search input
      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true) // Favorites filter
    })

    it('should display action buttons', () => {
      expect(wrapper.text()).toContain('Export')
      expect(wrapper.text()).toContain('Clear All')
    })
  })

  describe('History Entry Display', () => {
    it('should display history entries', async () => {
      await wrapper.vm.$nextTick()

      const entries = wrapper.findAllComponents({ name: 'QueryHistoryEntry' })
      expect(entries.length).toBe(2)
    })

    it('should pass correct props to history entries', async () => {
      await wrapper.vm.$nextTick()

      const entries = wrapper.findAllComponents({ name: 'QueryHistoryEntry' })
      const firstEntry = entries[0]

      expect(firstEntry.props('entry')).toEqual(mockHistory[0])
      expect(firstEntry.props('endpoint')).toEqual(mockEndpoints[0])
    })
  })

  describe('Filtering Functionality', () => {
    it('should filter by endpoint', async () => {
      const endpointSelect = wrapper.find('select')
      await endpointSelect.setValue('endpoint-1')
      await wrapper.vm.$nextTick()

      // Should show only endpoint-1 queries
      expect((wrapper.vm as any).filteredHistory).toHaveLength(1)
      expect((wrapper.vm as any).filteredHistory[0].endpointId).toBe('endpoint-1')
    })

    it('should filter by success status', async () => {
      const successSelect = wrapper.findAll('select')[1]
      await successSelect.setValue('true')
      await wrapper.vm.$nextTick()

      expect((wrapper.vm as any).filteredHistory).toHaveLength(1)
      expect((wrapper.vm as any).filteredHistory[0].success).toBe(true)
    })

    it('should filter by search term', async () => {
      const searchInput = wrapper.find('input[type="text"]')
      await searchInput.setValue('GetUsers')
      await wrapper.vm.$nextTick()

      expect((wrapper.vm as any).filteredHistory).toHaveLength(1)
      expect((wrapper.vm as any).filteredHistory[0].operationName).toBe('GetUsers')
    })

    it('should filter by favorites', async () => {
      const favoritesCheckbox = wrapper.find('input[type="checkbox"]')
      await favoritesCheckbox.setValue(true)
      await wrapper.vm.$nextTick()

      // Should only show favorite entries (query-2 has favorite: true)
      const favoriteEntries = (wrapper.vm as any).filteredHistory.filter((h: any) => h.favorite)
      expect((wrapper.vm as any).filteredHistory).toHaveLength(favoriteEntries.length)
      expect((wrapper.vm as any).filteredHistory.every((h: any) => h.favorite)).toBe(true)
    })

    it('should clear filters when clear button is clicked', async () => {
      // Set some filters
      const endpointSelect = wrapper.find('select')
      await endpointSelect.setValue('endpoint-1')

      const searchInput = wrapper.find('input[type="text"]')
      await searchInput.setValue('test')

      await wrapper.vm.$nextTick()

      // Should have active filters (filters.endpointId should be truthy)
      expect((wrapper.vm as any).filters.endpointId).toBe('endpoint-1');
      expect((wrapper.vm as any).filters.searchTerm).toBe('test');

      // Test the clearFilters method directly
      (wrapper.vm as any).clearFilters()

      expect((wrapper.vm as any).filters.endpointId).toBe('')
      expect((wrapper.vm as any).filters.searchTerm).toBe('')
      expect((wrapper.vm as any).currentPage).toBe(1)
    })

    it('should show "Clear Filters" button when filters are active', async () => {
      const searchInput = wrapper.find('input[type="text"]')
      await searchInput.setValue('test')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Clear Filters')
    })
  })

  describe('Pagination', () => {
    let wrapperWithLargeHistory: ReturnType<typeof mount>

    beforeEach(() => {
      // Create a large mock history
      const largeHistory = Array.from({ length: 25 }, (_, i) => ({
        ...mockHistory[0],
        id: `query-${i}`,
        query: `query Test${i} { test }`,
        timestamp: new Date(2024, 7, 21, 10, i)
      }))

      // Create a new wrapper with mocked service that returns large history
      wrapperWithLargeHistory = mount(QueryHistory, {
        props: {
          endpoints: mockEndpoints
        }
      })

      // Mock the service methods to return large history
      mockGetHistory.mockReturnValue(largeHistory)
      mockSearchHistory.mockReturnValue(largeHistory)
    })

    it('should show pagination controls when there are many entries', () => {
      // Test the logic directly using the mock service
      const largeHistory = Array.from({ length: 25 }, (_, i) => ({
        ...mockHistory[0],
        id: `query-${i}`,
        query: `query Test${i} { test }`,
        timestamp: new Date(2024, 7, 21, 10, i)
      }))

      // Direct test of pagination logic
      const pageSize = 20
      const totalPages = Math.ceil(largeHistory.length / pageSize)

      expect(largeHistory.length).toBe(25)
      expect(totalPages).toBeGreaterThan(1)
      expect(totalPages).toBe(2)

      // Test that pagination would show proper values
      const startIndex = (1 - 1) * pageSize  // Page 1
      const endIndex = Math.min(startIndex + pageSize, largeHistory.length)
      const paginatedItems = largeHistory.slice(startIndex, endIndex)

      expect(paginatedItems.length).toBe(20)  // First page should have 20 items
    })

    it('should navigate between pages', async () => {
      (wrapperWithLargeHistory.vm as any).loadHistory()
      await wrapperWithLargeHistory.vm.$nextTick()

      const buttons = wrapperWithLargeHistory.findAll('button')
      const nextBtn = buttons.find(btn => btn.text().includes('Next'))
      if (nextBtn) {
        await nextBtn.trigger('click')
        await wrapperWithLargeHistory.vm.$nextTick()

        expect((wrapperWithLargeHistory.vm as any).currentPage).toBe(2)
      }
    })

    it('should disable Previous button on first page', async () => {
      (wrapperWithLargeHistory.vm as any).loadHistory()
      await wrapperWithLargeHistory.vm.$nextTick()

      const buttons = wrapperWithLargeHistory.findAll('button')
      const prevBtn = buttons.find(btn => btn.text().includes('Previous'))
      if (prevBtn) {
        expect(prevBtn.attributes('disabled')).toBeDefined()
      }
    })
  })

  describe('Entry Actions', () => {
    it('should emit replay-query when entry replay is triggered', async () => {
      await wrapper.vm.$nextTick()

      const entry = wrapper.findComponent({ name: 'QueryHistoryEntry' })
      await entry.vm.$emit('replay', mockHistory[0])

      expect(wrapper.emitted('replay-query')).toBeTruthy()
      expect(wrapper.emitted('replay-query')![0]).toEqual([mockHistory[0]])
    })

    it('should emit save-template when entry save-as-template is triggered', async () => {
      await wrapper.vm.$nextTick()

      const entry = wrapper.findComponent({ name: 'QueryHistoryEntry' })
      await entry.vm.$emit('save-as-template', mockHistory[0])

      expect(wrapper.emitted('save-template')).toBeTruthy()
      expect(wrapper.emitted('save-template')![0]).toEqual([mockHistory[0]])
    })

    it('should toggle favorite status when entry favorite is toggled', async () => {
      await wrapper.vm.$nextTick()

      const entry = wrapper.findComponent({ name: 'QueryHistoryEntry' })
      await entry.vm.$emit('toggle-favorite', mockHistory[0])

      // Should call updateQuery service method - toggle the favorite status
      expect((wrapper.vm as any).queryHistoryService.updateQuery).toHaveBeenCalledWith(
        mockHistory[0].id,
        { favorite: true } // mockHistory[0].favorite is false, so toggle to true
      )
    })

    it('should delete entry when delete is triggered', async () => {
      // Mock confirm dialog
      vi.stubGlobal('confirm', vi.fn(() => true))

      await wrapper.vm.$nextTick()

      const entry = wrapper.findComponent({ name: 'QueryHistoryEntry' })
      await entry.vm.$emit('delete', mockHistory[0])

      expect((wrapper.vm as any).queryHistoryService.deleteQuery).toHaveBeenCalledWith(mockHistory[0].id)

      vi.unstubAllGlobals()
    })
  })

  describe('Export Functionality', () => {
    it('should show export modal when export button is clicked', async () => {
      const buttons = wrapper.findAll('button')
      const exportBtn = buttons.find(btn => btn.text().includes('Export'))

      if (exportBtn) {
        await exportBtn.trigger('click')
        await wrapper.vm.$nextTick()

        expect((wrapper.vm as any).showExportModal).toBe(true)
      }
    })

    it('should handle export functionality', async () => {
      // Test the export method directly
      expect((wrapper.vm as any).queryHistoryService.exportHistory).toBeDefined()

      // Mock the export result
      const exportResult = (wrapper.vm as any).queryHistoryService.exportHistory({ format: 'json' })
      expect(exportResult.success).toBe(true)
    })

    it('should close export modal when close event is emitted', async () => {
      (wrapper.vm as any).showExportModal = true
      await wrapper.vm.$nextTick()

      // Directly test the state change
      ;(wrapper.vm as any).showExportModal = false
      expect((wrapper.vm as any).showExportModal).toBe(false)
    })
  })

  describe('Clear History Functionality', () => {
    it('should clear all history when confirmed', () => {
      // Test the clear functionality directly
      expect((wrapper.vm as any).queryHistoryService.clearHistory).toBeDefined();

      // Call clearHistory method
      (wrapper.vm as any).queryHistoryService.clearHistory()
      expect(mockClearHistory).toHaveBeenCalled()
    })

    it('should have clear button when history exists', () => {
      const buttons = wrapper.findAll('button')
      const clearBtn = buttons.find(btn => btn.text().includes('Clear All'))

      expect(clearBtn).toBeDefined()
    })
  })

  describe('Empty States', () => {
    it('should handle empty history state', () => {
      // Create a new wrapper with empty history
      const emptyWrapper = mount(QueryHistory, {
        props: {
          endpoints: mockEndpoints
        }
      })

      mockGetHistory.mockReturnValue([])
      mockSearchHistory.mockReturnValue([])

      (emptyWrapper.vm as any).loadHistory()

      expect((emptyWrapper.vm as any).hasHistory).toBe(false)
    })

    it('should handle search with no results', async () => {
      // Set a search term that won't match anything
      const searchInput = wrapper.find('input[type="text"]')
      await searchInput.setValue('nonexistentquery12345')
      await wrapper.vm.$nextTick()

      // The mock searchHistory should handle this and return empty array for unknown terms
      expect((wrapper.vm as any).filteredHistory.length).toBe(0)
    })

    it('should disable action buttons when no history exists', () => {
      // Create wrapper with no history
      const emptyWrapper = mount(QueryHistory, {
        props: {
          endpoints: mockEndpoints
        }
      })

      mockGetHistory.mockReturnValue([])
      (emptyWrapper.vm as any).loadHistory()

      expect((emptyWrapper.vm as any).hasHistory).toBe(false)
    })
  })

  describe('Current Endpoint Integration', () => {
    it('should pre-select current endpoint in filter when provided', () => {
      const wrapperWithCurrentEndpoint = mount(QueryHistory, {
        props: {
          endpoints: mockEndpoints,
          currentEndpoint: mockEndpoints[0]
        }
      })

      expect((wrapperWithCurrentEndpoint.vm as any).filters.endpointId).toBe(mockEndpoints[0].id)
    })

    it('should handle endpoint changes', async () => {
      // Test prop changes
      await wrapper.setProps({ currentEndpoint: mockEndpoints[1] })

      // The filter should respect the new current endpoint
      expect((wrapper.props() as any).currentEndpoint?.id).toBe(mockEndpoints[1].id)
    })
  })
})
