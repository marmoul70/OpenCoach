import { fitnessData } from './data'

export function FitnessDetails() {
  const data = fitnessData

  return (
    <div className="space-y-5">
      <div className="text-center">
        <p className="text-5xl font-bold text-slate-900">
          {data.score}
        </p>

        <p className="mt-1 text-slate-500">
          {data.label}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Metric
          label="Charge"
          value={data.trainingLoad}
        />

        <Metric
          label="Récupération"
          value={data.recovery}
        />

        <Metric
          label="Fatigue"
          value={data.fatigue}
        />
      </div>

      <div className="rounded-xl bg-slate-50 p-4">
        <p className="font-medium text-slate-900">
          Interprétation
        </p>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          Votre état de forme est actuellement favorable.
          Les indicateurs disponibles suggèrent une bonne
          capacité à réaliser une séance d'entraînement.
        </p>
      </div>
    </div>
  )
}

interface MetricProps {
  label: string
  value: number
}

function Metric({
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-slate-50 p-4 text-center">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-2xl font-semibold text-slate-900">
        {value}
      </p>
    </div>
  )
}