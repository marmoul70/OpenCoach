import {
  CalendarDays,
  Check,
  ChevronRight,
  MoveRight,
  Settings2,
  X,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  fetchTrainingSessionMoveOptions,
  type TrainingSessionMoveDay,
  type TrainingSessionMoveOptions,
} from '../../core/training/api'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  CorosWorkoutAction,
} from './CorosWorkoutAction'

import type {
  TrainingSession,
} from './types'


interface TrainingSessionActionsProps {
  session: TrainingSession
  compact?: boolean

  onRealized: () => void

  onSkipped: () => Promise<void>

  onMoved: (
    targetDate: string,
  ) => Promise<void>
}


export function TrainingSessionActions({
  session,
  compact = false,
  onRealized,
  onSkipped,
  onMoved,
}: TrainingSessionActionsProps) {
  const {
    toast,
  } = useToast()

  const [
    actionsOpen,
    setActionsOpen,
  ] = useState(false)

  const [
    moveOpen,
    setMoveOpen,
  ] = useState(false)

  const [
    options,
    setOptions,
  ] = useState<
    TrainingSessionMoveOptions | null
  >(null)

  const [
    selectedDate,
    setSelectedDate,
  ] = useState<string | null>(
    null,
  )

  const [
    loadingOptions,
    setLoadingOptions,
  ] = useState(false)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )


  useEffect(() => {
    setActionsOpen(false)
    setMoveOpen(false)
    setOptions(null)
    setSelectedDate(null)
    setError(null)
  }, [
    session.id,
    session.date,
  ])


  if (
    session.status !== 'planned'
    || session.type === 'rest'
  ) {
    return null
  }


  async function openMove() {
    setMoveOpen(true)

    if (options) {
      return
    }

    setLoadingOptions(true)
    setError(null)

    try {
      const result =
        await fetchTrainingSessionMoveOptions(
          session.id,
        )

      setOptions(
        result,
      )

      setSelectedDate(
        result.bestDate ?? null,
      )
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : (
              'Impossible de calculer '
              + 'les jours disponibles.'
            ),
      )
    } finally {
      setLoadingOptions(false)
    }
  }


  async function skipSession() {
    const confirmed =
      window.confirm(
        (
          'Marquer cette séance comme '
          + 'non réalisée ?'
        ),
      )

    if (!confirmed) {
      return
    }

    setSaving(true)
    setError(null)

    try {
      await onSkipped()

      setActionsOpen(false)

      toast({
        type: 'success',
        title: 'Séance non réalisée',
        message: (
          'OpenCoach en tiendra compte '
          + 'dans le suivi de la semaine.'
        ),
      })
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : (
              'Impossible de modifier '
              + 'la séance.'
            ),
      )
    } finally {
      setSaving(false)
    }
  }


  async function applyMove() {
    if (!selectedDate) {
      return
    }

    const selected =
      options?.days.find(
        day =>
          day.date === selectedDate,
      )

    if (
      !selected
      || !selected.selectable
    ) {
      return
    }

    setSaving(true)
    setError(null)

    try {
      await onMoved(
        selectedDate,
      )

      toast({
        type: 'success',
        title: 'Séance déplacée',
        message:
          `Nouvelle date : ${formatLongDate(selectedDate)}.`,
      })

      setMoveOpen(false)
      setActionsOpen(false)
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : (
              'Impossible de déplacer '
              + 'la séance.'
            ),
      )
    } finally {
      setSaving(false)
    }
  }


  if (compact) {
    return (
      <div
        className="
          relative
          shrink-0
        "
      >
        <button
          type="button"
          aria-label="Actions de la séance"
          aria-expanded={actionsOpen}
          onClick={() => {
            setActionsOpen(
              current => !current,
            )

            if (actionsOpen) {
              setMoveOpen(false)
            }
          }}
          className="
            inline-flex
            h-7
            w-7
            items-center
            justify-center
            rounded-[8px]
            border
            border-[var(--oc-border)]
            bg-[var(--oc-surface-raised)]
            text-[var(--oc-text-secondary)]
            shadow-[var(--oc-shadow-card)]
            transition
            hover:border-[var(--oc-border-strong)]
            hover:bg-[var(--oc-surface-hover)]
            hover:text-[var(--oc-text)]
          "
        >
          <Settings2
            className="h-3.5 w-3.5"
          />
        </button>


        {actionsOpen && (
          <div
            className={[
              'absolute right-0 top-[calc(100%+6px)] z-50 ',
              moveOpen
                ? 'w-[330px] '
                : 'w-[220px] ',
              'rounded-[12px] border ',
              'border-[var(--oc-border)] ',
              'bg-[var(--oc-surface-raised)] p-2 ',
              'shadow-[var(--oc-shadow-popover)]',
            ].join(' ')}
          >
            <div
              className="
                px-2
                pb-1.5
                pt-1
              "
            >
              <p
                className="
                  text-[9.5px]
                  font-bold
                  uppercase
                  tracking-[0.12em]
                  text-[var(--oc-text-secondary)]
                "
              >
                Actions
              </p>
            </div>


            {!moveOpen && (
              <div className="space-y-0.5">
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => {
                    setActionsOpen(false)
                    onRealized()
                  }}
                  className="
                    flex
                    w-full
                    items-center
                    gap-2.5
                    rounded-[8px]
                    px-2.5
                    py-2
                    text-left
                    text-[11.5px]
                    font-medium
                    text-[var(--oc-text)]
                    transition
                    hover:bg-emerald-500/[0.07]
                    hover:text-emerald-700
                    disabled:opacity-40
                     dark:hover:bg-emerald-400/[0.07]
                    dark:hover:text-emerald-300
                  "
                >
                  <span
                    className="
                      flex
                      h-6
                      w-6
                      items-center
                      justify-center
                      rounded-[7px]
                      bg-emerald-500/[0.08]
                      text-emerald-600
                      dark:text-emerald-400
                    "
                  >
                    <Check
                      className="h-3.5 w-3.5"
                    />
                  </span>

                  Réalisée
                </button>


                <button
                  type="button"
                  disabled={saving}
                  onClick={() =>
                    void skipSession()
                  }
                  className="
                    flex
                    w-full
                    items-center
                    gap-2.5
                    rounded-[8px]
                    px-2.5
                    py-2
                    text-left
                    text-[11.5px]
                    font-medium
                    text-[var(--oc-text)]
                    transition
                    hover:bg-red-500/[0.06]
                    hover:text-red-600
                    disabled:opacity-40
                     dark:hover:bg-red-400/[0.06]
                    dark:hover:text-red-400
                  "
                >
                  <span
                    className="
                      flex
                      h-6
                      w-6
                      items-center
                      justify-center
                      rounded-[7px]
                      bg-red-500/[0.07]
                      text-red-500
                    "
                  >
                    <X
                      className="h-3.5 w-3.5"
                    />
                  </span>

                  Non réalisée
                </button>


                <button
                  type="button"
                  disabled={saving}
                  onClick={() =>
                    void openMove()
                  }
                  className="
                    flex
                    w-full
                    items-center
                    gap-2.5
                    rounded-[8px]
                    px-2.5
                    py-2
                    text-left
                    text-[11.5px]
                    font-medium
                    text-[var(--oc-text)]
                    transition
                    hover:bg-[var(--oc-surface-hover)]
                    disabled:opacity-40
                     
                  "
                >
                  <span
                    className="
                      flex
                      h-6
                      w-6
                      items-center
                      justify-center
                      rounded-[7px]
                      bg-[var(--oc-surface-muted)]
                      text-[var(--oc-text-secondary)]
                    "
                  >
                    <MoveRight
                      className="h-3.5 w-3.5"
                    />
                  </span>

                  Déplacer

                  <ChevronRight
                    className="
                      ml-auto
                      h-3.5
                      w-3.5
                      text-[var(--oc-text-secondary)]
                    "
                  />
                </button>

                <CorosWorkoutAction session={session} />
              </div>
            )}


            {error && (
              <div
                className="
                  mx-1
                  mt-2
                  rounded-[8px]
                  border
                  border-red-500/15
                  bg-red-500/[0.045]
                  px-2.5
                  py-2
                  text-[10.5px]
                  leading-4
                  text-red-600
                  dark:text-red-400
                "
              >
                {error}
              </div>
            )}


            {moveOpen && (
              <div
                className="
                  mt-1
                  border-t
                  border-[var(--oc-border)]
                  px-1
                  pt-2.5
                  
                "
              >
                <div
                  className="
                    mb-2.5
                    flex
                    items-start
                    gap-2
                  "
                >
                  <CalendarDays
                    className="
                      mt-0.5
                      h-3.5
                      w-3.5
                      shrink-0
                      text-emerald-500
                    "
                  />

                  <div>
                    <p
                      className="
                        text-[11px]
                        font-semibold
                        text-[var(--oc-text)]
                      "
                    >
                      Nouveau jour
                    </p>

                    <p
                      className="
                        mt-0.5
                        text-[9.5px]
                        leading-4
                        text-[var(--oc-text-secondary)]
                      "
                    >
                      Placement recommandé par OpenCoach
                    </p>
                  </div>
                </div>


                {loadingOptions ? (
                  <div
                    className="
                      flex
                      min-h-24
                      items-center
                      justify-center
                    "
                  >
                    <span
                      className="
                        size-4
                        animate-spin
                        rounded-full
                        border-2
                        border-[var(--oc-border-strong)]
                        border-t-emerald-500
                        
                        dark:border-t-emerald-400
                      "
                    />
                  </div>
                ) : options ? (
                  options.days.some(
                    day => day.selectable,
                  ) ? (
                    <>
                      <div
                        className="
                          grid
                          grid-cols-7
                          gap-1
                        "
                      >
                        {options.days.map(
                          day => (
                            <MoveDayButton
                              key={day.date}
                              day={day}
                              selected={
                                selectedDate
                                === day.date
                              }
                              onSelect={() => {
                                if (
                                  day.selectable
                                ) {
                                  setSelectedDate(
                                    day.date,
                                  )
                                }
                              }}
                            />
                          ),
                        )}
                      </div>


                      {selectedDate && (
                        <SelectedDayAdvice
                          day={
                            options.days.find(
                              day =>
                                day.date
                                === selectedDate,
                            ) ?? null
                          }
                        />
                      )}


                      <div
                        className="
                          mt-2.5
                          flex
                          items-center
                          justify-between
                          gap-2
                        "
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setMoveOpen(false)
                          }}
                          className="
                            rounded-[8px]
                            px-2.5
                            py-1.5
                            text-[10.5px]
                            font-medium
                            text-[var(--oc-text-secondary)]
                            transition
                            hover:bg-[var(--oc-surface-hover)]
                            
                            
                          "
                        >
                          Retour
                        </button>

                        <button
                          type="button"
                          disabled={
                            !selectedDate
                            || saving
                          }
                          onClick={() =>
                            void applyMove()
                          }
                          className="
                            inline-flex
                            items-center
                            gap-1
                            rounded-[8px]
                            bg-emerald-600
                            px-2.5
                            py-1.5
                            text-[10.5px]
                            font-semibold
                            text-white
                            transition
                            hover:bg-emerald-700
                            disabled:cursor-not-allowed
                            disabled:opacity-40
                          "
                        >
                          Déplacer ici

                          <ChevronRight
                            className="h-3 w-3"
                          />
                        </button>
                      </div>
                    </>
                  ) : (
                    <div
                      className="
                        rounded-[8px]
                        bg-amber-500/[0.05]
                        px-2.5
                        py-2
                        text-[10.5px]
                        text-[var(--oc-text-secondary)]
                        
                      "
                    >
                      Aucun autre jour disponible.
                    </div>
                  )
                ) : null}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }


  return (
    <section
      className="
        mt-1
        rounded-[12px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        p-3
        
        
      "
    >
      <div
        className="
          mb-2.5
          flex
          items-center
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-[10px]
              font-bold
              uppercase
              tracking-[0.12em]
              text-[var(--oc-text-secondary)]
            "
          >
            Actions
          </p>

          <p
            className="
              mt-0.5
              text-[12px]
              font-medium
              text-[var(--oc-text)]
              
            "
          >
            Que souhaitez-vous faire ?
          </p>
        </div>
      </div>


      <div
        className="
          grid
          grid-cols-1
          gap-2
          sm:grid-cols-3
        "
      >
        <ActionButton
          icon={<Check className="h-3.5 w-3.5" />}
          label="Réalisée"
          onClick={onRealized}
          disabled={saving}
        />

        <ActionButton
          icon={<X className="h-3.5 w-3.5" />}
          label="Non réalisée"
          onClick={() =>
            void skipSession()
          }
          disabled={saving}
        />

        <ActionButton
          icon={
            <MoveRight
              className="h-3.5 w-3.5"
            />
          }
          label="Déplacer"
          onClick={() =>
            void openMove()
          }
          disabled={saving}
        />
      </div>

      <CorosWorkoutAction session={session} />

      {error && (
        <div
          className="
            mt-3
            rounded-[9px]
            border
            border-red-500/15
            bg-red-500/[0.045]
            px-3
            py-2
            text-[11px]
            leading-5
            text-red-600
            dark:text-red-400
          "
        >
          {error}
        </div>
      )}


      {moveOpen && (
        <div
          className="
            mt-3
            border-t
            border-[var(--oc-border)]
            pt-3
            
          "
        >
          <div
            className="
              mb-3
              flex
              items-start
              gap-2
            "
          >
            <CalendarDays
              className="
                mt-0.5
                h-4
                w-4
                shrink-0
                text-emerald-500
              "
            />

            <div>
              <p
                className="
                  text-[12px]
                  font-semibold
                  text-[var(--oc-text)]
                  
                "
              >
                Choisir un nouveau jour
              </p>

              <p
                className="
                  mt-0.5
                  text-[10.5px]
                  leading-4
                  text-[var(--oc-text-secondary)]
                "
              >
                Le score indique la qualité du
                placement selon votre semaine.
              </p>
            </div>
          </div>


          {loadingOptions ? (
            <div
              className="
                flex
                min-h-28
                items-center
                justify-center
              "
            >
              <span
                className="
                  size-4
                  animate-spin
                  rounded-full
                  border-2
                  border-[var(--oc-border-strong)]
                  border-t-emerald-500
                  
                  dark:border-t-emerald-400
                "
              />
            </div>
          ) : options ? (
            options.days.some(
              day => day.selectable,
            ) ? (
              <>
                <div
                  className="
                    grid
                    grid-cols-7
                    gap-1
                  "
                >
                {options.days.map(
                  day => (
                    <MoveDayButton
                      key={day.date}
                      day={day}
                      selected={
                        selectedDate
                        === day.date
                      }
                      onSelect={() => {
                        if (
                          day.selectable
                        ) {
                          setSelectedDate(
                            day.date,
                          )
                        }
                      }}
                    />
                  ),
                )}
              </div>


              {selectedDate && (
                <SelectedDayAdvice
                  day={
                    options.days.find(
                      day =>
                        day.date
                        === selectedDate,
                    ) ?? null
                  }
                />
              )}


              <div
                className="
                  mt-3
                  flex
                  items-center
                  justify-end
                  gap-2
                "
              >
                <button
                  type="button"
                  onClick={() => {
                    setMoveOpen(false)
                  }}
                  className="
                    rounded-[9px]
                    px-3
                    py-2
                    text-[11.5px]
                    font-medium
                    text-[var(--oc-text-secondary)]
                    transition
                    hover:bg-[var(--oc-surface-hover)]
                    
                    
                  "
                >
                  Annuler
                </button>

                <button
                  type="button"
                  disabled={
                    !selectedDate
                    || saving
                  }
                  onClick={() =>
                    void applyMove()
                  }
                  className="
                    inline-flex
                    items-center
                    gap-1.5
                    rounded-[9px]
                    bg-emerald-600
                    px-3
                    py-2
                    text-[11.5px]
                    font-semibold
                    text-white
                    transition
                    hover:bg-emerald-700
                    disabled:cursor-not-allowed
                    disabled:opacity-40
                  "
                >
                  Déplacer ici

                  <ChevronRight
                    className="h-3 w-3"
                  />
                </button>
                </div>
              </>
            ) : (
              <div
                className="
                  rounded-[10px]
                  border
                  border-amber-500/15
                  bg-amber-500/[0.045]
                  px-3
                  py-3
                  dark:border-amber-400/15
                  dark:bg-amber-400/[0.04]
                "
              >
                <p
                  className="
                    text-[12px]
                    font-semibold
                    text-[var(--oc-text)]
                    
                  "
                >
                  Déplacement impossible
                </p>

                <p
                  className="
                    mt-1
                    text-[10.5px]
                    leading-4
                    text-[var(--oc-text-secondary)]
                    
                  "
                >
                  Cette séance ne peut plus être
                  déplacée cette semaine.
                </p>

                <div
                  className="
                    mt-3
                    flex
                    justify-end
                  "
                >
                  <button
                    type="button"
                    onClick={() => {
                      setMoveOpen(false)
                    }}
                    className="
                      rounded-[9px]
                      px-3
                      py-2
                      text-[11.5px]
                      font-medium
                      text-[var(--oc-text-secondary)]
                      transition
                      hover:bg-[var(--oc-surface-hover)]
                      
                      
                    "
                  >
                    Fermer
                  </button>
                </div>
              </div>
            )
          ) : null}
        </div>
      )}
    </section>
  )
}


function ActionButton({
  icon,
  label,
  onClick,
  disabled,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  disabled: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="
        inline-flex
        min-h-9
        items-center
        justify-center
        gap-1.5
        rounded-[9px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface-muted)]
        px-3
        text-[11.5px]
        font-semibold
        text-[var(--oc-text)]
        transition
        hover:border-emerald-500/25
        hover:bg-emerald-50/60
        hover:text-emerald-700
        disabled:cursor-not-allowed
        disabled:opacity-40
        
        
        
        dark:hover:bg-emerald-500/[0.06]
        dark:hover:text-emerald-400
      "
    >
      {icon}
      {label}
    </button>
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
  const date =
    new Date(
      `${day.date}T12:00:00`,
    )

  const weekday =
    date.toLocaleDateString(
      'fr-FR',
      {
        weekday: 'short',
      },
    ).replace('.', '')

  const dayNumber =
    date.getDate()

  return (
    <button
      type="button"
      disabled={
        !day.selectable
      }
      onClick={onSelect}
      title={
        day.blockingReasons[0]
        ?? day.reasons[0]
        ?? undefined
      }
      className={[
        (
          'relative flex min-w-0 flex-col '
          + 'items-center rounded-[9px] border '
          + 'px-1 py-2 transition'
        ),

        selected
          ? (
              'border-emerald-500/45 '
              + 'bg-emerald-50 '
              + 'dark:bg-emerald-500/[0.08]'
            )
          : (
              'border-[var(--oc-border)] '
              + 'bg-[var(--oc-surface-muted)] '
              + ' '
              + ''
            ),

        !day.selectable
          ? 'cursor-not-allowed opacity-40'
          : (
              'hover:border-emerald-500/30 '
              + 'hover:bg-emerald-50/50'
            ),
      ].join(' ')}
    >
      {day.recommended && (
        <span
          className="
            absolute
            -right-1
            -top-1
            flex
            h-3.5
            w-3.5
            items-center
            justify-center
            rounded-full
            bg-emerald-500
            text-[8px]
            font-bold
            text-white
          "
        >
          ★
        </span>
      )}

      <span
        className="
          text-[9.5px]
          font-semibold
          uppercase
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-text-secondary)]
        "
      >
        {weekday}
      </span>

      <span
        className="
          mt-0.5
          text-[13px]
          font-bold
          text-[var(--oc-text)]
          
        "
      >
        {dayNumber}
      </span>

      <span
        className={[
          (
            'mt-1 text-[10px] '
            + 'font-bold'
          ),

          scoreClass(
            day,
          ),
        ].join(' ')}
      >
        {day.current
          ? 'Actuel'
          : `${day.score}%`}
      </span>
    </button>
  )
}


