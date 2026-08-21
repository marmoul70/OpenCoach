import type {
  Race,
} from './types'


export function getUpcomingRaces(
  races: Race[],
  today = new Date(),
): Race[] {
  const startOfToday =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
    )

  return [...races]
    .filter(
      (race) =>
        race.status === 'planned'
        && new Date(
          `${race.date}T12:00:00`,
        ) >= startOfToday,
    )
    .sort(
      (
        first,
        second,
      ) =>
        new Date(
          `${first.date}T12:00:00`,
        ).getTime()
        -
        new Date(
          `${second.date}T12:00:00`,
        ).getTime(),
    )
}


export function getNextRace(
  races: Race[],
  today = new Date(),
): Race | undefined {
  return getUpcomingRaces(
    races,
    today,
  )[0]
}


export function getNextPrimaryRace(
  races: Race[],
  today = new Date(),
): Race | undefined {
  return getUpcomingRaces(
    races,
    today,
  ).find(
    (race) =>
      race.priority === 'primary',
  )
}

export function getTrainingRacesBeforeNextPrimary(
  races: Race[],
  today = new Date(),
): Race[] {
  const nextPrimaryRace =
    getNextPrimaryRace(
      races,
      today,
    )

  if (!nextPrimaryRace) {
    return []
  }

  const primaryDate =
    new Date(
      `${nextPrimaryRace.date}T12:00:00`,
    )

  return getUpcomingRaces(
    races,
    today,
  ).filter(
    (race) =>
      race.priority === 'training'
      && new Date(
        `${race.date}T12:00:00`,
      ) < primaryDate,
  )
}