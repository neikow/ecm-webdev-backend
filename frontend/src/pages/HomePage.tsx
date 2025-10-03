import type { RefObject } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { NavLink, useNavigate } from 'react-router'
import { z } from 'zod'
import { cn } from '../utils/cn.ts'

export const GameRoomPasswordSchema = z.string().min(5, 'Room password muse be at least 5 characters long').max(32, 'Room password is too long')

const JoinGameFormSchema = z.object({
  password: GameRoomPasswordSchema,
})

function JoinGameModal(props: {
  modalRef: RefObject<HTMLDialogElement | null>
}) {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(JoinGameFormSchema),
  })

  async function onSubmit(data: z.infer<typeof JoinGameFormSchema>) {
    setIsLoading(true)
    const response = await fetch(`/api/game_rooms/find-by-password?password=${data.password}`)
    setIsLoading(false)
    if (response.ok) {
      const room = await response.json()
      navigate(`/game-rooms/${room.id}?password=${data.password}`)
    }
    else if (response.status === 404) {
      setError('password', { message: 'Room not found' })
    }
    else {
      setError('password', { message: 'Something went wrong' })
    }
  }

  return (
    <dialog ref={props.modalRef} className="modal">
      <div className="modal-box flex flex-col items-center">
        <h3 className="font-bold text-2xl">Join a room</h3>
        <div className="py-4 flex flex-col gap-4 items-center">
          <p className="text-center text-balance">
            Enter the room password, your friend should have given it to you.
          </p>
          <form onSubmit={handleSubmit(onSubmit)} className="w-xs">
            <input
              {...register('password')}
              type="text"
              placeholder="Room Password"
              className={cn({ 'input w-full': true, 'input-error': errors.password })}
            />
            {errors.password && (
              <p className="text-error mt-2 text-sm text-center w-full">
                {errors.password.message}
              </p>
            )}

            <button disabled={isLoading} type="submit" className="btn btn-primary mt-4 w-full">Join Room</button>
          </form>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  )
}

export function HomePage() {
  const modalRef = useRef<HTMLDialogElement>(null)

  function openModal() {
    modalRef.current?.showModal()
  }

  return (
    <div className="hero bg-base-200 min-h-screen">
      <div className="hero-content text-center">
        <div className="max-w-md">
          <div className="flex flex-row justify-center mb-8">
            <svg className="w-1/3 rotate-45 fill-primary" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path
                d="M19 5V19H5V5H19M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3M7.5 6C6.7 6 6 6.7 6 7.5S6.7 9 7.5 9 9 8.3 9 7.5 8.3 6 7.5 6M16.5 15C15.7 15 15 15.7 15 16.5C15 17.3 15.7 18 16.5 18C17.3 18 18 17.3 18 16.5C18 15.7 17.3 15 16.5 15M16.5 6C15.7 6 15 6.7 15 7.5S15.7 9 16.5 9C17.3 9 18 8.3 18 7.5S17.3 6 16.5 6M12 10.5C11.2 10.5 10.5 11.2 10.5 12S11.2 13.5 12 13.5 13.5 12.8 13.5 12 12.8 10.5 12 10.5M7.5 15C6.7 15 6 15.7 6 16.5C6 17.3 6.7 18 7.5 18S9 17.3 9 16.5C9 15.7 8.3 15 7.5 15Z"
              />
            </svg>
          </div>

          <h1 className="text-5xl font-bold">Open Game Engine</h1>
          <p className="py-6 text-balance">
            A collection of games using my Open Game Engine for the web.
          </p>
          <div className="flex flex-row gap-4 justify-center items-center">
            <NavLink to="/game-rooms/new" className="btn btn-primary">Create a room</NavLink>
            <button
              onClick={openModal}
              className="btn btn-secondary"
            >
              Join an existing room
            </button>
          </div>
        </div>
      </div>

      <JoinGameModal modalRef={modalRef} />
    </div>
  )
}
