import type {
  ReactNode,
} from 'react'

import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Clock3,
  Gauge,
  MapPin,
  Target,
} from 'lucide-react'

import type {
  SessionGuidance,
  SessionGuidanceIntensityTarget,
  SessionGuidanceStep,
} from './sessionGuidanceApi'


interface Props {
  guidance: SessionGuidance
}


export function SessionGuidancePanel({
  guidance,
}: Props) {
  return (
    <div className="space-y-5">
      <section>
        <div
          className="
            mb-3
            flex
            items-center
            justify-between
          "
        >
          <div>
            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-primary
              "
            >
              Séance
            </p>

            <h3
              className="
                mt-0.5
                font-bold
                text-base-content
              "
            >
              Déroulé
            </h3>
          </div>

          <span
            className="
              badge
              badge-primary
              badge-outline
            "
          >
            3 étapes
          </span>
        </div>

        <div className="space-y-4">
          <ExecutionStage
            number={1}
            title="Échauffement"
            steps={
              guidance.warmup
            }
          />

          <ExecutionStage
            number={2}
            title="Cœur de séance"
            steps={
              guidance.main_set
            }
            emphasized
          />

          <ExecutionStage
            number={3}
            title="Retour au calme"
            steps={
              guidance.cooldown
            }
          />
        </div>
      </section>

      <details
        className="
          overflow-hidden
          rounded-xl
          border
          border-base-300
          bg-base-100
        "
      >
        <summary
          className="
            cursor-pointer
            list-none
            px-4 py-3
            font-semibold
            text-base-content
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
            <span>
              Conseils & contexte
            </span>

            <span
              className="
                text-xs
                font-normal
                text-base-content/45
              "
            >
              Objectif, terrain, conseils
            </span>
          </div>
        </summary>

        <div
          className="
            space-y-5
            border-t
            border-base-300
            p-4
          "
        >
          <section
            className="
              rounded-xl
              border
              border-primary/20
              bg-primary/5
              p-4
            "
          >
            <div
              className="
                flex
                items-start
                gap-3
              "
            >
              <Target
                size={18}
                className="
                  mt-0.5
                  shrink-0
                  text-primary
                "
              />

              <div>
                <p
                  className="
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-primary
                  "
                >
                  Objectif
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    font-semibold
                    leading-6
                    text-base-content
                  "
                >
                  {guidance.objective}
                </p>
              </div>
            </div>
          </section>

          <GuidanceSection
            title="Pourquoi ?"
            icon={
              <Brain size={18} />
            }
          >
            <p>
              {guidance.coach_rationale}
            </p>
          </GuidanceSection>

          <GuidanceSection
            title="Terrain"
            icon={
              <MapPin size={18} />
            }
          >
            <p>
              {
                guidance
                  .terrain_recommendation
              }
            </p>
          </GuidanceSection>

          {guidance.preparation.length > 0 && (
            <GuidanceSection
              title="Avant"
              icon={
                <CheckCircle2
                  size={18}
                />
              }
            >
              <BulletList
                values={
                  guidance.preparation
                }
              />
            </GuidanceSection>
          )}

          {guidance.execution_advice.length > 0 && (
            <GuidanceSection
              title="Conseils"
              icon={
                <Gauge size={18} />
              }
            >
              <BulletList
                values={
                  guidance
                    .execution_advice
                }
              />
            </GuidanceSection>
          )}

          {guidance.warnings.length > 0 && (
            <section
              className="
                rounded-xl
                border
                border-warning/30
                bg-warning/5
                p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-2
                "
              >
                <AlertTriangle
                  size={18}
                  className="
                    text-warning
                  "
                />

                <h3
                  className="
                    font-bold
                    text-base-content
                  "
                >
                  À éviter
                </h3>
              </div>

              <div
                className="
                  mt-3
                  text-sm
                  leading-6
                  text-base-content/65
                "
              >
                <BulletList
                  values={
                    guidance.warnings
                  }
                />
              </div>
            </section>
          )}

          {guidance.analysis_targets.length > 0 && (
            <div
              className="
                flex
                flex-wrap
                gap-2
              "
            >
              {
                guidance
                  .analysis_targets
                  .map(
                    (target) => (
                      <span
                        key={target}
                        className="
                          badge
                          badge-outline
                          badge-sm
                        "
                      >
                        {
                          formatAnalysisTarget(
                            target,
                          )
                        }
                      </span>
                    ),
                  )
              }
            </div>
          )}
        </div>
      </details>
    </div>
  )
}


