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
    const players = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' as const },
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin' as const },
    ]

    act(() => {
      result.current.setPlayers(() => players)
    })

    expect(result.current.players).toHaveLength(2)
    expect(result.current.players).toEqual(players)
  })

  it('should replace existing players when setPlayers is called', () => {
    const { result } = renderHook(() => usePlayersStore())
    const initialPlayers = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' as const },
    ]
    const newPlayers = [
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin' as const },
      { id: '3', user_name: 'Charlie', room_id: 1, role: 'player' as const },
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
    const initialPlayers = [
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' as const },
    ]
    const additionalPlayer = { id: '2', user_name: 'Bob', room_id: 1, role: 'admin' as const }

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
      { id: '1', user_name: 'Alice', room_id: 1, role: 'player' },
      { id: '2', user_name: 'Bob', room_id: 1, role: 'admin' },
    ])
  })
})
