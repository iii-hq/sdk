import { type ApiRequest, type ApiResponse, type Context, getContext } from 'iii-sdk'
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
