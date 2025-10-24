import type { Player } from '../types/player.ts'
import { useEffect, useMemo } from 'react'
import { useGameRoom } from '../providers/GameRoomProvider.tsx'
import { usePlayersStore } from '../stores/usePlayersStore.tsx'

export function useRoomPlayers() {
  const { client, roomId } = useGameRoom()
  const { players, setPlayers } = usePlayersStore()

  useEffect(() => {
    return client.on((message) => {
      if (message.type === 'snapshot') {
        if (message.data.players)
          setPlayers(message.data.players.map(player => ({ ...player, room_id: roomId })))
      }
      else if (message.type === 'event') {
        if (message.event.type === 'player.joined') {
          const player = message.event.data as Player
          setPlayers(players => [...players, { ...player, status: 'connected' }])
        }
        else if (message.event.type === 'player.left') {
          if (!message.event.data) {
            console.error('player.left event missing data')
            return
          }
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
