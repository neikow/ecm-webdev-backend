import { createBrowserRouter } from 'react-router'
import { CreateGameRoomPage } from './pages/CreateGameRoomPage.tsx'
import { ErrorPage } from './pages/ErrorPage.tsx'
import { GameRoomPage } from './pages/GameRoomPage.tsx'
import { HomePage } from './pages/HomePage.tsx'

const router = createBrowserRouter([
  {
    path: '/',
    index: true,
    element: <HomePage />,
  },
  {
    path: '/game-rooms/new',
    element: <CreateGameRoomPage />,
  },
  {
    path: '/game-rooms/:id',
    element: <GameRoomPage />,
  },
  {
    path: '*',
    element: <ErrorPage />,
  },
])

export { router }
