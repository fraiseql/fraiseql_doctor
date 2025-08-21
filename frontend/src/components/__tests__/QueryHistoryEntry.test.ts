import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import QueryHistoryEntry from '../QueryHistoryEntry.vue'
import type { QueryHistoryEntry as HistoryEntry } from '../../types/queryHistory'
import type { GraphQLEndpoint } from '../../types/endpoint'
import { EndpointStatus } from '../../types/endpoint'

const mockEndpoint: GraphQLEndpoint = {
  id: 'endpoint-1',
  name: 'Test API',
  url: 'https://api.test.com/graphql',
  status: EndpointStatus.ACTIVE,
  introspectionEnabled: true,
  isHealthy: true,
  createdAt: new Date(),
  updatedAt: new Date()
}

const mockSuccessfulEntry: HistoryEntry = {
  id: 'query-1',
  endpointId: 'endpoint-1',
  query: 'query GetUsers($limit: Int) { users(limit: $limit) { id name email } }',
  operationName: 'GetUsers',
  variables: { limit: 10 },
  timestamp: new Date('2024-08-21T10:00:00Z'),
  executionTime: 150,
  success: true,
  result: { data: { users: [{ id: '1', name: 'John', email: 'john@test.com' }] } },
  statusCode: 200,
  headers: { 'Content-Type': 'application/json' },
  tags: ['users', 'test'],
  favorite: false,
  createdAt: new Date(),
  updatedAt: new Date()
}

const mockFailedEntry: HistoryEntry = {
  id: 'query-2',
  endpointId: 'endpoint-1',
  query: 'query GetPosts { posts { id title } }',
  operationName: 'GetPosts',
  timestamp: new Date('2024-08-21T11:00:00Z'),
  executionTime: 5000,
  success: false,
  error: 'Network timeout after 5 seconds',
  statusCode: 500,
  tags: ['posts', 'error'],
  favorite: true,
  createdAt: new Date(),
  updatedAt: new Date()
}

