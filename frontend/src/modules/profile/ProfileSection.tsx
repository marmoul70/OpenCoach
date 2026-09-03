import {
  ChevronDown,
} from 'lucide-react'

import {
  useState,
  type ReactNode,
} from 'react'


interface ProfileSectionProps {
  title: string
  description?: string
  children: ReactNode
  defaultOpen?: boolean
  trailing?: ReactNode
  icon?: ReactNode
  iconClassName?: string
}


export function ProfileSection({
  title,
  description,
  children,
  defaultOpen = false,
  trailing,
  icon,
  iconClassName,
}: ProfileSectionProps) {
  const [
    open,
    setOpen,
  ] = useState(
    defaultOpen,
  )


  return (
    <section
      className="
        overflow-hidden
        rounded-[14px]
        border
        border-black/[0.06]
        bg-white
        shadow-[0_1px_2px_rgba(15,23,42,0.02)]
        dark:border-white/[0.07]
        dark:bg-[#171d21]
        dark:shadow-none
      "
    >
      <button
        type="button"
        onClick={() =>
          setOpen(
            (current) =>
              !current,
          )
        }
        className="
          flex
          w-full
          items-center
          justify-between
          gap-4
          px-5
          py-4
          text-left
          transition
          hover:bg-slate-50/60
          dark:hover:bg-white/[0.02]
        "
        aria-expanded={open}
      >
        <div
          className="
            flex
            min-w-0
            flex-1
            items-center
            gap-3
          "
        >
          {icon && (
            <div
              className={[
                (
                  'flex h-10 w-10 shrink-0 '
                  + 'items-center justify-center '
                  + 'rounded-[10px]'
                ),
                (
                  iconClassName
                  ?? (
                    'bg-emerald-500/[0.08] '
                    + 'text-emerald-600 '
                    + 'dark:bg-emerald-400/[0.08] '
                    + 'dark:text-emerald-300'
                  )
                ),
              ].join(' ')}
            >
              {icon}
            </div>
          )}

          <div
            className="
              min-w-0
              flex-1
            "
          >
            <h2
              className="
                text-[14px]
                font-semibold
                tracking-[-0.01em]
                text-slate-800
                dark:text-slate-100
              "
            >
              {title}
            </h2>

            {description && (
              <p
                className="
                  mt-1
                  text-[10.5px]
                  leading-relaxed
                  text-slate-500
                  dark:text-slate-400
                "
              >
                {description}
              </p>
            )}
          </div>
        </div>

        <div
          className="
            flex
            shrink-0
            items-center
            gap-2
          "
        >
          {trailing && (
            <div>
              {trailing}
            </div>
          )}

          <ChevronDown
            className={[
              (
                'h-4 w-4 '
                + 'text-slate-400 '
                + 'transition-transform '
                + 'duration-200 '
                + 'dark:text-slate-500'
              ),
              open
                ? 'rotate-180'
                : '',
            ].join(' ')}
            strokeWidth={1.8}
          />
        </div>
      </button>

      {open && (
        <div
          className="
            border-t
            border-black/[0.06]
            px-5
            pb-5
            pt-4
            dark:border-white/[0.07]
          "
        >
          {children}
        </div>
      )}
    </section>
  )
}
