import type { Player } from '../../types/player.ts'
import type { ClassValue } from '../../utils/cn.ts'
import { cn } from '../../utils/cn.ts'

interface PlayerListProps {
  className?: ClassValue
  players?: Player[]
}

function PlayerListItem(props: { player: Player }) {
  return (
    <li className="px-3 py-2 bg-base-100 rounded flex flex-row items-center gap-2">
      <span className="font-black">
        {props.player.user_name}
      </span>
      {
        props.player.role === 'admin'
        && <div className="badge badge-soft badge-primary badge-sm select-none">Host</div>
      }
    </li>
  )
}

export function PlayerList(props: PlayerListProps) {
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
            props.players?.length ?? 0
          }
        </div>
      </div>
      <ul className="flex flex-col gap-1 overflow-y-auto">
        {props.players?.map((player, index) => (
          <PlayerListItem key={`player-${index}`} player={player} />
        ))}
      </ul>
    </div>
  )
}
