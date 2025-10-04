export type ServerMessage
  = | { type: 'snapshot', last_seq: number, data: any }
    | { type: 'event', seq: number, event: any }
    | { type: 'ping' }

export type Listener = (msg: ServerMessage) => void

export class RoomEventClient {
  private ws?: WebSocket
  private url: string
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
    this.url = `${config.urlBase.replace(/\/$/, '')}/ws/rooms/${config.roomId}${
      config.lastSeq ? `?last_seq=${config.lastSeq}` : ''
    }`
    this.roomId = config.roomId
    this.lastSeq = config.lastSeq ?? null
  }

  connect() {
    this.ws = new WebSocket(this.url)
    this.ws!.onmessage = (e) => {
      const msg: ServerMessage = JSON.parse(e.data)
      if (msg.type === 'snapshot') {
        this.lastSeq = msg.last_seq
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

  reconnect() {
    this.retries += 1
    const seq: number = this.lastSeq ?? Number.parseInt(
      localStorage.getItem(`room:${this.roomId}:last_seq`) || '0',
    )
    this.url = this.url.replace(/(&last_seq=\d+)?$/, `&last_seq=${seq}`)
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
