import { afterAll, describe, expect, it, vi } from 'vitest'
import { cn } from './classes'

const classnamesDefault = vi.hoisted(() => vi.fn(() => 'class-names-mock'))
const twMerge = vi.hoisted(() => vi.fn(() => 'tailwind-merge-mock'))

vi.mock('classnames', () => {
  return { default: classnamesDefault }
})

vi.mock('tailwind-merge', () => {
  return { twMerge }
})

afterAll(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe('cn', () => {
  it('should call classNames and twMerge with correct arguments', () => {
    const args = ['class1', { class2: true, class3: false }, 'class4']
    const result = cn(...args)

    expect(result).toBe('tailwind-merge-mock')
    expect(classnamesDefault).toHaveBeenCalledWith(args)
    expect(twMerge).toHaveBeenCalledWith('class-names-mock')
  })
})
