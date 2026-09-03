import {
  CalendarDays,
  Check,
  Sparkles,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  acceptDailyAdaptation,
  applyDailyReplanning,
  fetchDailyReplanning,
  type DailyCheckInState,
  type DailyReplanningState,
  type ReplanningOption,
  type ReplanningProposal,
} from '../../core/checkin'

import {
  SidePanel,
} from '../../components/ui/SidePanel'

import {
  useToast,
} from '../../components/ui/ToastProvider'


import {
  TRAINING_SESSION_UPDATED_EVENT,
} from '../../core/events'


interface DailyDecisionModalProps {
  open: boolean
  state: DailyCheckInState | null
  onClose: () => void
  onStateChanged: () => Promise<void>
}


export function DailyDecisionModal({
  open,
  state,
  onClose,
  onStateChanged,
}: DailyDecisionModalProps) {
  const {
    toast,
  } = useToast()

  const startedRef =
    useRef(false)

  const [
    replanning,
    setReplanning,
  ] = useState<DailyReplanningState | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(
    false,
  )

  const [
    applyingSessionId,
    setApplyingSessionId,
  ] = useState<string | null>(
    null,
  )

  const [
    resolvedSessionIds,
    setResolvedSessionIds,
  ] = useState<Set<string>>(
    () => new Set(),
  )


  const loadProposals =
    useCallback(
      async () => {
        if (
          !state
          || !state.adaptation
        ) {
          return
        }

        try {
          setLoading(
            true,
          )

          await acceptDailyAdaptation(
            state.checkin.id,
          )

          const result =
            await fetchDailyReplanning(
              state.checkin.id,
            )

          setReplanning(
            result,
          )

          await onStateChanged()

          if (
            result.proposals.length === 0
          ) {
            toast({
              type: 'success',
              title: 'Analyse terminée',
              message:
                'OpenCoach a traité la séance du jour.',
            })
          }
        } catch (reason) {
          startedRef.current =
            false

          toast({
            type: 'error',
            title: 'Adaptation impossible',
            message:
              getErrorMessage(
                reason,
              ),
          })
        } finally {
          setLoading(
            false,
          )
        }
      },
      [
        state,
        onStateChanged,
        toast,
      ],
    )


  const visibleProposals =
    replanning?.proposals.filter(
      (proposal) => {
        const id =
          proposal.source_session.id

        return (
          id === null
          || !resolvedSessionIds.has(
            id,
          )
        )
      },
    )
    ?? []


  useEffect(() => {
    if (!open) {
      startedRef.current =
        false

      setReplanning(
        null,
      )

      setResolvedSessionIds(
        new Set(),
      )

      return
    }

    if (
      startedRef.current
      || !state
      || !state.adaptation
    ) {
      return
    }

    startedRef.current =
      true

    void loadProposals()
  }, [
    open,
    state,
    loadProposals,
  ])


  if (
    !open
    || !state
    || !state.adaptation
  ) {
    return null
  }

  const currentState =
    state


  async function applyOption(
    proposal: ReplanningProposal,
    option: ReplanningOption,
  ) {
    const sourceId =
      proposal.source_session.id

    if (!sourceId) {
      return
    }

    try {
      setApplyingSessionId(
        sourceId,
      )

      await applyDailyReplanning(
        currentState.checkin.id,
        {
          source_session_id:
            sourceId,

          action:
            option.action,

          target_date:
            option.target_date,
        },
      )

      window.dispatchEvent(
        new Event(
          TRAINING_SESSION_UPDATED_EVENT,
        ),
      )

      setResolvedSessionIds(
        (previous) => {
          const next =
            new Set(
              previous,
            )

          next.add(
            sourceId,
          )

          return next
        },
      )

      toast({
        type: 'success',
        title:
          getActionSuccessTitle(
            option,
          ),
        message:
          getActionSuccessMessage(
            option,
          ),
      })

      await onStateChanged()
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Replanification impossible',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setApplyingSessionId(
        null,
      )
    }
  }


  const allResolved =
    replanning !== null
    && visibleProposals.length === 0


  return (
    <SidePanel
      open={open}
      onClose={onClose}
      eyebrow="Adaptation"
      title="Adapter l’entraînement"
    >
      <div className="space-y-4">

        {loading && !replanning && (
          <div
            className="
              flex
              min-h-40
              flex-col
              items-center
              justify-center
              gap-3
              text-center
            "
          >
            <span
              className="
                h-7
                w-7
                animate-spin
                rounded-full
                border-[2.5px]
                border-slate-200
                border-t-emerald-500
                dark:border-white/[0.10]
                dark:border-t-emerald-400
              "
              aria-hidden="true"
            />

            <div>
              <p
                className="
                  font-semibold
                  text-slate-800 dark:text-slate-100
                "
              >
                Analyse du planning
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  text-slate-500 dark:text-slate-400
                "
              >
                Recherche des meilleures options
                de replanification.
              </p>
            </div>
          </div>
        )}


        {replanning && !allResolved && (
          <>
            <div
              className="
                flex
                items-center
                gap-2
              "
            >
              <Sparkles
                className="
                  h-4
                  w-4
                  text-emerald-600 dark:text-emerald-400
                "
              />

              <p
                className="
                  text-sm
                  font-semibold
                  text-slate-800 dark:text-slate-100
                "
              >
                Choisissez l’action à appliquer
              </p>
            </div>

            {replanning.coordination_reasons.length > 0 && (
              <section
                className="
                  rounded-xl
                  border
                  border-emerald-500/15
                  bg-emerald-500/[0.05]
                  dark:border-emerald-400/15
                  dark:bg-emerald-400/[0.05]
                  p-3
                "
              >
                <p
                  className="
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-emerald-600 dark:text-emerald-400
                  "
                >
                  Analyse OpenCoach
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    leading-relaxed
                    text-slate-500 dark:text-slate-400
                  "
                >
                  {
                    replanning
                      .coordination_reasons[0]
                  }
                </p>
              </section>
            )}

            <div className="space-y-3">
              {visibleProposals.map(
                (proposal) => (
                  <SessionDecisionCard
                    key={
                      proposal.source_session.id
                      ?? proposal.source_session.title
                    }
                    proposal={proposal}
                    loading={
                      applyingSessionId
                      === proposal.source_session.id
                    }
                    onChoose={(option) => {
                      void applyOption(
                        proposal,
                        option,
                      )
                    }}
                  />
                ),
              )}
            </div>
          </>
        )}


        {allResolved && (
          <section
            className="
              rounded-2xl
              border
              border-emerald-500/15
              bg-emerald-500/[0.05]
              dark:border-emerald-400/15
              dark:bg-emerald-400/[0.05]
              p-5
              text-center
            "
          >
            <div
              className="
                mx-auto
                flex
                size-11
                items-center
                justify-center
                rounded-full
                bg-emerald-500/[0.10]
                text-emerald-600
                dark:bg-emerald-400/[0.10]
                dark:text-emerald-400
              "
            >
              <Check
                className="h-6 w-6"
              />
            </div>

            <h3
              className="
                mt-3
                font-semibold
                text-slate-800 dark:text-slate-100
              "
            >
              Planning mis à jour
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-slate-500 dark:text-slate-400
              "
            >
              Le planning de la semaine
              a été mis à jour.
            </p>

            <button
              type="button"
              className="
                mt-4
                inline-flex
                h-8
                items-center
                justify-center
                rounded-[8px]
                border
                border-emerald-500/15
                bg-emerald-500/[0.10]
                px-3.5
                text-[10.5px]
                font-semibold
                text-emerald-600 dark:text-emerald-400
                outline-none
                transition
                hover:border-emerald-500/25
                hover:bg-emerald-500/[0.15]
                active:scale-[0.98]
                dark:border-emerald-400/15
                dark:bg-emerald-400/[0.09]
                dark:text-emerald-300
                dark:hover:bg-emerald-400/[0.14]
              "
              onClick={onClose}
            >
              Terminer
            </button>
          </section>
        )}

      </div>
    </SidePanel>
  )
}


