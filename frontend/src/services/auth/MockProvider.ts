import { ref } from 'vue'
import type { BaseAuthProvider, User, AuthProviderType } from '@/types/auth'

export class MockProvider implements BaseAuthProvider {
  readonly type = 'mock' as AuthProviderType.MOCK
  readonly isAuthenticated = ref(false)
  readonly user = ref<User | null>(null)

  private mockUser: User = {
    id: 'mock-user-123',
    name: 'Mock User',
    email: 'mock@example.com',
    picture: 'https://via.placeholder.com/150'
  }

  async login(): Promise<void> {
    // Simulate async login
    await new Promise(resolve => setTimeout(resolve, 100))
    
    this.isAuthenticated.value = true
    this.user.value = this.mockUser
  }

  async logout(): Promise<void> {
    // Simulate async logout
    await new Promise(resolve => setTimeout(resolve, 50))
    
    this.isAuthenticated.value = false
    this.user.value = null
  }

  async checkAuth(): Promise<boolean> {
    // Mock auth check - could simulate stored session
    return this.isAuthenticated.value
  }

  async getToken(): Promise<string | null> {
    if (!this.isAuthenticated.value) {
      return null
    }
    
    // Return mock JWT token
    return 'mock-jwt-token-' + Date.now()
  }
}