import type { NavigateFunction } from 'react-router'
import type { API } from '../../types'
import { LeaveButton } from './LeaveButton.tsx'

export interface HeaderProps {
  data?: API['GetGameRoomResponse']
  navigate: NavigateFunction
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
                {props.data.game_room.id}
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
                  {props.data.game_room.password}
                </span>
              </span>
            )}
        <LeaveButton navigate={props.navigate} />
      </div>
    </header>
  )
}
