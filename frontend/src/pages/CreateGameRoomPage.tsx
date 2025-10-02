import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { NavLink } from 'react-router'
import { z } from 'zod'
import { cn } from '../utils/cn.ts'
import { GameRoomPasswordSchema } from './HomePage.tsx'

const AvailableGameTypes = ['connect_four'] as const
const AvailableGameTypeDefinitions: {
  [GameType in (typeof AvailableGameTypes)[number]]: {
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
  gameType: z.enum(AvailableGameTypes),
  roomPassword: GameRoomPasswordSchema,
})

export function CreateGameRoomPage() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(CreateGameRoomSchema),
  })

  function onSubmit(data: z.infer<typeof CreateGameRoomSchema>) {
    console.log(data)
  }

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
                  {...register('gameType')}
                  className={cn({
                    'select w-full max-w-xs mx-auto': true,
                    'select-error': errors.gameType,
                  })}
                >
                  {
                    Object.values(AvailableGameTypeDefinitions).map((gameType, index) => (
                      <option key={gameType.value} value={gameType.value} selected={index === 0}>
                        {gameType.label}
                      </option>
                    ))
                  }
                </select>
                {errors.gameType && (
                  <span className="text-error mt-2 text-sm text-center w-full">{errors.gameType.message}</span>
                )}
              </div>

              <div className="flex flex-col">
                <input
                  {...register('roomPassword')}
                  type="text"
                  placeholder="Room Password"
                  className={cn({ 'input w-full max-w-xs mx-auto': true, 'input-error': errors.roomPassword })}
                />
                {errors.roomPassword && (
                  <span className="text-error mt-2 text-sm text-center w-full">{errors.roomPassword.message}</span>
                )}
              </div>
              <button className="btn btn-primary mx-auto" type="submit">
                Create Room
              </button>
              <NavLink to="/" className="btn btn-outline mx-auto" type="submit">
                Back
              </NavLink>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
