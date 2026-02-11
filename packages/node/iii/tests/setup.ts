import { afterAll, beforeAll } from 'vitest'
import { checkServerAvailability, iii } from './utils'

const isCI = Boolean(process.env.CI)
const hasExplicitServerUrl = Boolean(process.env.III_BRIDGE_URL || process.env.III_HTTP_URL)

let serverAvailable = false

beforeAll(async () => {
  if (isCI && !hasExplicitServerUrl) {
    console.warn('Running in CI without explicit server URL. Skipping integration tests.')
    console.warn('To run tests in CI, set III_BRIDGE_URL and III_HTTP_URL environment variables,')
    console.warn('or ensure the III Engine server is started before running tests.')
    serverAvailable = false
    return
  }

  serverAvailable = await checkServerAvailability()

  if (!serverAvailable) {
    console.warn('III Engine server is not available. Skipping integration tests.')
    console.warn(`Expected server at: ${process.env.III_HTTP_URL ?? 'http://localhost:3111'}`)
    console.warn('To run tests locally, start the III Engine server first.')
  }
})

afterAll(async () => {
  try {
    const sdk = iii as { shutdown?: () => Promise<void> }
    if (sdk.shutdown) {
      await sdk.shutdown()
    }
  } catch (error) {
    console.error('Error shutting down SDK:', error)
  }
})

export function skipIfServerUnavailable(): boolean {
  if (isCI && !hasExplicitServerUrl) {
    return true
  }
  return false
}
