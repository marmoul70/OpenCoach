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
          bg-white dark:bg-[#151b1f]
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
            border-black/[0.06] dark:border-white/[0.07]
            bg-white dark:bg-[#151b1f]/95
            px-5 py-4
            backdrop-blur
          "
        >
          <div>
            <p
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-emerald-600 dark:text-emerald-400
              "
            >
              Protocole OpenCoach
            </p>

            <h2
              className="
                text-xl font-bold
                text-slate-800 dark:text-slate-100
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
              inline-flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center
              rounded-[8px]
              text-slate-400
              transition
              hover:bg-slate-100
              hover:text-slate-700
              dark:text-slate-500
              dark:hover:bg-white/[0.05]
              dark:hover:text-slate-200
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
          </div>
        )}


        {error && (
          <div className="p-6">
            <div
              className="
                rounded-[11px]
                border
                border-rose-500/15
                bg-rose-500/[0.05]
                px-4
                py-3
                text-[11px]
                font-medium
                text-rose-700
                dark:border-rose-400/15
                dark:bg-rose-400/[0.05]
                dark:text-rose-300
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
                text-slate-500 dark:text-slate-400
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
                bg-emerald-500/[0.04] dark:bg-emerald-400/[0.04]
                p-4
              "
            >
              <p
                className="
                  font-semibold
                  text-slate-800 dark:text-slate-100
                "
              >
                Ce qu’OpenCoach analysera
              </p>

              <p
                className="
                  mt-2 text-sm
                  leading-6
                  text-slate-500 dark:text-slate-400
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
        flex
        items-center
        gap-3
        rounded-[11px]
        border
        border-black/[0.05]
        bg-slate-50/70
        p-4
        dark:border-white/[0.06]
        dark:bg-white/[0.025]
      "
    >
      <span
        className="
          text-emerald-600
          dark:text-emerald-400
        "
      >
        {icon}
      </span>

      <span>
        <span
          className="
            block
            text-[9.5px]
            font-medium
            text-slate-400
            dark:text-slate-500
          "
        >
          {title}
        </span>

        <span
          className="
            text-[12px]
            font-semibold
            text-slate-800
            dark:text-slate-100
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
          <span
            className="
              text-emerald-600
              dark:text-emerald-400
            "
          >
            {icon}
          </span>
        )}

        <h3
          className="
            text-[12.5px]
            font-semibold
            text-slate-800
            dark:text-slate-100
          "
        >
          {title}
        </h3>
      </div>

      <div
        className="
          text-[10.5px]
          leading-[1.65]
          text-slate-500
          dark:text-slate-400
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
          mb-3
          text-[12.5px]
          font-semibold
          text-slate-800
          dark:text-slate-100
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
                      'border-emerald-500/18 '
                      + 'bg-emerald-500/[0.045] '
                      + 'dark:border-emerald-400/18 '
                      + 'dark:bg-emerald-400/[0.04]'
                    )
                  : (
                      'border-black/[0.06] '
                      + 'bg-white '
                      + 'dark:border-white/[0.07] '
                      + 'dark:bg-[#171d21]'
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
                    text-[11.5px]
                    font-semibold
                    text-slate-800
                    dark:text-slate-100
                  "
                >
                  {step.title}
                </p>

                {step.duration_minutes
                  != null && (
                    <span
                      className="
                        inline-flex
                        items-center
                        rounded-full
                        border
                        border-black/[0.07]
                        bg-white/70
                        px-2
                        py-0.5
                        text-[8.5px]
                        font-semibold
                        text-slate-500
                        dark:border-white/[0.08]
                        dark:bg-white/[0.025]
                        dark:text-slate-400
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
                  mt-2
                  text-[10.5px]
                  leading-[1.6]
                  text-slate-500
                  dark:text-slate-400
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
