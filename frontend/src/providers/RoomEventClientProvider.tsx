import type { ReactNode } from 'react'
import type { Listener } from '../events/RoomEventClient.ts'
import { createContext, useContext, useEffect, useMemo } from 'react'
import { RoomEventClient } from '../events/RoomEventClient.ts'
import { getNumberFromLocalStorage } from '../utils/localStorage.ts'

const RoomEventClientContext = createContext<RoomEventClient | null>(null)

export function RoomEventClientProvider(props: {
  children: ReactNode
  roomId: number
}) {
  const client = useMemo(() => new RoomEventClient({
    urlBase: import.meta.env.WS_URL_BASE,
    roomId: props.roomId,
    lastSeq: getNumberFromLocalStorage(`room:${props.roomId}:last_seq`, null),
  }), [props.roomId])

  return (
    <RoomEventClientContext.Provider value={client}>
      {props.children}
    </RoomEventClientContext.Provider>
  )
}

export function useRoomEventClient() {
  const client = useContext(RoomEventClientContext)
  if (!client) {
    throw new Error('useRoomEventClient must be used within a RoomEventClientProvider')
  }
  return client
}

export function useRoomEventClientListener(
  listener: Listener,
) {
  const client = useRoomEventClient()

  useEffect(() => {
    return client.on(listener)
  }, [])
}
