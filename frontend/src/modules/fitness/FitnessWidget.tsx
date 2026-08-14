import { Activity, HeartPulse, TrendingUp } from 'lucide-react'

import { fitnessData } from './data'

interface FitnessWidgetProps {
  onClick: () => void
}

export function FitnessWidget({
  onClick,
}: FitnessWidgetProps) {
  const data = fitnessData

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="card-body p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-success/10">
              <HeartPulse className="h-5 w-5 text-success" />
            </div>

            <div className="min-w-0">
              <p className="text-sm font-medium text-base-content/60">
                État de forme
              </p>

              <p className="mt-1 text-3xl font-bold text-base-content">
                {data.score}
                <span className="ml-1 text-base font-normal text-base-content/40">
                  / 100
                </span>
              </p>
            </div>
          </div>

          <span className="badge badge-success badge-outline shrink-0">
            {data.label}
          </span>
        </div>

        <div className="mt-5">
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="text-base-content/50">
              Score de forme
            </span>

            <span className="font-medium text-success">
              {data.score} %
            </span>
          </div>

          <progress
            className="progress progress-success w-full"
            value={data.score}
            max="100"
          />
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <Metric
            icon={<Activity className="h-4 w-4" />}
            label="Charge"
            value={data.trainingLoad}
          />

          <Metric
            icon={<TrendingUp className="h-4 w-4" />}
            label="Récup."
            value={data.recovery}
          />

          <Metric
            icon={<HeartPulse className="h-4 w-4" />}
            label="Fatigue"
            value={data.fatigue}
          />
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-base-content/50">
            Analyse de votre état de forme
          </span>

          <span className="text-sm font-medium text-success">
            Voir →
          </span>
        </div>
      </div>
    </button>
  )
}

interface MetricProps {
  icon: React.ReactNode
  label: string
  value: number
}

function Metric({
  icon,
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-base-200 p-3">
      <div className="flex items-center gap-1.5 text-base-content/50">
        {icon}

        <span className="text-xs">
          {label}
        </span>
      </div>

      <p className="mt-1 text-lg font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}