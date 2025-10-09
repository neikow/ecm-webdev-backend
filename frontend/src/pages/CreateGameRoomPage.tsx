import type { API } from '../types'
import { zodResolver } from '@hookform/resolvers/zod'
import { useCallback, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { NavLink, useNavigate } from 'react-router'
import { z } from 'zod'
import { cn } from '../utils/classes.ts'
import { apiClient } from '../utils/fetch.ts'
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
  user_name: z.string().min(1, 'Name is required').max(32, 'Name is too long'),
  password: GameRoomPasswordSchema,
})

export function CreateGameRoomPage() {
  const navigate = useNavigate()
  const alreadyInAGameModalRef = useRef<HTMLDialogElement | null>(null)
  const [canEndGame, setCanEndGame] = useState(false)
  const [activeGameRoomId, setActiveGameRoomId] = useState<number | null>(null)
  const { register, handleSubmit, formState: { errors }, setError } = useForm({
    resolver: zodResolver(CreateGameRoomSchema),
  })

  const { mutate: createGameRoom, isPending: isGameRoomCreationLoading } = apiClient.useMutation('post', '/game_rooms/', {
    onSuccess: (data) => {
      navigate(`/game-rooms/${data.game_room.id}`)
    },
    onError: (error) => {
      const errorData = error as API['ApiErrorDetail']
      if (errorData.code === 'already_in_game_room') {
        if (errorData.role === 'admin') {
          setCanEndGame(true)
        }

        setActiveGameRoomId(Number(errorData.room_id))
        alreadyInAGameModalRef.current?.showModal()
      }

      setError('root', { message: errorData.message })
    },
  })

  const {
    mutate: endGameRoom,
    isPending: isEndGameRoomLoading,
  } = apiClient.useMutation('post', '/game_rooms/{game_room_id}/end/', {
    onSuccess: (data) => {
      if (!data.success) {
        setError('root', { message: 'Failed to end the previous game room' })
      }
      else {
        alreadyInAGameModalRef.current?.close()
        setCanEndGame(false)
      }
    },
    onError: (error) => {
      const errorData = error as API['ApiErrorDetail']
      setError('root', { message: errorData.message })
    },
  })

  async function onSubmit(data: z.infer<typeof CreateGameRoomSchema>) {
    createGameRoom({
      body: data,
    })
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

    endGameRoom({
      params: {
        path: {
          game_room_id: activeGameRoomId,
        },
      },
    })
  }, [activeGameRoomId, setError])

  const hasErrors = errors.root || errors.game_type || errors.user_name || errors.password

  return (
    <div className="min-h-screen">
      <div className="hero min-h-screen bg-base-200">
        <div className="hero-content text-center">
          <div className="max-w-md">
            <h1 className="text-5xl font-bold">Create a Game Room</h1>
            <p className="py-6 text-balance">
              Create a game room and invite your friends to play together!
            </p>
            <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
              <div className="flex flex-col">
                <select
                  {...register('game_type')}
                  defaultValue={'connect_four' as AvailableGameType}
                  className={cn({
                    'select w-full max-w-xs mx-auto': true,
                    'select-error': errors.game_type || errors.root,
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
                  {...register('user_name')}
                  type="text"
                  placeholder="User Name"
                  className={cn({
                    'input w-full max-w-xs mx-auto': true,
                    'input-error': errors.user_name || errors.root,
                  })}
                />
                {errors.user_name && (
                  <span className="text-error mt-2 text-sm text-center w-full">{errors.user_name.message}</span>
                )}
              </div>

              <div className="flex flex-col">
                <input
                  {...register('password')}
                  type="text"
                  placeholder="Room Password"
                  className={cn({
                    'input w-full max-w-xs mx-auto': true,
                    'input-error': errors.password || errors.root,
                  })}
                />
                {errors.password && (
                  <span className="text-error mt-2 text-sm text-center w-full">{errors.password.message}</span>
                )}
              </div>
              <button
                disabled={isGameRoomCreationLoading}
                className={cn({
                  'btn mx-auto': true,
                  'btn-disabled': isGameRoomCreationLoading,
                  'btn-primary': !isGameRoomCreationLoading && !hasErrors,
                  'btn-error': !isGameRoomCreationLoading && hasErrors,
                })}
                type="submit"
              >
                Create
              </button>
              {errors.root && (
                <span className="text-error text-sm text-center w-full">{errors.root.message}</span>
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
                disabled={isEndGameRoomLoading}
                className={cn({
                  'btn mx-auto': true,
                  'btn-disabled': isEndGameRoomLoading,
                  'btn-secondary': !isEndGameRoomLoading && !hasErrors,
                  'btn-error': !isEndGameRoomLoading && hasErrors,
                })}
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
