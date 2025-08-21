import { WEBSOCKET_CONFIG, WEBSOCKET_EVENTS, type WebSocketConfig } from '../config/websocket'

export interface HealthUpdate {
  endpointId: string
  isHealthy: boolean
  responseTime: number
  timestamp: string
  errorMessage?: string
}

export interface WebSocketMessage {
  type: string
  payload: any
}

export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

export class WebSocketService extends EventTarget {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED
  private reconnectAttempts: number = 0
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private isManualDisconnect: boolean = false

  constructor(url?: string, config?: Partial<WebSocketConfig>) {
    super()
    this.config = {
      ...WEBSOCKET_CONFIG,
      ...(url && { url }),
      ...config
    }
  }

  get state(): ConnectionState {
    return this.connectionState
  }

  get isConnected(): boolean {
    return this.connectionState === ConnectionState.CONNECTED
  }

  async connect(): Promise<void> {
    if (this.connectionState === ConnectionState.CONNECTED ||
        this.connectionState === ConnectionState.CONNECTING) {
      return
    }

    this.isManualDisconnect = false
    return this.attemptConnection()
  }

  private async attemptConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.connectionState = ConnectionState.CONNECTING
      this.dispatchEvent(new CustomEvent(WEBSOCKET_EVENTS.CONNECTED, {
        detail: { state: this.connectionState }
      }))

      try {
        this.ws = new WebSocket(this.config.url)

        this.ws.onopen = () => {
          this.connectionState = ConnectionState.CONNECTED
          this.reconnectAttempts = 0
          this.clearReconnectTimer()
          this.startHeartbeat()

          this.dispatchEvent(new CustomEvent(WEBSOCKET_EVENTS.CONNECTED, {
            detail: { state: this.connectionState }
          }))
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onclose = (event) => {
          this.handleDisconnection(event)
          if (this.connectionState === ConnectionState.CONNECTING) {
            reject(new Error(`WebSocket connection failed: ${event.reason}`))
          }
        }

        this.ws.onerror = (error) => {
          this.handleError(error)
          if (this.connectionState === ConnectionState.CONNECTING) {
            reject(error)
          }
        }
      } catch (error) {
        this.connectionState = ConnectionState.ERROR
        this.handleError(error)
        reject(error)
      }
    })
  }

  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data)

      // Handle heartbeat responses
      if (message.type === WEBSOCKET_EVENTS.HEARTBEAT) {
        return // Just acknowledge the heartbeat
      }

      // Handle endpoint health updates
      if (message.type === WEBSOCKET_EVENTS.ENDPOINT_HEALTH_UPDATE) {
        this.dispatchEvent(new CustomEvent(WEBSOCKET_EVENTS.ENDPOINT_HEALTH_UPDATE, {
          detail: message.payload
        }))
        return
      }

      // Dispatch any other message types
      this.dispatchEvent(new CustomEvent(message.type, {
        detail: message.payload
      }))
    } catch (error) {
      this.handleError(new Error(`Failed to parse WebSocket message: ${error}`))
    }
  }

  private handleDisconnection(event: CloseEvent): void {
    this.clearHeartbeat()
    this.ws = null

    if (this.isManualDisconnect) {
      this.connectionState = ConnectionState.DISCONNECTED
      this.dispatchEvent(new CustomEvent(WEBSOCKET_EVENTS.DISCONNECTED, {
        detail: { reason: 'Manual disconnect', code: event.code }
      }))
      return
    }

    // Attempt reconnection if not a manual disconnect
    if (this.reconnectAttempts < this.config.reconnectAttempts) {
      this.connectionState = ConnectionState.RECONNECTING
      this.scheduleReconnect()
    } else {
      this.connectionState = ConnectionState.ERROR
      this.dispatchEvent(new CustomEvent(WEBSOCKET_EVENTS.ERROR, {
        detail: {
          message: 'Max reconnection attempts exceeded',
          attempts: this.reconnectAttempts
        }
      }))
    }
  }

  private handleError(error: any): void {
    this.dispatchEvent(new CustomEvent(WEBSOCKET_EVENTS.ERROR, {
      detail: {
        message: error instanceof Error ? error.message : 'WebSocket error',
        error,
        state: this.connectionState
      }
    }))
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++
    this.clearReconnectTimer()

    this.reconnectTimer = window.setTimeout(() => {
      if (!this.isManualDisconnect) {
        this.attemptConnection().catch(() => {
          // Error handling is done in attemptConnection
        })
      }
    }, this.config.reconnectInterval)
  }

  private startHeartbeat(): void {
    this.clearHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      this.send({ type: WEBSOCKET_EVENTS.HEARTBEAT, timestamp: Date.now() })
    }, this.config.heartbeatInterval)
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  disconnect(): void {
    this.isManualDisconnect = true
    this.clearReconnectTimer()
    this.clearHeartbeat()

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }

    this.connectionState = ConnectionState.DISCONNECTED
  }

  send(message: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message))
        return true
      } catch (error) {
        this.handleError(error)
        return false
      }
    }
    return false
  }

  // Event listener helpers for better TypeScript support
  on(event: 'connected', listener: (data: { state: ConnectionState }) => void): void
  on(event: 'disconnected', listener: (data: { reason: string; code: number }) => void): void
  on(event: 'endpoint-health-update', listener: (update: HealthUpdate) => void): void
  on(event: 'error', listener: (error: { message: string; error?: any; state?: ConnectionState }) => void): void
  on(event: string, listener: (data?: any) => void): void {
    this.addEventListener(event, (e: any) => {
      listener(e.detail)
    })
  }
}
