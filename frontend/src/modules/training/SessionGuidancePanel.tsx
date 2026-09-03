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
    <div className="training-guidance-v3">
      <div
        className="
          divide-y
          divide-black/[0.06] dark:divide-white/[0.07]
        "
      >
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

      <details
        className="
          workout-coach-context
          overflow-hidden
          rounded-xl
          border
          border-black/[0.06] dark:border-white/[0.07]
          bg-white dark:bg-[#141a1e]
        "
      >
        <summary
          className="
            cursor-pointer
            list-none
            px-4 py-3
            font-semibold
            text-slate-900 dark:text-slate-100
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
                text-slate-400 dark:text-slate-500
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
            border-black/[0.06] dark:border-white/[0.07]
            p-4
          "
        >
          <section
            className="
              workout-objective-card
              rounded-xl
              border
              border-emerald-500/20 dark:border-emerald-400/20
              bg-emerald-500/[0.045] dark:bg-emerald-400/[0.055]
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
                  text-emerald-600 dark:text-emerald-400
                "
              />

              <div>
                <p
                  className="
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-emerald-600 dark:text-emerald-400
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
                    text-slate-900 dark:text-slate-100
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
                border-amber-500/20 dark:border-amber-400/20
                bg-amber-500/[0.05] dark:bg-amber-400/[0.055]
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
                    text-amber-600 dark:text-amber-400
                  "
                />

                <h3
                  className="
                    font-bold
                    text-slate-900 dark:text-slate-100
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
                  text-slate-600 dark:text-slate-300
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
                          inline-flex
                          items-center
                          rounded-full
                          border
                          border-black/[0.08]
                          bg-white
                          px-2.5
                          py-1
                          text-[10.5px]
                          font-medium
                          text-slate-500
                          dark:border-white/[0.09]
                          dark:bg-white/[0.025]
                          dark:text-slate-400
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
      className="
        training-guidance-v3__stage
        relative
        pb-4
        last:pb-0
      "
    >
      <div
        className="
          flex
          items-center
          gap-2.5
        "
      >
        <span
          className={[
            (
              'relative z-10 '
              + 'flex size-6 shrink-0 '
              + 'items-center justify-center '
              + 'rounded-full border '
              + 'text-[9.5px] font-bold'
            ),
            emphasized
              ? (
                  'border-emerald-500 '
                  + 'bg-emerald-500 '
                  + 'text-white'
                )
              : (
                  'border-slate-200 '
                  + 'bg-white '
                  + 'text-slate-500 '
                  + 'dark:border-white/[0.10] '
                  + 'dark:bg-[#151b1f] '
                  + 'dark:text-slate-400'
                ),
          ].join(' ')}
        >
          {number}
        </span>

        <h3
          className={[
            (
              'text-[11.5px] '
              + 'font-bold uppercase '
              + 'tracking-[0.055em]'
            ),
            emphasized
              ? (
                  'text-emerald-700 '
                  + 'dark:text-emerald-400'
                )
              : (
                  'text-slate-800 '
                  + 'dark:text-slate-200'
                ),
          ].join(' ')}
        >
          {title}
        </h3>
      </div>


      <div
        aria-hidden="true"
        className="
          absolute
          bottom-0
          left-[11.5px]
          top-7
          w-px
          bg-slate-200
          dark:bg-white/[0.07]
        "
      />


      <div
        className="
          ml-8
          mt-1.5
        "
      >
        {steps.length > 0 ? (
          <div className="space-y-2.5">
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
                  stageTitle={title}
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
              text-[11px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Aucune consigne spécifique.
          </p>
        )}
      </div>
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
              text-emerald-600 dark:text-emerald-400
            "
          >
            {icon}
          </span>
        )}

        <h3
          className="
            font-bold
            text-slate-900 dark:text-slate-100
          "
        >
          {title}
        </h3>
      </div>

      <div
        className="
          text-sm
          leading-6
          text-slate-600 dark:text-slate-300
        "
      >
        {children}
      </div>
    </section>
  )
}



