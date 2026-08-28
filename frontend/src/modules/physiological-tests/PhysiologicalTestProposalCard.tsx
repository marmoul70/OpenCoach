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
        rounded-2xl
        border
        border-primary/25
        bg-base-100
        shadow-sm
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
              flex h-11 w-11
              shrink-0
              items-center
              justify-center
              rounded-xl
              bg-primary/10
              text-primary
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
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-primary
                "
              >
                Recommandation du coach
              </span>

              <span
                className="
                  badge
                  badge-primary
                  badge-outline
                  badge-sm
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
                text-base-content
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
                text-base-content/65
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
                text-base-content/55
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
                  text-base-content/45
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
              btn
              btn-ghost
              btn-sm
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
              btn
              btn-primary
              btn-sm
              gap-2
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
                      loading
                      loading-spinner
                      loading-xs
                    "
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
              btn
              btn-ghost
              btn-sm
              gap-2
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
                      loading
                      loading-spinner
                      loading-xs
                    "
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
