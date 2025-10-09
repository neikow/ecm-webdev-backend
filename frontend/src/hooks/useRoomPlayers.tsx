import { useEffect, useMemo } from 'react'
import { useGameRoom } from '../providers/GameRoomProvider.tsx'
import { usePlayersStore } from '../stores/usePlayersStore.tsx'

export function useRoomPlayers() {
  const { client } = useGameRoom()
  const { players, setPlayers } = usePlayersStore()

  useEffect(() => {
    return client.on((message) => {
      console.log(message)

      if (message.type === 'snapshot') {
        setPlayers(message.data.players)
      }
      else if (message.type === 'event') {
        if (message.event.type === 'player.joined') {
          const player = message.event.data
          setPlayers(players => [...players, { ...player, status: 'connected' }])
        }
        else if (message.event.type === 'player.left') {
          const id = message.event.data.id
          setPlayers((players) => {
            return players.map((player) => {
              if (player.id === id) {
                return { ...player, status: 'disconnected' }
              }
              return player
            })
          })
        }
      }
    })
  }, [client])

  const activePlayers = useMemo(() => {
    return players.filter(player => player.status === 'connected')
  }, [players])

  return useMemo(() => {
    return {
      activePlayers,
      players,
    }
  }, [activePlayers, players])
}