function GuidanceStepCard({
  step,
  stageTitle,
  emphasized,
}: {
  step: SessionGuidanceStep
  stageTitle: string
  emphasized: boolean
}) {
  const hasIntervalStructure = (
    step.repetitions != null
    && step.work_distance_meters != null
  )

  const hasRepetitionDuration = (
    step.repetition_fast_seconds != null
    && step.repetition_slow_seconds != null
  )

  const showTitle =
    !isRedundantStepTitle(
      stageTitle,
      step.title,
    )

  return (
    <div
      className={[
        (
          'training-guidance-v3__step '
          + 'min-w-0'
        ),
        emphasized
          ? (
              'rounded-[10px] '
              + 'border border-emerald-500/15 '
              + 'bg-emerald-500/[0.025] '
              + 'px-3 py-2.5 '
              + 'dark:border-emerald-400/15 '
              + 'dark:bg-emerald-400/[0.03]'
            )
          : (
              'py-1'
            ),
      ].join(' ')}
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-3
        "
      >
        <div className="min-w-0">
          {showTitle && (
            <p
              className="
                text-[12px]
                font-semibold
                leading-5
                text-slate-900
                dark:text-slate-100
              "
            >
              {step.title}
            </p>
          )}

          {step.description && (
            <p
              className={[
                (
                  'text-[10.5px] leading-[1.5] '
                  + 'text-slate-500 '
                  + 'dark:text-slate-400'
                ),
                showTitle
                  ? 'mt-1'
                  : '',
              ].join(' ')}
            >
              {step.description}
            </p>
          )}
        </div>


        {step.duration_minutes != null && (
          <span
            className="
              inline-flex
              shrink-0
              items-center
              gap-1
              rounded-[6px]
              bg-slate-100
              px-1.5
              py-0.5
              text-[9px]
              font-semibold
              text-slate-500
              dark:bg-white/[0.055]
              dark:text-slate-400
            "
          >
            <Clock3
              size={10}
            />

            {step.duration_minutes} min
          </span>
        )}
      </div>


      {hasIntervalStructure && (
        <div
          className="
            mt-2.5
            border-t
            border-black/[0.055]
            pt-2.5
            dark:border-white/[0.06]
          "
        >
          <div
            className="
              flex
              flex-wrap
              items-baseline
              justify-between
              gap-x-3
              gap-y-1
            "
          >
            <div>
              <p
                className="
                  text-[8.5px]
                  font-bold
                  uppercase
                  tracking-[0.09em]
                  text-emerald-600
                  dark:text-emerald-400
                "
              >
                Effort
              </p>

              <p
                className="
                  mt-0.5
                  text-[12px]
                  font-semibold
                  text-slate-900
                  dark:text-slate-100
                "
              >
                {step.work_distance_meters} m
                {' '}
                / répétition
              </p>
            </div>


            {hasRepetitionDuration && (
              <p
                className="
                  text-[11px]
                  font-semibold
                  text-slate-500
                  dark:text-slate-400
                "
              >
                {
                  formatDuration(
                    step.repetition_fast_seconds!,
                  )
                }
                {'–'}
                {
                  formatDuration(
                    step.repetition_slow_seconds!,
                  )
                }
              </p>
            )}
          </div>


          {step.intensity_targets.length > 0 && (
            <IntensityTargets
              targets={
                step.intensity_targets
              }
            />
          )}


          {(
            step.intensity_targets.length === 0
            && (
              step.intensity_target
              || step.heart_rate_target
            )
          ) && (
            <div
              className="
                mt-2.5
                flex
                flex-wrap
                gap-x-4
                gap-y-1.5
              "
            >
              {step.intensity_target && (
                <CompactTarget
                  label="Intensité"
                  value={
                    formatIntensity(
                      step.intensity_target,
                    )
                  }
                />
              )}

              {step.heart_rate_target && (
                <CompactTarget
                  label="FC"
                  value={
                    step.heart_rate_target
                  }
                />
              )}
            </div>
          )}


          {step.recovery_description && (
            <div
              className="
                mt-1.5
                flex
                flex-wrap
                items-center
                gap-1.5
                border-t
                border-black/[0.055]
                pt-2
                dark:border-white/[0.06]
              "
            >
              <span
                className="
                  rounded-[5px]
                  bg-emerald-500/[0.08]
                  px-1.5
                  py-0.5
                  text-[8.5px]
                  font-bold
                  uppercase
                  tracking-[0.035em]
                  text-emerald-700
                  dark:bg-emerald-400/[0.08]
                  dark:text-emerald-400
                "
              >
                Récupération
              </span>

              <span
                className="
                  text-[10.5px]
                  font-semibold
                  text-slate-700
                  dark:text-slate-200
                "
              >
                {step.recovery_description}
              </span>
            </div>
          )}
        </div>
      )}


      {(
        !hasIntervalStructure
        && hasRepetitionDuration
      ) && (
        <div
          className="
            mt-2.5
            flex
            items-baseline
            justify-between
            gap-3
            border-t
            border-black/[0.055]
            pt-2
            dark:border-white/[0.06]
          "
        >
          <span
            className="
              text-[9px]
              font-semibold
              uppercase
              tracking-[0.06em]
              text-slate-400
            "
          >
            Cible
          </span>

          <span
            className="
              text-[11.5px]
              font-semibold
              text-slate-800
              dark:text-slate-200
            "
          >
            {
              formatDuration(
                step.repetition_fast_seconds!,
              )
            }
            {'–'}
            {
              formatDuration(
                step.repetition_slow_seconds!,
              )
            }
          </span>
        </div>
      )}


      {(
        !hasIntervalStructure
        && step.intensity_targets.length > 0
      ) && (
        <IntensityTargets
          targets={
            step.intensity_targets
          }
        />
      )}


      {(
        !hasIntervalStructure
        && step.intensity_targets.length === 0
        && (
          step.intensity_target
          || step.heart_rate_target
          || step.recovery_description
        )
      ) && (
        <div
          className="
            mt-2
            flex
            flex-wrap
            gap-x-4
            gap-y-1.5
          "
        >
          {step.intensity_target && (
            <CompactTarget
              label="Intensité"
              value={
                formatIntensity(
                  step.intensity_target,
                )
              }
            />
          )}

          {step.heart_rate_target && (
            <CompactTarget
              label="FC"
              value={
                step.heart_rate_target
              }
            />
          )}

          {step.recovery_description && (
            <CompactTarget
              label="Récupération"
              value={
                step.recovery_description
              }
            />
          )}
        </div>
      )}
    </div>
  )
}


