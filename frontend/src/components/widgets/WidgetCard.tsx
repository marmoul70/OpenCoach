import {
  ArrowRight,
  CircleAlert,
  CircleCheck,
  Info,
  TriangleAlert,
} from 'lucide-react'

import type {
  WidgetDefinition,
} from '../../core/widgets'


type WidgetStatus =
  NonNullable<
    WidgetDefinition['status']
  >

type WidgetAccent =
  NonNullable<
    WidgetDefinition['accent']
  >


interface WidgetCardProps {
  widget: WidgetDefinition
  onClick?: () => void
}


const accentClasses:
  Record<
    WidgetAccent,
    {
      foreground: string
      background: string
    }
  > = {
    neutral: {
      foreground:
        'text-slate-500',
      background:
        (
          'bg-slate-100 '
          + 'dark:bg-white/[0.06]'
        ),
    },

    primary: {
      foreground:
        (
          'text-emerald-600 '
          + 'dark:text-emerald-400'
        ),
      background:
        (
          'bg-emerald-50 '
          + 'dark:bg-emerald-500/10'
        ),
    },

    secondary: {
      foreground:
        (
          'text-violet-600 '
          + 'dark:text-violet-400'
        ),
      background:
        (
          'bg-violet-50 '
          + 'dark:bg-violet-500/10'
        ),
    },

    accent: {
      foreground:
        (
          'text-cyan-600 '
          + 'dark:text-cyan-400'
        ),
      background:
        (
          'bg-cyan-50 '
          + 'dark:bg-cyan-500/10'
        ),
    },

    info: {
      foreground:
        (
          'text-sky-600 '
          + 'dark:text-sky-400'
        ),
      background:
        (
          'bg-sky-50 '
          + 'dark:bg-sky-500/10'
        ),
    },

    success: {
      foreground:
        (
          'text-emerald-600 '
          + 'dark:text-emerald-400'
        ),
      background:
        (
          'bg-emerald-50 '
          + 'dark:bg-emerald-500/10'
        ),
    },

    warning: {
      foreground:
        (
          'text-amber-600 '
          + 'dark:text-amber-400'
        ),
      background:
        (
          'bg-amber-50 '
          + 'dark:bg-amber-500/10'
        ),
    },

    error: {
      foreground:
        (
          'text-red-600 '
          + 'dark:text-red-400'
        ),
      background:
        (
          'bg-red-50 '
          + 'dark:bg-red-500/10'
        ),
    },
  }


export function WidgetCard({
  widget,
  onClick,
}: WidgetCardProps) {
  const status =
    widget.status
    ?? 'neutral'

  const accent =
    widget.accent
    ?? 'neutral'

  const Icon =
    widget.icon

  const colors =
    accentClasses[
      accent
    ]


  return (
    <button
      type="button"
      onClick={onClick}
      className="
        group
        flex
        min-h-44
        w-full
        flex-col
        rounded-2xl
        border
        border-black/[0.07]
        bg-white
        p-5
        text-left
        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
        transition
        duration-200
        hover:-translate-y-0.5
        hover:shadow-[0_12px_35px_rgba(15,23,42,0.055)]
        focus-visible:outline-none
        focus-visible:ring-2
        focus-visible:ring-emerald-500/40
        dark:border-white/[0.08]
        dark:bg-[#14181d]
      "
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-4
        "
      >
        {Icon ? (
          <div
            className={[
              (
                'flex h-10 w-10 '
                + 'shrink-0 '
                + 'items-center '
                + 'justify-center '
                + 'rounded-xl'
              ),
              colors.background,
              colors.foreground,
            ].join(' ')}
          >
            <Icon
              className="h-5 w-5"
            />
          </div>
        ) : (
          <div />
        )}

        <Status
          status={status}
        />
      </div>


      <div
        className="
          mt-4
          flex-1
        "
      >
        <h3
          className="
            text-base
            font-bold
            tracking-[-0.02em]
            text-slate-950
            dark:text-white
          "
        >
          {widget.title}
        </h3>

        {widget.description && (
          <p
            className="
              mt-1.5
              text-sm
              leading-6
              text-slate-500
              dark:text-slate-400
            "
          >
            {widget.description}
          </p>
        )}
      </div>


      <div
        className="
          mt-5
          flex
          items-center
          justify-between
          border-t
          border-black/[0.06]
          pt-4
          dark:border-white/[0.07]
        "
      >
        <span
          className="
            text-[11px]
            font-medium
            text-slate-400
          "
        >
          Détails
        </span>

        <ArrowRight
          className={[
            (
              'h-4 w-4 '
              + 'transition-transform '
              + 'group-hover:translate-x-1'
            ),
            colors.foreground,
          ].join(' ')}
        />
      </div>
    </button>
  )
}


function Status({
  status,
}: {
  status: WidgetStatus
}) {
  if (
    status === 'success'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-emerald-50
          px-2
          py-1
          text-[10px]
          font-semibold
          text-emerald-600
          dark:bg-emerald-500/10
          dark:text-emerald-400
        "
      >
        <CircleCheck
          className="h-3 w-3"
        />
        OK
      </span>
    )
  }

  if (
    status === 'warning'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-amber-50
          px-2
          py-1
          text-[10px]
          font-semibold
          text-amber-600
          dark:bg-amber-500/10
          dark:text-amber-400
        "
      >
        <TriangleAlert
          className="h-3 w-3"
        />
        Vigilance
      </span>
    )
  }

  if (
    status === 'danger'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-red-50
          px-2
          py-1
          text-[10px]
          font-semibold
          text-red-600
          dark:bg-red-500/10
          dark:text-red-400
        "
      >
        <CircleAlert
          className="h-3 w-3"
        />
        Alerte
      </span>
    )
  }

  return (
    <span
      className="
        inline-flex
        items-center
        gap-1
        rounded-full
        bg-slate-50
        px-2
        py-1
        text-[10px]
        font-semibold
        text-slate-400
        dark:bg-white/[0.05]
      "
    >
      <Info
        className="h-3 w-3"
      />
      Info
    </span>
  )
}
