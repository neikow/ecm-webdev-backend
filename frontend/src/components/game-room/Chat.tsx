import type { Player } from '../../types/player.ts'
import type { ClassValue } from '../../utils/cn.ts'
import { cn } from '../../utils/cn.ts'

interface ChatProps {
  className?: ClassValue
  players?: Player
}

export function Chat(props: ChatProps) {
  return (
    <div
      className={
        cn(
          'card bg-base-200 shadow-md p-4 flex flex-col',
          props.className,
        )
      }
    >
      <h3 className="mb-2 font-bold text-lg">
        Chat
      </h3>
      <div className="flex-1">

      </div>
      <div>
        <input
          type="text"
          placeholder="Type a message..."
          className="input input-bordered w-full"
        />
      </div>
    </div>
  )
}
