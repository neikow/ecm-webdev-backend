import { useEffect } from 'react'
import { fetchClient } from '../utils/fetch.ts'

const REFRESH_INTERVAL_MS = 5 * 60 * 1000 // 5 minutes

export function usePeriodicTokensRefresh() {
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchClient.POST('/game_auth/refresh', {
        method: 'POST',
        credentials: 'include',
      }).catch((error) => {
        console.error('Failed to refresh tokens:', error)
      })
    }, REFRESH_INTERVAL_MS)

    return () => clearInterval(intervalId)
  }, [])
}
