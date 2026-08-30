import type {
  TrainingSession,
} from './types'


const dayLabels = [
  'Lundi',
  'Mardi',
  'Mercredi',
  'Jeudi',
  'Vendredi',
  'Samedi',
  'Dimanche',
]


export function getWeekSessions(
  sessions:
    TrainingSession[],
) {
  const today =
    new Date()

  const currentDay =
    today.getDay()

  const mondayOffset =
    currentDay === 0
      ? -6
      : 1 - currentDay

  const monday =
    new Date(
      today,
    )

  monday.setHours(
    12,
    0,
    0,
    0,
  )

  monday.setDate(
    today.getDate()
    + mondayOffset,
  )

  const todayString =
    formatLocalDate(
      today,
    )

  return dayLabels.map(
    (
      label,
      index,
    ) => {
      const date =
        new Date(
          monday,
        )

      date.setDate(
        monday.getDate()
        + index,
      )

      const dateString =
        formatLocalDate(
          date,
        )

      return {
        label,
        date:
          dateString,

        sessions:
          sessions.filter(
            (session) =>
              session.date
              === dateString,
          ),

        isToday:
          dateString
          === todayString,
      }
    },
  )
}


export function formatLocalDate(
  date: Date,
): string {
  const year =
    date.getFullYear()

  const month =
    String(
      date.getMonth()
      + 1,
    ).padStart(
      2,
      '0',
    )

  const day =
    String(
      date.getDate(),
    ).padStart(
      2,
      '0',
    )

  return (
    `${year}-${month}-${day}`
  )
}
