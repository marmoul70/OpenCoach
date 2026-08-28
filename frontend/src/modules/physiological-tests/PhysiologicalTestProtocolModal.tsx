import {
  useEffect,
  useState,
} from 'react'

import {
  Activity,
  Clock3,
  MapPin,
  ShieldCheck,
  X,
} from 'lucide-react'

import {
  getPhysiologicalTestProtocolDetails,
} from './api'

import type {
  PhysiologicalTestProtocolDetails,
  PhysiologicalTestProtocolStep,
} from './api'


interface Props {
  protocol: string
  onClose: () => void
}


export function PhysiologicalTestProtocolModal({
  protocol,
  onClose,
}: Props) {
  const [
    details,
    setDetails,
  ] = useState<
    PhysiologicalTestProtocolDetails
    | null
  >(null)

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    error,
    setError,
  ] = useState(false)


  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setLoading(true)
        setError(false)

        const value =
          await getPhysiologicalTestProtocolDetails(
            protocol,
          )

        if (!cancelled) {
          setDetails(value)
        }
      } catch {
        if (!cancelled) {
          setError(true)
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
  }, [
    protocol,
  ])


  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-end
        justify-center
        bg-black/40
        p-0
        sm:items-center
        sm:p-5
      "
      role="dialog"
      aria-modal="true"
    >
      <div
        className="
          max-h-[92vh]
          w-full
          max-w-3xl
          overflow-y-auto
          rounded-t-3xl
          bg-base-100
          shadow-2xl
          sm:rounded-3xl
        "
      >
        <div
          className="
            sticky top-0 z-10
            flex items-center
            justify-between
            border-b
            border-base-300
            bg-base-100/95
            px-5 py-4
            backdrop-blur
          "
        >
          <div>
            <p
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-primary
              "
            >
              Protocole OpenCoach
            </p>

            <h2
              className="
                text-xl font-bold
                text-base-content
              "
            >
              {
                details?.title
                ?? 'Test physiologique'
              }
            </h2>
          </div>

          <button
            type="button"
            className="
              btn btn-circle btn-ghost btn-sm
            "
            onClick={onClose}
            aria-label="Fermer"
          >
            <X size={18} />
          </button>
        </div>


        {loading && (
          <div
            className="
              flex min-h-72
              items-center justify-center
            "
          >
            <span
              className="
                loading loading-spinner
                loading-md text-primary
              "
            />
          </div>
        )}


        {error && (
          <div className="p-6">
            <div
              className="
                alert alert-error
              "
            >
              Impossible de charger
              le protocole du test.
            </div>
          </div>
        )}


        {details && (
          <div
            className="
              space-y-6
              p-5
              sm:p-6
            "
          >
            <p
              className="
                text-sm leading-6
                text-base-content/65
              "
            >
              {
                details.short_description
              }
            </p>


            <div
              className="
                grid gap-3
                sm:grid-cols-2
              "
            >
              <InfoCard
                icon={
                  <Clock3 size={18} />
                }
                title="Durée estimée"
                value={
                  `${details.total_duration_minutes} min`
                }
              />

              <InfoCard
                icon={
                  <Activity size={18} />
                }
                title="Mesure principale"
                value={
                  details.target_metrics
                    .map(formatMetric)
                    .join(' · ')
                }
              />
            </div>


            <Section
              title="Terrain recommandé"
              icon={
                <MapPin size={18} />
              }
            >
              <p>
                {
                  details.terrain_recommendation
                }
              </p>
            </Section>


            <Section
              title="Avant le test"
            >
              <BulletList
                values={
                  details.preparation
                }
              />
            </Section>


            <StepsSection
              title="Échauffement"
              steps={
                details.warmup
              }
            />


            <StepsSection
              title="Test"
              steps={
                details.test_steps
              }
              emphasized
            />


            <StepsSection
              title="Retour au calme"
              steps={
                details.cooldown
              }
            />


            <Section
              title="Conseils d’exécution"
              icon={
                <ShieldCheck
                  size={18}
                />
              }
            >
              <BulletList
                values={
                  details.execution_advice
                }
              />
            </Section>


            <Section
              title="Quand le résultat peut être invalidé"
            >
              <BulletList
                values={
                  details.invalidation_reasons
                }
              />
            </Section>


            <div
              className="
                rounded-2xl
                bg-primary/5
                p-4
              "
            >
              <p
                className="
                  font-semibold
                  text-base-content
                "
              >
                Ce qu’OpenCoach analysera
              </p>

              <p
                className="
                  mt-2 text-sm
                  leading-6
                  text-base-content/60
                "
              >
                Distance, allure ou vitesse,
                fréquence cardiaque,
                dénivelé et régularité
                de l’effort lorsque ces
                données sont disponibles.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


function InfoCard({
  icon,
  title,
  value,
}: {
  icon: React.ReactNode
  title: string
  value: string
}) {
  return (
    <div
      className="
        flex items-center gap-3
        rounded-xl
        bg-base-200/60
        p-4
      "
    >
      <span className="text-primary">
        {icon}
      </span>

      <span>
        <span
          className="
            block text-xs
            text-base-content/45
          "
        >
          {title}
        </span>

        <span
          className="
            font-semibold
            text-base-content
          "
        >
          {value}
        </span>
      </span>
    </div>
  )
}


function Section({
  title,
  icon,
  children,
}: {
  title: string
  icon?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section>
      <div
        className="
          mb-3
          flex items-center gap-2
        "
      >
        {icon && (
          <span className="text-primary">
            {icon}
          </span>
        )}

        <h3
          className="
            font-bold
            text-base-content
          "
        >
          {title}
        </h3>
      </div>

      <div
        className="
          text-sm leading-6
          text-base-content/65
        "
      >
        {children}
      </div>
    </section>
  )
}


function BulletList({
  values,
}: {
  values: string[]
}) {
  return (
    <ul
      className="
        space-y-2
        pl-5
        list-disc
      "
    >
      {values.map(
        (value) => (
          <li key={value}>
            {value}
          </li>
        ),
      )}
    </ul>
  )
}


function StepsSection({
  title,
  steps,
  emphasized = false,
}: {
  title: string
  steps:
    PhysiologicalTestProtocolStep[]
  emphasized?: boolean
}) {
  return (
    <section>
      <h3
        className="
          mb-3 font-bold
          text-base-content
        "
      >
        {title}
      </h3>

      <div className="space-y-3">
        {steps.map(
          (
            step,
            index,
          ) => (
            <div
              key={
                `${step.title}-${index}`
              }
              className={[
                'rounded-xl border p-4',
                emphasized
                  ? (
                      'border-primary/30 '
                      + 'bg-primary/5'
                    )
                  : (
                      'border-base-300 '
                      + 'bg-base-100'
                    ),
              ].join(' ')}
            >
              <div
                className="
                  flex items-center
                  justify-between
                  gap-3
                "
              >
                <p
                  className="
                    font-semibold
                    text-base-content
                  "
                >
                  {step.title}
                </p>

                {step.duration_minutes
                  != null && (
                    <span
                      className="
                        badge
                        badge-outline
                        badge-sm
                      "
                    >
                      {
                        step.duration_minutes
                      } min
                    </span>
                  )}
              </div>

              <p
                className="
                  mt-2 text-sm
                  leading-6
                  text-base-content/60
                "
              >
                {step.description}
              </p>
            </div>
          ),
        )}
      </div>
    </section>
  )
}


function formatMetric(
  metric: string,
): string {
  const labels:
    Record<string, string> = {
      vma: 'VMA',
      max_heart_rate: 'FC max',
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
