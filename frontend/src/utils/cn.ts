import classNames from 'classnames'
import { twMerge } from 'tailwind-merge'

export function cn(...classes: Parameters<typeof classNames>) {
  return twMerge(classNames(classes))
}
