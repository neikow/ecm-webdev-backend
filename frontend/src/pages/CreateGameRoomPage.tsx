import { zodResolver } from '@hookform/resolvers/zod'
import { useCallback, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { NavLink, useNavigate } from 'react-router'
import { z } from 'zod'
import { cn } from '../utils/cn.ts'
import { GameRoomPasswordSchema } from './HomePage.tsx'

const AvailableGameTypes = ['connect_four'] as const
type AvailableGameType = (typeof AvailableGameTypes)[number]
const AvailableGameTypeDefinitions: {
  [GameType in AvailableGameType]: {
    value: GameType
    label: string
  }
} = {
  connect_four: {
    value: 'connect_four',
    label: 'Connect Four',
  },
}

const CreateGameRoomSchema = z.object({
  game_type: z.enum(AvailableGameTypes),
  password: GameRoomPasswordSchema,
})

export function CreateGameRoomPage() {
  const navigate = useNavigate()
  const alreadyInAGameModalRef = useRef<HTMLDialogElement | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [canEndGame, setCanEndGame] = useState(false)
  const [activeGameRoomId, setActiveGameRoomId] = useState<number | null>(null)
  const { register, handleSubmit, formState: { errors }, setError } = useForm({
    resolver: zodResolver(CreateGameRoomSchema),
  })

  async function onSubmit(data: z.infer<typeof CreateGameRoomSchema>) {
    setIsLoading(true)
    const response = await fetch('/api/game_rooms/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    setIsLoading(false)

    if (response.ok) {
      const successData: {
        game_room: {
          id: string
        }
      } = await response.json()

      navigate(`/game-rooms/${successData.game_room.id}`)
    }
    else {
      const errorData: {
        detail: {
          code: string
          message: string
          room_id: string
          role: 'admin' | 'player'
        }
      } = await response.json()

      if (errorData.detail.code === 'already_in_game_room') {
        alreadyInAGameModalRef.current?.showModal()
        setActiveGameRoomId(Number(errorData.detail.room_id))
        if (errorData.detail.role === 'admin') {
          setCanEndGame(true)
        }
      }

      setError('root', { message: errorData.detail.message })
    }
  }

  const returnToActiveGameRoom = useCallback(() => {
    navigate(
      `/game-rooms/${activeGameRoomId}`,
    )
  }, [activeGameRoomId, navigate])

  const endPreviousGameRoom = useCallback(async () => {
    if (!activeGameRoomId) {
      return
    }

    setIsLoading(true)
    const response = await fetch(`/api/game_rooms/${activeGameRoomId}/end`, {
      method: 'POST',
    })
    setIsLoading(false)

    if (response.ok) {
      alreadyInAGameModalRef.current?.close()
      setCanEndGame(false)
    }
    else {
      const errorData: {
        detail: {
          code: string
          message: string
        }
      } = await response.json()
      setError('root', { message: errorData.detail.message })
    }
  }, [activeGameRoomId, setError])

  return (
    <div className="min-h-screen">
      <div className="hero min-h-screen bg-base-200">
        <div className="hero-content text-center">
          <div className="max-w-md">
            <h1 className="text-5xl font-bold">Create a Game Room</h1>
            <p className="py-6">
              Create a game room and invite your friends to play together!
            </p>
            <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
              <div className="flex flex-col">
                <select
                  {...register('game_type')}
                  defaultValue={'connect_four' as AvailableGameType}
                  className={cn({
                    'select w-full max-w-xs mx-auto': true,
                    'select-error': errors.game_type,
                  })}
                >
                  {
                    Object.values(AvailableGameTypeDefinitions).map(gameType => (
                      <option key={gameType.value} value={gameType.value}>
                        {gameType.label}
                      </option>
                    ))
                  }
                </select>
                {errors.game_type && (
                  <span className="text-error mt-2 text-sm text-center w-full">{errors.game_type.message}</span>
                )}
              </div>

              <div className="flex flex-col">
                <input
                  {...register('password')}
                  type="text"
                  placeholder="Room Password"
                  className={cn({ 'input w-full max-w-xs mx-auto': true, 'input-error': errors.password })}
                />
                {errors.password && (
                  <span className="text-error mt-2 text-sm text-center w-full">{errors.password.message}</span>
                )}
              </div>
              <button disabled={isLoading} className="btn btn-primary mx-auto" type="submit">
                Create Room
              </button>
              {errors.root && (
                <span className="text-error mt-2 text-sm text-center w-full">{errors.root.message}</span>
              )}
              <NavLink to="/" className="btn btn-outline mx-auto" type="submit">
                Back
              </NavLink>
            </form>
          </div>
        </div>
      </div>

      <dialog ref={alreadyInAGameModalRef} className="modal">
        <div className="modal-box flex flex-col items-center">
          <h3 className="font-bold text-2xl">Already playing</h3>
          <div className="pt-4 flex flex-col gap-4 items-center">
            <p className="text-center text-balance">
              You are already in a game room. Do you want to go back to it?
            </p>
          </div>
          <div className="modal-action">
            {canEndGame && (
              <button
                className="btn"
                onClick={endPreviousGameRoom}
              >
                End previous
              </button>
            )}
            <button
              className="btn btn-primary"
              onClick={returnToActiveGameRoom}
            >
              Return to game room
            </button>
          </div>
        </div>
        <form method="dialog" className="modal-backdrop">
          <button>close</button>
        </form>
      </dialog>
    </div>
  )
}
