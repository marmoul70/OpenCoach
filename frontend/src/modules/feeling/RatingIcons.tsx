import {
  Heart,
  Star,
} from 'lucide-react'


type RatingKind =
  | 'energy'
  | 'comfort'


interface RatingIconsProps {
  kind: RatingKind
  value: number
  interactive?: boolean
  onChange?: (
    value: number,
  ) => void
  size?: 'sm' | 'md'
}


export function RatingIcons({
  kind,
  value,
  interactive = false,
  onChange,
  size = 'sm',
}: RatingIconsProps) {
  const Icon =
    kind === 'energy'
      ? Heart
      : Star

  const colorClass =
    kind === 'energy'
      ? 'text-rose-500 dark:text-rose-400'
      : 'text-emerald-500 dark:text-emerald-400'

  const iconClass =
    size === 'md'
      ? 'h-6 w-6'
      : 'h-4 w-4'

  return (
    <div
      className="flex items-center gap-1"
      role={
        interactive
          ? 'group'
          : undefined
      }
    >
      {[1, 2, 3, 4, 5].map(
        (rating) => {
          const active =
            rating <= value

          const icon = (
            <Icon
              className={`
                ${iconClass}
                ${
                  active
                    ? colorClass
                    : 'text-slate-200 dark:text-slate-700'
                }
              `}
              strokeWidth={1.8}
            />
          )

          if (
            !interactive
            || !onChange
          ) {
            return (
              <span
                key={rating}
                aria-hidden="true"
              >
                {icon}
              </span>
            )
          }

          return (
            <button
              key={rating}
              type="button"
              className="
                flex
                h-9
                flex-1
                items-center
                justify-center
                rounded-lg
                transition-colors
                hover:bg-slate-100 dark:hover:bg-white/[0.04]
              "
              aria-label={`${rating} sur 5`}
              onClick={() => {
                onChange(
                  rating,
                )
              }}
            >
              {icon}
            </button>
          )
        },
      )}
    </div>
  )
}
