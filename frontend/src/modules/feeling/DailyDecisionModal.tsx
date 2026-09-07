import {
  ArrowLeft,
  Ban,
  CalendarDays,
  ChevronRight,
  Gauge,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  acceptDailyAdaptation,
  declineDailyAdaptation,
  fetchDailyAdaptationOptions,
  type DailyAdaptationOption,
  type DailyCheckInState,
} from '../../core/checkin'

import {
  fetchTrainingSessionMoveOptions,
  fetchTrainingSessions,
  moveTrainingSession,
  updateTrainingSessionStatus,
  type TrainingSessionMoveDay,
  type TrainingSessionMoveOptions,
} from '../../core/training/api'

import {
  notifyTrainingSessionUpdated,
} from '../../core/events'

import {
  SidePanel,
} from '../../components/ui/SidePanel'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import type {
  TrainingSession,
} from '../training/types'


export type FeelingSessionAction =
  | 'reduce'
  | 'move'
  | 'cancel'


interface DailyDecisionModalProps {
  open: boolean
  initialAction: FeelingSessionAction | null
  state: DailyCheckInState | null
  onClose: () => void
  onStateChanged: () => Promise<void>
}


export function DailyDecisionModal({
  open,
  initialAction,
  state,
  onClose,
  onStateChanged,
}: DailyDecisionModalProps) {
  const { toast } = useToast()
  const [action, setAction] = useState<FeelingSessionAction | null>(initialAction)
  const [sessions, setSessions] = useState<TrainingSession[]>([])
  const [reductions, setReductions] = useState<DailyAdaptationOption[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [moveOptions, setMoveOptions] = useState<TrainingSessionMoveOptions | null>(null)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) {
      setAction(null)
      setSessions([])
      setReductions([])
      setSelectedSessionId(null)
      setMoveOptions(null)
      setSelectedDate(null)
      return
    }

    setAction(initialAction)

    if (!state) {
      return
    }

    const date = state.checkin.date

    async function loadSessions() {
      try {
        setLoading(true)
        const result = await fetchTrainingSessions(date, date)
        setSessions(
          result.filter(
            session => session.status === 'planned' && session.type !== 'rest',
          ),
        )
      } catch (reason) {
        toast({
          type: 'error',
          title: 'Séances indisponibles',
          message: reason instanceof Error
            ? reason.message
            : 'Une erreur inattendue est survenue.',
        })
      } finally {
        setLoading(false)
      }
    }

    void loadSessions()
  }, [open, initialAction, state, toast])

  useEffect(() => {
    if (!open || action !== 'reduce' || !state?.adaptation) {
      return
    }

    const checkinId = state.checkin.id

    async function loadReductions() {
      try {
        setLoading(true)
        const result = await fetchDailyAdaptationOptions(checkinId)
        setReductions(result.options)
      } catch (reason) {
        toast({
          type: 'error',
          title: 'Réduction impossible',
          message: reason instanceof Error
            ? reason.message
            : 'Une erreur inattendue est survenue.',
        })
      } finally {
        setLoading(false)
      }
    }

    void loadReductions()
  }, [open, action, state, toast])

  if (!open || !state) {
    return null
  }

  async function reduce(option: DailyAdaptationOption) {
    const sourceId = option.source_session.id
    if (!sourceId) return

    try {
      setSaving(true)
      const result = await acceptDailyAdaptation(state!.checkin.id, sourceId)

      if (
        !result.session_adapted
        || !result.adapted_session
      ) {
        throw new Error(
          result.already_accepted
            ? (
                'Cette adaptation avait déjà été '
                + 'acceptée, mais la réduction '
                + 'n’a pas été appliquée à la séance.'
              )
            : (
                'La réduction n’a pas été appliquée '
                + 'à la séance.'
              ),
        )
      }
      notifyTrainingSessionUpdated()
      await onStateChanged()
      toast({
        type: 'success',
        title: 'Séance réduite',
        message: result.adapted_session
          ? `${result.adapted_session.title} · ${result.adapted_session.duration_minutes} min`
          : 'La réduction a été enregistrée.',
      })
      onClose()
    } catch (reason) {
      showError('Réduction impossible', reason)
    } finally {
      setSaving(false)
    }
  }

  async function chooseMoveSession(session: TrainingSession) {
    try {
      setSelectedSessionId(session.id)
      setMoveOptions(null)
      setSelectedDate(null)
      setLoading(true)
      const result = await fetchTrainingSessionMoveOptions(session.id)
      setMoveOptions(result)
      setSelectedDate(result.bestDate ?? null)
    } catch (reason) {
      showError('Déplacement impossible', reason)
    } finally {
      setLoading(false)
    }
  }

  async function move() {
    if (!selectedSessionId || !selectedDate) return

    try {
      setSaving(true)
      await moveTrainingSession(selectedSessionId, selectedDate)
      if (state!.adaptation?.awaiting_athlete_decision) {
        await declineDailyAdaptation(state!.checkin.id)
      }
      notifyTrainingSessionUpdated()
      await onStateChanged()
      toast({
        type: 'success',
        title: 'Séance déplacée',
        message: `Nouvelle date : ${formatDate(selectedDate)}.`,
      })
      onClose()
    } catch (reason) {
      showError('Déplacement impossible', reason)
    } finally {
      setSaving(false)
    }
  }

  async function cancel(session: TrainingSession) {
    const confirmed = window.confirm(
      `Annuler « ${session.title} » ?\n\nLa séance restera dans le planning comme non faite.`,
    )
    if (!confirmed) return

    try {
      setSaving(true)
      await updateTrainingSessionStatus(session.id, 'skipped')
      if (state!.adaptation?.awaiting_athlete_decision) {
        await declineDailyAdaptation(state!.checkin.id)
      }
      notifyTrainingSessionUpdated()
      await onStateChanged()
      toast({
        type: 'success',
        title: 'Séance annulée / non faite',
        message: 'OpenCoach la conservera dans le suivi de la semaine.',
      })
      onClose()
    } catch (reason) {
      showError('Annulation impossible', reason)
    } finally {
      setSaving(false)
    }
  }

  function showError(title: string, reason: unknown) {
    toast({
      type: 'error',
      title,
      message: reason instanceof Error
        ? reason.message
        : 'Une erreur inattendue est survenue.',
    })
  }

  return (
    <SidePanel
      open={open}
      onClose={onClose}
      eyebrow="Ressenti"
      title={
        action === 'reduce'
          ? 'Réduire une séance'
          : action === 'move'
            ? 'Déplacer une séance'
            : action === 'cancel'
              ? 'Annuler une séance'
              : 'Adapter l’entraînement'
      }
    >
      <div className="space-y-4">
        {action && (
          <button
            type="button"
            onClick={() => {
              setAction(null)
              setSelectedSessionId(null)
              setMoveOptions(null)
              setSelectedDate(null)
            }}
            className="inline-flex items-center gap-1.5 text-[10.5px] font-medium text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Changer d’action
          </button>
        )}

        {!action && (
          <div className="grid gap-2">
            <button type="button" onClick={() => setAction('reduce')} className="rounded-[11px] border border-black/[0.07] p-3 text-left dark:border-white/[0.07]">
              <div className="flex items-center gap-3">
                <Gauge className="h-4 w-4 text-emerald-500" />
                <div><p className="text-[12px] font-semibold">Réduire</p><p className="text-[10px] text-slate-400">Alléger une séance du jour.</p></div>
              </div>
            </button>
            <button type="button" onClick={() => setAction('move')} className="rounded-[11px] border border-black/[0.07] p-3 text-left dark:border-white/[0.07]">
              <div className="flex items-center gap-3"><CalendarDays className="h-4 w-4 text-sky-500" /><div><p className="text-[12px] font-semibold">Déplacer</p><p className="text-[10px] text-slate-400">Reporter avec les règles du planning.</p></div></div>
            </button>
            <button type="button" onClick={() => setAction('cancel')} className="rounded-[11px] border border-rose-500/15 p-3 text-left">
              <div className="flex items-center gap-3"><Ban className="h-4 w-4 text-rose-500" /><div><p className="text-[12px] font-semibold">Annuler</p><p className="text-[10px] text-slate-400">Marquer la séance comme non faite.</p></div></div>
            </button>
          </div>
        )}

        {loading && <div className="py-10 text-center text-[11px] text-slate-400">Chargement…</div>}

        {!loading && action === 'reduce' && (
          <div className="space-y-3">
            {reductions.length === 0 && (
              <p className="rounded-[10px] border border-black/[0.06] p-3 text-[10.5px] text-slate-500 dark:border-white/[0.07]">Aucune séance du jour ne peut être réduite.</p>
            )}
            {reductions.map(option => (
              <section key={option.source_session.id ?? option.source_session.title} className="rounded-[12px] border border-black/[0.07] p-3.5 dark:border-white/[0.07]">
                <p className="text-[12px] font-semibold">{option.source_session.title}</p>
                <div className="mt-2 grid grid-cols-2 gap-2 text-[10px]">
                  <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-white/[0.025]">
                    <p className="font-semibold text-slate-400">Actuelle</p>
                    <p className="mt-1">{option.source_session.duration_minutes} min</p>
                    <p>{option.source_session.intensity}</p>
                  </div>
                  <div className="rounded-lg bg-emerald-500/[0.05] p-2.5">
                    <p className="font-semibold text-emerald-600 dark:text-emerald-400">Réduite</p>
                    <p className="mt-1">{option.adapted_session.duration_minutes} min</p>
                    <p>{option.adapted_session.intensity}</p>
                  </div>
                </div>
                <p className="mt-2 text-[9.5px] text-slate-400">{option.adapted_session.type} · {option.adapted_session.sport_type}</p>
                <button type="button" disabled={saving || !option.changed} onClick={() => void reduce(option)} className="mt-3 h-8 rounded-[8px] border border-emerald-500/20 bg-emerald-500/[0.08] px-3 text-[10px] font-semibold text-emerald-700 disabled:opacity-40 dark:text-emerald-300">Appliquer cette réduction</button>
              </section>
            ))}
          </div>
        )}

        {!loading && action === 'move' && (
          <div className="space-y-3">
            {sessions.map(session => (
              <button
                key={session.id}
                type="button"
                onClick={() => void chooseMoveSession(session)}
                className={[
                  'flex w-full items-center gap-3 rounded-[10px] border p-3 text-left transition',
                  selectedSessionId === session.id
                    ? 'border-emerald-500/30 bg-emerald-500/[0.06]'
                    : 'border-black/[0.06] dark:border-white/[0.07]',
                ].join(' ')}
              >
                <CalendarDays className="h-4 w-4 shrink-0 text-emerald-500" />
                <div className="min-w-0">
                  <p className="truncate text-[11.5px] font-semibold">{session.title}</p>
                  <p className="mt-0.5 text-[9.5px] text-slate-400">
                    {session.durationMinutes} min · {session.sportType}
                  </p>
                </div>
              </button>
            ))}

            {moveOptions && (
              <div className="border-t border-black/[0.06] pt-3 dark:border-white/[0.06]">
                <div className="mb-3 flex items-start gap-2">
                  <CalendarDays className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  <div>
                    <p className="text-[12px] font-semibold text-slate-800 dark:text-slate-200">
                      Choisir un nouveau jour
                    </p>
                    <p className="mt-0.5 text-[10.5px] leading-4 text-slate-400 dark:text-slate-500">
                      Le score indique la qualité du placement selon votre semaine.
                    </p>
                  </div>
                </div>

                {moveOptions.days.some(day => day.selectable) ? (
                  <>
                    <div className="grid grid-cols-7 gap-1">
                      {moveOptions.days.map(day => (
                        <MoveDayButton
                          key={day.date}
                          day={day}
                          selected={selectedDate === day.date}
                          onSelect={() => {
                            if (day.selectable) {
                              setSelectedDate(day.date)
                            }
                          }}
                        />
                      ))}
                    </div>

                    {selectedDate && (
                      <SelectedDayAdvice
                        day={moveOptions.days.find(day => day.date === selectedDate) ?? null}
                      />
                    )}

                    <div className="mt-3 flex items-center justify-end gap-2">
                      <button
                        type="button"
                        disabled={!selectedDate || saving}
                        onClick={() => void move()}
                        className="inline-flex items-center gap-1.5 rounded-[9px] bg-emerald-600 px-3 py-2 text-[11.5px] font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Déplacer ici
                        <ChevronRight className="h-3 w-3" />
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="rounded-[10px] border border-amber-500/15 bg-amber-500/[0.045] px-3 py-3 dark:border-amber-400/15 dark:bg-amber-400/[0.04]">
                    <p className="text-[12px] font-semibold text-slate-800 dark:text-slate-200">
                      Déplacement impossible
                    </p>
                    <p className="mt-1 text-[10.5px] leading-4 text-slate-500 dark:text-slate-400">
                      Cette séance ne peut plus être déplacée cette semaine.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {!loading && action === 'cancel' && (
          <div className="space-y-2">
            {sessions.map(session => (
              <button key={session.id} type="button" disabled={saving} onClick={() => void cancel(session)} className="flex w-full items-center gap-3 rounded-[10px] border border-rose-500/15 p-3 text-left disabled:opacity-40">
                <Ban className="h-4 w-4 text-rose-500" />
                <div><p className="text-[11.5px] font-semibold">{session.title}</p><p className="text-[9.5px] text-slate-400">{session.durationMinutes} min · {session.sportType}</p></div>
              </button>
            ))}
          </div>
        )}
      </div>
    </SidePanel>
  )
}


function MoveDayButton({
  day,
  selected,
  onSelect,
}: {
  day: TrainingSessionMoveDay
  selected: boolean
  onSelect: () => void
}) {
  const date = new Date(`${day.date}T12:00:00`)
  const weekday = date
    .toLocaleDateString('fr-FR', { weekday: 'short' })
    .replace('.', '')
  const dayNumber = date.getDate()

  return (
    <button
      type="button"
      disabled={!day.selectable}
      onClick={onSelect}
      title={day.blockingReasons[0] ?? day.reasons[0] ?? undefined}
      className={[
        'relative flex min-w-0 flex-col items-center rounded-[9px] border px-1 py-2 transition',
        selected
          ? 'border-emerald-500/45 bg-emerald-50 dark:bg-emerald-500/[0.08]'
          : 'border-black/[0.06] bg-slate-50 dark:border-white/[0.06] dark:bg-white/[0.02]',
        !day.selectable
          ? 'cursor-not-allowed opacity-40'
          : 'hover:border-emerald-500/30 hover:bg-emerald-50/50',
      ].join(' ')}
    >
      {day.recommended && (
        <span className="absolute -right-1 -top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-500 text-[8px] font-bold text-white">
          ★
        </span>
      )}
      <span className="text-[9.5px] font-semibold uppercase text-slate-400 dark:text-slate-500">
        {weekday}
      </span>
      <span className="mt-0.5 text-[13px] font-bold text-slate-800 dark:text-slate-200">
        {dayNumber}
      </span>
      <span className={['mt-1 text-[10px] font-bold', scoreClass(day)].join(' ')}>
        {day.current ? 'Actuel' : `${day.score}%`}
      </span>
    </button>
  )
}


function SelectedDayAdvice({
  day,
}: {
  day: TrainingSessionMoveDay | null
}) {
  if (!day) return null

  return (
    <div className="mt-3 rounded-[10px] border border-black/[0.06] bg-slate-50 p-3 dark:border-white/[0.06] dark:bg-white/[0.02]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold text-slate-800 dark:text-slate-200">
            {formatLongDate(day.date)}
          </p>
          <p className="mt-0.5 text-[10.5px] font-medium text-slate-400 dark:text-slate-500">
            {levelLabel(day)}
          </p>
        </div>
        <span className={['text-[18px] font-bold', scoreClass(day)].join(' ')}>
          {day.score}%
        </span>
      </div>
      <div className="mt-2 space-y-1">
        {day.reasons.slice(0, 4).map(reason => (
          <p key={reason} className="text-[10.5px] leading-4 text-slate-500 dark:text-slate-400">
            • {reason}
          </p>
        ))}
      </div>
    </div>
  )
}


function scoreClass(day: TrainingSessionMoveDay): string {
  if (!day.selectable) return 'text-slate-400 dark:text-slate-600'
  if (day.score >= 85) return 'text-emerald-600 dark:text-emerald-400'
  if (day.score >= 70) return 'text-lime-600 dark:text-lime-400'
  if (day.score >= 50) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-500 dark:text-red-400'
}


function levelLabel(day: TrainingSessionMoveDay): string {
  switch (day.level) {
    case 'excellent': return 'Excellent choix'
    case 'good': return 'Bon choix'
    case 'possible': return 'Possible'
    case 'discouraged': return 'Déconseillé'
    case 'impossible': return 'Impossible'
    case 'current': return 'Emplacement actuel'
  }
}


function formatLongDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(
    'fr-FR',
    { weekday: 'long', day: 'numeric', month: 'long' },
  )
}


function formatDate(value: string): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    { weekday: 'long', day: 'numeric', month: 'long' },
  ).format(new Date(`${value}T12:00:00`))
}
