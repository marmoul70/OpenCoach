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
      + ' border-emerald-500/20'
      + ' bg-emerald-500/[0.08]'
      + ' text-emerald-600 dark:text-emerald-400'
    )
  }

  if (weekType === 'taper') {
    return (
      base
      + ' border-violet-500/20'
      + ' bg-violet-500/[0.08]'
      + ' text-violet-600 dark:text-violet-400'
    )
  }

  if (weekType === 'return_to_training') {
    return (
      base
      + ' border-sky-500/20'
      + ' bg-sky-500/[0.08]'
      + ' text-sky-600 dark:text-sky-400'
    )
  }

  if (weekType === 'suspended') {
    return (
      base
      + ' border-amber-500/20'
      + ' bg-amber-500/[0.08]'
      + ' text-amber-600 dark:text-amber-400'
    )
  }

  return (
    base
    + ' border-emerald-500/20'
    + ' bg-emerald-500/[0.08]'
    + ' text-emerald-600 dark:text-emerald-400'
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
      + ' text-sky-600 dark:text-sky-400'
    )
  }

  if (phase === 'base') {
    return (
      base
      + ' text-emerald-600 dark:text-emerald-400'
    )
  }

  if (phase === 'build') {
    return (
      base
      + ' text-amber-600 dark:text-amber-400'
    )
  }

  if (phase === 'specific') {
    return (
      base
      + ' text-violet-600 dark:text-violet-400'
    )
  }

  if (phase === 'taper') {
    return (
      base
      + ' text-cyan-600 dark:text-cyan-400'
    )
  }

  if (phase === 'recovery') {
    return (
      base
      + ' text-emerald-600 dark:text-emerald-400'
    )
  }

  return (
    base
    + ' text-sky-600 dark:text-sky-400'
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
