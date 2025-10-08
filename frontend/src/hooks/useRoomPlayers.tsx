import { useEffect } from 'react'
import { useGameRoom } from '../providers/GameRoomProvider.tsx'
import { usePlayersStore } from '../stores/usePlayersStore.tsx'

export function useRoomPlayers() {
  const { client } = useGameRoom()
  const { players, setPlayers } = usePlayersStore()

  useEffect(() => {
    return client.on((message) => {
      if (message.type === 'snapshot') {
        setPlayers(message.data.players)
      }
      else if (message.type === 'event') {
        if (message.event.type === 'player.joined') {
          const player = message.event.data
          setPlayers(players => [...players, player])
        }
        else if (message.event.type === 'player.left') {
          const id = message.event.data.id
          setPlayers(players => players.filter(p => p.id !== id))
        }
      }
    })
  }, [client])

  return players
}