function CompactTarget({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <span
      className="
        text-[10px]
        text-slate-500
        dark:text-slate-400
      "
    >
      <span
        className="
          font-semibold
          text-slate-700
          dark:text-slate-300
        "
      >
        {label}
      </span>

      {' · '}

      {value}
    </span>
  )
}


function isRedundantStepTitle(
  stageTitle: string,
  stepTitle: string,
): boolean {
  const normalize = (
    value: string,
  ) => (
    value
      .normalize('NFD')
      .replace(
        /[\u0300-\u036f]/g,
        '',
      )
      .trim()
      .toLowerCase()
  )

  const stage =
    normalize(
      stageTitle,
    )

  const step =
    normalize(
      stepTitle,
    )


  if (stage === step) {
    return true
  }


  if (
    stage === 'echauffement'
    && (
      step === 'course facile'
      || step === 'mise en route'
    )
  ) {
    return true
  }


  if (
    stage === 'retour au calme'
    && (
      step === 'course facile'
      || step === 'footing facile'
      || step === 'recuperation'
    )
  ) {
    return true
  }


  return false
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

  const values = [
    heartRate
      ? {
          title: 'FC',
          value: formatRange(
            heartRate.minimum,
            heartRate.maximum,
            'bpm',
          ),
        }
      : null,

    vma
      ? {
          title: 'VMA',
          value: formatRange(
            vma.minimum,
            vma.maximum,
            '%',
          ),
        }
      : null,

    (
      vma?.speed_min_kmh != null
      && vma.speed_max_kmh != null
    )
      ? {
          title: 'Vitesse',
          value: (
            `${formatDecimal(
              vma.speed_min_kmh,
            )}–${formatDecimal(
              vma.speed_max_kmh,
            )} km/h`
          ),
        }
      : null,

    (
      vma?.pace_fastest_seconds_per_km != null
      && vma.pace_slowest_seconds_per_km != null
    )
      ? {
          title: 'Allure',
          value: (
            `${formatPace(
              vma.pace_slowest_seconds_per_km,
            )}–${formatPace(
              vma.pace_fastest_seconds_per_km,
            )}/km`
          ),
        }
      : null,

    rpe
      ? {
          title: 'Effort',
          value: formatRange(
            rpe.minimum,
            rpe.maximum,
            '/10',
          ),
        }
      : null,
  ].filter(
    (
      item,
    ): item is {
      title: string
      value: string
    } => item !== null,
  )

  return (
    <div
      className="
        mt-2.5
        flex
        flex-wrap
        items-center
        gap-x-2
        gap-y-1.5
        border-t
        border-black/[0.055]
        pt-2.5
        dark:border-white/[0.06]
      "
    >
      {values.map(
        (
          item,
          index,
        ) => (
          <div
            key={
              item.title
            }
            className="
              flex
              items-center
              gap-2
            "
          >
            {index > 0 && (
              <span
                aria-hidden="true"
                className="
                  hidden
                  text-[9px]
                  text-slate-300
                  sm:inline
                  dark:text-slate-600
                "
              >
                •
              </span>
            )}

            <IntensityValue
              title={
                item.title
              }
              value={
                item.value
              }
            />
          </div>
        ),
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
        inline-flex
        items-center
        gap-1.5
        whitespace-nowrap
      "
    >
      <span
        className="
          rounded-[5px]
          bg-slate-100
          px-1.5
          py-0.5
          text-[8.5px]
          font-bold
          uppercase
          tracking-[0.035em]
          text-slate-500
          dark:bg-white/[0.055]
          dark:text-slate-400
        "
      >
        {title}
      </span>

      <span
        className="
          text-[10.5px]
          font-semibold
          text-slate-700
          dark:text-slate-200
        "
      >
        {value}
      </span>
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
