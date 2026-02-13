import { beforeEach, describe, expect, it } from 'vitest'
import { skipIfServerUnavailable } from './setup'
import { iii } from './utils'
import type { StateSetResult } from './types'

type TestData = {
  name?: string
  value: number
  updated?: boolean
}

describe.skipIf(skipIfServerUnavailable())('State Operations', () => {
  const testScope = 'test-group'
  const testKey = 'test-item'

  beforeEach(async () => {
    await iii.call('state.delete', { scope: testScope, key: testKey }).catch(() => void 0)
  })

  describe('state.set', () => {
    it('should set a new state item', async () => {
      const testData = {
        name: 'Test Item',
        value: 42,
        metadata: { created: new Date().toISOString() },
      }

      const result = await iii.call('state.set', {
        scope: testScope,
        key: testKey,
        data: testData,
      })

      expect(result).toBeDefined()
      expect(result).toEqual({ old_value: null, new_value: testData })
    })

    it('should overwrite an existing state item', async () => {
      const initialData: TestData = { value: 1 }
      const updatedData: TestData = { value: 2, updated: true }

      await iii.call('state.set', {
        scope: testScope,
        key: testKey,
        data: initialData,
      })

      const result: StateSetResult = await iii.call('state.set', {
        scope: testScope,
        key: testKey,
        data: updatedData,
      })

      expect(result.old_value).toEqual(initialData)
      expect(result.new_value).toEqual(updatedData)
    })
  })

  describe('state.get', () => {
    it('should get an existing state item', async () => {
      const testData: TestData = { name: 'Test', value: 100 }

      await iii.call('state.set', {
        scope: testScope,
        key: testKey,
        data: testData,
      })

      const result: TestData = await iii.call('state.get', {
        scope: testScope,
        key: testKey,
      })

      expect(result).toBeDefined()
      expect(result).toEqual(testData)
    })

    it('should return null for non-existent item', async () => {
      const result = await iii.call('state.get', {
        scope: testScope,
        key: 'non-existent-item',
      })

      expect(result).toBeUndefined()
    })
  })

  describe('state.delete', () => {
    it('should delete an existing state item', async () => {
      await iii.call('state.set', {
        scope: testScope,
        key: testKey,
        data: { test: true },
      })

      await iii.call('state.delete', {
        scope: testScope,
        key: testKey,
      })

      const result = await iii.call('state.get', {
        scope: testScope,
        key: testKey,
      })

      expect(result).toBeUndefined()
    })

    it('should handle deleting non-existent item gracefully', async () => {
      await expect(
        iii.call('state.delete', {
          scope: testScope,
          key: 'non-existent',
        }),
      ).resolves.not.toThrow()
    })
  })

  describe('state.list', () => {
    it('should get all items in a group', async () => {
      type TestDataWithId = TestData & { id: string }

      const groupId = `state-${Date.now()}`
      const items: TestDataWithId[] = [
        { id: 'state-item1', value: 1 },
        { id: 'state-item2', value: 2 },
        { id: 'state-item3', value: 3 },
      ]

      // Set multiple items
      for (const item of items) {
        await iii.call('state.set', {
          scope: groupId,
          key: item.id,
          data: item,
        })
      }

      const result: TestDataWithId[] = await iii.call('state.list', { scope: groupId })
      const sort = (a: TestDataWithId, b: TestDataWithId) => a.id.localeCompare(b.id)

      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBeGreaterThanOrEqual(items.length)
      expect(result.sort(sort)).toEqual(items.sort(sort))
    })
  })
})
