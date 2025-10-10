import type { API } from '../types'
import { create } from 'zustand/react'

export type MessageData = API['SnapshotChatMessage']

interface ChatState {
  messages: MessageData[]
  addMessage: (message: MessageData) => void
  setMessages: (messages: MessageData[]) => void
}

export const useChatStore = create<ChatState>(set => ({
  messages: [],
  addMessage: (message) => {
    set(state => ({ messages: [...state.messages, message] }))
  },
  setMessages: messages =>
    set({ messages }),
}))
