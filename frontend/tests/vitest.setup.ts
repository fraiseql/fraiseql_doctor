import { beforeAll, afterEach } from 'vitest'

// Mock DOM methods that JSDOM doesn't fully support
beforeAll(() => {
  // Mock document methods
  if (typeof document !== 'undefined') {
    // Ensure document.body exists
    if (!document.body) {
      document.body = document.createElement('body')
    }
    
    // Mock insertBefore if it doesn't exist properly
    const originalInsertBefore = document.body.insertBefore
    if (!originalInsertBefore || typeof originalInsertBefore !== 'function') {
      document.body.insertBefore = function(newNode: Node, referenceNode: Node | null) {
        if (referenceNode) {
          return this.appendChild(newNode)
        }
        return this.appendChild(newNode)
      }
    }
  }

  // Mock URL and Blob for file download tests
  global.URL = {
    createObjectURL: () => 'blob:test-url',
    revokeObjectURL: () => {}
  } as any

  global.Blob = class MockBlob {
    constructor(content: any[], options?: any) {
      this.size = 0
      this.type = options?.type || ''
    }
    size: number
    type: string
  } as any

  // Mock confirm and alert
  global.confirm = () => true
  global.alert = () => {}
})

// Cleanup after each test
afterEach(() => {
  // Reset any global mocks if needed
  if (typeof window !== 'undefined') {
    // Clean up any DOM modifications
  }
})