import type { paths } from '../types/api'
import createFetchClient from 'openapi-fetch'
import createClient from 'openapi-react-query'

export const fetchClient = createFetchClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'https://localhost:8000',
  credentials: 'include',
})

export const apiClient = createClient(fetchClient)
