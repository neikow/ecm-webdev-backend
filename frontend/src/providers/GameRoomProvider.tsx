import type { ReactNode } from 'react'
import { createContext, useContext, useEffect, useMemo } from 'react'
import { RoomEventClient } from '../events/RoomEventClient.ts'

interface GameRoomData {
  roomId: number
  client: RoomEventClient
}

const RoomDataContext = createContext<GameRoomData | undefined>(undefined)

export function GameRoomProvider(props: {
  roomId: number
  children: ReactNode
}) {
  const client = useMemo(() => new RoomEventClient({
    urlBase: import.meta.env.VITE_WS_URL_BASE,
    roomId: props.roomId,
  }), [props.roomId])

  useEffect(() => {
    client.connect()
    return () => {
      client.close()
    }
  }, [])

  const value = useMemo(() => ({
    roomId: props.roomId,
    client,
  } satisfies GameRoomData), [
    client,
    props.roomId,
  ])

  return (
    <RoomDataContext.Provider value={value}>
      {props.children}
    </RoomDataContext.Provider>
  )
}

export function useGameRoom() {
  const context = useContext(RoomDataContext)
  if (context === undefined) {
    throw new Error('useGameRoom must be used within a GameRoomProvider')
  }
  return context
}
