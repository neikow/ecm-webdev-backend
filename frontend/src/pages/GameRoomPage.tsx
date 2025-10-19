import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router'
import { Chat } from '../components/game-room/Chat.tsx'
import { GameBoard } from '../components/game-room/GameBoard.tsx'
import { Header } from '../components/game-room/Header.tsx'
import { PlayerList } from '../components/game-room/PlayerList.tsx'
import { usePeriodicTokensRefresh } from '../hooks/usePeriodicTokensRefresh.tsx'
import { GameRoomProvider } from '../providers/GameRoomProvider.tsx'
import { useCurrentPlayer } from '../stores/useCurrentPlayer.tsx'
import { apiClient } from '../utils/fetch.ts'
import { ErrorPage } from './ErrorPage.tsx'

export function GameRoomPage() {
  const { id: rawId } = useParams<'id'>()
  const roomId = Number(rawId)
  const navigate = useNavigate()
  const { setCurrentPlayer } = useCurrentPlayer()

  usePeriodicTokensRefresh()

  const { data, isError } = apiClient.useQuery('get', '/game_rooms/data/{game_room_id}/', {
    enabled: !Number.isNaN(roomId),
    retry: false,
    params: {
      path: {
        game_room_id: Number(rawId),
      },
    },
  })

  useEffect(() => {
    if (data?.current_player) {
      setCurrentPlayer({
        id: data.current_player.id!,
        user_name: data.current_player.user_name,
        role: data.current_player.role,
        room_id: data.current_player.room_id,
        status: 'connected',
      })
    }
    else {
      setCurrentPlayer(null)
    }
  }, [data])

  if (Number.isNaN(roomId) || isError) {
    return (
      <ErrorPage
        title="Failed to find the Game Room"
        message="The requested game room does not seem to be active, or you are not authorized to access it"
      />
    )
  }

  return (
    <GameRoomProvider roomId={roomId}>
      <div className="min-h-screen flex flex-col bg-base-300">
        <Header data={data} navigate={navigate} />
        <div className="grid grid-cols-6 lg:grid-cols-7 items-center h-[calc(100vh-96px)]">
          <div className="hidden lg:block col-span-1 h-full"></div>
          <div className="col-span-4 h-full pr-4">
            <GameBoard />
          </div>
          <div className="col-span-2 pr-4 flex flex-col h-[calc(100vh-96px)]">
            <PlayerList className="min-h-48 max-h-64 flex-shrink-0" />
            <Chat className="flex-1 min-h-0" />
          </div>
        </div>
      </div>
    </GameRoomProvider>
  )
}
