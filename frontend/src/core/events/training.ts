export const TRAINING_SESSION_UPDATED_EVENT =
  'opencoach:training-session-updated'


export function notifyTrainingSessionUpdated(): void {
  window.dispatchEvent(
    new Event(
      TRAINING_SESSION_UPDATED_EVENT,
    ),
  )
}
