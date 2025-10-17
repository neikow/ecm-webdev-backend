import { create } from 'zustand'

export interface ConnectFourGameState {
  current_player: 1 | 2
  grid: (0 | 1 | 2)[][]
  state: 'ongoing'
  winning_positions: [number, number][] | null
}

export interface CurrentGameStateStore {
  gameState: ConnectFourGameState | null
  setGameState: (gameState: ConnectFourGameState) => void
  resetGameState: () => void
}

export const useCurrentGameStateStore = create<CurrentGameStateStore>(set => ({
  gameState: null,
  setGameState: gameState => set({ gameState }),
  resetGameState: () => set({ gameState: null }),
}))
