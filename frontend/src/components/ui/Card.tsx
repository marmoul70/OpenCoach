import type {
  HTMLAttributes,
} from 'react'

import {
  cn,
} from '../../lib/cn'


export function Card({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        [
          'rounded-2xl',
          'border border-black/[0.07]',
          'bg-white',
          'shadow-[0_1px_2px_rgba(15,23,42,0.03)]',
          'dark:border-white/[0.08]',
          'dark:bg-[#14181d]',
        ],
        className,
      )}
      {...props}
    />
  )
}


export function CardHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'p-5 pb-0',
        className,
      )}
      {...props}
    />
  )
}


export function CardContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'p-5',
        className,
      )}
      {...props}
    />
  )
}
