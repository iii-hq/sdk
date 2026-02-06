import { iii } from './iii'
import type { Todo } from './types'

export const streams = {
  get: async (stream_name: string, group_id: string, item_id: string): Promise<any | null> => {
    return iii.call('streams.get', { stream_name, group_id, item_id })
  },
  set: async (stream_name: string, group_id: string, item_id: string, data: any): Promise<any> => {
    return iii.call('streams.set', { stream_name, group_id, item_id, data })
  },
  delete: async (stream_name: string, group_id: string, item_id: string): Promise<void> => {
    return iii.call('streams.delete', { stream_name, group_id, item_id })
  },
  getGroup: async (stream_name: string, group_id: string): Promise<any[]> => {
    return iii.call('streams.getGroup', { stream_name, group_id })
  },
  listGroups: async (stream_name: string): Promise<string[]> => {
    return iii.call('streams.listGroups', { stream_name })
  },
}

let todoState: Todo[] = []

iii.createStream('todo', {
  get: async input => todoState.find(todo => todo.id === input.item_id),
  set: async input => {
    const existingTodo = todoState.find(todo => todo.id === input.item_id)

    if (existingTodo) {
      const newTodo = { ...existingTodo, ...input.data }
      todoState = todoState.map(todo => (todo.id === input.item_id ? newTodo : todo))
      return { old_value: existingTodo, new_value: newTodo }
    }

    const newTodo = {
      id: input.item_id,
      groupId: input.group_id,
      description: input.data.description,
      dueDate: input.data.dueDate,
      completedAt: null,
    }

    todoState.push(newTodo)

    return { old_value: undefined, new_value: newTodo }
  },
  delete: async input => {
    const old_value = todoState.find(todo => todo.id === input.item_id)
    todoState = todoState.filter(todo => todo.id !== input.item_id)
    return { old_value }
  },
  getGroup: async input => todoState.filter(todo => todo.groupId === input.group_id),
  listGroups: async () => [...new Set(todoState.map(todo => todo.groupId))],
  update: async () => {
    throw new Error('Not implemented')
  },
})
