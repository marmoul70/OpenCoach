import {
  useEffect,
  useState,
} from 'react'

import {
  Activity,
  CalendarDays,
  Check,
  ChevronRight,
  FlaskConical,
  X,
} from 'lucide-react'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  PhysiologicalTestProtocolModal,
} from './PhysiologicalTestProtocolModal'

import {
  acceptPhysiologicalTest,
  declinePhysiologicalTest,
  getPendingPhysiologicalTests,
} from './api'

import type {
  PhysiologicalTestProposal,
} from './api'


export function PhysiologicalTestProposalCard() {
  const {
    toast,
  } = useToast()

  const [
    proposal,
    setProposal,
  ] = useState<
    PhysiologicalTestProposal
    | null
  >(null)

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    showProtocol,
    setShowProtocol,
  ] = useState(false)

  const [
    action,
    setAction,
  ] = useState<
    'accept'
    | 'decline'
    | null
  >(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setLoading(true)

        const proposals =
          await getPendingPhysiologicalTests()

        if (!cancelled) {
          setProposal(
            proposals[0]
            ?? null,
          )
        }
      } catch {
        if (!cancelled) {
          setProposal(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [])


  async function handleAccept() {
    if (!proposal) {
      return
    }

    try {
      setAction(
        'accept',
      )

      const result =
        await acceptPhysiologicalTest(
          proposal.id,
        )

      setProposal(null)

      toast({
        type: 'success',
        title: 'Test accepté',
        message:
          result.message
          || (
            'La séance a été remplacée '
            + 'par le test proposé.'
          ),
        duration: 5000,
      })

      window.dispatchEvent(
        new CustomEvent(
          'opencoach:training-changed',
        ),
      )
    } catch (error) {
      toast({
        type: 'error',
        title:
          'Impossible d’accepter le test',
        message:
          error instanceof Error
            ? error.message
            : (
                'Une erreur est survenue.'
              ),
        duration: 6000,
      })
    } finally {
      setAction(null)
    }
  }


  async function handleDecline() {
    if (!proposal) {
      return
    }

    try {
      setAction(
        'decline',
      )

      const result =
        await declinePhysiologicalTest(
          proposal.id,
        )

      setProposal(null)

      toast({
        type: 'info',
        title:
          'Test reporté',
        message:
          result.message
          || (
            'La séance qualitative '
            + 'initiale est conservée.'
          ),
        duration: 5000,
      })
    } catch (error) {
      toast({
        type: 'error',
        title:
          'Impossible de refuser le test',
        message:
          error instanceof Error
            ? error.message
            : (
                'Une erreur est survenue.'
              ),
        duration: 6000,
      })
    } finally {
      setAction(null)
    }
  }


  if (
    loading
    || !proposal
  ) {
    return null
  }

  const protocol =
    formatProtocol(
      proposal.protocol,
    )

  const metrics =
    proposal.target_metrics.map(
      formatMetric,
    )

  return (
    <section
      className="
        mb-5
        overflow-hidden
        rounded-[14px]
        border
        border-emerald-500/15
        bg-white
        shadow-[0_1px_2px_rgba(15,23,42,0.02)]
        dark:border-emerald-400/15
        dark:bg-[#171d21]
        dark:shadow-none
      "
    >
      <div
        className="
          flex flex-col gap-4
          p-4
          sm:p-5
          lg:flex-row
          lg:items-center
          lg:justify-between
        "
      >
        <div
          className="
            flex min-w-0
            items-start gap-3
            sm:gap-4
          "
        >
          <div
            className="
              flex
              h-10
              w-10
              shrink-0
              items-center
              justify-center
              rounded-[10px]
              border
              border-emerald-500/10
              bg-emerald-500/[0.08]
              text-emerald-600
              dark:border-emerald-400/10
              dark:bg-emerald-400/[0.08]
              dark:text-emerald-300
            "
          >
            <FlaskConical
              size={22}
            />
          </div>

          <div className="min-w-0">
            <div
              className="
                flex flex-wrap
                items-center
                gap-2
              "
            >
              <span
                className="
                  text-[9.5px]
                  font-bold
                  uppercase
                  tracking-[0.07em]
                  text-emerald-600
                  dark:text-emerald-400
                "
              >
                Recommandation du coach
              </span>

              <span
                className="
                  inline-flex
                  items-center
                  rounded-full
                  border
                  border-emerald-500/15
                  bg-emerald-500/[0.06]
                  px-2
                  py-0.5
                  text-[8.5px]
                  font-semibold
                  text-emerald-700
                  dark:border-emerald-400/15
                  dark:bg-emerald-400/[0.06]
                  dark:text-emerald-300
                "
              >
                Test physiologique
              </span>
            </div>

            <h2
              className="
                mt-1
                text-lg
                font-bold
                text-slate-800 dark:text-slate-100
                sm:text-xl
              "
            >
              {protocol}
            </h2>

            <p
              className="
                mt-1
                max-w-3xl
                text-sm
                leading-6
                text-slate-500 dark:text-slate-400
              "
            >
              {
                proposal.recommendation
              }
            </p>

            <div
              className="
                mt-3
                flex flex-wrap
                gap-x-4
                gap-y-2
                text-xs
                font-medium
                text-slate-500 dark:text-slate-400
              "
            >
              <span
                className="
                  inline-flex
                  items-center
                  gap-1.5
                "
              >
                <CalendarDays
                  size={14}
                />

                {
                  formatDate(
                    proposal.proposed_date,
                  )
                }
              </span>

              {metrics.length > 0 && (
                <span
                  className="
                    inline-flex
                    items-center
                    gap-1.5
                  "
                >
                  <Activity
                    size={14}
                  />

                  {
                    metrics.join(
                      ' · ',
                    )
                  }
                </span>
              )}
            </div>

            {proposal.reason && (
              <p
                className="
                  mt-3
                  text-xs
                  leading-5
                  text-slate-400 dark:text-slate-500
                "
              >
                Pourquoi maintenant ?
                {' '}
                {proposal.reason}
              </p>
            )}
          </div>
        </div>


        <div
          className="
            flex shrink-0
            flex-col gap-2
            sm:flex-row
            lg:flex-col
            xl:flex-row
          "
        >
          <button
            type="button"
            className="
              inline-flex
              h-9
              items-center
              justify-center
              rounded-[9px]
              border
              border-black/[0.06]
              bg-white/70
              px-3
              text-[10.5px]
              font-semibold
              text-slate-600
              transition
              hover:border-black/[0.10]
              hover:bg-slate-100
              dark:border-white/[0.07]
              dark:bg-white/[0.025]
              dark:text-slate-300
              dark:hover:border-white/[0.11]
              dark:hover:bg-white/[0.05]
            "
            onClick={() => {
              setShowProtocol(true)
            }}
          >
            Voir le protocole
          </button>

          <button
            type="button"
            className="
              inline-flex
              h-9
              items-center
              justify-center
              gap-2
              rounded-[9px]
              border
              border-emerald-500/15
              bg-emerald-500/[0.09]
              px-3
              text-[10.5px]
              font-semibold
              text-emerald-700
              transition
              hover:border-emerald-500/25
              hover:bg-emerald-500/[0.14]
              disabled:cursor-not-allowed
              disabled:opacity-50
              dark:border-emerald-400/15
              dark:bg-emerald-400/[0.08]
              dark:text-emerald-300
              dark:hover:bg-emerald-400/[0.13]
            "
            disabled={
              action !== null
            }
            onClick={() => {
              void handleAccept()
            }}
          >
            {action === 'accept'
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
              : (
                  <Check
                    size={15}
                  />
                )}

            Faire le test

            <ChevronRight
              size={14}
            />
          </button>

          <button
            type="button"
            className="
              inline-flex
              h-9
              items-center
              justify-center
              gap-2
              rounded-[9px]
              border
              border-black/[0.06]
              bg-white/70
              px-3
              text-[10.5px]
              font-semibold
              text-slate-600
              transition
              hover:border-black/[0.10]
              hover:bg-slate-100
              disabled:cursor-not-allowed
              disabled:opacity-50
              dark:border-white/[0.07]
              dark:bg-white/[0.025]
              dark:text-slate-300
              dark:hover:border-white/[0.11]
              dark:hover:bg-white/[0.05]
            "
            disabled={
              action !== null
            }
            onClick={() => {
              void handleDecline()
            }}
          >
            {action === 'decline'
              ? (
                  <span
                    className="
                      h-3.5
                      w-3.5
                      animate-spin
                      rounded-full
                      border-2
                      border-slate-300
                      border-t-slate-600
                      dark:border-white/[0.12]
                      dark:border-t-slate-300
                    "
                    aria-hidden="true"
                  />
                )
              : (
                  <X
                    size={15}
                  />
                )}

            Pas maintenant
          </button>
        </div>
      </div>

      {showProtocol && (
        <PhysiologicalTestProtocolModal
          protocol={
            proposal.protocol
          }
          onClose={() => {
            setShowProtocol(false)
          }}
        />
      )}
    </section>
  )
}


function formatProtocol(
  protocol: string,
): string {
  const labels:
    Record<string, string> = {
      half_cooper:
        'Demi-Cooper · 6 minutes',
      cooper:
        'Cooper · 12 minutes',
      threshold_30_min:
        'Test seuil · 30 minutes',
    }

  return (
    labels[protocol]
    ?? protocol
      .replaceAll(
        '_',
        ' ',
      )
  )
}


function formatMetric(
  metric: string,
): string {
  const labels:
    Record<string, string> = {
      vma: 'VMA',
      max_heart_rate: 'FC max',
      resting_heart_rate:
        'FC repos',
      threshold_heart_rate_1:
        'SV1',
      threshold_heart_rate_2:
        'SV2',
    }

  return (
    labels[metric]
    ?? metric.toUpperCase()
  )
}


function formatDate(
  value: string,
): string {
  const date =
    new Date(
      `${value}T12:00:00`,
    )

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    date,
  )
}
