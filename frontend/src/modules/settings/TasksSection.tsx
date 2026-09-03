import {
  Activity,
  CalendarClock,
  CheckCircle2,
  CircleAlert,
  Clock3,
  LoaderCircle,
  RefreshCw,
  TimerOff,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  fetchAutomatedTasks,
  type AutomatedTask,
  type AutomatedTaskStatus,
} from './tasksApi'


export function TasksSection() {
  const [
    tasks,
    setTasks,
  ] = useState<
    AutomatedTask[]
  >([])

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    refreshing,
    setRefreshing,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null)


  const loadTasks =
    useCallback(
      async (
        refresh = false,
      ) => {
        if (refresh) {
          setRefreshing(true)
        }

        try {
          const result =
            await fetchAutomatedTasks()

          setTasks(result)
          setError(null)
        } catch (reason) {
          setError(
            reason instanceof Error
              ? reason.message
              : (
                  'Impossible de charger '
                  + 'les tâches.'
                ),
          )
        } finally {
          setLoading(false)
          setRefreshing(false)
        }
      },
      [],
    )


  useEffect(() => {
    void loadTasks()
  }, [
    loadTasks,
  ])


  const summary =
    useMemo(
      () =>
        buildSummary(
          tasks,
          error,
        ),
      [
        tasks,
        error,
      ],
    )


  const okCount =
    tasks.filter(
      task =>
        task.status === 'ok',
    ).length

  const problemCount =
    tasks.filter(
      task =>
        (
          task.status === 'error'
          || task.status === 'inactive'
        ),
    ).length


  if (loading) {
    return (
      <div
        className="
          flex
          min-h-[190px]
          items-center
          justify-center
          rounded-[12px]
          border
          border-black/[0.065]
          bg-white
          dark:border-white/[0.065]
          dark:bg-[#151b1f]
        "
      >
        <div
          className="
            flex
            items-center
            gap-2
            text-[10.5px]
            text-slate-400
          "
        >
          <LoaderCircle
            className="
              h-4
              w-4
              animate-spin
              text-emerald-500
            "
          />

          Chargement des automatisations…
        </div>
      </div>
    )
  }


  return (
    <div className="space-y-3">

      {/* =============================================
          OVERVIEW
          ============================================= */}

      <section
        className="
          overflow-hidden
          rounded-[12px]
          border
          border-black/[0.065]
          bg-white
          dark:border-white/[0.065]
          dark:bg-[#151b1f]
        "
      >
        <div
          className="
            relative
            overflow-hidden
            px-4
            py-4
          "
        >
          <div
            className="
              pointer-events-none
              absolute
              -right-16
              -top-20
              h-44
              w-44
              rounded-full
              bg-emerald-500/[0.05]
              blur-3xl
            "
          />

          <div
            className="
              relative
              flex
              items-start
              justify-between
              gap-3
            "
          >
            <div
              className="
                flex
                min-w-0
                items-start
                gap-3
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
                  rounded-[11px]
                  bg-emerald-50
                  text-emerald-600
                  dark:bg-emerald-500/[0.08]
                  dark:text-emerald-400
                "
              >
                <Clock3
                  className="
                    h-[18px]
                    w-[18px]
                  "
                />
              </div>

              <div>
                <div
                  className="
                    flex
                    flex-wrap
                    items-center
                    gap-2
                  "
                >
                  <h3
                    className="
                      text-[14px]
                      font-bold
                      tracking-[-0.02em]
                      text-slate-950
                      dark:text-white
                    "
                  >
                    Automatisations
                  </h3>

                  <SummaryStatus
                    status={
                      summary.status
                    }
                    label={
                      summary.label
                    }
                  />
                </div>

                <p
                  className="
                    mt-1
                    text-[10px]
                    text-slate-400
                    dark:text-slate-500
                  "
                >
                  Tâches système exécutées
                  automatiquement par OpenCoach.
                </p>
              </div>
            </div>


            <button
              type="button"
              disabled={refreshing}
              onClick={() =>
                void loadTasks(true)
              }
              className="
                flex
                h-8
                shrink-0
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-emerald-500/35
                px-2.5
                text-[9.5px]
                font-semibold
                text-emerald-700
                transition
                hover:border-emerald-500/55
                hover:bg-emerald-50
                disabled:opacity-40
                dark:border-emerald-400/30
                dark:text-emerald-400
                dark:hover:bg-emerald-500/[0.07]
              "
            >
              {
                refreshing
                  ? (
                      <LoaderCircle
                        className="
                          h-3
                          w-3
                          animate-spin
                        "
                      />
                    )
                  : (
                      <RefreshCw
                        className="
                          h-3
                          w-3
                        "
                      />
                    )
              }

              Actualiser
            </button>
          </div>
        </div>


        <div
          className="
            grid
            grid-cols-3
            border-t
            border-black/[0.055]
            dark:border-white/[0.06]
          "
        >
          <SummaryMetric
            label="Tâches"
            value={
              String(tasks.length)
            }
          />

          <SummaryMetric
            label="Opérationnelles"
            value={
              String(okCount)
            }
          />

          <SummaryMetric
            label="À surveiller"
            value={
              String(problemCount)
            }
          />
        </div>
      </section>


      {/* =============================================
          ERROR
          ============================================= */}

      {error && (
        <div
          className="
            flex
            items-start
            gap-2
            rounded-[10px]
            border
            border-red-500/15
            bg-red-50
            px-3
            py-2.5
            text-[10px]
            text-red-600
            dark:bg-red-500/[0.06]
            dark:text-red-400
          "
        >
          <CircleAlert
            className="
              mt-px
              h-3.5
              w-3.5
              shrink-0
            "
          />

          {error}
        </div>
      )}


      {/* =============================================
          TASK LIST
          ============================================= */}

      {!error && (
        <section
          className="
            overflow-hidden
            rounded-[12px]
            border
            border-black/[0.065]
            bg-white
            dark:border-white/[0.065]
            dark:bg-[#151b1f]
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              gap-3
              border-b
              border-black/[0.055]
              px-4
              py-3
              dark:border-white/[0.06]
            "
          >
            <div>
              <p
                className="
                  text-[9px]
                  font-bold
                  uppercase
                  tracking-[0.1em]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Planification
              </p>

              <p
                className="
                  mt-1
                  text-[11.5px]
                  font-semibold
                  text-slate-800
                  dark:text-slate-200
                "
              >
                Tâches programmées
              </p>
            </div>

            <span
              className="
                text-[9px]
                text-slate-400
                dark:text-slate-500
              "
            >
              {tasks.length}
            </span>
          </div>


          {tasks.length === 0 ? (
            <div
              className="
                px-4
                py-6
                text-center
              "
            >
              <TimerOff
                className="
                  mx-auto
                  h-5
                  w-5
                  text-slate-200
                  dark:text-slate-700
                "
              />

              <p
                className="
                  mt-2
                  text-[10px]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Aucune tâche OpenCoach détectée.
              </p>
            </div>
          ) : (
            <div>
              {tasks.map(
                (
                  task,
                  index,
                ) => (
                  <TaskRow
                    key={
                      task.unit
                    }
                    task={task}
                    divided={
                      index > 0
                    }
                  />
                ),
              )}
            </div>
          )}
        </section>
      )}
    </div>
  )
}


function TaskRow({
  task,
  divided,
}: {
  task: AutomatedTask
  divided: boolean
}) {
  const config =
    getStatusConfig(
      task.status,
    )

  const Icon =
    config.icon

  return (
    <div
      className={[
        (
          'grid gap-3 px-4 py-3.5 '
          + 'sm:grid-cols-[minmax(0,1fr)_180px] '
          + 'sm:items-center'
        ),
        divided
          ? (
              'border-t '
              + 'border-black/[0.055] '
              + 'dark:border-white/[0.06]'
            )
          : '',
      ].join(' ')}
    >
      <div
        className="
          flex
          min-w-0
          items-start
          gap-3
        "
      >
        <div
          className={[
            (
              'flex h-9 w-9 '
              + 'shrink-0 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-[10px]'
            ),
            config.iconClassName,
          ].join(' ')}
        >
          <Icon
            className="
              h-4
              w-4
            "
          />
        </div>

        <div
          className="
            min-w-0
            flex-1
          "
        >
          <div
            className="
              flex
              flex-wrap
              items-center
              gap-2
            "
          >
            <p
              className="
                truncate
                text-[11px]
                font-semibold
                text-slate-800
                dark:text-slate-200
              "
            >
              {task.label}
            </p>

            <TaskStatus
              status={
                task.status
              }
            />
          </div>

          <div
            className="
              mt-1.5
              flex
              items-center
              gap-1.5
              text-[9px]
              text-slate-400
              dark:text-slate-500
            "
          >
            <Activity
              className="
                h-3
                w-3
              "
            />

            Dernière exécution :

            <span
              className="
                font-medium
                text-slate-500
                dark:text-slate-400
              "
            >
              {
                formatSystemdDate(
                  task.last_run,
                )
              }
            </span>
          </div>
        </div>
      </div>


      <div
        className="
          rounded-[9px]
          bg-slate-50
          px-3
          py-2
          dark:bg-white/[0.025]
        "
      >
        <div
          className="
            flex
            items-center
            gap-1.5
          "
        >
          <CalendarClock
            className="
              h-3
              w-3
              text-emerald-500
            "
          />

          <p
            className="
              text-[8px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-slate-400
              dark:text-slate-500
            "
          >
            Prochaine exécution
          </p>
        </div>

        <p
          className="
            mt-1
            text-[10.5px]
            font-semibold
            tabular-nums
            text-slate-700
            dark:text-slate-300
          "
        >
          {
            formatSystemdDate(
              task.next_run,
            )
          }
        </p>
      </div>
    </div>
  )
}


function SummaryMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        px-3
        py-3
        text-center
        not-last:border-r
        not-last:border-black/[0.055]
        dark:not-last:border-white/[0.06]
      "
    >
      <p
        className="
          text-[14px]
          font-bold
          tabular-nums
          text-slate-800
          dark:text-slate-200
        "
      >
        {value}
      </p>

      <p
        className="
          mt-1
          text-[8px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </p>
    </div>
  )
}


function TaskStatus({
  status,
}: {
  status:
    AutomatedTaskStatus
}) {
  const config =
    getStatusConfig(status)

  return (
    <span
      className={[
        (
          'inline-flex items-center '
          + 'gap-1 rounded-full '
          + 'px-1.5 py-0.5 '
          + 'text-[8px] '
          + 'font-semibold'
        ),
        config.badgeClassName,
      ].join(' ')}
    >
      <span
        className={[
          (
            'h-1.5 w-1.5 '
            + 'rounded-full'
          ),
          config.dotClassName,
        ].join(' ')}
      />

      {config.label}
    </span>
  )
}


function SummaryStatus({
  status,
  label,
}: {
  status:
    | AutomatedTaskStatus
    | 'empty'
  label: string
}) {
  const className =
    status === 'ok'
      ? (
          'bg-emerald-50 '
          + 'text-emerald-700 '
          + 'dark:bg-emerald-500/[0.08] '
          + 'dark:text-emerald-400'
        )
      : status === 'error'
        ? (
            'bg-red-50 '
            + 'text-red-600 '
            + 'dark:bg-red-500/[0.07] '
            + 'dark:text-red-400'
          )
        : status === 'inactive'
          ? (
              'bg-amber-50 '
              + 'text-amber-700 '
              + 'dark:bg-amber-500/[0.07] '
              + 'dark:text-amber-400'
            )
          : (
              'bg-slate-100 '
              + 'text-slate-400 '
              + 'dark:bg-white/[0.04] '
              + 'dark:text-slate-500'
            )

  return (
    <span
      className={[
        (
          'rounded-full '
          + 'px-1.5 py-0.5 '
          + 'text-[8px] '
          + 'font-semibold'
        ),
        className,
      ].join(' ')}
    >
      {label}
    </span>
  )
}


function buildSummary(
  tasks: AutomatedTask[],
  error: string | null,
): {
  status:
    | AutomatedTaskStatus
    | 'empty'
  label: string
} {
  if (error) {
    return {
      status: 'error',
      label: 'Erreur',
    }
  }

  if (tasks.length === 0) {
    return {
      status: 'empty',
      label: 'Aucune tâche',
    }
  }

  const errors =
    tasks.filter(
      task =>
        task.status
        === 'error',
    ).length

  if (errors > 0) {
    return {
      status: 'error',

      label:
        `${errors} erreur`
        + (
          errors > 1
            ? 's'
            : ''
        ),
    }
  }

  const inactive =
    tasks.filter(
      task =>
        task.status
        === 'inactive',
    ).length

  if (inactive > 0) {
    return {
      status: 'inactive',

      label:
        `${inactive} inactive`
        + (
          inactive > 1
            ? 's'
            : ''
        ),
    }
  }

  const pending =
    tasks.filter(
      task =>
        task.status
        === 'pending',
    ).length

  if (pending > 0) {
    return {
      status: 'pending',
      label:
        `${pending} en attente`,
    }
  }

  return {
    status: 'ok',
    label: 'Tout fonctionne',
  }
}


function getStatusConfig(
  status: AutomatedTaskStatus,
): {
  label: string
  badgeClassName: string
  iconClassName: string
  dotClassName: string
  icon:
    typeof CheckCircle2
} {
  if (status === 'ok') {
    return {
      label: 'OK',

      badgeClassName:
        (
          'bg-emerald-50 '
          + 'text-emerald-700 '
          + 'dark:bg-emerald-500/[0.08] '
          + 'dark:text-emerald-400'
        ),

      iconClassName:
        (
          'bg-emerald-50 '
          + 'text-emerald-600 '
          + 'dark:bg-emerald-500/[0.07] '
          + 'dark:text-emerald-400'
        ),

      dotClassName:
        'bg-emerald-500',

      icon:
        CheckCircle2,
    }
  }

  if (status === 'error') {
    return {
      label: 'Erreur',

      badgeClassName:
        (
          'bg-red-50 '
          + 'text-red-600 '
          + 'dark:bg-red-500/[0.07] '
          + 'dark:text-red-400'
        ),

      iconClassName:
        (
          'bg-red-50 '
          + 'text-red-500 '
          + 'dark:bg-red-500/[0.07] '
          + 'dark:text-red-400'
        ),

      dotClassName:
        'bg-red-500',

      icon:
        CircleAlert,
    }
  }

  if (status === 'inactive') {
    return {
      label: 'Inactive',

      badgeClassName:
        (
          'bg-amber-50 '
          + 'text-amber-700 '
          + 'dark:bg-amber-500/[0.07] '
          + 'dark:text-amber-400'
        ),

      iconClassName:
        (
          'bg-amber-50 '
          + 'text-amber-600 '
          + 'dark:bg-amber-500/[0.07] '
          + 'dark:text-amber-400'
        ),

      dotClassName:
        'bg-amber-500',

      icon:
        TimerOff,
    }
  }

  return {
    label: 'En attente',

    badgeClassName:
      (
        'bg-slate-100 '
        + 'text-slate-400 '
        + 'dark:bg-white/[0.04] '
        + 'dark:text-slate-500'
      ),

    iconClassName:
      (
        'bg-slate-50 '
        + 'text-slate-400 '
        + 'dark:bg-white/[0.025] '
        + 'dark:text-slate-500'
      ),

    dotClassName:
      'bg-slate-300',

    icon:
      Clock3,
  }
}


function formatSystemdDate(
  value: string | null,
): string {
  if (!value) {
    return '—'
  }

  const match =
    value.match(
      /(?:[A-Za-z]{3}\s+)?(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})(?::\d{2})?/,
    )

  if (!match) {
    return value
  }

  const [
    ,
    yearText,
    monthText,
    dayText,
    hourText,
    minuteText,
  ] = match

  const year =
    Number(yearText)

  const month =
    Number(monthText)

  const day =
    Number(dayText)

  const target =
    new Date(
      year,
      month - 1,
      day,
    )

  const today =
    new Date()

  const todayStart =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
    )

  const differenceDays =
    Math.round(
      (
        target.getTime()
        - todayStart.getTime()
      )
      / 86_400_000,
    )

  const time =
    `${hourText}:${minuteText}`

  if (differenceDays === 0) {
    return `Aujourd’hui à ${time}`
  }

  if (differenceDays === 1) {
    return `Demain à ${time}`
  }

  if (differenceDays === -1) {
    return `Hier à ${time}`
  }

  if (
    differenceDays > 1
    && differenceDays <= 6
  ) {
    const weekday =
      new Intl.DateTimeFormat(
        'fr-FR',
        {
          weekday: 'long',
        },
      ).format(target)

    return (
      `${capitalizeFirst(weekday)} `
      + `à ${time}`
    )
  }

  const formattedDate =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: 'numeric',
        month: 'long',
        year:
          year !== today.getFullYear()
            ? 'numeric'
            : undefined,
      },
    ).format(target)

  return (
    `${formattedDate} à ${time}`
  )
}


function capitalizeFirst(
  value: string,
): string {
  return (
    value.charAt(0).toUpperCase()
    + value.slice(1)
  )
}
