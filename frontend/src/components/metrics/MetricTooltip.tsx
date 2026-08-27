import {
  Info,
} from 'lucide-react'

import {
  useToast,
} from '../ui/ToastProvider'


export type MetricKey =
  | 'hrv'
  | 'resting_hr'
  | 'ctl'
  | 'atl'
  | 'tsb'
  | 'training_load'
  | 'readiness'
  | 'vma'
  | 'sv1'
  | 'sv2'
  | 'max_hr'
  | 'reference_confidence'


type MetricDefinition = {
  title: string
  description: string
}


export const METRIC_DEFINITIONS: Record<
  MetricKey,
  MetricDefinition
> = {
  hrv: {
    title: 'HRV — Variabilité de la fréquence cardiaque',
    description:
      'Variation du temps entre deux battements du cœur. '
      + 'OpenCoach la compare surtout à ta valeur habituelle. '
      + 'Une baisse inhabituelle peut accompagner fatigue, '
      + 'stress ou récupération incomplète.',
  },

  resting_hr: {
    title: 'FC au repos',
    description:
      'Nombre de battements du cœur par minute au repos. '
      + 'OpenCoach surveille surtout les écarts inhabituels '
      + 'par rapport à ta référence personnelle.',
  },

  ctl: {
    title: 'CTL — Charge chronique',
    description:
      'Estimation de ta charge d’entraînement de fond sur '
      + 'plusieurs semaines. OpenCoach l’utilise pour situer '
      + 'ton niveau habituel et éviter des progressions trop brutales.',
  },

  atl: {
    title: 'ATL — Charge aiguë',
    description:
      'Estimation de ta charge récente. Elle réagit rapidement '
      + 'aux dernières séances et donne une indication de la '
      + 'fatigue liée à ton entraînement récent.',
  },

  tsb: {
    title: 'Balance — Équilibre de charge',
    description:
      'Différence entre charge chronique et charge aiguë. '
      + 'Une valeur négative accompagne généralement une période '
      + 'plus fatigante, une valeur positive davantage de fraîcheur.',
  },

  training_load: {
    title: 'Charge d’entraînement',
    description:
      'Mesure de la contrainte produite par ton entraînement. '
      + 'OpenCoach s’en sert pour comparer ta semaine réelle '
      + 'à la charge adaptée à ton niveau actuel.',
  },

  readiness: {
    title: 'Forme du jour',
    description:
      'Synthèse de ton état du jour à partir de la récupération, '
      + 'du sommeil, de la charge récente et des autres signaux disponibles.',
  },

  vma: {
    title: 'VMA — Vitesse maximale aérobie',
    description:
      'Vitesse associée à ta puissance aérobie maximale. '
      + 'Elle sert de référence pour certaines intensités d’entraînement.',
  },

  sv1: {
    title: 'SV1 — Premier seuil ventilatoire',
    description:
      'Intensité à partir de laquelle la respiration commence '
      + 'à augmenter plus nettement. Elle aide à situer la limite '
      + 'haute des efforts faciles et durables.',
  },

  sv2: {
    title: 'SV2 — Deuxième seuil ventilatoire',
    description:
      'Intensité élevée proche du seuil anaérobie. '
      + 'Elle sert de référence pour le travail soutenu '
      + 'et les séances au seuil.',
  },

  max_hr: {
    title: 'FC maximale',
    description:
      'Fréquence cardiaque maximale utilisée comme référence '
      + 'pour calculer certaines zones d’intensité.',
  },

  reference_confidence: {
    title: 'Confiance de la référence',
    description:
      'Indique la quantité d’historique utilisée pour construire '
      + 'ta référence d’entraînement. Plus OpenCoach dispose '
      + 'de semaines de données, plus cette référence devient stable.',
  },
}


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
          inline-flex h-4 w-4 shrink-0 items-center justify-center
          rounded-full text-base-content/35
          transition-colors
          hover:text-info
          focus:text-info
          focus:outline-none
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
