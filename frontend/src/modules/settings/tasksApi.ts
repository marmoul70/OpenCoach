export type AutomatedTaskStatus =
  | 'ok'
  | 'error'
  | 'inactive'
  | 'pending'


export interface AutomatedTask {
  unit: string
  service: string
  label: string
  description: string | null
  active: boolean
  enabled: boolean
  unit_file_state: string | null
  status: AutomatedTaskStatus
  last_result: string | null
  last_run: string | null
  next_run: string | null
  service_active_state: string | null
  service_sub_state: string | null
  exec_status: number | null
}


interface TasksResponse {
  tasks: AutomatedTask[]
  count: number
}


export async function fetchAutomatedTasks():
Promise<AutomatedTask[]> {
  const response =
    await fetch(
      '/api/system/tasks',
      {
        credentials:
          'same-origin',
        cache:
          'no-store',
      },
    )

  if (!response.ok) {
    throw new Error(
      'Impossible de charger les tâches automatisées.',
    )
  }

  const payload: TasksResponse =
    await response.json()


  return payload.tasks
}
