import type {
  ReactNode,
} from 'react'

import {
  ChevronDown,
} from 'lucide-react'


interface SidePanelSectionProps {
  sectionId: string

  eyebrow: string

  title: string

  badge?: string | null

  open: boolean

  onOpenChange: (
    sectionId: string | null,
  ) => void

  children: ReactNode
}


export function SidePanelSection({
  sectionId,
  eyebrow,
  title,
  badge,
  open,
  onOpenChange,
  children,
}: SidePanelSectionProps) {
  return (
    <section
      className="
        border-b
        border-black/[0.06]
        pb-3
        dark:border-white/[0.07]
      "
    >
      <button
        type="button"
        onClick={() => {
          onOpenChange(
            open
              ? null
              : sectionId,
          )
        }}
        aria-expanded={open}
        className="
          flex
          w-full
          items-center
          justify-between
          gap-3
          py-1
          text-left
        "
      >
        <div className="min-w-0">
          <p
            className="
              text-[8.5px]
              font-bold
              uppercase
              tracking-[0.13em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            {eyebrow}
          </p>

          <h3
            className="
              mt-0.5
              truncate
              text-[13px]
              font-semibold
              text-slate-900
              dark:text-slate-100
            "
          >
            {title}
          </h3>
        </div>


        <div
          className="
            flex
            shrink-0
            items-center
            gap-2
          "
        >
          {badge && (
            <span
              className={[
                (
                  'rounded-full border '
                  + 'px-2 py-0.5 '
                  + 'text-[9px] font-semibold'
                ),
                sectionId === 'training'
                  ? (
                      'border-black/[0.07] '
                      + 'bg-slate-50 '
                      + 'text-slate-500 '
                      + 'dark:border-white/[0.08] '
                      + 'dark:bg-white/[0.04] '
                      + 'dark:text-slate-400'
                    )
                  : (
                      'border-emerald-500/20 '
                      + 'bg-emerald-500/[0.06] '
                      + 'text-emerald-600 '
                      + 'dark:border-emerald-400/20 '
                      + 'dark:bg-emerald-400/[0.06] '
                      + 'dark:text-emerald-400'
                    ),
              ].join(' ')}
            >
              {badge}
            </span>
          )}

          <ChevronDown
            className={[
              (
                'h-4 w-4 shrink-0 '
                + 'text-slate-400 '
                + 'transition-transform '
                + 'duration-200'
              ),
              open
                ? 'rotate-180'
                : '',
            ].join(' ')}
          />
        </div>
      </button>


      <div
        className={[
          (
            'grid '
            + 'transition-[grid-template-rows,opacity] '
            + 'duration-200 '
            + 'ease-out'
          ),
          open
            ? (
                'mt-3 '
                + 'grid-rows-[1fr] '
                + 'opacity-100'
              )
            : (
                'grid-rows-[0fr] '
                + 'opacity-0'
              ),
        ].join(' ')}
      >
        <div
          className="
            min-h-0
            overflow-hidden
          "
        >
          {children}
        </div>
      </div>
    </section>
  )
}
