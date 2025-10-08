import type { Listener } from '../events/RoomEventClient.ts'
import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GameRoomProvider } from '../providers/GameRoomProvider.tsx'
import { usePlayersStore } from '../stores/usePlayersStore.tsx'
import { useRoomPlayers } from './useRoomPlayers.tsx'

const onMock = vi.hoisted(() => vi.fn(() => vi.fn()))

const RoomEventClientMock = vi.hoisted(
  () => vi.fn().mockImplementation(() => ({
    on: onMock,
    connect: vi.fn(),
  })),
)

vi.mock('../events/RoomEventClient.ts', () => ({
  RoomEventClient: RoomEventClientMock,
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('useRoomPlayers', () => {
  beforeEach(() => {
    const { result } = renderHook(() => usePlayersStore())
    act(() => result.current.setPlayers(() => []))
  })

  it('should return an array of users', () => {
    const { result } = renderHook(() => useRoomPlayers(), {
      wrapper: ({ children }) => (
        <GameRoomProvider roomId={0}>
          {children}
        </GameRoomProvider>
      ),
    })

    expect(Array.isArray(result.current)).toBe(true)
    expect(result.current).toHaveLength(0)
  })

  it('should reflect players from the store', () => {
    const { result: playersResult } = renderHook(() => usePlayersStore())
    const { result: roomPlayersResult } = renderHook(() => useRoomPlayers(), {
      wrapper: ({ children }) => (
        <GameRoomProvider roomId={0}>
          {children}
        </GameRoomProvider>
      ),
    })

    const players = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' as const },
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin' as const },
    ]

    act(() => {
      playersResult.current.setPlayers(() => players)
    })

    expect(roomPlayersResult.current).toHaveLength(2)
    expect(roomPlayersResult.current).toEqual(players)
  })

  it('should update when client receives a snapshot event', () => {
    const { result } = renderHook(() => useRoomPlayers(), {
      wrapper: ({ children }) => (
        <GameRoomProvider roomId={1}>
          {children}
        </GameRoomProvider>
      ),
    })

    // @ts-expect-error accessing an existing index
    const listener = onMock.mock.calls[0][0] as Listener

    act(() => {
      listener({
        type: 'snapshot',
        last_seq: 1,
        data: {
          players: [
            { id: '1', user_name: 'Alice', role: 'player' as const },
            { id: '2', user_name: 'Bob', role: 'admin' as const },
          ],
        },
      })
    })

    expect(result.current).toHaveLength(2)
    expect(result.current).toStrictEqual([
      { id: '1', user_name: 'Alice', role: 'player' },
      { id: '2', user_name: 'Bob', role: 'admin' },
    ])
  })

  it('should update when client receives a player.joined event', () => {
    const { result } = renderHook(() => useRoomPlayers(), {
      wrapper: ({ children }) => (
        <GameRoomProvider roomId={1}>
          {children}
        </GameRoomProvider>
      ),
    })

    const { result: playersResult } = renderHook(() => usePlayersStore())

    const players = [
      { id: '1', user_name: 'Alice', role: 'player' as const },
    ]

    act(() => {
      playersResult.current.setPlayers(players)
    })

    // @ts-expect-error accessing an existing index
    const listener = onMock.mock.calls[0][0] as Listener

    act(() => {
      listener({
        type: 'event',
        seq: 2,
        event: {
          type: 'player.joined',
          data: {
            id: '2',
            user_name: 'Bob',
            role: 'admin',
          },
        },
      })
    })

    expect(result.current).toHaveLength(2)
    expect(result.current).toEqual([
      { id: '1', user_name: 'Alice', role: 'player' },
      { id: '2', user_name: 'Bob', role: 'admin' },
    ])
  })

  it('should update when client receives a player.left event', () => {
    const { result } = renderHook(() => useRoomPlayers(), {
      wrapper: ({ children }) => (
        <GameRoomProvider roomId={1}>
          {children}
        </GameRoomProvider>
      ),
    })
    const { result: playersResult } = renderHook(() => usePlayersStore())

    const players = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' as const },
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin' as const },
    ]

    act(() => {
      playersResult.current.setPlayers(players)
    })

    // @ts-expect-error accessing an existing index
    const listener = onMock.mock.calls[0][0] as Listener

    act(() => {
      listener({
        type: 'event',
        seq: 3,
        event: {
          type: 'player.left',
          data: {
            id: '2',
          },
        },
      })
    })

    expect(result.current).toHaveLength(1)
    expect(result.current).toEqual([
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' },
    ])
  })
})
