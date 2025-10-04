import type { GameRoomData } from '../../pages/GameRoomPage.tsx'
import { LeaveButton } from './LeaveButton.tsx'

interface HeaderProps {
  data: GameRoomData | undefined
}

export function Header(props: HeaderProps) {
  return (
    <header className="flex flex-row justify-between">
      <div className="flex flex-row gap-4 items-center justify-start p-4">
        {!props.data
          ? <div className="skeleton h-10 w-96"></div>
          : (
              <h1 className="text-4xl font-bold text-secondary">
                Game Room #
                {props.data.id}
              </h1>
            )}
      </div>
      <div className="p-4 flex flex-row gap-4 items-center">
        {!props.data
          ? <div className="skeleton h-10 w-36"></div>
          : (
              <span className="font-sans select-none">
                Password:
                <span className="select-all font-mono font-bold p-2 border border-white/20 ml-2 rounded">
                  {props.data.password}
                </span>
              </span>
            )}
        <LeaveButton />
      </div>
    </header>
  )
}