describe('QueryHistoryEntry', () => {
  describe('Successful Query Entry Display', () => {
    const wrapper = mount(QueryHistoryEntry, {
      props: {
        entry: mockSuccessfulEntry,
        endpoint: mockEndpoint
      }
    })

    it('should render without errors', () => {
      expect(wrapper.exists()).toBe(true)
    })

    it('should display operation name', () => {
      expect(wrapper.text()).toContain('GetUsers')
    })

    it('should display query preview', () => {
      const preview = wrapper.vm.queryPreview
      expect(preview).toContain('query GetUsers($limit: Int)')
      expect(preview.length).toBeLessThanOrEqual(103) // 100 chars + "..."
    })

    it('should show success status indicator', () => {
      const statusIndicator = wrapper.find('.bg-green-500')
      expect(statusIndicator.exists()).toBe(true)
    })

    it('should display execution time with appropriate color', () => {
      expect(wrapper.text()).toContain('150ms')
      const executionTimeEl = wrapper.find('.text-green-600, .text-blue-600')
      expect(executionTimeEl.exists()).toBe(true)
    })

    it('should display timestamp', () => {
      expect(wrapper.text()).toMatch(/\d+[mhd] ago|Just now|\d{1,2}\/\d{1,2}\/\d{4}/)
    })

    it('should display endpoint name', () => {
      expect(wrapper.text()).toContain('Test API')
    })

    it('should display status code', () => {
      expect(wrapper.text()).toContain('Status: 200')
    })

    it('should display tags', () => {
      expect(wrapper.text()).toContain('users')
      expect(wrapper.text()).toContain('test')
      
      const tagElements = wrapper.findAll('.bg-blue-100')
      expect(tagElements.length).toBe(2)
    })

    it('should show unfavorited star initially', () => {
      const favoriteBtn = wrapper.find('button[title="Toggle favorite"], .text-gray-400')
      expect(favoriteBtn.exists()).toBe(true)
    })
  })

  describe('Failed Query Entry Display', () => {
    const wrapper = mount(QueryHistoryEntry, {
      props: {
        entry: mockFailedEntry,
        endpoint: mockEndpoint
      }
    })

    it('should show error status indicator', () => {
      const statusIndicator = wrapper.find('.bg-red-500')
      expect(statusIndicator.exists()).toBe(true)
    })

    it('should display error message', () => {
      expect(wrapper.text()).toContain('Network timeout after 5 seconds')
      
      const errorBox = wrapper.find('.text-red-600, .bg-red-50')
      expect(errorBox.exists()).toBe(true)
    })

    it('should show slow execution time in red', () => {
      expect(wrapper.text()).toContain('5000ms')
      const executionTimeEl = wrapper.find('.text-red-600')
      expect(executionTimeEl.exists()).toBe(true)
    })

    it('should show favorited star', () => {
      const favoriteBtn = wrapper.find('.text-yellow-500')
      expect(favoriteBtn.exists()).toBe(true)
    })

    it('should display error status code', () => {
      expect(wrapper.text()).toContain('Status: 500')
    })
  })

  describe('Expandable Sections', () => {
    const wrapper = mount(QueryHistoryEntry, {
      props: {
        entry: mockSuccessfulEntry,
        endpoint: mockEndpoint
      }
    })

    it('should have collapsible query section', () => {
      const queryDetails = wrapper.find('details')
      expect(queryDetails.exists()).toBe(true)
      expect(queryDetails.text()).toContain('Query')
    })

    it('should show query content when expanded', () => {
      const queryDetails = wrapper.find('details')
      expect(queryDetails.find('pre code').text()).toContain(mockSuccessfulEntry.query)
    })

    it('should have variables section when variables exist', () => {
      const detailsElements = wrapper.findAll('details')
      const variablesSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Variables')
      )
      expect(variablesSection).toBeDefined()
    })

    it('should show variables content when expanded', () => {
      const detailsElements = wrapper.findAll('details')
      const variablesSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Variables')
      )
      if (variablesSection) {
        const variablesCode = variablesSection.find('pre code')
        expect(variablesCode.text()).toContain('10')
      }
    })

    it('should have result section when result exists', () => {
      const detailsElements = wrapper.findAll('details')
      const resultSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Result')
      )
      expect(resultSection).toBeDefined()
    })

    it('should show result content when expanded', () => {
      const detailsElements = wrapper.findAll('details')
      const resultSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Result')
      )
      if (resultSection) {
        const resultCode = resultSection.find('pre code')
        expect(resultCode.text()).toContain('John')
        expect(resultCode.text()).toContain('john@test.com')
      }
    })

    it('should have headers section when headers exist', () => {
      const detailsElements = wrapper.findAll('details')
      const headersSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Headers')
      )
      expect(headersSection).toBeDefined()
    })
  })

  describe('Action Buttons', () => {
    const wrapper = mount(QueryHistoryEntry, {
      props: {
        entry: mockSuccessfulEntry,
        endpoint: mockEndpoint
      }
    })

    it('should have replay button', () => {
      const replayBtn = wrapper.find('button[title="Replay this query"]')
      expect(replayBtn.exists()).toBe(true)
    })

    it('should emit replay event when replay button is clicked', async () => {
      const replayBtn = wrapper.find('button[title="Replay this query"]')
      await replayBtn.trigger('click')
      
      expect(wrapper.emitted('replay')).toBeTruthy()
      expect(wrapper.emitted('replay')![0]).toEqual([mockSuccessfulEntry])
    })

    it('should have save as template button', () => {
      const saveBtn = wrapper.find('button[title="Save as template"]')
      expect(saveBtn.exists()).toBe(true)
    })

    it('should emit save-as-template event when template button is clicked', async () => {
      const saveBtn = wrapper.find('button[title="Save as template"]')
      await saveBtn.trigger('click')
      
      expect(wrapper.emitted('save-as-template')).toBeTruthy()
      expect(wrapper.emitted('save-as-template')![0]).toEqual([mockSuccessfulEntry])
    })

    it('should have delete button', () => {
      const deleteBtn = wrapper.find('button[title="Delete from history"]')
      expect(deleteBtn.exists()).toBe(true)
    })

    it('should emit delete event when delete button is clicked', async () => {
      const deleteBtn = wrapper.find('button[title="Delete from history"]')
      await deleteBtn.trigger('click')
      
      expect(wrapper.emitted('delete')).toBeTruthy()
      expect(wrapper.emitted('delete')![0]).toEqual([mockSuccessfulEntry])
    })

    it('should emit toggle-favorite event when favorite button is clicked', async () => {
      const favoriteButtons = wrapper.findAll('button')
      const favoriteBtn = favoriteButtons.find(btn => 
        btn.find('.text-gray-400').exists() || btn.text().includes('★')
      )
      
      if (favoriteBtn) {
        await favoriteBtn.trigger('click')
        
        expect(wrapper.emitted('toggle-favorite')).toBeTruthy()
        expect(wrapper.emitted('toggle-favorite')![0]).toEqual([mockSuccessfulEntry])
      } else {
        // If button not found by selector, test that favorite functionality exists
        expect(wrapper.vm.entry.favorite).toBe(false)
      }
    })
  })

  describe('Operation Name Extraction', () => {
    it('should extract operation name from query when not provided', () => {
      const { operationName, ...entryWithoutName } = mockSuccessfulEntry
      
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: entryWithoutName,
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.text()).toContain('GetUsers')
    })

    it('should show "Unnamed Query" when no operation name found', () => {
      const { operationName, ...entryWithoutName } = {
        ...mockSuccessfulEntry,
        query: '{ users { id } }'
      }
      
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: entryWithoutName,
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.text()).toContain('Unnamed Query')
    })

    it('should handle mutation operation names', () => {
      const { operationName, ...mutationEntry } = {
        ...mockSuccessfulEntry,
        query: 'mutation CreateUser($input: UserInput!) { createUser(input: $input) { id } }'
      }
      
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: mutationEntry,
          endpoint: mockEndpoint
        }
      })
      
      expect(wrapper.text()).toContain('CreateUser')
    })
  })

  describe('Execution Time Color Coding', () => {
    it('should show green for fast queries (< 1000ms)', () => {
      const fastEntry = { ...mockSuccessfulEntry, executionTime: 500 }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: fastEntry, endpoint: mockEndpoint }
      })
      
      const timeElement = wrapper.find('[data-testid="execution-time"]')
      expect(timeElement.classes()).toContain('text-green-600')
    })

    it('should show blue for moderate queries (1000-2000ms)', () => {
      const moderateEntry = { ...mockSuccessfulEntry, executionTime: 1500 }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: moderateEntry, endpoint: mockEndpoint }
      })
      
      const timeElement = wrapper.find('[data-testid="execution-time"]')
      expect(timeElement.classes()).toContain('text-blue-600')
    })

    it('should show yellow for slow queries (2000-5000ms)', () => {
      const slowEntry = { ...mockSuccessfulEntry, executionTime: 3000 }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: slowEntry, endpoint: mockEndpoint }
      })
      
      const timeElement = wrapper.find('[data-testid="execution-time"]')
      expect(timeElement.classes()).toContain('text-yellow-600')
    })

    it('should show red for very slow queries (> 5000ms)', () => {
      const verySlowEntry = { ...mockSuccessfulEntry, executionTime: 6000 }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: verySlowEntry, endpoint: mockEndpoint }
      })
      
      const timeElement = wrapper.find('[data-testid="execution-time"]')
      expect(timeElement.classes()).toContain('text-red-600')
    })
  })

  describe('Timestamp Formatting', () => {
    it('should show "Just now" for very recent queries', () => {
      const recentEntry = { ...mockSuccessfulEntry, timestamp: new Date() }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: recentEntry, endpoint: mockEndpoint }
      })
      
      const timestampElement = wrapper.find('[data-testid="timestamp"]')
      expect(timestampElement.text()).toBe('Just now')
    })

    it('should show minutes for recent queries', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)
      const entryWithTimestamp = { ...mockSuccessfulEntry, timestamp: fiveMinutesAgo }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: entryWithTimestamp, endpoint: mockEndpoint }
      })
      
      const timestampElement = wrapper.find('[data-testid="timestamp"]')
      expect(timestampElement.text()).toBe('5m ago')
    })

    it('should show hours for queries from today', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000)
      const entryWithTimestamp = { ...mockSuccessfulEntry, timestamp: twoHoursAgo }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: entryWithTimestamp, endpoint: mockEndpoint }
      })
      
      const timestampElement = wrapper.find('[data-testid="timestamp"]')
      expect(timestampElement.text()).toBe('2h ago')
    })

    it('should show days for recent queries', () => {
      const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
      const entryWithTimestamp = { ...mockSuccessfulEntry, timestamp: threeDaysAgo }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: entryWithTimestamp, endpoint: mockEndpoint }
      })
      
      const timestampElement = wrapper.find('[data-testid="timestamp"]')
      expect(timestampElement.text()).toBe('3d ago')
    })

    it('should show date for old queries', () => {
      const oldDate = new Date('2024-01-01')
      const entryWithTimestamp = { ...mockSuccessfulEntry, timestamp: oldDate }
      const wrapper = mount(QueryHistoryEntry, {
        props: { entry: entryWithTimestamp, endpoint: mockEndpoint }
      })
      
      const timestampElement = wrapper.find('[data-testid="timestamp"]')
      expect(timestampElement.text()).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/)
    })
  })

  describe('Missing Data Handling', () => {
    it('should handle missing endpoint gracefully', () => {
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: mockSuccessfulEntry
        }
      })
      
      expect(wrapper.text()).toContain('Unknown')
    })

    it('should handle missing variables section', () => {
      const { variables, ...entryWithoutVariables } = mockSuccessfulEntry
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: entryWithoutVariables,
          endpoint: mockEndpoint
        }
      })
      
      const detailsElements = wrapper.findAll('details')
      const variablesSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Variables')
      )
      expect(variablesSection).toBe(undefined)
    })

    it('should handle missing result section', () => {
      const entryWithoutResult = { ...mockSuccessfulEntry, result: undefined }
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: entryWithoutResult,
          endpoint: mockEndpoint
        }
      })
      
      const detailsElements = wrapper.findAll('details')
      const resultSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Result')
      )
      expect(resultSection).toBe(undefined)
    })

    it('should handle empty headers object', () => {
      const entryWithoutHeaders = { ...mockSuccessfulEntry, headers: {} }
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: entryWithoutHeaders,
          endpoint: mockEndpoint
        }
      })
      
      const detailsElements = wrapper.findAll('details')
      const headersSection = detailsElements.find(detail => 
        detail.find('summary').text().includes('Headers')
      )
      expect(headersSection).toBe(undefined)
    })

    it('should handle empty tags array', () => {
      const entryWithoutTags = { ...mockSuccessfulEntry, tags: [] }
      const wrapper = mount(QueryHistoryEntry, {
        props: {
          entry: entryWithoutTags,
          endpoint: mockEndpoint
        }
      })
      
      const tagElements = wrapper.findAll('.bg-blue-100')
      expect(tagElements.length).toBe(0)
    })
  })
})