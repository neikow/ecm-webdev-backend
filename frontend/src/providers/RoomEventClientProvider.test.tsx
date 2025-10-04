import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RoomEventClientProvider, useRoomEventClient, useRoomEventClientListener } from './RoomEventClientProvider'

const onMock = vi.hoisted(() => vi.fn(() => vi.fn()))

const RoomEventClientMock = vi.hoisted(
  () => vi.fn().mockImplementation(() => ({
    on: onMock,
  })),
)

vi.mock('../events/RoomEventClient.ts', () => ({
  RoomEventClient: RoomEventClientMock,
}))

vi.mock('../utils/localStorage.ts', () => ({
  getNumberFromLocalStorage: vi.fn(() => 123),
}))

beforeEach(() => {
  vi.stubEnv('WS_URL_BASE', 'ws://test')
})

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.clearAllMocks()
})

describe('roomEventClientProvider', () => {
  it('provides RoomEventClient to children', () => {
    function Child() {
      const client = useRoomEventClient()
      return <div data-testid="client">{client ? 'ok' : 'fail'}</div>
    }

    render(
      <RoomEventClientProvider roomId={42}>
        <Child />
      </RoomEventClientProvider>,
    )
    expect(screen.getByTestId('client').textContent).toBe('ok')
    expect(RoomEventClientMock).toHaveBeenCalledWith({
      urlBase: 'ws://test',
      roomId: 42,
      lastSeq: 123,
    })
  })

  it('throws if useRoomEventClient is used outside provider', () => {
    function Child() {
      useRoomEventClient()
      return null
    }

    expect(() => render(<Child />)).toThrow()
  })
})

describe('useRoomEventClientListener', () => {
  it('registers and cleans up listener', () => {
    const listener = vi.fn()

    function Child() {
      useRoomEventClientListener(listener)
      return null
    }

    const { unmount } = render(
      <RoomEventClientProvider roomId={1}>
        <Child />
      </RoomEventClientProvider>,
    )
    expect(onMock).toHaveBeenCalledWith(listener)
    unmount()
    expect(onMock.mock.results[0].value).toHaveBeenCalled()
  })
})
