import type { API } from '../../types'
import { useMutation } from '@tanstack/react-query'
import { useCurrentGameState } from '../../hooks/useCurrentGameState.tsx'
import { useGameRoom } from '../../providers/GameRoomProvider.tsx'
import { useCurrentPlayer } from '../../stores/useCurrentPlayer.tsx'
import { cn } from '../../utils/classes.ts'
import { Board } from '../games/connect-four/Board.tsx'

export function GameBoard() {
  const { client } = useGameRoom()
  const { currentPlayer } = useCurrentPlayer()

  const { mutate: startGame, isPending: isStartPending, error: startError } = useMutation({
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

  const { mutate: resetGame, isPending: isResetPending, error: resetError } = useMutation({
    mutationFn: () => client.sendWithResponse({
      type: 'game_reset',
    } as API['ClientMessageGameReset']),
    onError: (error) => {
      console.error(error)
    },
    onSuccess: () => {
      console.log('Game reset')
    },
  })

  const { gameState } = useCurrentGameState()

  const isAdmin = currentPlayer?.role === 'admin'
  const hasGameStarted = gameState && gameState?.status !== 'not_started'
  const canStartGame = gameState && gameState?.can_start

  const hasGameEnded = gameState?.status === 'win' || gameState?.status === 'draw'

  return (
    <div className="w-full h-full card bg-base-200 shadow-md p-4 flex items-center justify-center">
      {
        !hasGameStarted && !canStartGame && (
          <div className="text-center text-sm text-base-content/70">
            Waiting for more players to join to start the game...
          </div>
        )
      }

      {
        !hasGameStarted && isAdmin && canStartGame && (
          <>
            <button
              disabled={isStartPending}
              className={cn('btn btn-lg mb-2', {
                'cursor-progress': isStartPending,
                'btn-primary': !startError,
                'btn-error': !!startError,
              })}
              onClick={() => startGame()}
            >
              Start Game
            </button>
            {startError && (
              <p className="text-error">
                <span>
                  Failed to start the game:&nbsp;
                </span>
                <span>
                  {(startError as Error).message}
                </span>
              </p>
            )}
          </>
        )
      }

      {
        !hasGameStarted && !isAdmin && canStartGame && (
          <div className="text-center text-sm text-base-content/70 mb-4">
            Waiting for the host to start the game...
          </div>
        )
      }

      {gameState && gameState?.status !== 'not_started' && <Board grid={gameState.grid} />}

      {
        hasGameEnded && isAdmin && (
          <>
            <button
              disabled={isResetPending}
              className={cn('btn btn-lg mt-8', {
                'cursor-progress': isResetPending,
                'btn-primary': !resetError,
                'btn-error': !!resetError,
              })}
              onClick={() => resetGame()}
            >
              Restart Game
            </button>
            {resetError && (
              <p className="text-error">
                <span>
                  Failed to restart the game:&nbsp;
                </span>
                <span>
                  {(resetError as Error).message}
                </span>
              </p>
            )}
          </>
        )
      }
    </div>
  )
}
