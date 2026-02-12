/**
 * Log exporter for the III Engine.
 */

import { ExportResultCode, type ExportResult } from '@opentelemetry/core'
import type { LogRecordExporter, ReadableLogRecord } from '@opentelemetry/sdk-logs'
import { JsonLogsSerializer } from '@opentelemetry/otlp-transformer'

import type { SharedEngineConnection } from './connection'
import { PREFIX_LOGS } from './types'

/**
 * Log exporter using the shared WebSocket connection.
 */
export class EngineLogExporter implements LogRecordExporter {
  private static readonly MAX_PENDING_EXPORTS = 100
  private lastDropWarnTime = 0
  private connection: SharedEngineConnection
  private pendingExports: Array<{
    logs: ReadableLogRecord[]
    callback: (result: ExportResult) => void
  }> = []

  constructor(connection: SharedEngineConnection) {
    this.connection = connection
    this.connection.onConnected(() => this.flushPending())
  }

  private flushPending(): void {
    const pending = this.pendingExports.splice(0, this.pendingExports.length)
    for (const { logs, callback } of pending) {
      this.doExport(logs, callback)
    }
  }

  private doExport(
    logs: ReadableLogRecord[],
    resultCallback: (result: ExportResult) => void,
  ): void {
    if (this.connection.getState() !== 'connected') {
      if (this.pendingExports.length >= EngineLogExporter.MAX_PENDING_EXPORTS) {
        const dropped = this.pendingExports.shift()
        dropped?.callback({ code: ExportResultCode.FAILED, error: new Error('Queue overflow') })
        const now = Date.now()
        if (now - this.lastDropWarnTime > 10_000) {
          console.warn('[OTel] Logs export queue full, dropping oldest entries')
          this.lastDropWarnTime = now
        }
      }
      this.pendingExports.push({ logs, callback: resultCallback })
      return
    }

    try {
      const serialized = JsonLogsSerializer.serializeRequest(logs)
      if (!serialized) {
        resultCallback({ code: ExportResultCode.SUCCESS })
        return
      }

      this.connection.send(PREFIX_LOGS, serialized, err => {
        if (err) {
          console.error('[OTel] Failed to send logs:', err.message)
          resultCallback({ code: ExportResultCode.FAILED, error: err })
        } else {
          resultCallback({ code: ExportResultCode.SUCCESS })
        }
      })
    } catch (err) {
      console.error('[OTel] Error exporting logs:', err)
      resultCallback({ code: ExportResultCode.FAILED, error: err as Error })
    }
  }

  export(logs: ReadableLogRecord[], resultCallback: (result: ExportResult) => void): void {
    this.doExport(logs, resultCallback)
  }

  async shutdown(): Promise<void> {
    for (const { callback } of this.pendingExports) {
      callback({ code: ExportResultCode.FAILED, error: new Error('Exporter shutdown') })
    }
    this.pendingExports = []
  }
}
