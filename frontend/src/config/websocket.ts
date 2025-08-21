export interface WebSocketConfig {
  url: string
  reconnectAttempts: number
  reconnectInterval: number
  heartbeatInterval: number
}

export const WEBSOCKET_CONFIG: WebSocketConfig = {
  url: import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8080/health',
  reconnectAttempts: 5,
  reconnectInterval: 3000, // 3 seconds
  heartbeatInterval: 30000 // 30 seconds
}

export const WEBSOCKET_EVENTS = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
  ENDPOINT_HEALTH_UPDATE: 'endpoint-health-update',
  HEARTBEAT: 'heartbeat'
} as const

export type WebSocketEvent = typeof WEBSOCKET_EVENTS[keyof typeof WEBSOCKET_EVENTS]
