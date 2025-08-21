export function isBearerToken(token: string): boolean {
  return token.startsWith('Bearer ')
}

export function sanitizeToken(token: string): string {
  return token.trim()
}