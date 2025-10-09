import type { Player } from '../../types/player.ts'
import type { ClassValue } from '../../utils/classes.ts'
import { useRoomPlayers } from '../../hooks/useRoomPlayers.tsx'
import { useCurrentPlayer } from '../../stores/useCurrentPlayer.tsx'
import { cn } from '../../utils/classes.ts'

interface PlayerListProps {
  className?: ClassValue
}

function PlayerListItem(props: { player: Player, isCurrent: boolean }) {
  return (
    <li className="px-3 py-2 bg-base-100 rounded flex flex-row items-center gap-2">
      <span
        className={cn('font-black', {
          'text-primary': props.isCurrent,
        })}
      >
        {props.player.user_name}
      </span>
      {
        props.player.role === 'admin'
        && <span role="note" className="badge badge-soft badge-primary badge-sm select-none">Host</span>
      }
    </li>
  )
}

export function PlayerList(props: PlayerListProps) {
  const { activePlayers } = useRoomPlayers()
  const { currentPlayer } = useCurrentPlayer()

  if (!currentPlayer?.id) {
    return (
      <div
        className={cn(
          'skeleton mb-4',
          props.className,
        )}
      >
      </div>
    )
  }

  return (
    <div
      className={cn(
        'card bg-base-200 shadow-md mb-4 p-4',
        props.className,
      )}
    >
      <div className="mb-2 font-bold text-lg flex flex-row items-center justify-between">
        <span>Players</span>
        <div className="badge badge-soft badge-primary select-none">
          {
            activePlayers.length ?? 0
          }
        </div>
      </div>
      <ul className="flex flex-col gap-1 overflow-y-auto">
        {activePlayers.map((player, index) => (
          <PlayerListItem key={`player-${index}`} player={player} isCurrent={currentPlayer.id === player.id} />
        ))}
      </ul>
    </div>
  )
}
