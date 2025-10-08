import classNames from 'classnames'
import { twMerge } from 'tailwind-merge'

export type ClassValue = Parameters<typeof classNames>[number]

export function cn(...classes: ClassValue[]) {
  return twMerge(classNames(classes))
}
