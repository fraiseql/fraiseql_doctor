import type { Ref } from 'vue'

export enum AuthProviderType {
  AUTH0 = 'auth0',
  MOCK = 'mock'
}

export interface User {
  id: string
  name: string
  email: string
  picture?: string
}

export interface BaseAuthProvider {
  readonly type: AuthProviderType
  readonly isAuthenticated: Ref<boolean>
  readonly user: Ref<User | null>
  login(): Promise<void>
  logout(): Promise<void>
  checkAuth(): Promise<boolean>
  getToken(): Promise<string | null>
}