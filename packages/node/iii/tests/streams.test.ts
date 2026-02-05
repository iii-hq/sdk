import { beforeEach, describe, expect, it } from 'vitest'
import { iii } from './utils'
import type { StreamSetInput, StreamSetResult } from '../src/streams'

type TestData = {
  name?: string
  value: number
  updated?: boolean
}

describe('Stream Operations', () => {
  const testStreamName = 'test-stream'
  const testGroupId = 'test-group'
  const testItemId = 'test-item'

  beforeEach(async () => {
    await iii
      .invokeFunction('streams.delete', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
      })
      .catch(() => void 0)
  })

  describe('streams.set', () => {
    it('should set a new stream item', async () => {
      const testData = {
        name: 'Test Item',
        value: 42,
        metadata: { created: new Date().toISOString() },
      }

      const result = await iii.invokeFunction<StreamSetInput, StreamSetResult<TestData>>(
        'streams.set',
        {
          stream_name: testStreamName,
          group_id: testGroupId,
          item_id: testItemId,
          data: testData,
        },
      )

      expect(result).toBeDefined()
      expect(result).toEqual({ old_value: null, new_value: testData })
    })

    it('should overwrite an existing stream item', async () => {
      const initialData: TestData = { value: 1 }
      const updatedData: TestData = { value: 2, updated: true }

      await iii.invokeFunction('streams.set', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
        data: initialData,
      })

      const result: StreamSetResult<any> = await iii.invokeFunction('streams.set', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
        data: updatedData,
      })

      expect(result.old_value).toEqual(initialData)
      expect(result.new_value).toEqual(updatedData)
    })
  })

  describe('streams.get', () => {
    it('should get an existing stream item', async () => {
      const testData: TestData = { name: 'Test', value: 100 }

      await iii.invokeFunction('streams.set', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
        data: testData,
      })

      const result: TestData = await iii.invokeFunction('streams.get', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
      })

      expect(result).toBeDefined()
      expect(result).toEqual(testData)
    })

    it('should return null for non-existent item', async () => {
      const result = await iii.invokeFunction('streams.get', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: 'non-existent-item',
      })

      expect(result).toBeUndefined()
    })
  })

  describe('streams.delete', () => {
    it('should delete an existing stream item', async () => {
      await iii.invokeFunction('streams.set', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
        data: { test: true },
      })

      await iii.invokeFunction('streams.delete', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
      })

      const result = await iii.invokeFunction('streams.get', {
        stream_name: testStreamName,
        group_id: testGroupId,
        item_id: testItemId,
      })

      expect(result).toBeUndefined()
    })

    it('should handle deleting non-existent item gracefully', async () => {
      await expect(
        iii.invokeFunction('streams.delete', {
          stream_name: testStreamName,
          group_id: testGroupId,
          item_id: 'non-existent',
        }),
      ).resolves.not.toThrow()
    })
  })

  describe('streams.list', () => {
    it('should get all items in a group', async () => {
      type TestDataWithId = TestData & { id: string }

      const groupId = `streams-${Date.now()}`
      const items: TestDataWithId[] = [
        { id: 'streams-item1', value: 1 },
        { id: 'streams-item2', value: 2 },
        { id: 'streams-item3', value: 3 },
      ]

      // Set multiple items
      for (const item of items) {
        await iii.invokeFunction('streams.set', {
          stream_name: testStreamName,
          group_id: groupId,
          item_id: item.id,
          data: item,
        })
      }

      const result: TestDataWithId[] = await iii.invokeFunction('streams.list', {
        stream_name: testStreamName,
        group_id: groupId,
      })
      const sort = (a: TestDataWithId, b: TestDataWithId) => a.id.localeCompare(b.id)

      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBeGreaterThanOrEqual(items.length)
      expect(result.sort(sort)).toEqual(items.sort(sort))
    })
  })
})
