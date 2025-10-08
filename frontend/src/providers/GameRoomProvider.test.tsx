import { cleanup, render, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GameRoomProvider, useGameRoom } from './GameRoomProvider.tsx'

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

beforeEach(() => {
  vi.stubEnv('VITE_WS_URL_BASE', 'ws://test')
})

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.clearAllMocks()
})

describe('gameRoomProvider', () => {
  it('should provide static room data to children', () => {
    const roomId = 10

    const { result } = renderHook(() => useGameRoom(), {
      wrapper: ({ children }) => (
        <GameRoomProvider roomId={roomId}>
          {children}
        </GameRoomProvider>
      ),
    })

    expect(result.current.roomId).toBe(roomId)
    expect(result.current.client).toBeDefined()
    expect(RoomEventClientMock).toHaveBeenCalledWith({
      urlBase: 'ws://test',
      roomId: 10,
    })
  })

  it('should throw if useGameRoom is used outside provider', () => {
    function Child() {
      useGameRoom()
      return null
    }

    expect(() => render(<Child />)).toThrow()
  })
})
