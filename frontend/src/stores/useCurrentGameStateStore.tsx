import type { API } from '../types'
import { create } from 'zustand'

export type ConnectFourPlayerState = API['ConnectFourPlayerData']

export interface ConnectFourGameState {
  current_player: 1 | 2
  grid: (0 | 1 | 2)[][]
  status: 'ongoing' | 'not_started' | 'win' | 'draw'
  winning_positions: [number, number][] | null
  can_start: boolean
}

export interface CurrentGameStateStore {
  playerState: ConnectFourPlayerState | null
  gameState: ConnectFourGameState | null
  setPlayerState: (playerState: ConnectFourPlayerState) => void
  setGameState: (gameState: ConnectFourGameState) => void
  reset: () => void
}

export const useCurrentGameStateStore = create<CurrentGameStateStore>(set => ({
  gameState: null,
  playerState: null,
  setGameState: gameState => set({ gameState }),
  setPlayerState: playerState => set({ playerState }),
  reset: () => set({ gameState: null, playerState: null }),
}))
