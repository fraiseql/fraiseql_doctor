import { ref } from 'vue'

export interface ConnectionTestResult {
  success: boolean
  message: string
}

export function useConnectionTest() {
  const testing = ref(false)
  const testResult = ref<ConnectionTestResult | null>(null)

  const testConnection = async (url: string, _authConfig?: any): Promise<ConnectionTestResult> => {
    testing.value = true
    testResult.value = null

    try {
      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Mock success/failure based on URL
      const isValidUrl = !!(url && url.includes('api.example'))

      const result: ConnectionTestResult = {
        success: isValidUrl,
        message: isValidUrl
          ? 'Connection successful! GraphQL endpoint is responding.'
          : 'Connection failed: Unable to reach the GraphQL endpoint.'
      }

      testResult.value = result
      return result
    } catch (error) {
      const result: ConnectionTestResult = {
        success: false,
        message: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`
      }

      testResult.value = result
      return result
    } finally {
      testing.value = false
    }
  }

  return {
    testing,
    testResult,
    testConnection
  }
}
