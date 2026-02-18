/**
 * Global fetch auto-instrumentation for the III Node SDK.
 *
 * Patches globalThis.fetch to create OTel CLIENT spans for every HTTP request.
 * Works on all runtimes (Bun, Node.js, Deno) unlike UndiciInstrumentation
 * which only works when fetch is backed by Node.js's undici.
 */

import {
  type Tracer,
  SpanKind,
  SpanStatusCode,
  context,
  propagation,
} from '@opentelemetry/api'

let originalFetch: typeof globalThis.fetch | null = null

/**
 * Patch globalThis.fetch to create OTel CLIENT spans for every HTTP request.
 */
export function patchGlobalFetch(tracer: Tracer): void {
  if (originalFetch) return

  originalFetch = globalThis.fetch

  globalThis.fetch = async (
    input: string | URL | Request,
    init?: RequestInit,
  ): Promise<Response> => {
    const url = input instanceof Request ? input.url : String(input)
    const method = (init?.method ?? (input instanceof Request ? input.method : 'GET')).toUpperCase()

    let host: string | undefined
    let scheme: string | undefined
    let path: string | undefined
    let port: number | undefined
    try {
      const parsed = new URL(url)
      host = parsed.hostname
      scheme = parsed.protocol.replace(':', '')
      path = parsed.pathname
      port = parsed.port ? parseInt(parsed.port, 10) : undefined
    } catch {
      // relative URL or invalid — skip host/scheme/path attributes
    }

    const spanAttributes: Record<string, string | number> = {
      'http.request.method': method,
      'url.full': url,
    }
    if (host) spanAttributes['server.address'] = host
    if (scheme) {
      spanAttributes['url.scheme'] = scheme
      spanAttributes['network.protocol.name'] = 'http'
    }
    if (path) spanAttributes['url.path'] = path
    if (port) spanAttributes['server.port'] = port

    const spanName = path ? `${method} ${path}` : method

    return tracer.startActiveSpan(
      spanName,
      { kind: SpanKind.CLIENT, attributes: spanAttributes },
      context.active(),
      async (span) => {
        try {
          const carrier: Record<string, string> = {}
          propagation.inject(context.active(), carrier)

          const headers = new Headers(
            init?.headers ?? (input instanceof Request ? input.headers : undefined),
          )
          for (const [key, value] of Object.entries(carrier)) {
            headers.set(key, value)
          }

          const response = await originalFetch!(input, { ...init, headers })

          span.setAttribute('http.response.status_code', response.status)

          if (response.status >= 400) {
            span.setAttribute('error.type', String(response.status))
            span.setStatus({ code: SpanStatusCode.ERROR })
          } else {
            span.setStatus({ code: SpanStatusCode.OK })
          }

          return response
        } catch (error) {
          span.setAttribute('error.type', (error as Error).name ?? 'Error')
          span.setStatus({ code: SpanStatusCode.ERROR, message: (error as Error).message })
          span.recordException(error as Error)
          throw error
        } finally {
          span.end()
        }
      },
    )
  }
}

/**
 * Restore globalThis.fetch to its original implementation.
 */
export function unpatchGlobalFetch(): void {
  if (originalFetch) {
    globalThis.fetch = originalFetch
    originalFetch = null
  }
}
