import type {
  CoachTrainingPhase,
  CoachWeekType,
} from '../coach/types'


export type CoachTrajectoryMode =
  | 'maintenance'
  | 'race_preparation'


export interface CoachTrajectoryWeek {
  weekStart: string
  weekEnd: string

  mode: CoachTrajectoryMode

  phase: CoachTrainingPhase
  weekType: CoachWeekType

  phaseWeekIndex: number

  targetLoad: number
  loadMin: number
  loadMax: number
}


export interface CoachTrajectory {
  targetRaceName: string
  targetRaceDate: string

  preparationStartDate: string

  weeks: CoachTrajectoryWeek[]
}


interface CoachTrajectoryWeekApiResponse {
  week_start: string
  week_end: string

  mode: CoachTrajectoryMode

  phase: CoachTrainingPhase
  week_type: CoachWeekType

  phase_week_index: number

  target_load: number
  load_min: number
  load_max: number
}


interface CoachTrajectoryApiResponse {
  target_race_name: string
  target_race_date: string

  preparation_start_date: string

  weeks: CoachTrajectoryWeekApiResponse[]
}


export async function fetchCoachTrajectory():
Promise<CoachTrajectory | null> {
  const response =
    await fetch(
      '/api/coach/trajectory',
    )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger la trajectoire (${response.status}).`,
    )
  }

  const data =
    (
      await response.json()
    ) as CoachTrajectoryApiResponse | null

  if (!data) {
    return null
  }

  return {
    targetRaceName:
      data.target_race_name,

    targetRaceDate:
      data.target_race_date,

    preparationStartDate:
      data.preparation_start_date,

    weeks:
      data.weeks.map(
        (week) => ({
          weekStart:
            week.week_start,

          weekEnd:
            week.week_end,

          mode:
            week.mode,

          phase:
            week.phase,

          weekType:
            week.week_type,

          phaseWeekIndex:
            week.phase_week_index,

          targetLoad:
            week.target_load,

          loadMin:
            week.load_min,

          loadMax:
            week.load_max,
        }),
      ),
  }
}
