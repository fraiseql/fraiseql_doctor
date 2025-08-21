export function buildApolloStudioUrl(endpointUrl: string): string {
  const params = new URLSearchParams({
    endpoint: endpointUrl
  })
  
  return `https://studio.apollographql.com/sandbox/explorer?${params.toString()}`
}