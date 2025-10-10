import type { API } from '../types'

export type ServerMessage
  = | API['WSMessageSnapshot']
    | API['WSMessageError']
    | API['WSMessageEvent']
    | API['WSMessageResponse']
    | API['WSMessagePing']

export type ClientMessage = API['ClientMessageChatMessage'] | API['ClientMessagePing'] | {
  type: 'action'
  action: string
  request_id: string
  data: Record<string, unknown>
}

export type Listener = (msg: ServerMessage) => void

export class RoomEventClient {
  private ws?: WebSocket
  private url: URL
  private readonly roomId: number
  private lastSeq: number | null
  private listeners: Set<Listener>

  private retriesDelay: number[] = [
    500,
    1000,
    2000,
    5000,
    10000,
    20000,
    30000,
  ]

  private retries: number = 0

  constructor(config: {
    urlBase: string
    roomId: number
    lastSeq?: number | null
  }) {
    this.listeners = new Set()
    this.url = new URL(`${config.urlBase.replace(/\/$/, '')}/ws/game_rooms/${config.roomId}`)
    this.roomId = config.roomId
    this.lastSeq = config.lastSeq ?? null
  }

  connect() {
    this.ws = new WebSocket(this.url)
    this.ws!.onmessage = (e) => {
      this.retries = 0

      const msg: ServerMessage = JSON.parse(e.data)

      if (msg.type === 'snapshot') {
        this.lastSeq = msg.last_seq
        this.listeners.forEach(listener => listener(msg))
      }
      else if (msg.type === 'event') {
        this.lastSeq = msg.seq
        localStorage.setItem(`room:${this.roomId}:last_seq`, String(this.lastSeq))
      }
      this.listeners.forEach(listener => listener(msg))
    }
    this.ws!.onclose = () => {
      setTimeout(
        () => this.reconnect(),
        this.currentRetryDelay,
      )
    }
  }

  send(data: ClientMessage) {
    if (!this.ws) {
      throw new Error('WebSocket is not connected')
    }
    this.ws.send(
      JSON.stringify(data),
    )
  }

  reconnect() {
    this.retries += 1
    const seq: number = this.lastSeq ?? Number.parseInt(
      localStorage.getItem(`room:${this.roomId}:last_seq`) || '0',
    )
    const url = new URL(this.url.toString())
    if (seq) {
      url.searchParams.set('last_seq', String(seq))
    }
    this.url = url
    this.connect()
  }

  private get currentRetryDelay() {
    return this.retriesDelay[Math.min(this.retries, this.retriesDelay.length - 1)]
  }

  on(listener: Listener) {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  close() {
    this.ws?.close()
  }
}
