import type {
  ButtonHTMLAttributes,
} from 'react'

import {
  Slot,
} from '@radix-ui/react-slot'

import {
  cn,
} from '../../lib/cn'


interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  variant?: 'primary' | 'secondary' | 'ghost'
}


export function Button({
  asChild = false,
  variant = 'primary',
  className,
  ...props
}: ButtonProps) {
  const Component =
    asChild
      ? Slot
      : 'button'

  return (
    <Component
      className={cn(
        [
          'inline-flex min-h-11 items-center justify-center',
          'gap-2 rounded-[var(--oc-radius-control)] px-4',
          'text-sm font-semibold',
          'transition-colors duration-200',
          'focus-visible:outline-none',
          'focus-visible:ring-2',
          'focus-visible:ring-emerald-500/40',
          'disabled:pointer-events-none',
          'disabled:opacity-50',
        ],
        variant === 'primary' && [
          'bg-[var(--oc-accent)] text-white',
          'hover:bg-[var(--oc-accent-hover)]',
        ],
        variant === 'secondary' && [
          'border border-[var(--oc-border)]',
          'bg-[var(--oc-surface)] text-[var(--oc-text)]',
          'hover:bg-[var(--oc-surface-hover)]',
        ],
        variant === 'ghost' && [
          'bg-transparent',
          'text-[var(--oc-text-secondary)]',
          'hover:bg-[var(--oc-surface-muted)]',
        ],
        className,
      )}
      {...props}
    />
  )
}
