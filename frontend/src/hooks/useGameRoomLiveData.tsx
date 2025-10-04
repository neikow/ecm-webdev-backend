import type { ServerMessage } from '../events/RoomEventClient.ts'
import type { Player } from '../types/player.ts'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { RoomEventClient } from '../events/RoomEventClient.ts'
import { getNumberFromLocalStorage, setNumberToLocalStorage } from '../utils/localStorage.ts'

interface ChatMessage {

}

interface LiveData {
  room_id: number
  status: 'waiting_for_players'
  chat_messages: ChatMessage[]
  players: Player[]
}

export function useGameRoomLiveData(roomId: number) {
  const [isLoading, setIsLoading] = useState(true)
  const roomEventClient = useRef(new RoomEventClient({
    urlBase: import.meta.env.VITE_WS_URL_BASE,
    lastSeq: getNumberFromLocalStorage(`room:${roomId}:last_seq`, null),
    roomId,
  }))

  const [liveData, setLiveData] = useState<LiveData>()

  const handleEvent = useCallback((message: ServerMessage) => {
    if (message.type === 'snapshot') {
      setIsLoading(false)
      setLiveData(message.data)
      setNumberToLocalStorage(`room:${roomId}:last_seq`, message.last_seq)
    }
    else if (message.type === 'ping') {
      // ignore
    }
    else if (message.type === 'event') {
      setNumberToLocalStorage(`room:${roomId}:last_seq`, message.seq)
      console.log(message.event)
    }
  }, [roomId])

  useEffect(() => {
    roomEventClient.current.connect()
    return roomEventClient.current.on(handleEvent)
  }, [])

  return useMemo(() => ({ data: liveData, isLoading }), [liveData, isLoading])
}
