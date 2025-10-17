import type { API } from '../types'

export type ServerMessage
  = | API['WSMessageSnapshot']
    | API['WSMessageError']
    | API['WSMessageEvent']
    | API['WSMessageResponse']
    | API['WSMessagePing']

export type ClientMessage
  = | API['ClientMessageChatMessage'] & { data?: never }
    | API['ClientMessagePing'] & { data?: never, text?: never }
    | API['ClientMessageGameAction'] & { text?: never }
    | API['ClientMessageGameStart'] & { data?: never, text?: never }

export type Listener = (msg: ServerMessage) => void

export class WebsocketClosedError extends Error {
}

export class ResponseTimeoutError extends Error {
}

export class WebsocketResponseError extends Error {
  code: API['WSMessageError']['code'] | 'unknown'

  constructor(data: API['WSMessageError'] | undefined) {
    super(data?.message)
    this.code = data?.code ?? 'unknown'
  }
}

export class RoomEventClient {
  private ws?: WebSocket
  private url: URL
  private readonly roomId: number
  private lastSeq: number | null
  private listeners: Set<Listener>
  private closedByUser: boolean = false

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
      if (!this.closedByUser) {
        setTimeout(
          () => {
            if (this.closedByUser) {
              return
            }
            this.reconnect()
          },
          this.currentRetryDelay,
        )
      }
    }
  }

  send(data: ClientMessage) {
    if (!this.ws) {
      throw new WebsocketClosedError('WebSocket is not connected')
    }
    this.ws.send(
      JSON.stringify(data),
    )
  }

  sendWithResponse(
    data: Omit<ClientMessage, 'event_key'>,
    timeoutMs: number = 5000,
  ) {
    return new Promise<boolean>((resolve, reject) => {
      if (!this.ws) {
        return reject(new WebsocketClosedError('WebSocket is not connected'))
      }

      const eventKey = crypto.randomUUID() // If this key is too long, switch to nanoid

      const dataWithKey = {
        ...data,
        event_key: eventKey,
      } as ClientMessage

      const onMessage: Listener = (msg) => {
        if (msg.type === 'response' && msg.event_key === eventKey) {
          this.listeners.delete(onMessage)

          if (msg.success) {
            resolve(true)
          }

          reject(new WebsocketResponseError(msg.error || undefined))
        }
      }

      setTimeout(() => {
        this.listeners.delete(onMessage)
        reject(new ResponseTimeoutError('Response timed out'))
      }, timeoutMs)

      this.send(dataWithKey)

      this.listeners.add(onMessage)
    })
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
    this.closedByUser = true
    this.listeners.clear()
    this.ws?.close()
  }
}
