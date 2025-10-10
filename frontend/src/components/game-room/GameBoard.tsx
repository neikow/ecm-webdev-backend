import type { API } from '../../types'
import { useMutation } from '@tanstack/react-query'
import { useGameRoom } from '../../providers/GameRoomProvider.tsx'
import { useCurrentPlayer } from '../../stores/useCurrentPlayer.tsx'
import { cn } from '../../utils/classes.ts'

interface GameState {
  can_start_game: boolean
}

function useGameState(): GameState {
  return {
    can_start_game: true,
  }
}

export function GameBoard() {
  const { can_start_game } = useGameState()
  const { client } = useGameRoom()
  const { currentPlayer } = useCurrentPlayer()

  const { mutate: startGame, isPending, error } = useMutation({
    mutationFn: () => client.sendWithResponse({
      type: 'game_start',
    } as API['ClientMessageGameStart']),
    onError: (error) => {
      console.error(error)
    },
    onSuccess: () => {
      console.log('Game started')
    },
  })

  return (
    <div className="w-full h-full card bg-base-200 shadow-md p-4 flex items-center justify-center">
      {
        can_start_game && (
          currentPlayer?.role === 'admin'
            ? isPending
              ? <div className="loading"></div>
              : (
                  <>
                    <button
                      className={cn('btn btn-lg mb-2', {
                        'btn-primary': !error,
                        'btn-error': !!error,
                      })}
                      onClick={() => startGame()}
                    >
                      Start Game
                    </button>
                    {error && (
                      <p className="text-error">
                        <span>
                          Failed to start the game:&nbsp;
                        </span>
                        <span>
                          {(error as Error).message}
                        </span>
                      </p>
                    )}
                  </>
                )
            : <span className="text-sm text-base-content/70">Waiting for the host to start the game...</span>
        )
      }

    </div>
  )
}
