export interface PerformanceSubscription {
  id: string
  status: 'active' | 'error' | 'closed'
}

export interface QueryPerformanceData {
  id: string
  endpointId: string
  operationName: string
  query: string
  variables: Record<string, any>
  executionTime: number
  responseSize: number
  timestamp: Date
  status: 'success' | 'error'
  errors: any[] | null
  fieldExecutionTimes: Record<string, number>
}

export interface SubscriptionConfig {
  endpoint: string
  reconnectAttempts: number
  heartbeatInterval: number
}

export interface PerformanceMetricsOptions {
  endpointId: string
  callback: (data: QueryPerformanceData) => void
  onError?: (error: any) => void
}

export interface AggregatedMetricsOptions {
  endpointId: string
  timeWindow: string
  callback: (data: any) => void
}

export interface SchemaChangesOptions {
  endpointId: string
  callback: (change: any) => void
}

export class GraphQLSubscriptionClient extends EventTarget {
  private config: SubscriptionConfig
  private ws: WebSocket | null = null
  private subscriptions: Map<string, PerformanceSubscription> = new Map()
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private reconnectAttempts: number = 0

  constructor(config: SubscriptionConfig) {
    super()
    this.config = config
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.endpoint)

        this.ws.onopen = () => {
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onclose = (event) => {
          this.handleClose(event)
        }

        this.ws.onerror = (error) => {
          reject(error)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  async subscribeToPerformanceMetrics(options: PerformanceMetricsOptions): Promise<PerformanceSubscription> {
    // Auto-connect if not connected
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      await this.connect()
    }

    const subscriptionId = this.generateId()

    const subscription: PerformanceSubscription = {
      id: subscriptionId,
      status: 'active'
    }

    this.subscriptions.set(subscriptionId, subscription)

    // Send subscription message
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'start',
        payload: {
          query: 'subscription queryPerformanceUpdates { queryPerformanceUpdates { id endpointId operationName } }'
        }
      }))
    }

    // Store callback for later use
    ;(subscription as any).callback = options.callback
    ;(subscription as any).onError = options.onError

    return subscription
  }

  async subscribeToAggregatedMetrics(options: AggregatedMetricsOptions): Promise<PerformanceSubscription> {
    // Auto-connect if not connected
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      await this.connect()
    }

    const subscriptionId = this.generateId()

    const subscription: PerformanceSubscription = {
      id: subscriptionId,
      status: 'active'
    }

    this.subscriptions.set(subscriptionId, subscription)

    // Send subscription message
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'start',
        payload: {
          query: 'subscription aggregatedPerformanceMetrics { aggregatedPerformanceMetrics { endpointId metrics } }'
        }
      }))
    }

    ;(subscription as any).callback = options.callback

    return subscription
  }

  async subscribeToSchemaChanges(options: SchemaChangesOptions): Promise<PerformanceSubscription> {
    // Auto-connect if not connected
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      await this.connect()
    }

    const subscriptionId = this.generateId()

    const subscription: PerformanceSubscription = {
      id: subscriptionId,
      status: 'active'
    }

    this.subscriptions.set(subscriptionId, subscription)

    // Send subscription message
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'start',
        payload: {
          query: 'subscription schemaChanges { schemaChanges { endpointId changeType } }'
        }
      }))
    }

    ;(subscription as any).callback = options.callback

    return subscription
  }

  disconnect(): void {
    this.clearTimers()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.subscriptions.clear()
  }

  getActiveSubscriptions(): PerformanceSubscription[] {
    return Array.from(this.subscriptions.values())
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data)

      // Handle heartbeat responses
      if (message.type === 'heartbeat' || message.type === 'pong') {
        return
      }

      if (message.type === 'data') {
        // Handle subscription data with better routing
        if (message.payload?.data?.queryPerformanceUpdates) {
          this.dispatchToSubscriptions('queryPerformanceUpdates', message.payload.data.queryPerformanceUpdates)
        }

        if (message.payload?.data?.aggregatedPerformanceMetrics) {
          this.dispatchToSubscriptions('aggregatedPerformanceMetrics', message.payload.data.aggregatedPerformanceMetrics)
        }

        if (message.payload?.data?.schemaChanges) {
          this.dispatchToSubscriptions('schemaChanges', message.payload.data.schemaChanges)
        }
      }

      if (message.type === 'error') {
        this.handleSubscriptionError(message.payload)
      }

      if (message.type === 'connection_ack') {
        // Connection acknowledged successfully
        this.dispatchEvent(new CustomEvent('connected'))
      }

      if (message.type === 'complete') {
        // Subscription completed
        this.handleSubscriptionComplete(message.id)
      }
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: {
          type: 'parse_error',
          message: `Failed to parse message: ${error instanceof Error ? error.message : String(error)}`,
          rawData: data
        }
      }))
    }
  }

  private dispatchToSubscriptions(type: string, data: any): void {
    this.subscriptions.forEach(subscription => {
      const callback = (subscription as any).callback
      if (callback) {
        callback(data)
      }
    })
  }

  private handleSubscriptionError(error: any): void {
    this.subscriptions.forEach(subscription => {
      const onError = (subscription as any).onError
      if (onError) {
        onError(error)
      }
      subscription.status = 'error'
    })
  }

  private handleSubscriptionComplete(subscriptionId: string): void {
    const subscription = this.subscriptions.get(subscriptionId)
    if (subscription) {
      subscription.status = 'closed'
      this.subscriptions.delete(subscriptionId)
    }
  }

  private handleClose(event: CloseEvent): void {
    this.clearTimers()

    if (this.reconnectAttempts < this.config.reconnectAttempts) {
      this.scheduleReconnect()
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 8000)

    this.reconnectTimer = window.setTimeout(async () => {
      try {
        await this.connect()
        this.dispatchEvent(new CustomEvent('reconnected'))
      } catch (error) {
        this.handleClose(new CloseEvent('close', { code: 1006 }))
      }
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }))
      }
    }, this.config.heartbeatInterval)
  }

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private generateId(): string {
    return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Add proper event listener support for the tests
  on(event: string, listener: (...args: any[]) => void): void {
    this.addEventListener(event, listener as EventListener)
  }
}
