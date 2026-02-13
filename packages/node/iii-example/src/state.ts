import { iii } from './iii'

export const state = {
  get: <T>(scope: string, key: string): Promise<T | null> => iii.call('state.get', { scope, key }),
  set: <T>(scope: string, key: string, data: T): Promise<T> =>
    iii.call('state.set', { scope, key, data }),
  delete: (scope: string, key: string): Promise<void> => iii.call('state.delete', { scope, key }),
  list: <T>(scope: string): Promise<T[]> => iii.call('state.list', { scope }),
}