function ExecutionStage({
  number,
  title,
  steps,
  emphasized = false,
}: {
  number: number
  title: string
  steps: SessionGuidanceStep[]
  emphasized?: boolean
}) {
  return (
    <section
      className={[
        (
          'rounded-xl border '
          + 'p-3 sm:p-4'
        ),
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
          mb-3
          flex
          items-center
          gap-3
        "
      >
        <span
          className={[
            (
              'flex size-7 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-full '
              + 'text-xs font-bold'
            ),
            emphasized
              ? (
                'bg-primary '
                + 'text-primary-content'
              )
              : (
                'bg-base-200 '
                + 'text-base-content/60'
              ),
          ].join(' ')}
        >
          {number}
        </span>

        <h3
          className="
            font-bold
            text-base-content
          "
        >
          {title}
        </h3>
      </div>

      {steps.length > 0 ? (
        <div className="space-y-3">
          {steps.map(
            (
              step,
              index,
            ) => (
              <GuidanceStepCard
                key={
                  `${step.title}-${index}`
                }
                step={step}
                emphasized={
                  emphasized
                }
              />
            ),
          )}
        </div>
      ) : (
        <p
          className="
            text-sm
            text-base-content/45
          "
        >
          Aucune consigne spécifique.
        </p>
      )}
    </section>
  )
}


function GuidanceSection({
  title,
  icon,
  children,
}: {
  title: string
  icon?: ReactNode
  children: ReactNode
}) {
  return (
    <section>
      <div
        className="
          mb-3
          flex items-center
          gap-2
        "
      >
        {icon && (
          <span
            className="
              text-primary
            "
          >
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
          text-sm
          leading-6
          text-base-content/65
        "
      >
        {children}
      </div>
    </section>
  )
}



function GuidanceStepCard({
  step,
  emphasized,
}: {
  step: SessionGuidanceStep
  emphasized: boolean
}) {
  return (
    <div
      className={[
        'rounded-2xl border p-4',
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
          flex
          flex-wrap
          items-start
          justify-between
          gap-2
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

        <div
          className="
            flex flex-wrap
            gap-1.5
          "
        >
          {step.duration_minutes
            != null && (
              <span
                className="
                  badge
                  badge-outline
                  badge-sm
                  gap-1
                "
              >
                <Clock3
                  size={11}
                />

                {
                  step.duration_minutes
                } min
              </span>
            )}

          {step.repetitions
            != null && (
              <span
                className="
                  badge
                  badge-outline
                  badge-sm
                "
              >
                {
                  step.repetitions
                } répétitions
              </span>
            )}
        </div>
      </div>


      <p
        className="
          mt-2
          text-sm
          leading-6
          text-base-content/60
        "
      >
        {step.description}
      </p>


      {(
        step.repetition_fast_seconds
        != null
        && step.repetition_slow_seconds
        != null
      ) && (
        <div
          className="
            mt-3
            rounded-xl
            bg-base-200/60
            px-3 py-2.5
          "
        >
          <p
            className="
              text-xs
              text-base-content/45
            "
          >
            Cible par répétition
          </p>

          <p
            className="
              mt-0.5
              font-semibold
              text-base-content
            "
          >
            {
              formatDuration(
                step.repetition_fast_seconds,
              )
            }
            {'–'}
            {
              formatDuration(
                step.repetition_slow_seconds,
              )
            }
          </p>
        </div>
      )}

      {step.recovery_description && (
        <p
          className="
            mt-2
            text-xs
            text-base-content/50
          "
        >
          Récupération · {
            step.recovery_description
          }
        </p>
      )}


      {step.intensity_targets.length
        > 0 && (
          <IntensityTargets
            targets={
              step.intensity_targets
            }
          />
        )}


      {(
        step.intensity_targets.length
        === 0
        && (
          step.intensity_target
          || step.heart_rate_target
          || step.recovery_description
        )
      ) && (
        <div
          className="
            mt-3
            flex flex-wrap
            gap-2
          "
        >
          {step.intensity_target && (
            <span
              className="
                badge
                badge-primary
                badge-outline
                badge-sm
              "
            >
              Intensité · {
                formatIntensity(
                  step.intensity_target,
                )
              }
            </span>
          )}

          {step.heart_rate_target && (
            <span
              className="
                badge
                badge-secondary
                badge-outline
                badge-sm
              "
            >
              FC · {
                step.heart_rate_target
              }
            </span>
          )}

          {step.recovery_description && (
            <span
              className="
                badge
                badge-outline
                badge-sm
              "
            >
              Récupération · {
                step.recovery_description
              }
            </span>
          )}
        </div>
      )}
    </div>
  )
}


function IntensityTargets({
  targets,
}: {
  targets:
    SessionGuidanceIntensityTarget[]
}) {
  const heartRate = targets.find(
    (target) =>
      target.reference
      === 'heart_rate'
      || target.reference
      === 'heart_rate_reserve',
  )

  const vma = targets.find(
    (target) =>
      target.reference
      === 'vma_percent',
  )

  const rpe = targets.find(
    (target) =>
      target.reference
      === 'rpe',
  )

  return (
    <div
      className="
        mt-4
        grid gap-2
        sm:grid-cols-2
      "
    >
      {heartRate && (
        <IntensityValue
          title="Fréquence cardiaque"
          value={
            formatRange(
              heartRate.minimum,
              heartRate.maximum,
              'bpm',
            )
          }
        />
      )}

      {vma && (
        <IntensityValue
          title="VMA"
          value={
            formatRange(
              vma.minimum,
              vma.maximum,
              '%',
            )
          }
        />
      )}

      {vma?.speed_min_kmh
        != null
        && vma.speed_max_kmh
        != null && (
          <IntensityValue
            title="Vitesse"
            value={
              `${formatDecimal(
                vma.speed_min_kmh,
              )}–${formatDecimal(
                vma.speed_max_kmh,
              )} km/h`
            }
          />
        )}

      {vma?.pace_fastest_seconds_per_km
        != null
        && vma.pace_slowest_seconds_per_km
        != null && (
          <IntensityValue
            title="Allure"
            value={
              `${formatPace(
                vma.pace_slowest_seconds_per_km,
              )}–${formatPace(
                vma.pace_fastest_seconds_per_km,
              )} /km`
            }
          />
        )}

      {rpe && (
        <IntensityValue
          title="Effort perçu"
          value={
            formatRange(
              rpe.minimum,
              rpe.maximum,
              '/10',
            )
          }
        />
      )}
    </div>
  )
}


function IntensityValue({
  title,
  value,
}: {
  title: string
  value: string
}) {
  return (
    <div
      className="
        rounded-xl
        bg-base-200/60
        px-3 py-2.5
      "
    >
      <p
        className="
          text-xs
          text-base-content/45
        "
      >
        {title}
      </p>

      <p
        className="
          mt-0.5
          font-semibold
          text-base-content
        "
      >
        {value}
      </p>
    </div>
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
        list-disc
        space-y-2
        pl-5
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


function formatRange(
  minimum: number,
  maximum: number,
  unit: string,
): string {
  return (
    `${formatDecimal(minimum)}`
    + `–${formatDecimal(maximum)} `
    + unit
  )
}


function formatDecimal(
  value: number,
): string {
  return new Intl.NumberFormat(
    'fr-FR',
    {
      maximumFractionDigits: 1,
    },
  ).format(
    value,
  )
}


function formatDuration(
  seconds: number,
): string {
  if (seconds < 60) {
    return (
      `${new Intl.NumberFormat(
        'fr-FR',
        {
          maximumFractionDigits: 1,
        },
      ).format(seconds)} s`
    )
  }

  const rounded = Math.round(
    seconds,
  )

  const minutes = Math.floor(
    rounded / 60,
  )

  const remaining =
    rounded % 60

  return (
    `${minutes}:`
    + `${remaining}`
      .padStart(
        2,
        '0',
      )
  )
}


function formatPace(
  secondsPerKm: number,
): string {
  const rounded = Math.round(
    secondsPerKm,
  )

  const minutes = Math.floor(
    rounded / 60,
  )

  const seconds =
    rounded % 60

  return (
    `${minutes}:`
    + `${seconds}`
      .padStart(
        2,
        '0',
      )
  )
}


function formatIntensity(
  value: string,
): string {
  const labels:
    Record<string, string> = {
      easy: 'Facile',
      moderate: 'Modérée',
      hard: 'Élevée',
      very_hard: 'Très élevée',
      'très facile':
        'Très facile',
      facile: 'Facile',
    }

  return (
    labels[value]
    ?? value
  )
}


function formatAnalysisTarget(
  value: string,
): string {
  const labels:
    Record<string, string> = {
      duration: 'Durée',
      distance: 'Distance',
      pace: 'Allure',
      speed: 'Vitesse',
      heart_rate:
        'Fréquence cardiaque',
      max_heart_rate:
        'FC maximale',
      heart_rate_drift:
        'Dérive cardiaque',
      elevation_gain: 'D+',
      elevation_loss: 'D−',
      interval_consistency:
        'Régularité',
      recovery: 'Récupération',
      cadence: 'Cadence',
      nutrition: 'Nutrition',
      training_load:
        'Charge',
      completion:
        'Réalisation',
      perceived_effort:
        'Ressenti',
      wellness:
        'Bien-être',
      fatigue: 'Fatigue',
      sleep: 'Sommeil',
    }

  return (
    labels[value]
    ?? value.replaceAll(
      '_',
      ' ',
    )
  )
}
