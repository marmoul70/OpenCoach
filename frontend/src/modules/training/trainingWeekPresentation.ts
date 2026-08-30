import {
  useCoachToday,
} from '../coach/useCoachToday'


export function formatWeekType(
  weekType: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['weekType'],
): string {
  if (weekType === 'loading') {
    return 'Travail'
  }

  if (weekType === 'recovery') {
    return 'Récupération'
  }

  if (weekType === 'taper') {
    return 'Affûtage'
  }

  if (weekType === 'return_to_training') {
    return 'Reprise'
  }

  return 'Suspendue'
}


export function weekTypeBadgeClass(
  weekType: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['weekType'],
): string {
  const base = (
    'inline-flex items-center gap-2 '
    + 'rounded-full border px-3 py-1.5 '
    + 'text-xs shadow-sm'
  )

  if (weekType === 'recovery') {
    return (
      base
      + ' border-success/25'
      + ' bg-success/10'
      + ' text-success'
    )
  }

  if (weekType === 'taper') {
    return (
      base
      + ' border-secondary/25'
      + ' bg-secondary/10'
      + ' text-secondary'
    )
  }

  if (weekType === 'return_to_training') {
    return (
      base
      + ' border-info/25'
      + ' bg-info/10'
      + ' text-info'
    )
  }

  if (weekType === 'suspended') {
    return (
      base
      + ' border-warning/25'
      + ' bg-warning/10'
      + ' text-warning'
    )
  }

  return (
    base
    + ' border-primary/25'
    + ' bg-primary/10'
    + ' text-primary'
  )
}


export function phaseTextClass(
  phase: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['phase'],
): string {
  const base =
    'font-semibold'

  if (phase === 'foundation') {
    return (
      base
      + ' text-info'
    )
  }

  if (phase === 'base') {
    return (
      base
      + ' text-primary'
    )
  }

  if (phase === 'build') {
    return (
      base
      + ' text-warning'
    )
  }

  if (phase === 'specific') {
    return (
      base
      + ' text-secondary'
    )
  }

  if (phase === 'taper') {
    return (
      base
      + ' text-accent'
    )
  }

  if (phase === 'recovery') {
    return (
      base
      + ' text-success'
    )
  }

  return (
    base
    + ' text-info'
  )
}


export function formatTrainingPhase(
  phase: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['phase'],
): string {
  if (phase === 'foundation') {
    return 'Fondation'
  }

  if (phase === 'base') {
    return 'Base'
  }

  if (phase === 'build') {
    return 'Développement'
  }

  if (phase === 'specific') {
    return 'Spécifique'
  }

  if (phase === 'taper') {
    return 'Affûtage'
  }

  if (phase === 'recovery') {
    return 'Récupération'
  }

  return 'Reprise'
}


export function formatTrainingWeekRange(
  start: string,
  end: string,
): string {
  const startDate = new Date(
    `${start}T12:00:00`,
  )

  const endDate = new Date(
    `${end}T12:00:00`,
  )

  const startDay =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: 'numeric',
      },
    ).format(
      startDate,
    )

  const endDateFormatted =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      },
    ).format(
      endDate,
    )

  return (
    `Semaine du ${startDay} au ${endDateFormatted}`
  )
}


export function humanizeWeeklyTrainingStatus(
  status: string,
): string {
  if (status === 'aligned') {
    return 'Semaine dans la cible'
  }

  if (status === 'under_target') {
    return 'Charge sous la cible'
  }

  if (status === 'over_target') {
    return 'Charge au-dessus de la cible'
  }

  return 'Cible en cours d’évaluation'
}


export function formatRaceDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'short',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
  )
}


export function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    'fr-FR',
    {
      maximumFractionDigits: 1,
    },
  ).format(
    value,
  )
}
