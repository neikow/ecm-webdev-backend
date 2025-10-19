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

  const { gameState } = useCurrentGameState()

  return (
    <div className="w-full h-full card bg-base-200 shadow-md p-4 flex items-center justify-center">
      {
        gameState?.status === 'not_started'
          ? gameState?.can_start
            ? (
                currentPlayer?.role === 'admin'
                  ? isPending
                    ? <div className="loading">Loading</div>
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
            : <div>Waiting for players to join...</div>
          : null
      }

      {gameState?.status === 'win' && (
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">
            Player
            {gameState.current_player}
            Wins!
          </h2>
        </div>
      )}

      {gameState?.status === 'ongoing' && <Board grid={gameState.grid} />}
    </div>
  )
}
