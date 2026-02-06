import {
  type ApiRequest,
  type ApiResponse,
  type Context,
  type FunctionMessage,
  getContext,
  LogCallback,
  LogConfig,
} from '@iii-dev/sdk'
import { iii } from './iii'

export const useApi = (
  config: {
    api_path: string
    http_method: string
    description?: string
    metadata?: Record<string, any>
  },
  handler: (req: ApiRequest<any>, context: Context) => Promise<ApiResponse>,
) => {
  const function_id = `api.${config.http_method.toLowerCase()}.${config.api_path}`

  iii.registerFunction({ id: function_id, metadata: config.metadata }, req =>
    handler(req, getContext()),
  )
  iii.registerTrigger({
    trigger_type: 'api',
    function_id,
    config: {
      api_path: config.api_path,
      http_method: config.http_method,
      description: config.description,
      metadata: config.metadata,
    },
  })
}

export const useFunctionsAvailable = (
  callback: (functions: FunctionMessage[]) => void,
): (() => void) => {
  return iii.onFunctionsAvailable(callback)
}

export const useOnLog = (handler: LogCallback, config?: LogConfig): (() => void) => {
  return iii.onLog(handler, config)
}
