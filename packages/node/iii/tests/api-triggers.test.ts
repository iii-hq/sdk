import { describe, expect, it } from 'vitest'
import type { ApiRequest, ApiResponse } from '../src'
import { execute, httpRequest, iii, sleep } from './utils'

describe('API Triggers', () => {
  it('should register GET endpoint', async () => {
    const fn = iii.registerFunction(
      { id: 'test.api.get' },
      async (_req: ApiRequest): Promise<ApiResponse> => ({
        status_code: 200,
        body: { message: 'Hello from GET' },
      }),
    )

    const trigger = iii.registerTrigger({
      type: 'http',
      function_id: fn.id,
      config: {
        api_path: 'test/hello',
        http_method: 'GET',
      },
    })

    await sleep(300)

    const response = await execute(async () => httpRequest('GET', '/test/hello'))

    expect(response.status).toBe(200)
    expect(response.data).toEqual({ message: 'Hello from GET' })

    fn.unregister()
    trigger.unregister()
  })

  it('should register POST endpoint with body', async () => {
    const fn = iii.registerFunction(
      { id: 'test.api.post' },
      async (req: ApiRequest): Promise<ApiResponse> => {
        const body = (req.body as Record<string, unknown>) ?? {}
        return {
          status_code: 201,
          body: { received: body, created: true },
        }
      },
    )

    const trigger = iii.registerTrigger({
      type: 'http',
      function_id: fn.id,
      config: {
        api_path: 'test/items',
        http_method: 'POST',
      },
    })

    await sleep(300)

    const response = await execute(async () =>
      httpRequest('POST', '/test/items', { name: 'test item', value: 123 }),
    )

    expect(response.status).toBe(201)
    expect(response.data.created).toBe(true)
    expect(response.data.received).toHaveProperty('name', 'test item')

    fn.unregister()
    trigger.unregister()
  })

  it('should handle path parameters', async () => {
    const fn = iii.registerFunction(
      { id: 'test.api.getById' },
      async (req: ApiRequest): Promise<ApiResponse> => ({
        status_code: 200,
        body: { id: req.path_params?.id },
      }),
    )

    const trigger = iii.registerTrigger({
      type: 'http',
      function_id: fn.id,
      config: {
        api_path: 'test/items/:id',
        http_method: 'GET',
      },
    })

    await sleep(300)

    const response = await execute(async () => httpRequest('GET', '/test/items/abc123'))

    expect(response.status).toBe(200)
    expect(response.data).toEqual({ id: 'abc123' })

    fn.unregister()
    trigger.unregister()
  })

  it('should handle query parameters', async () => {
    const fn = iii.registerFunction(
      { id: 'test.api.search' },
      async (req: ApiRequest): Promise<ApiResponse> => {
        const q = req.query_params?.q
        const limit = req.query_params?.limit
        const qVal = Array.isArray(q) ? q[0] : q
        const limitVal = Array.isArray(limit) ? limit[0] : limit
        return {
          status_code: 200,
          body: { query: qVal, limit: limitVal },
        }
      },
    )

    const trigger = iii.registerTrigger({
      type: 'http',
      function_id: fn.id,
      config: {
        api_path: 'test/search',
        http_method: 'GET',
      },
    })

    await sleep(300)

    const response = await execute(async () => httpRequest('GET', '/test/search?q=hello&limit=10'))

    expect(response.status).toBe(200)
    expect(response.data.query).toBe('hello')
    expect(response.data.limit).toBe('10')

    fn.unregister()
    trigger.unregister()
  })

  it('should return custom status code', async () => {
    const fn = iii.registerFunction(
      { id: 'test.api.notfound' },
      async (_req: ApiRequest): Promise<ApiResponse<404>> => ({
        status_code: 404,
        body: { error: 'Not found' },
      }),
    )

    const trigger = iii.registerTrigger({
      type: 'http',
      function_id: fn.id,
      config: {
        api_path: 'test/missing',
        http_method: 'GET',
      },
    })

    await sleep(300)

    const response = await execute(async () => httpRequest('GET', '/test/missing'))

    expect(response.status).toBe(404)
    expect(response.data).toEqual({ error: 'Not found' })

    fn.unregister()
    trigger.unregister()
  })
})
