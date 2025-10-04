import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { localStorageMock } from '../tests/utils.ts'
import { getNumberFromLocalStorage, setNumberToLocalStorage } from './localStorage.ts'

describe('localStorage', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', localStorageMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('getNumberFromLocalStorage', () => {
    it('should return default value if key does not exist', () => {
      expect(getNumberFromLocalStorage('room:1:last_seq', 10)).toBe(10)
    })

    it('should return number if key exists and is a valid number', () => {
      localStorage.setItem('room:1:last_seq', '42')
      expect(getNumberFromLocalStorage('room:1:last_seq', 10)).toBe(42)
    })

    it('should return default value if key exists but is not a valid number', () => {
      localStorage.setItem('room:1:last_seq', 'not-a-number')
      expect(getNumberFromLocalStorage('room:1:last_seq', 10)).toBe(10)
    })
  })

  describe('setNumberToLocalStorage', () => {
    it('should set the number as a string in localStorage', () => {
      setNumberToLocalStorage('room:1:last_seq', 42)
      expect(localStorage.getItem('room:1:last_seq')).toBe('42')
    })

    it('should overwrite existing value', () => {
      localStorage.setItem('room:1:last_seq', '10')
      setNumberToLocalStorage('room:1:last_seq', 42)
      expect(localStorage.getItem('room:1:last_seq')).toBe('42')
    })
  })
})
