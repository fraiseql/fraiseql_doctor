import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocketService } from '../../src/services/websocket'

// Mock WebSocket for testing
class MockWebSocket {
  url: string
  readyState: number = WebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    // Simulate connection after next tick
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send(_data: string) {
    // Mock send - we'll trigger onmessage in tests
  }

  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  // Helper method for tests to simulate receiving messages
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', {
        data: JSON.stringify(data)
      }))
    }
  }
}

// Replace global WebSocket with our mock
global.WebSocket = MockWebSocket as any

describe('WebSocketService', () => {
  let service: WebSocketService

  beforeEach(() => {
    service = new WebSocketService('ws://localhost:8080/health')
  })

  afterEach(() => {
    if (service) {
      service.disconnect()
    }
  })

  it('should connect to WebSocket and emit connection events', async () => {
    const onConnect = vi.fn()

    service.on('connected', onConnect)
    await service.connect()

    expect(onConnect).toHaveBeenCalled()
  })

  it('should receive real-time endpoint health updates', async () => {
    const onHealthUpdate = vi.fn()

    service.on('endpoint-health-update', onHealthUpdate)
    await service.connect()

    // Access the internal WebSocket to simulate message
    const ws = (service as any).ws as MockWebSocket

    // Simulate receiving a health update message
    ws.simulateMessage({
      type: 'endpoint-health-update',
      payload: {
        endpointId: 'test-endpoint',
        isHealthy: false,
        responseTime: 5000,
        timestamp: new Date().toISOString()
      }
    })

    expect(onHealthUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        endpointId: 'test-endpoint',
        isHealthy: false,
        responseTime: 5000,
        timestamp: expect.any(String)
      })
    )
  })

  it('should handle connection errors gracefully', async () => {
    const onError = vi.fn()

    service.on('error', onError)
    await service.connect()

    // Simulate an error
    const ws = (service as any).ws as MockWebSocket
    if (ws.onerror) {
      ws.onerror(new Event('error'))
    }

    expect(onError).toHaveBeenCalled()
  })

  it('should allow disconnection', async () => {
    const onDisconnect = vi.fn()

    service.on('disconnected', onDisconnect)
    await service.connect()
    service.disconnect()

    expect(onDisconnect).toHaveBeenCalled()
  })

  it('should handle invalid JSON messages gracefully', async () => {
    const onError = vi.fn()

    service.on('error', onError)
    await service.connect()

    // Access the internal WebSocket
    const ws = (service as any).ws as MockWebSocket

    // Simulate receiving invalid JSON
    if (ws.onmessage) {
      ws.onmessage(new MessageEvent('message', {
        data: 'invalid-json{'
      }))
    }

    expect(onError).toHaveBeenCalled()
  })
})
