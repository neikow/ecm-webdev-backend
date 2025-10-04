import type { ClassValue } from '../../utils/cn.ts'
import { cn } from '../../utils/cn.ts'

interface PlayerListProps {
  className?: ClassValue
}

export function PlayerList(props: PlayerListProps) {
  return (
    <div
      className={cn(
        'card bg-base-100 shadow-md mb-4 p-4',
        props.className,
      )}
    >
      <h3 className="mb-2 font-bold text-lg">
        Players
      </h3>
    </div>
  )
}
