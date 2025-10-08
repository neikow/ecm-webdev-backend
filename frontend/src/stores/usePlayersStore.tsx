import type { Player } from '../types/player.ts'
import { create } from 'zustand/react'

interface PlayersState {
  players: Player[]
  setPlayers: (setterOrValue: Player[] | ((prev: Player[]) => Player[])) => void
}

export const usePlayersStore = create<PlayersState>(set => ({
  players: [],
  setPlayers: setterOrValue => set(prev => ({ players: Array.isArray(setterOrValue) ? setterOrValue : setterOrValue(prev.players) })),
}))
