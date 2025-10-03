import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { LeaveGameRoomButton } from '../components/LeaveGameRoomButton.tsx'
import { ErrorPage } from './ErrorPage.tsx'

interface GameRoomData {
  id: number | null
  created_at: string
  password: string
  game_type: string
  is_active: boolean
}

export function GameRoomPage() {
  const { id: rawId } = useParams<'id'>()

  const { data, error, isPending } = useQuery<GameRoomData>({
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

  if (isPending) {
    return <div>Loading...</div>
  }

  return (
    <div className="flex flex-col bg-base-200">
      <header className="flex flex-row justify-between mb-6">
        <div className="flex flex-row gap-4 items-center justify-start p-4">
          <h1 className="text-4xl font-bold">
            Game Room #
            {data?.id}
          </h1>
          <h2 className="text-xl font-bold">
            {data?.game_type}
          </h2>
        </div>
        <div className="p-4 flex flex-row gap-4 items-center">
          <span className="font-sans select-none">
            Password:
            <span className="select-all font-mono font-bold p-2 border border-white/20 ml-2 rounded">
              {data?.password}
            </span>
          </span>
          <LeaveGameRoomButton />
        </div>
      </header>
      <div className="min-h-screen grid grid-cols-5 items-center">
        <div>

        </div>
        <div
          className="col-span-3 h-full"
        >
          <h3>
            Players
          </h3>
        </div>
        <div>

        </div>
      </div>
    </div>
  )
}
