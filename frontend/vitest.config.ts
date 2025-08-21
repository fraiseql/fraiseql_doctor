import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      setupFiles: ['./tests/vitest.setup.ts'],
      env: {
        VITE_AUTH_PROVIDER: 'mock',
        VITE_AUTH0_DOMAIN: 'test-domain.auth0.com',
        VITE_AUTH0_CLIENT_ID: 'test-client-id',
        VITE_API_URL: 'http://localhost:8000',
        VITE_WS_URL: 'ws://localhost:8001',
      },
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        thresholds: {
          global: {
            branches: 85,
            functions: 85,
            lines: 85,
            statements: 85
          }
        }
      }
    }
  })
)
