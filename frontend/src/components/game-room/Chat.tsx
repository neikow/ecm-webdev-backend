import type { ClassValue } from '../../utils/classes.ts'
import { zodResolver } from '@hookform/resolvers/zod'
import { useCallback, useMemo, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useRoomChat } from '../../hooks/useRoomChat.tsx'
import { usePlayersStore } from '../../stores/usePlayersStore.tsx'
import { cn } from '../../utils/classes.ts'

interface ChatProps {
  className?: ClassValue
  currentPlayerId: string | undefined
}

const MessageSchema = z.object({ message: z.string().max(500, 'Message must be between 1 and 500 characters') })

export function Chat(props: ChatProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset: resetForm,
  } = useForm({
    resolver: zodResolver(MessageSchema),
  })

  const chatMessagesRef = useRef<HTMLDivElement | null>(null)

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      if (chatMessagesRef.current) {
        chatMessagesRef.current.scrollTo({
          top: chatMessagesRef.current.scrollHeight,
          behavior: 'smooth',
        })
      }
    }, 50)
  }, [chatMessagesRef])

  const { messages, sendMessage } = useRoomChat(scrollToBottom)

  const onSubmit = (data: z.infer<typeof MessageSchema>) => {
    if (data.message.trim() === '') {
      resetForm()
      return
    }
    sendMessage(data.message)
    scrollToBottom()
    resetForm()
  }

  const { players } = usePlayersStore()

  const userNames = useMemo(() => {
    return new Map(players.map(player => [player.id, player.user_name]))
  }, [players])

  if (!props.currentPlayerId) {
    return <div className="skeleton w-full h-full"></div>
  }

  console.log(messages, props.currentPlayerId)

  return (
    <div
      className={cn(
        'card bg-base-200 shadow-md p-4 flex flex-col min-h-0',
        props.className,
      )}
    >
      <h3 className="mb-2 font-bold text-lg">Chat</h3>
      <div className="flex-1 overflow-hidden flex flex-col mb-4">
        <div className="flex-1 overflow-y-auto flex flex-col gap-2" ref={chatMessagesRef}>
          {messages.length === 0
            ? (
                <div className="text-center text-sm text-gray-500 mt-4">
                  No messages yet.
                </div>
              )
            : (
                messages.map((msg, index) => (
                  <div key={index} className="chat-message">
                    <div
                      className={cn('flex items-end', {
                        'justify-end': msg.sender_id === props.currentPlayerId,
                      })}
                    >
                      <div className="flex flex-col space-y-1 text-xs max-w-xs mx-2 order-2 items-start">
                        <div
                          className="flex flex-row items-center w-full"
                        >
                          <span
                            className={cn('px-2 py-2 rounded-lg flex flex-col', {
                              'bg-gray-200 text-gray-800': msg.sender_id !== props.currentPlayerId,
                              'bg-primary text-white': msg.sender_id === props.currentPlayerId,
                            })}
                          >
                            {msg.sender_id !== props.currentPlayerId && (
                              <span className="font-bold mr-2">
                                {userNames.get(msg.sender_id) || msg.sender_id}
                              </span>
                            )}
                            <span>
                              {msg.value}
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
        </div>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="flex-shrink-0">
        <input
          {...register('message')}
          type="text"
          placeholder="Type a message..."
          className="input input-bordered w-full"
        />
        {errors.message && (
          <p className="text-red-500 text-sm mt-1">{errors.message.message}</p>
        )}
      </form>
    </div>
  )
}
