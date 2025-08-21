// Remove unused import
import { AuthProviderType } from '@/types/auth'
import { MockProvider } from './MockProvider'
import { Auth0Provider } from './Auth0Provider'

// Global provider instance
let providerInstance: MockProvider | Auth0Provider

function createProvider() {
  const authProviderType = import.meta.env.VITE_AUTH_PROVIDER as AuthProviderType

  switch (authProviderType) {
    case AuthProviderType.AUTH0:
      return new Auth0Provider()
    case AuthProviderType.MOCK:
    default:
      return new MockProvider()
  }
}

// Test provider instance for consistent state in tests
let testProviderInstance: MockProvider | Auth0Provider

function getProvider() {
  // In test mode, use a consistent test instance
  if (import.meta.env.MODE === 'test') {
    if (!testProviderInstance) {
      testProviderInstance = createProvider()
    }
    return testProviderInstance
  }

  if (!providerInstance) {
    providerInstance = createProvider()
  }
  return providerInstance
}

export function useAuth() {
  const provider = getProvider()

  return {
    // Provider info
    provider: {
      type: provider.type
    },

    // Auth state
    isAuthenticated: provider.isAuthenticated,
    user: provider.user,

    // Auth methods
    login: provider.login.bind(provider),
    logout: provider.logout.bind(provider),
    checkAuth: provider.checkAuth.bind(provider),
    getToken: provider.getToken.bind(provider)
  }
}

// Test helper function to reset auth state
export function resetAuthForTesting() {
  if (import.meta.env.MODE === 'test' && testProviderInstance) {
    testProviderInstance.isAuthenticated.value = false
    testProviderInstance.user.value = null
  }
}
