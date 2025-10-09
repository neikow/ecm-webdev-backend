import type { Player } from '../types/player.ts'
import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { usePlayersStore } from './usePlayersStore.tsx'

describe('usePlayersStore', () => {
  beforeEach(() => {
    usePlayersStore.setState({ players: [] })
  })

  it('should initialize with empty players', () => {
    const { result } = renderHook(() => usePlayersStore())
    expect(result.current.players).toStrictEqual([])
  })

  it('should set players', () => {
    const { result } = renderHook(() => usePlayersStore())
    const players: Player[] = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player', status: 'connected' },
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin', status: 'connected' },
    ]

    act(() => {
      result.current.setPlayers(() => players)
    })

    expect(result.current.players).toHaveLength(2)
    expect(result.current.players).toEqual(players)
  })

  it('should replace existing players when setPlayers is called', () => {
    const { result } = renderHook(() => usePlayersStore())
    const initialPlayers: Player[] = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player', status: 'connected' },
    ]
    const newPlayers: Player[] = [
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin', status: 'connected' },
      { id: '3', user_name: 'Charlie', room_id: 1, role: 'player', status: 'connected' },
    ]

    act(() => {
      result.current.setPlayers(initialPlayers)
    })

    expect(result.current.players).toHaveLength(1)
    expect(result.current.players).toEqual(initialPlayers)

    act(() => {
      result.current.setPlayers(newPlayers)
    })

    expect(result.current.players).toHaveLength(2)
    expect(result.current.players).toEqual(newPlayers)
  })

  it('should update players using a function', () => {
    const { result } = renderHook(() => usePlayersStore())
    const initialPlayers: Player[] = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player', status: 'connected' },
    ]
    const additionalPlayer: Player = { id: '2', user_name: 'Bob', room_id: 1, role: 'admin', status: 'connected' }

    act(() => {
      result.current.setPlayers(initialPlayers)
    })

    expect(result.current.players).toHaveLength(1)
    expect(result.current.players).toEqual(initialPlayers)

    act(() => {
      result.current.setPlayers(prev => [...prev, additionalPlayer])
    })

    expect(result.current.players).toHaveLength(2)
    expect(result.current.players).toEqual([
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player', status: 'connected' },
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin', status: 'connected' },
    ] satisfies Player[])
  })
})
