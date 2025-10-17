import { useEffect } from 'react'
import { useGameRoom } from '../providers/GameRoomProvider.tsx'
import { useCurrentGameStateStore } from '../stores/useCurrentGameStateStore.tsx'

export function useCurrentGameState() {
  const { client } = useGameRoom()
  const { gameState, setGameState, resetGameState } = useCurrentGameStateStore()

  useEffect(() => {
    return client.on((msg) => {
      if (msg.type === 'snapshot') {
        setGameState(msg.data.game_state as any)
      }
      else if (msg.type === 'event' && msg.event.type === 'game.state.update') {
        setGameState(msg.event.data as any)
      }
      else if (msg.type === 'event' && msg.event.type === 'room.closed') {
        resetGameState()
      }
    })
  }, [])

  return gameState
}
