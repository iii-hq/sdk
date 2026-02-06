import { iii } from './iii'

export const state = {
  get: async (group_id: string, item_id: string): Promise<any | null> => {
    return iii.invokeFunction('state.get', { group_id, item_id })
  },
  set: async (group_id: string, item_id: string, data: any): Promise<any> => {
    return iii.invokeFunction('state.set', { group_id, item_id, data })
  },
  delete: async (group_id: string, item_id: string): Promise<void> => {
    return iii.invokeFunction('state.delete', { group_id, item_id })
  },
  getGroup: async (group_id: string): Promise<any[]> => {
    return iii.invokeFunction('state.getGroup', { group_id })
  },
}
