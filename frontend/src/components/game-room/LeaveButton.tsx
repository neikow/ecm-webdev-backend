import type { NavigateFunction } from 'react-router'
import { useCurrentPlayer } from '../../stores/useCurrentPlayer.tsx'
import { cn } from '../../utils/classes.ts'
import { apiClient } from '../../utils/fetch.ts'

interface LeaveButtonProps {
  navigate: NavigateFunction
}

export function LeaveButton(
  props: LeaveButtonProps,
) {
  const { setCurrentPlayer } = useCurrentPlayer()
  const { isError, isPending, mutate: leaveGame } = apiClient.useMutation('post', '/game_rooms/leave', {
    onSuccess: () => {
      setCurrentPlayer(null)
      props.navigate('/')
    },
    onError: (error) => {
      console.error(error)
    },
  })

  return (
    <button
      className={cn(
        ['btn btn-primary', {
          'btn-error': isError,
          'btn-disabled loading': isPending,
        }],
      )}
      onClick={() => leaveGame({})}
    >
      Leave
    </button>
  )
}
