# Sub-PRD: GraphQL API Configuration Admin UI

## 🎯 Problem Statement

You need a simple, focused admin interface to configure and monitor your three GraphQL APIs:
- `api.example.dev`
- `api.example.st`
- `api.example.io`

Currently, there's no centralized way to manage monitoring settings, view health status, or configure alert thresholds for these endpoints.

## 📋 Requirements

### Core Features
1. **API Endpoint Management**
   - Add/edit/remove GraphQL endpoints
   - Configure authentication (API keys, headers)
   - Set monitoring intervals

2. **Monitoring Configuration**
   - Set performance thresholds (execution time, error rate)
   - Configure alert rules
   - Define sampling rates

3. **Health Dashboard**
   - Real-time status for all 3 APIs
   - Quick health indicators (green/yellow/red)
   - Last check timestamps

### User Stories
- As an admin, I want to see the health status of all my GraphQL APIs at a glance
- As an admin, I want to configure alert thresholds for each API independently
- As an admin, I want to add new API endpoints without code changes

## 🏗️ Technical Design

### Component Structure
```
src/components/admin/
├── ApiConfigurationAdmin.vue          # Main admin page
├── components/
│   ├── ApiEndpointCard.vue           # Individual API config card
│   ├── ApiHealthIndicator.vue        # Status indicator
│   ├── MonitoringSettings.vue        # Threshold configuration
│   └── ApiEndpointForm.vue           # Add/edit form
└── types/
    └── adminTypes.ts                 # TypeScript interfaces
```

### Data Model
```typescript
interface ApiEndpoint {
  id: string
  name: string
  url: string
  environment: 'dev' | 'staging' | 'prod'
  authentication: {
    type: 'bearer' | 'api_key' | 'none'
    headers: Record<string, string>
  }
  monitoring: {
    enabled: boolean
    interval: number // seconds
    thresholds: {
      executionTime: { warning: number; critical: number }
      errorRate: { warning: number; critical: number }
    }
    samplingRate: number
  }
  status: {
    isHealthy: boolean
    lastCheck: Date
    responseTime: number
    errorCount: number
  }
}
```

## 🎨 UI Design

### Main Admin Page Layout
```
┌─────────────────────────────────────────────────────────┐
│ GraphQL API Configuration                    [+ Add API] │
├─────────────────────────────────────────────────────────┤
│ ┌─ api.example.dev ────┐ ┌─ api.example.st ────┐  │
│ │ 🟢 Healthy              │ │ 🟡 Slow Response        │  │
│ │ Response: 45ms          │ │ Response: 250ms         │  │
│ │ Error Rate: 0.1%        │ │ Error Rate: 2.1%        │  │
│ │ Last Check: 2min ago    │ │ Last Check: 1min ago    │  │
│ │                         │ │                         │  │
│ │ [Configure] [Test]      │ │ [Configure] [Test]      │  │
│ └─────────────────────────┘ └─────────────────────────┘  │
│                                                         │
│ ┌─ api.example.io ─────┐                            │
│ │ 🟢 Healthy              │                            │
│ │ Response: 38ms          │                            │
│ │ Error Rate: 0.0%        │                            │
│ │ Last Check: 30sec ago   │                            │
│ │                         │                            │
│ │ [Configure] [Test]      │                            │
│ └─────────────────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

### Configuration Modal
```
┌─ Configure API: api.example.dev ─────────────────────┐
│                                                         │
│ Basic Settings                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Name: [Example Dev API                            ] │ │
│ │ URL:  [https://api.example.dev/graphql            ] │ │
│ │ Env:  [Development ▼]                              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Authentication                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Type: [Bearer Token ▼]                             │ │
│ │ Token: [********************************           ] │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Monitoring Thresholds                                   │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Execution Time Warning:  [200ms]                   │ │
│ │ Execution Time Critical: [500ms]                   │ │
│ │ Error Rate Warning:      [1%   ]                   │ │
│ │ Error Rate Critical:     [5%   ]                   │ │
│ │ Check Interval:          [30sec]                   │ │
│ │ Sampling Rate:           [100% ]                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│                                    [Cancel] [Save]     │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Implementation Plan

### Phase 1: Basic Structure
1. Create main admin page component
2. Add API endpoint cards with health indicators
3. Implement basic CRUD operations for endpoints

### Phase 2: Configuration
1. Build configuration modal
2. Add authentication settings
3. Implement monitoring threshold configuration

### Phase 3: Real-time Integration
1. Connect to existing LivePerformanceDashboard
2. Add real-time health status updates
3. Implement test connection functionality

## 📊 Integration Points

### With Existing System
- **LivePerformanceDashboard**: Subscribe to health status updates
- **GraphQLSubscriptionClient**: Monitor real-time performance
- **RealTimeQueryHistoryApi**: Fetch historical performance data
- **GraphQLInstrumentation**: Configure per-endpoint sampling

### Storage
```typescript
// Local storage for persistence
interface AdminConfig {
  endpoints: ApiEndpoint[]
  globalSettings: {
    refreshInterval: number
    alertsEnabled: boolean
  }
}

// Service for managing configuration
class ApiConfigurationService {
  saveEndpoint(endpoint: ApiEndpoint): void
  getEndpoints(): ApiEndpoint[]
  testConnection(endpoint: ApiEndpoint): Promise<boolean>
  updateEndpointStatus(id: string, status: ApiEndpoint['status']): void
}
```

## 🎯 Success Criteria

1. **Functional Requirements**
   - ✅ Can add/edit/remove the 3 specific GraphQL APIs
   - ✅ Real-time health status display for all endpoints
   - ✅ Configurable monitoring thresholds per endpoint
   - ✅ Test connection functionality

2. **Non-Functional Requirements**
   - ✅ UI loads in <2 seconds
   - ✅ Real-time updates within 5 seconds
   - ✅ Configuration persists across browser sessions
   - ✅ Responsive design for desktop and tablet

3. **User Experience**
   - ✅ Admin can configure all APIs in under 5 minutes
   - ✅ Health status is immediately visible upon page load
   - ✅ Configuration changes take effect immediately

## 📅 Timeline

- **Week 1**: Phase 1 - Basic Structure
- **Week 2**: Phase 2 - Configuration Interface
- **Week 3**: Phase 3 - Real-time Integration
- **Week 4**: Testing and Polish

## 🔐 Security Considerations

1. **Authentication Tokens**
   - Store securely in encrypted local storage
   - Mask sensitive values in UI
   - Provide clear indication of token validity

2. **API Access**
   - Validate URLs to prevent SSRF attacks
   - Implement rate limiting for test connections
   - Log all configuration changes

## 📈 Future Enhancements

1. **Advanced Features** (Post-MVP)
   - Bulk configuration operations
   - Export/import configuration
   - Alert notification routing
   - Historical performance charts per endpoint

2. **Monitoring Expansion**
   - Custom GraphQL query monitoring
   - Schema change detection
   - Performance regression alerts
   - SLA tracking and reporting

---

*Created: 2025-01*
*Version: 1.0*
*Status: Ready for Implementation*
