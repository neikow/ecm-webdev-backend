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

  return (
    <div>
      {gameState && (gameState.current_player === 1
        ? (
            <span
              className="badge badge-primary mb-2"
            >
              {playerState?.player === gameState.current_player ? 'Your turn' : 'Red\'s Turn'}
            </span>
          )
        : (
            <span className="badge badge-secondary mb-2">
              {playerState?.player === gameState.current_player ? 'Your turn' : 'Yellow\'s Turn'}
            </span>
          )
      )}

      <div className="grid grid-cols-7 gap-2 bg-base-100 p-2 rounded-lg border">
        {Array.from({ length: colsCount }).map((_, colIndex) => (
          <div
            key={colIndex}
            className={cn('flex flex-col gap-2', {
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
      </div>
    </div>
  )
}
