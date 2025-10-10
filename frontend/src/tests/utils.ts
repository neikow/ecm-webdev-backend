import { vi } from 'vitest'

export class MockWebSocket {
  url: string

  onmessage: ((e: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  close = vi.fn()
  send = vi.fn()

  constructor(url: string) {
    this.url = url
  }
}

export const localStorageMock: Storage = (() => {
  const store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    key(index: number): string | null {
      const keys = Object.keys(store)
      return keys[index] ?? null
    },
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      for (const key in store) {
        delete store[key]
      }
    }),
    get length() {
      return Object.keys(store).length
    },
  } satisfies Storage
})()
