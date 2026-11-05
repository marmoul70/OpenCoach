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
        border-[var(--oc-border)]
        pb-3
        border-[var(--oc-border)]
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
              text-[var(--oc-text)]
              text-[var(--oc-text)]
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
                      'border-[var(--oc-border)] '
                      + 'bg-[var(--oc-surface-muted)] '
                      + 'text-[var(--oc-muted)] '
                      + 'border-[var(--oc-border)] '
                      + 'bg-[var(--oc-surface-muted)] '
                      + 'text-[var(--oc-muted)]'
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
                + 'text-[var(--oc-muted)] '
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
