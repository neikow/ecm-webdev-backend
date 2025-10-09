import type { Player } from '../types/player.ts'
import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export interface CurrentPlayerState {
  setCurrentPlayer: (player: Player | null) => void
  currentPlayer: Player | null
}

export const useCurrentPlayer = create<CurrentPlayerState>()(
  persist(
    set => ({
      currentPlayer: null,
      setCurrentPlayer: player => set({ currentPlayer: player }),
    }),
    {
      name: 'player-storage',
      storage: createJSONStorage(() => localStorage),
    },
  ),
)
