import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { Chat } from '../components/game-room/Chat.tsx'
import { Header } from '../components/game-room/Header.tsx'
import { PlayerList } from '../components/game-room/PlayerList.tsx'
import { ErrorPage } from './ErrorPage.tsx'

export interface GameRoomData {
  id: number | null
  created_at: string
  password: string
  game_type: string
  is_active: boolean
}

export function GameRoomPage() {
  const { id: rawId } = useParams<'id'>()

  const { data, error } = useQuery<GameRoomData>({
    queryFn: () => fetch(`/api/game_rooms/data/${rawId}`).then((res) => {
      if (!res.ok) {
        throw new Error('Failed to fetch game room data')
      }
      return res.json()
    }),
    retry: false,
    queryKey: ['game-room', rawId],
    enabled: !!rawId,
  })

  if (!rawId) {
    throw new Error('Game room ID is missing from URL')
  }

  if (error) {
    return (
      <ErrorPage
        title="Failed to find the Game Room"
        message="The requested game room does not seem to be active, or you are not authorized to access it"
      />
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-base-200">
      <Header data={data} />
      <div className="grid grid-cols-7 items-center h-[calc(100vh-96px)]">
        <div className="col-span-1 h-full"></div>
        <div
          className="col-span-4 h-full pr-4"
        >
          <div className="w-full h-full card bg-base-100 shadow-md p-4">

          </div>
        </div>
        <div className="col-span-2 h-full pr-4 flex flex-col">
          <PlayerList className="min-h-48" />
          <Chat className="flex-1 " />
        </div>
      </div>
    </div>
  )
}
