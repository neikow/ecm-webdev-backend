import type { ConnectFourGameState } from '../../../stores/useCurrentGameStateStore.tsx'
import { useMutation } from '@tanstack/react-query'
import { useCallback } from 'react'
import { useCurrentGameState } from '../../../hooks/useCurrentGameState.tsx'
import { useGameRoom } from '../../../providers/GameRoomProvider.tsx'
import { cn } from '../../../utils/classes.ts'
import { Pin } from './Pin.tsx'

interface BoardProps {
  grid: ConnectFourGameState['grid']
}

export function Board(props: BoardProps) {
  const { client } = useGameRoom()
  const { gameState, playerState } = useCurrentGameState()

  const { mutate } = useMutation({
    mutationFn: async (col: number) => {
      if (!gameState || !playerState) {
        throw new Error('Game is not started')
      }

      return await client.sendWithResponse({
        type: 'action',
        data: {
          player: playerState.player,
          column: col,
        },
      })
    },
    onError: (error) => {
      console.error(error)
    },
  })

  const onClick = useCallback((col: number) => {
    mutate(col)
  }, [])

  const colsCount = props.grid[0]!.length
  const rowsCount = props.grid.length

  const isCurrentPlayerTurn = gameState && playerState?.player === gameState.current_player

  return (
    <div>
      <div className="flex flex-row justify-between items-center mb-1">
        {gameState && (
          <span
            className={cn('badge badge-lg mb-2 select-none', {
              'badge-primary': isCurrentPlayerTurn,
              'badge-secondary': !isCurrentPlayerTurn,
            })}
          >
            {isCurrentPlayerTurn ? 'Your turn' : 'Opponent\'s Turn'}
          </span>
        )}

        <div className="flex items-center">
          <span>
            Playing as&nbsp;
            {
              playerState?.player === 1 ? 'Red' : 'Yellow'
            }
          </span>
          <div
            className={cn('w-4 h-4 rounded-full inline-block ml-2', {
              'bg-red-400': playerState?.player === 1,
              'bg-yellow-400': playerState?.player === 2,
            })}
          >

          </div>
        </div>
      </div>

      <div
        className={cn('grid grid-cols-7 gap-2 bg-base-100 p-2 rounded-lg border transition-colors', {
          'border-green-400': isCurrentPlayerTurn && gameState?.status === 'win',
          'border-red-400': !isCurrentPlayerTurn && gameState?.status === 'win',
          'border-yellow-400': gameState?.status === 'draw',
          'border-primary': isCurrentPlayerTurn && gameState?.status === 'ongoing',
        })}
      >
        {Array.from({ length: colsCount }).map((_, colIndex) => (
          <div
            key={colIndex}
            className={cn('flex flex-col gap-2 transition-opacity', {
              'opacity-70': playerState?.player !== gameState?.current_player,
              'cursor-pointer': playerState?.player === gameState?.current_player,
            })}
            onClick={
              playerState?.player !== gameState?.current_player
                ? undefined
                : () => onClick(colIndex)
            }
          >
            {Array.from({ length: rowsCount }).map((_, rowIndex) => {
              const cellValue = props.grid[rowIndex]![colIndex]

              const isWinningPin = gameState?.winning_positions?.some(
                ([winRow, winCol]) => (rowsCount - winRow - 1) === rowIndex && winCol === colIndex,
              ) ?? false

              return (
                <Pin
                  isWinning={isWinningPin}
                  key={`pin-${colIndex}-${rowIndex}`}
                  color={
                    cellValue === 0 ? 'white' : cellValue === 1 ? 'red' : 'yellow'
                  }
                />
              )
            })}
          </div>
        ))}

        {gameState?.status === 'win' && (
          <div
            className={cn('absolute top-1/2 left-1/2 -translate-1/2 text-center px-6 py-3 bg-base-300 border rounded-lg shadow-lg select-none', {
              'border-green-400': isCurrentPlayerTurn,
              'border-red-400': !isCurrentPlayerTurn,
            })}
          >
            <h2 className="text-2xl font-bold">
              {isCurrentPlayerTurn ? 'You won !' : 'You lost !'}
            </h2>
          </div>
        )}
      </div>
    </div>
  )
}
