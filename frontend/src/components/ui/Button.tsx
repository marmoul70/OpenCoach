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
          'inline-flex h-10 items-center justify-center',
          'gap-2 rounded-xl px-4',
          'text-sm font-semibold',
          'transition-colors',
          'focus-visible:outline-none',
          'focus-visible:ring-2',
          'focus-visible:ring-emerald-500/40',
          'disabled:pointer-events-none',
          'disabled:opacity-50',
        ],
        variant === 'primary' && [
          'bg-emerald-600 text-white',
          'hover:bg-emerald-700',
          'dark:bg-emerald-500',
          'dark:hover:bg-emerald-400',
        ],
        variant === 'secondary' && [
          'border border-black/[0.08]',
          'bg-white text-slate-900',
          'hover:bg-slate-50',
          'dark:border-white/[0.1]',
          'dark:bg-[#181d22]',
          'dark:text-slate-100',
          'dark:hover:bg-[#20262c]',
        ],
        variant === 'ghost' && [
          'bg-transparent',
          'text-slate-600',
          'hover:bg-slate-100',
          'dark:text-slate-300',
          'dark:hover:bg-white/[0.06]',
        ],
        className,
      )}
      {...props}
    />
  )
}
