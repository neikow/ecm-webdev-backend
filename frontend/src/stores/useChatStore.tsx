import { create } from 'zustand/react'

export interface MessageData {
  type: 'text'
  sender_id: string
  value: string
}

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
