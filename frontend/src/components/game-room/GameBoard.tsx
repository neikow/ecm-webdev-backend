import { useCurrentPlayer } from '../../stores/useCurrentPlayer.tsx'

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
  const { currentPlayer } = useCurrentPlayer()

  return (
    <div className="w-full h-full card bg-base-200 shadow-md p-4 flex items-center justify-center">
      {
        can_start_game && (
          currentPlayer?.role === 'admin'
            ? <button className="btn btn-primary btn-lg">Start Game</button>
            : <span className="text-sm text-base-content/70">Waiting for the host to start the game...</span>
        )
      }
    </div>
  )
}
