import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'
import { Chat } from '../components/game-room/Chat.tsx'
import { Header } from '../components/game-room/Header.tsx'
import { PlayerList } from '../components/game-room/PlayerList.tsx'
import { GameRoomProvider } from '../providers/GameRoomProvider.tsx'
import { ErrorPage } from './ErrorPage.tsx'

export interface StaticGameRoomData {
  game_room: {
    id: number | null
    created_at: string
    password: string
    game_type: string
    is_active: boolean
  }
  current_player?: {
    id: string
  }
}

export interface ApiError {
  detail: {
    code: string
    message: string
  }
}

export function GameRoomPage() {
  const { id: rawId } = useParams<'id'>()
  const navigate = useNavigate()

  const { data, isError } = useQuery<StaticGameRoomData, Error | ApiError>({
    queryKey: ['game-room', rawId],
    retry: false,
    queryFn: async () => {
      const res = await fetch(`/api/game_rooms/data/${rawId}`)

      if (!res.ok) {
        throw await res.json()
      }

      return await res.json()
    },
  })

  if (isError || !rawId) {
    return (
      <ErrorPage
        title="Failed to find the Game Room"
        message="The requested game room does not seem to be active, or you are not authorized to access it"
      />
    )
  }

  return (
    <GameRoomProvider roomId={Number(rawId)}>
      <div className="min-h-screen flex flex-col bg-base-300">
        <Header data={data} navigate={navigate} />
        <div className="grid grid-cols-7 items-center h-[calc(100vh-96px)]">
          <div className="col-span-1 h-full"></div>
          <div className="col-span-4 h-full pr-4">
            <div className="w-full h-full card bg-base-200 shadow-md p-4">

            </div>
          </div>
          <div className="col-span-2 pr-4 flex flex-col h-[calc(100vh-96px)]">
            <PlayerList className="min-h-48 max-h-64 flex-shrink-0" />
            <Chat className="flex-1 min-h-0" currentPlayerId={data?.current_player?.id} />
          </div>
        </div>
      </div>
    </GameRoomProvider>
  )
}
