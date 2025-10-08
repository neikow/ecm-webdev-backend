import { useEffect, useMemo } from 'react'
import { useGameRoom } from '../providers/GameRoomProvider.tsx'
import { useChatStore } from '../stores/useChatStore.tsx'

export function useRoomChat(onNewMessage: () => void) {
  const { client } = useGameRoom()
  const { messages, setMessages, addMessage } = useChatStore()

  useEffect(() => {
    return client.on((message) => {
      if (message.type === 'snapshot') {
        setMessages(message.data.chat_messages)
        onNewMessage()
      }
      else if (message.type === 'event') {
        if (message.event.type === 'message.sent') {
          addMessage({
            sender_id: message.event.data.sender_id,
            value: message.event.data.value,
            type: 'text',
          })
          onNewMessage()
        }
      }
    })
  }, [client, addMessage, setMessages])

  return useMemo(() => ({
    messages,
    sendMessage: (msg: string) => {
      client.send({
        type: 'chat_message',
        text: msg,
      })
    },
  }), [messages])
}
