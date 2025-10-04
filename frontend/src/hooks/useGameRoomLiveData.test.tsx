import type { Mock } from 'vitest'
import type { RoomEventClient } from '../events/RoomEventClient.ts'
import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { setNumberToLocalStorage } from '../utils/localStorage.ts'
import { useGameRoomLiveData } from './useGameRoomLiveData'

vi.mock('../utils/localStorage.ts', () => ({
  getNumberFromLocalStorage: vi.fn(() => 0),
  setNumberToLocalStorage: vi.fn(),
}))

interface MockRoomEventClient extends Pick<RoomEventClient, 'on'> {
  emit: (msg: any) => void
  unsubscribe: Mock
}

type Constructor<T> = new (...args: any[]) => T

interface MockRoomEventClientModule {
  RoomEventClient: Constructor<MockRoomEventClient>
  __getLastInstance: () => MockRoomEventClient | undefined
}

vi.mock('../events/RoomEventClient.ts', () => {
  let lastInstance: MockRoomEventClient | undefined

  class MockClient implements MockRoomEventClient {
    private cb?: (msg: any) => void
    unsubscribe = vi.fn()

    constructor(_opts: any) {
      // eslint-disable-next-line ts/no-this-alias
      lastInstance = this
    }

    on(cb: (msg: any) => void) {
      this.cb = cb
      this.unsubscribe = vi.fn()
      return this.unsubscribe
    }

    emit(msg: any) {
      this.cb?.(msg)
    }
  }

  return {
    RoomEventClient: MockClient,
    __getLastInstance: () => lastInstance,
  } satisfies MockRoomEventClientModule
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('useGameRoomLiveData', () => {
  it('starts loading, then applies snapshot and persists last_seq', async () => {
    const roomId = 42
    const { result } = renderHook(() => useGameRoomLiveData(roomId))

    expect(result.current.isLoading).toBe(true)
    expect(result.current.liveData).toBeUndefined()

    const { __getLastInstance } = (await import('../events/RoomEventClient.ts')) as unknown as MockRoomEventClientModule
    const client = __getLastInstance()

    const snapshot = { a: 1, b: 2 }
    await act(async () => {
      client?.emit({ type: 'snapshot', data: snapshot, last_seq: 7 })
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.liveData).toEqual(snapshot)
    expect(setNumberToLocalStorage).toHaveBeenCalledWith(`room:${roomId}:last_seq`, 7)
  })

  it('persists seq on event and keeps existing data', async () => {
    const roomId = 1
    const { result } = renderHook(() => useGameRoomLiveData(roomId))
    const { __getLastInstance } = await import('../events/RoomEventClient.ts') as unknown as MockRoomEventClientModule
    const client = __getLastInstance()

    await act(async () => {
      client?.emit({ type: 'snapshot', data: { x: 'y' }, last_seq: 3 })
    })

    await act(async () => {
      client?.emit({ type: 'event', seq: 4, event: { foo: 'bar' } })
    })

    expect(result.current.liveData).toEqual({ x: 'y' })
    expect(setNumberToLocalStorage).toHaveBeenCalledWith(`room:${roomId}:last_seq`, 4)
  })

  it('calls unsubscribe on unmount', async () => {
    const roomId = 10
    const { unmount } = renderHook(() => useGameRoomLiveData(roomId))
    const { __getLastInstance } = await import('../events/RoomEventClient.ts') as unknown as MockRoomEventClientModule
    const client = __getLastInstance()

    unmount()
    expect(client?.unsubscribe).toHaveBeenCalledTimes(1)
  })
})
