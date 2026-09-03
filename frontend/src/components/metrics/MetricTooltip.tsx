import {
  Info,
} from 'lucide-react'

import {
  useToast,
} from '../ui/ToastProvider'


import {
  METRIC_DEFINITIONS,
  type MetricKey,
} from './metricDefinitions'


export function MetricTooltip({
  metric,
  label,
}: {
  metric: MetricKey
  label?: string
}) {
  const {
    toast,
  } = useToast()

  const definition =
    METRIC_DEFINITIONS[metric]

  return (
    <span className="inline-flex items-center gap-1">

      {label && (
        <span>
          {label}
        </span>
      )}

      <button
        type="button"
        className="
          inline-flex
          h-4
          w-4
          shrink-0
          items-center
          justify-center
          rounded-full
          text-slate-400
          transition-colors
          hover:text-emerald-600
          focus:text-emerald-600
          focus:outline-none
          dark:text-slate-500
          dark:hover:text-emerald-400
          dark:focus:text-emerald-400
        "
        onClick={(
          event,
        ) => {
          event.preventDefault()
          event.stopPropagation()

          toast({
            type: 'info',
            title: definition.title,
            message: definition.description,
            duration: 8000,
          })
        }}
        aria-label={`Expliquer ${label ?? metric}`}
      >
        <Info
          className="h-3.5 w-3.5"
          aria-hidden="true"
        />
      </button>

    </span>
  )
}
