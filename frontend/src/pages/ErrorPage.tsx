import { NavLink } from 'react-router'

export function ErrorPage(props: {
  title?: string
  message?: string
  actionText?: string
  actionTo?: string
}) {
  const defaultTitle = '404 - Page Not Found'
  const defaultMessage = 'The page you are looking for does not exist.'
  const defaultActionText = 'Go Home'
  const defaultActionTo = '/'

  return (
    <div className="hero bg-base-200 min-h-screen">
      <div className="hero-content text-center">
        <div className="max-w-md">
          <h1 className="text-5xl font-bold">
            {props.title ?? defaultTitle}
          </h1>
          <p className="py-6 text-balance">
            {props.message ?? defaultMessage}
          </p>
          <NavLink
            to={props.actionTo ?? defaultActionTo}
            className="btn btn-primary"
          >
            {props.actionText ?? defaultActionText}
          </NavLink>
        </div>
      </div>
    </div>
  )
}
