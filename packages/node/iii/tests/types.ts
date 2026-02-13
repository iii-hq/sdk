import type { UpdateOp, StreamSetResult } from '../src/stream'

export interface StateSetResult {
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  old_value?: any
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  new_value?: any
}

export type { StreamSetResult }

export interface StateSetInput {
  scope: string
  key: string
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  data: any
}

export interface StateGetInput {
  scope: string
  key: string
}

export interface StateDeleteInput {
  scope: string
  key: string
}

export interface StateUpdateInput {
  scope: string
  key: string
  ops: UpdateOp[]
}

export interface StateGetGroupInput {
  scope: string
}

export enum StateEventType {
  Created = 'state:created',
  Updated = 'state:updated',
  Deleted = 'state:deleted',
}

export interface StateEventData {
  type: string
  event_type: StateEventType
  scope: string
  key: string
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  old_value?: any
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  new_value?: any
}
