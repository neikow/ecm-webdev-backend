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
    <div className="min-h-screen flex flex-col bg-base-200">
      <header className="flex flex-row justify-between">
        <div className="flex flex-row gap-4 items-center justify-start p-4">
          <h1 className="text-4xl font-bold text-secondary">
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
      <div className="grid grid-cols-7 items-center h-[calc(100vh-96px)]">
        <div className="col-span-1 h-full"></div>
        <div
          className="col-span-4 h-full pr-4"
        >
          <div className="w-full h-full card bg-base-100 shadow-md p-4">

          </div>
        </div>
        <div className="col-span-2 h-full pr-4 flex flex-col">
          <div className="card bg-base-100 shadow-md mb-4 p-4 min-h-48">
            <h3 className="mb-2 font-bold text-lg">
              Players
            </h3>
          </div>
          <div className="card bg-base-100 shadow-md p-4 flex-1 flex flex-col">
            <h3 className="mb-2 font-bold text-lg">
              Chat
            </h3>
            <div className="flex-1">

            </div>
            <div>
              <input
                type="text"
                placeholder="Type a message..."
                className="input input-bordered w-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
