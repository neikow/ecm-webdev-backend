import { useState } from 'react'
import { useNavigate } from 'react-router'
import { cn } from '../utils/cn.ts'

export function LeaveGameRoomButton() {
  const navigate = useNavigate()
  const [isError, setIsError] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  async function handleLeave() {
    setIsLoading(true)
    const response = await fetch(`/api/game_rooms/leave`, {
      method: 'POST',
    })
    setIsError(false)

    if (response.ok) {
      navigate('/')
    }
    else {
      const errorData: {
        detail: {
          code: string
          message: string
        }
      } = await response.json()
      console.error('Failed to leave the game room:', errorData.detail.message)
      setIsError(true)
    }
  }

  return (
    <button
      className={cn(
        ['btn btn-primary', {
          'btn-error': isError,
          'btn-disabled loading': isLoading,
        }],
      )}
      onClick={handleLeave}
    >
      Leave
    </button>
  )
}
