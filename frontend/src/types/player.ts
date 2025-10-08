export interface Player {
  user_name: string
  id: string
  role: 'admin' | 'player'
  status: 'connected' | 'disconnected'
}
