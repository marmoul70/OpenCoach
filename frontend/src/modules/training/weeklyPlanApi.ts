import type {
  CoachTrainingPhase,
  CoachWeekType,
} from '../coach/types'


export interface TrainingWeeklyPlan {
  weekStart: string
  weekEnd: string

  phase: CoachTrainingPhase
  weekType?: CoachWeekType

  phaseWeekIndex: number
}


interface TrainingWeeklyPlanApiResponse {
  week_start: string
  week_end: string

  phase: CoachTrainingPhase
  week_type: CoachWeekType | null

  phase_week_index: number
}


export async function fetchTrainingWeeklyPlan(
  weekStart: string,
): Promise<TrainingWeeklyPlan | null> {
  const params =
    new URLSearchParams({
      week_start: weekStart,
    })

  const response = await fetch(
    `/api/coach/weekly-plan?${params.toString()}`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger le plan hebdomadaire (${response.status}).`,
    )
  }

  const data =
    (
      await response.json()
    ) as (
      TrainingWeeklyPlanApiResponse
      | null
    )

  if (!data) {
    return null
  }

  return {
    weekStart:
      data.week_start,

    weekEnd:
      data.week_end,

    phase:
      data.phase,

    weekType:
      data.week_type
      ?? undefined,

    phaseWeekIndex:
      data.phase_week_index,
  }
}
