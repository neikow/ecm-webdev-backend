import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { localStorageMock, MockWebSocket } from '../tests/utils.ts'
import { RoomEventClient } from './RoomEventClient.ts'

describe('roomEventClient', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.stubGlobal('localStorage', localStorageMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should connect and handle snapshot message', () => {
    const client = new RoomEventClient({ urlBase: 'ws://localhost', roomId: 1 })
    const listener = vi.fn()
    client.on(listener)
    client.connect()
    const ws = (client as any).ws as MockWebSocket
    ws.onmessage!({ data: JSON.stringify({ type: 'snapshot', last_seq: 42, data: {} }) })
    expect(listener).toHaveBeenCalledWith({ type: 'snapshot', last_seq: 42, data: {} })
    expect((client as any).lastSeq).toBe(42)
  })

  it('should handle event message and update localStorage', () => {
    const client = new RoomEventClient({ urlBase: 'ws://localhost', roomId: 2 })
    client.connect()
    const ws = (client as any).ws as MockWebSocket
    ws.onmessage!({ data: JSON.stringify({ type: 'event', seq: 7, event: {} }) })
    expect(localStorage.setItem).toHaveBeenCalledWith('room:2:last_seq', '7')
    expect((client as any).lastSeq).toBe(7)
  })

  it('should call listeners for all messages', () => {
    const client = new RoomEventClient({ urlBase: 'ws://localhost', roomId: 3 })
    const listener = vi.fn()
    client.on(listener)
    client.connect()
    const ws = (client as any).ws as MockWebSocket
    ws.onmessage!({ data: JSON.stringify({ type: 'ping' }) })
    expect(listener).toHaveBeenCalledWith({ type: 'ping' })
  })

  it('should reconnect on close', async () => {
    vi.useFakeTimers()
    const client = new RoomEventClient({ urlBase: 'ws://localhost', roomId: 4 })

    vi.spyOn(client, 'connect')

    client.connect()
    const ws = (client as any).ws as MockWebSocket
    ws.onclose!()
    vi.runAllTimers()
    expect((client as any).retries).toBe(1)
    expect(client.connect).toHaveBeenCalledTimes(2)
    vi.useRealTimers()
  })

  it('should close websocket', () => {
    const client = new RoomEventClient({ urlBase: 'ws://localhost', roomId: 5 })
    client.connect()
    const ws = (client as any).ws as MockWebSocket
    client.close()
    expect(ws.close).toHaveBeenCalled()
  })

  it('should allow sending messages to server', () => {
    const client = new RoomEventClient({ urlBase: 'ws://localhost', roomId: 6 })
    client.connect()
    const ws = (client as any).ws as MockWebSocket
    client.send({ type: 'test', payload: 'data' })
    expect(ws.send).toHaveBeenCalledOnce()
    expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: 'test', payload: 'data' }))
  })
})
