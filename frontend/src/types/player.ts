export interface Player {
  user_name: string
  id: string
  role: 'admin' | 'player'
  /*
   The status of the player in the room
    - 'connected': The player is currently connected to the room.
    - 'offline': The player has left the room but may return.
    - 'disconnected': The player has left the room and is not expected to return.
   */
  status: 'connected' | 'disconnected' | 'offline'
}
