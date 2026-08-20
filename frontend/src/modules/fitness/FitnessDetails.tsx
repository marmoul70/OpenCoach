import {
  Activity,
  BatteryCharging,
  Dumbbell,
  HeartPulse,
} from 'lucide-react'

import {
  fitnessData,
} from './data'


export function FitnessDetails() {
  const data =
    fitnessData

  return (
    <div className="space-y-5">
      <FitnessHeader
        score={data.score}
        label={data.label}
      />

      <FitnessOverview
        trainingLoad={
          data.trainingLoad
        }
        recovery={
          data.recovery
        }
        fatigue={
          data.fatigue
        }
      />

      <FitnessReading
        score={data.score}
        trainingLoad={
          data.trainingLoad
        }
        recovery={
          data.recovery
        }
        fatigue={
          data.fatigue
        }
      />
    </div>
  )
}


interface FitnessHeaderProps {
  score: number
  label: string
}


function FitnessHeader({
  score,
  label,
}: FitnessHeaderProps) {
  return (
    <div
      className="
        flex flex-col
        gap-4
        sm:flex-row
        sm:items-center
        sm:justify-between
      "
    >
      <div
        className="
          flex items-center
          gap-3
        "
      >
        <div
          className="
            flex size-10
            shrink-0
            items-center
            justify-center
            rounded-xl
            bg-success/10
            text-success
          "
        >
          <HeartPulse
            size={20}
          />
        </div>

        <div>
          <p
            className="
              text-sm
              text-base-content/50
            "
          >
            État de forme
          </p>

          <p
            className="
              text-lg
              font-semibold
              text-base-content
            "
          >
            {label}
          </p>
        </div>
      </div>


      <div
        className="
          flex items-baseline
          gap-1
        "
      >
        <span
          className="
            text-3xl
            font-bold
            text-success
          "
        >
          {score}
        </span>

        <span
          className="
            text-sm
            text-base-content/40
          "
        >
          /100
        </span>
      </div>
    </div>
  )
}


interface FitnessOverviewProps {
  trainingLoad: number
  recovery: number
  fatigue: number
}


function FitnessOverview({
  trainingLoad,
  recovery,
  fatigue,
}: FitnessOverviewProps) {
  return (
    <section
      className="
        overflow-hidden
        rounded-xl
        border border-base-300
      "
    >
      <div
        className="
          grid
          divide-y divide-base-300
          sm:grid-cols-3
          sm:divide-x
          sm:divide-y-0
        "
      >
        <OverviewItem
          icon={Dumbbell}
          label="Charge"
          value={trainingLoad}
          description="Charge récente"
        />

        <OverviewItem
          icon={BatteryCharging}
          label="Récupération"
          value={recovery}
          description="Capacité actuelle"
        />

        <OverviewItem
          icon={Activity}
          label="Fatigue"
          value={fatigue}
          description="Fatigue estimée"
        />
      </div>
    </section>
  )
}


interface OverviewItemProps {
  icon:
    typeof Activity

  label: string
  value: number
  description: string
}


function OverviewItem({
  icon: Icon,
  label,
  value,
  description,
}: OverviewItemProps) {
  return (
    <div
      className="
        flex items-center
        gap-3
        px-4 py-3
      "
    >
      <Icon
        size={17}
        className="
          shrink-0
          text-base-content/40
        "
      />

      <div className="min-w-0">
        <div
          className="
            flex items-baseline
            gap-2
          "
        >
          <span
            className="
              text-lg
              font-bold
              text-base-content
            "
          >
            {value}
          </span>

          <span
            className="
              text-xs
              font-medium
              text-base-content/55
            "
          >
            {label}
          </span>
        </div>

        <p
          className="
            text-xs
            text-base-content/40
          "
        >
          {description}
        </p>
      </div>
    </div>
  )
}


interface FitnessReadingProps {
  score: number
  trainingLoad: number
  recovery: number
  fatigue: number
}


function FitnessReading({
  score,
  trainingLoad,
  recovery,
  fatigue,
}: FitnessReadingProps) {
  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <div
        className="
          flex items-start
          gap-3
        "
      >
        <HeartPulse
          size={18}
          className="
            mt-0.5
            shrink-0
            text-success
          "
        />

        <div>
          <h3
            className="
              font-semibold
              text-base-content
            "
          >
            {getFitnessTitle(
              score,
            )}
          </h3>

          <p
            className="
              mt-1
              text-sm
              leading-relaxed
              text-base-content/55
            "
          >
            {getFitnessDescription(
              score,
              trainingLoad,
              recovery,
              fatigue,
            )}
          </p>
        </div>
      </div>
    </section>
  )
}


function getFitnessTitle(
  score: number,
): string {
  if (score >= 80) {
    return 'État de forme favorable'
  }

  if (score >= 60) {
    return 'État de forme correct'
  }

  if (score >= 40) {
    return 'Vigilance recommandée'
  }

  return 'Récupération prioritaire'
}


function getFitnessDescription(
  score: number,
  trainingLoad: number,
  recovery: number,
  fatigue: number,
): string {
  if (score >= 80) {
    return (
      'Les indicateurs disponibles sont favorables. '
      + 'Votre récupération est suffisante pour '
      + 'envisager normalement la séance prévue.'
    )
  }

  if (score >= 60) {
    return (
      'Votre état général reste correct. '
      + 'Adaptez néanmoins l’intensité si les sensations '
      + 'sont moins bonnes que prévu.'
    )
  }

  if (
    fatigue > recovery
    || trainingLoad >= 80
  ) {
    return (
      'La fatigue ou la charge récente sont élevées. '
      + 'Une séance allégée ou davantage de récupération '
      + 'peut être préférable.'
    )
  }

  return (
    'Les indicateurs montrent une disponibilité réduite. '
    + 'Privilégiez la récupération et une intensité faible.'
  )
}