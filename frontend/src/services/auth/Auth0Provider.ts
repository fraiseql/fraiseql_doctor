import { ref } from 'vue'
import type { BaseAuthProvider, User, AuthProviderType } from '@/types/auth'

export class Auth0Provider implements BaseAuthProvider {
  readonly type = 'auth0' as AuthProviderType.AUTH0
  readonly isAuthenticated = ref(false)
  readonly user = ref<User | null>(null)

  // TODO: Implement actual Auth0 integration in future iteration
  async login(): Promise<void> {
    throw new Error('Auth0Provider not fully implemented yet')
  }

  async logout(): Promise<void> {
    throw new Error('Auth0Provider not fully implemented yet')
  }

  async checkAuth(): Promise<boolean> {
    return false
  }

  async getToken(): Promise<string | null> {
    return null
  }
}
