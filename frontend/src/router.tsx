import { createBrowserRouter } from 'react-router'
import { CreateGameRoomPage } from './pages/CreateGameRoomPage.tsx'
import { ErrorPage } from './pages/ErrorPage.tsx'
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
    path: '*',
    element: <ErrorPage />,
  },
])

export { router }
