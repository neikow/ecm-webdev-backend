import type { MessageData } from './useChatStore'
import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { useChatStore } from './useChatStore'

describe('useChatStore', () => {
  beforeEach(() => {
    useChatStore.setState({ messages: [] })
  })

  it('should initialize with empty messages', () => {
    const { result } = renderHook(() => useChatStore())
    expect(result.current.messages).toStrictEqual([])
  })

  it('should add a single message', () => {
    const { result } = renderHook(() => useChatStore())
    const message: MessageData = {
      type: 'text',
      sender_id: 'user1',
      value: 'Hello world',
    }

    act(() => {
      result.current.addMessage(message)
    })

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0]).toEqual(message)
  })

  it('should add multiple messages', () => {
    const { result } = renderHook(() => useChatStore())
    const message1: MessageData = {
      type: 'text',
      sender_id: 'user1',
      value: 'First message',
    }
    const message2: MessageData = {
      type: 'text',
      sender_id: 'user2',
      value: 'Second message',
    }

    act(() => {
      result.current.addMessage(message1)
      result.current.addMessage(message2)
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages).toEqual([message1, message2])
  })

  it('should set messages', () => {
    const { result } = renderHook(() => useChatStore())
    const messages: MessageData[] = [
      { type: 'text', sender_id: 'user1', value: 'Message 1' },
      { type: 'text', sender_id: 'user2', value: 'Message 2' },
    ]

    act(() => {
      result.current.setMessages(messages)
    })

    expect(result.current.messages).toEqual(messages)
  })

  it('should replace existing messages when using setMessages', () => {
    const { result } = renderHook(() => useChatStore())
    const initialMessage: MessageData = {
      type: 'text',
      sender_id: 'user1',
      value: 'Initial',
    }
    const newMessages: MessageData[] = [
      { type: 'text', sender_id: 'user2', value: 'New' },
    ]

    act(() => {
      result.current.addMessage(initialMessage)
      result.current.setMessages(newMessages)
    })

    expect(result.current.messages).toEqual(newMessages)
  })
})
