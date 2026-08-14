import { HeartPulse } from 'lucide-react'

import { fitnessData } from './data'

export function FitnessDetails() {
  const data = fitnessData

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-success/10">
          <HeartPulse className="h-8 w-8 text-success" />
        </div>

        <p className="mt-4 text-6xl font-bold text-success">
          {data.score}
        </p>

        <p className="mt-1 text-base text-base-content/60">
          {data.label}
        </p>

        <progress
          className="progress progress-success mt-4 w-full"
          value={data.score}
          max="100"
        />
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

      <div className="alert alert-success">
        <HeartPulse className="h-5 w-5" />

        <div>
          <p className="font-medium">
            État de forme favorable
          </p>

          <p className="mt-1 text-sm">
            Les indicateurs disponibles suggèrent une bonne
            capacité à réaliser une séance d'entraînement.
          </p>
        </div>
      </div>

      <div className="rounded-xl bg-base-200 p-4">
        <p className="font-medium text-base-content">
          Lecture des indicateurs
        </p>

        <div className="mt-3 space-y-3 text-sm">
          <Indicator
            label="Charge"
            value={data.trainingLoad}
            description="Charge d'entraînement récente"
          />

          <Indicator
            label="Récupération"
            value={data.recovery}
            description="Capacité actuelle de récupération"
          />

          <Indicator
            label="Fatigue"
            value={data.fatigue}
            description="Niveau de fatigue estimé"
          />
        </div>
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
    <div className="rounded-xl bg-base-200 p-4 text-center">
      <p className="text-sm text-base-content/50">
        {label}
      </p>

      <p className="mt-1 text-2xl font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}

interface IndicatorProps {
  label: string
  value: number
  description: string
}

function Indicator({
  label,
  value,
  description,
}: IndicatorProps) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="font-medium text-base-content">
          {label}
        </span>

        <span className="font-semibold text-base-content">
          {value}
        </span>
      </div>

      <progress
        className="progress progress-success mt-1 w-full"
        value={value}
        max="100"
      />

      <p className="mt-1 text-xs text-base-content/50">
        {description}
      </p>
    </div>
  )
}