function SelectedDayAdvice({
  day,
}: {
  day: TrainingSessionMoveDay | null
}) {
  if (!day) {
    return null
  }

  return (
    <div
      className="
        mt-3
        rounded-[10px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface-muted)]
        p-3
      "
    >
      <div
        className="
          flex
          items-center
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-[12px]
              font-semibold
              text-[var(--oc-text)]
            "
          >
            {formatLongDate(
              day.date,
            )}
          </p>

          <p
            className="
              mt-0.5
              text-[10.5px]
              font-medium
              text-[var(--oc-text-secondary)]
            "
          >
            {levelLabel(
              day,
            )}
          </p>
        </div>

        <span
          className={[
            (
              'text-[18px] '
              + 'font-bold'
            ),
            scoreClass(day),
          ].join(' ')}
        >
          {day.score}%
        </span>
      </div>

      <div
        className="
          mt-2
          space-y-1
        "
      >
        {day.reasons
          .slice(0, 4)
          .map(reason => (
            <p
              key={reason}
              className="
                text-[10.5px]
                leading-4
                text-[var(--oc-text-secondary)]
              "
            >
              • {reason}
            </p>
          ))}
      </div>
    </div>
  )
}


function scoreClass(
  day: TrainingSessionMoveDay,
): string {
  if (!day.selectable) {
    return (
      'text-[var(--oc-text-secondary)]'
    )
  }

  if (day.score >= 85) {
    return (
      'text-emerald-600 '
      + 'dark:text-emerald-400'
    )
  }

  if (day.score >= 70) {
    return (
      'text-lime-600 '
      + 'dark:text-lime-400'
    )
  }

  if (day.score >= 50) {
    return (
      'text-amber-600 '
      + 'dark:text-amber-400'
    )
  }

  return (
    'text-red-500 '
    + 'dark:text-red-400'
  )
}


function levelLabel(
  day: TrainingSessionMoveDay,
): string {
  switch (day.level) {
    case 'excellent':
      return 'Excellent choix'

    case 'good':
      return 'Bon choix'

    case 'possible':
      return 'Possible'

    case 'discouraged':
      return 'Déconseillé'

    case 'impossible':
      return 'Impossible'

    case 'current':
      return 'Emplacement actuel'
  }
}


function formatLongDate(
  value: string,
): string {
  return new Date(
    `${value}T12:00:00`,
  ).toLocaleDateString(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  )
}
