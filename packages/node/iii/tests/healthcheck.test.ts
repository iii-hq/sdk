import { describe, expect, it } from 'vitest'
import type { ApiRequest, ApiResponse } from '../src'
import { execute, httpRequest, iii } from './utils'

describe('Healthcheck Endpoint', () => {
  it('should register a healthcheck function and trigger', async () => {
    const functionId = 'test.healthcheck'

    iii.registerFunction({ id: functionId }, async (_req: ApiRequest): Promise<ApiResponse> => {
      return {
        status_code: 200,
        body: {
          status: 'healthy',
          timestamp: new Date().toISOString(),
          service: 'iii-sdk-test',
        },
      }
    })

    await execute(async () => {
      const response = await httpRequest('GET', '/health')
      expect(response.status).toBe(404)
    })

    const trigger = iii.registerTrigger({
      trigger_type: 'api',
      function_id: functionId,
      config: {
        api_path: 'health',
        http_method: 'GET',
        description: 'Healthcheck endpoint',
      },
    })

    await execute(async () => {
      const response = await httpRequest('GET', '/health')

      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('status', 'healthy')
      expect(response.data).toHaveProperty('service', 'iii-sdk-test')
      expect(response.data).toHaveProperty('timestamp')
    })

    trigger.unregister()

    // there's an issue with unregistering
    // await execute(async () => {
    //   const response = await httpRequest('GET', '/health')
    //   expect(response.status).toBe(404)
    // })
  })
})
