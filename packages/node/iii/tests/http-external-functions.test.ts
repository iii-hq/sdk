import { createServer, type IncomingHttpHeaders } from 'node:http'
import type { AddressInfo } from 'node:net'
import { describe, expect, it } from 'vitest'
import { execute, iii, sleep } from './utils'

type CapturedWebhook = {
  method: string
  url: string
  headers: IncomingHttpHeaders
  body: unknown
  rawBody: string
}

class WebhookProbe {
  private server = createServer(async (req, res) => {
    const chunks: Buffer[] = []
    for await (const chunk of req) {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
    }

    const rawBody = Buffer.concat(chunks).toString('utf8')
    let body: unknown = rawBody
    if (rawBody) {
      try {
        body = JSON.parse(rawBody)
      } catch {
        body = rawBody
      }
    } else {
      body = null
    }

    const captured: CapturedWebhook = {
      method: req.method ?? 'POST',
      url: req.url ?? '/',
      headers: req.headers,
      body,
      rawBody,
    }

    const waiter = this.waiters.shift()
    if (waiter) {
      waiter(captured)
    } else {
      this.queue.push(captured)
    }

    res.writeHead(200, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ ok: true }))
  })

  private queue: CapturedWebhook[] = []
  private waiters: Array<(payload: CapturedWebhook) => void> = []

  async start(): Promise<void> {
    await new Promise<void>((resolve, reject) => {
      const onError = (error: Error) => {
        this.server.off('error', onError)
        reject(error)
      }

      this.server.once('error', onError)
      this.server.listen(0, '127.0.0.1', () => {
        this.server.off('error', onError)
        resolve()
      })
    })
  }

  async close(): Promise<void> {
    if (!this.server.listening) {
      return
    }

    await new Promise<void>((resolve, reject) => {
      this.server.close(error => {
        if (error) {
          reject(error)
          return
        }
        resolve()
      })
    })
  }

  url(path = '/webhook'): string {
    const address = this.server.address()
    if (!address || typeof address === 'string') {
      throw new Error('Webhook server is not listening')
    }

    const { port } = address as AddressInfo
    return `http://127.0.0.1:${port}${path}`
  }

  async waitForWebhook(timeoutMs = 5000): Promise<CapturedWebhook> {
    if (this.queue.length > 0) {
      const next = this.queue.shift()
      if (next) {
        return next
      }
    }

    return new Promise<CapturedWebhook>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Timeout waiting for webhook after ${timeoutMs}ms`))
      }, timeoutMs)

      this.waiters.push(payload => {
        clearTimeout(timeout)
        resolve(payload)
      })
    })
  }
}

function uniqueFunctionId(prefix: string): string {
  return `${prefix}::${Date.now()}::${Math.random().toString(36).slice(2, 10)}`
}

function uniqueTopic(prefix: string): string {
  return `${prefix}.${Date.now()}.${Math.random().toString(36).slice(2, 10)}`
}

describe('HTTP external functions', () => {
  it('delivers queue events to an externally registered HTTP function', async () => {
    await execute(async () => iii.listFunctions())

    const webhookProbe = new WebhookProbe()
    await webhookProbe.start()

    const functionId = uniqueFunctionId('test::http_external::target')
    const topic = uniqueTopic('test.http_external.topic')
    const payload = { hello: 'world', count: 1 }
    let trigger: { unregister(): void } | undefined
    let httpFn: { unregister(): void } | undefined

    try {
      httpFn = iii.registerHttpFunction(functionId, {
        url: webhookProbe.url(),
        method: 'POST',
        timeout_ms: 3000,
      })
      await sleep(300)

      trigger = iii.registerTrigger({
        type: 'queue',
        function_id: functionId,
        config: { topic },
      })
      await sleep(300)

      await execute(async () => iii.call('enqueue', { topic, data: payload }))

      const webhook = await webhookProbe.waitForWebhook(7000)

      expect(webhook.method).toBe('POST')
      expect(webhook.url).toBe('/webhook')
      expect(webhook.body).toMatchObject(payload)
    } finally {
      try {
        trigger?.unregister()
      } finally {
        httpFn?.unregister()
        await webhookProbe.close()
      }
    }
  })
})
