import type { UpdateOp, StreamSetResult } from '../src/stream'

export interface StateSetResult {
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  old_value?: any
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  new_value?: any
}

export type { StreamSetResult }

export interface StateSetInput {
  group_id: string
  item_id: string
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  data: any
}

export interface StateGetInput {
  group_id: string
  item_id: string
}

export interface StateDeleteInput {
  group_id: string
  item_id: string
}

export interface StateUpdateInput {
  group_id: string
  item_id: string
  ops: UpdateOp[]
}

export interface StateGetGroupInput {
  group_id: string
}

export enum StateEventType {
  Created = 'state:created',
  Updated = 'state:updated',
  Deleted = 'state:deleted',
}

export interface StateEventData {
  type: string
  event_type: StateEventType
  group_id: string
  item_id: string
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  old_value?: any
  // biome-ignore lint/suspicious/noExplicitAny: any is fine here
  new_value?: any
}