function SessionDecisionCard({
  proposal,
  loading,
  onChoose,
}: {
  proposal: ReplanningProposal
  loading: boolean
  onChoose: (
    option: ReplanningOption,
  ) => void
}) {
  const recommended =
    proposal.options.find(
      (option) =>
        option.recommended,
    )

  const others =
    proposal.options.filter(
      (option) =>
        !option.recommended,
    )

  return (
    <section
      className="
        rounded-[13px]
        border
        border-black/[0.06]
        bg-white
        p-3.5
        shadow-[0_1px_2px_rgba(15,23,42,0.02)]
        dark:border-white/[0.07]
        dark:bg-[#171d21]
      "
    >
      <div
        className="
          flex
          items-center
          gap-3
        "
      >
        <div
          className="
            flex
            size-8
            shrink-0
            items-center
            justify-center
            rounded-lg
            bg-emerald-500/[0.10]
            text-emerald-600
            dark:bg-emerald-400/[0.10]
            dark:text-emerald-400
          "
        >
          <CalendarDays
            className="h-4 w-4"
          />
        </div>

        <div>
          <p
            className="
              font-semibold
              text-slate-800 dark:text-slate-100
            "
          >
            {proposal.source_session.title}
          </p>

          <p
            className="
              text-xs
              text-slate-400 dark:text-slate-500
            "
          >
            {
              proposal
                .source_session
                .duration_minutes
            } min
          </p>
        </div>
      </div>


      {recommended && (
        <div
          className="
            mt-3
            rounded-xl
            border
            border-emerald-500/15
            bg-emerald-500/[0.05]
            dark:border-emerald-400/15
            dark:bg-emerald-400/[0.05]
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
              <span
                className="
                  inline-flex
                  h-5
                  items-center
                  rounded-full
                  border
                  border-emerald-500/15
                  bg-emerald-500/[0.08]
                  px-2
                  text-[9.5px]
                  font-bold
                  uppercase
                  tracking-[0.06em]
                  text-emerald-600 dark:text-emerald-400
                  dark:border-emerald-400/15
                  dark:bg-emerald-400/[0.08]
                  dark:text-emerald-300
                "
              >
                ★ Recommandé
              </span>

              <p
                className="
                  mt-2
                  text-sm
                  font-semibold
                  text-slate-800 dark:text-slate-100
                "
              >
                {
                  getOptionLabel(
                    recommended,
                  )
                }
              </p>

              <p
                className="
                  mt-0.5
                  text-xs
                  text-slate-500 dark:text-slate-400
                "
              >
                {
                  getOptionDetails(
                    recommended,
                  )
                }
              </p>
            </div>

            <button
              type="button"
              className="
                inline-flex
                h-8
                shrink-0
                items-center
                justify-center
                rounded-[8px]
                border
                border-emerald-500/15
                bg-emerald-500/[0.10]
                px-3
                text-[10.5px]
                font-semibold
                text-emerald-600 dark:text-emerald-400
                outline-none
                transition
                hover:border-emerald-500/25
                hover:bg-emerald-500/[0.15]
                active:scale-[0.98]
                disabled:cursor-not-allowed
                disabled:opacity-50
                dark:border-emerald-400/15
                dark:bg-emerald-400/[0.09]
                dark:text-emerald-300
                dark:hover:bg-emerald-400/[0.14]
              "
              disabled={loading}
              onClick={() => {
                onChoose(
                  recommended,
                )
              }}
            >
              {loading
                ? (
                    <span
                      className="
                        h-3.5
                        w-3.5
                        animate-spin
                        rounded-full
                        border-2
                        border-emerald-700/20
                        border-t-emerald-700
                        dark:border-emerald-300/20
                        dark:border-t-emerald-300
                      "
                      aria-hidden="true"
                    />
                  )
                : 'Appliquer'}
            </button>
          </div>
        </div>
      )}


      {others.length > 0 && (
        <div
          className="
            mt-2
            grid
            gap-2
            sm:grid-cols-2
          "
        >
          {others.map(
            (option) => (
              <button
                key={
                  option.action
                  + ':'
                  + (
                    option.target_date
                    ?? 'none'
                  )
                }
                type="button"
                className="
                  min-h-11
                  w-full
                  rounded-[9px]
                  border
                  border-black/[0.06]
                  bg-slate-50/70
                  px-3
                  py-2.5
                  text-left
                  text-slate-700
                  outline-none
                  transition
                  hover:border-black/[0.10]
                  hover:bg-slate-100
                  active:scale-[0.99]
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                  dark:border-white/[0.07]
                  dark:bg-white/[0.025]
                  dark:text-slate-200
                  dark:hover:border-white/[0.11]
                  dark:hover:bg-white/[0.05]
                "
                disabled={loading}
                onClick={() => {
                  onChoose(
                    option,
                  )
                }}
              >
                <span>
                  <span
                    className="
                      block
                      text-xs
                      font-semibold
                    "
                  >
                    {
                      getOptionLabel(
                        option,
                      )
                    }
                  </span>

                  <span
                    className="
                      mt-0.5
                      block
                      text-xs
                      font-normal
                      opacity-50
                    "
                  >
                    {
                      getOptionDetails(
                        option,
                      )
                    }
                  </span>
                </span>
              </button>
            ),
          )}
        </div>
      )}
    </section>
  )
}


function getOptionLabel(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return 'Annuler'
  }

  if (
    option.action
    === 'move_adapted'
  ) {
    return 'Déplacer et adapter'
  }

  return 'Déplacer sans modifier'
}


function getOptionDetails(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return ''
  }

  if (!option.target_date) {
    return ''
  }

  const date =
    formatDate(
      option.target_date,
    )

  const duration =
    option.session
      ?.duration_minutes

  return (
    duration
      ? `${date} · ${duration} min`
      : date
  )
}


function getActionSuccessTitle(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return 'Séance annulée'
  }

  if (
    option.action
    === 'move_adapted'
  ) {
    return 'Séance déplacée et adaptée'
  }

  return 'Séance déplacée'
}


function getActionSuccessMessage(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return 'La séance reste annulée.'
  }

  return getOptionDetails(
    option,
  )
}


function formatDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}


function getErrorMessage(
  reason: unknown,
): string {
  return (
    reason instanceof Error
      ? reason.message
      : 'Une erreur est survenue.'
  )
}
