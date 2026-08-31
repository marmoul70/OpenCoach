import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  CheckCircle2,
  CircleAlert,
  Clock3,
  RefreshCw,
  TimerOff,
} from 'lucide-react'

import {
  ProfileSection,
} from '../profile/ProfileSection'

import {
  fetchAutomatedTasks,
  type AutomatedTask,
  type AutomatedTaskStatus,
} from './tasksApi'


export function TasksSection() {
  const [
    tasks,
    setTasks,
  ] = useState<AutomatedTask[]>(
    [],
  )

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  )

  const [
    refreshing,
    setRefreshing,
  ] = useState(
    false,
  )

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )


  const loadTasks =
    useCallback(
      async (
        refresh = false,
      ) => {
        if (refresh) {
          setRefreshing(
            true,
          )
        }

        try {
          const result =
            await fetchAutomatedTasks()

          setTasks(
            result,
          )

          setError(
            null,
          )
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
          setLoading(
            false,
          )

          setRefreshing(
            false,
          )
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


  return (
    <ProfileSection
      title="Tâches"
      description={
        'Automatisations OpenCoach.'
      }
      icon={
        <Clock3
          size={21}
        />
      }
      iconClassName="
        bg-secondary/10
        text-secondary
      "
      trailing={
        <SummaryBadge
          status={
            summary.status
          }
          label={
            summary.label
          }
        />
      }
    >
      <div
        className="
          space-y-4
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
          <p
            className="
              text-sm
              text-base-content/60
            "
          >
            {tasks.length > 0
              ? (
                `${tasks.length} tâche`
                + (
                  tasks.length > 1
                    ? 's'
                    : ''
                )
                + ' automatisée'
                + (
                  tasks.length > 1
                    ? 's'
                    : ''
                )
              )
              : 'Tâches automatisées'}
          </p>

          <button
            type="button"
            className="
              btn
              btn-ghost
              btn-sm
              gap-2
            "
            disabled={
              refreshing
            }
            onClick={() => {
              void loadTasks(
                true,
              )
            }}
          >
            {refreshing ? (
              <span
                className="
                  loading
                  loading-spinner
                  loading-xs
                "
              />
            ) : (
              <RefreshCw
                size={15}
              />
            )}

            Actualiser
          </button>
        </div>


        {loading ? (
          <div
            className="
              flex
              justify-center
              py-6
            "
          >
            <span
              className="
                loading
                loading-spinner
                loading-md
                text-secondary
              "
            />
          </div>
        ) : error ? (
          <div
            className="
              alert
              alert-error
            "
          >
            <CircleAlert
              size={18}
            />

            <span>
              {error}
            </span>
          </div>
        ) : tasks.length === 0 ? (
          <div
            className="
              rounded-xl
              bg-base-200
              p-4
              text-sm
              text-base-content/60
            "
          >
            Aucune tâche OpenCoach détectée.
          </div>
        ) : (
          <div
            className="
              divide-y
              divide-base-300
              overflow-hidden
              rounded-xl
              border
              border-base-300
              bg-base-100
            "
          >
            {tasks.map(
              (task) => (
                <TaskRow
                  key={
                    task.unit
                  }
                  task={
                    task
                  }
                />
              ),
            )}
          </div>
        )}
      </div>
    </ProfileSection>
  )
}


function TaskRow({
  task,
}: {
  task: AutomatedTask
}) {
  return (
    <div
      className="
        flex
        flex-col
        gap-3
        px-4
        py-4
        sm:flex-row
        sm:items-center
        sm:justify-between
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
        <TaskStatusIcon
          status={
            task.status
          }
        />

        <div
          className="
            min-w-0
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
            <h3
              className="
                font-semibold
                text-base-content
              "
            >
              {task.label}
            </h3>

            <TaskStatusBadge
              status={
                task.status
              }
            />
          </div>

          <p
            className="
              mt-1
              text-xs
              text-base-content/50
            "
          >
            Dernière exécution :{' '}
            {formatSystemdDate(
              task.last_run,
            )}
          </p>
        </div>
      </div>

      <div
        className="
          shrink-0
          sm:text-right
        "
      >
        <p
          className="
            text-xs
            font-medium
            uppercase
            tracking-wide
            text-base-content/40
          "
        >
          Prochaine exécution
        </p>

        <p
          className="
            mt-1
            text-sm
            font-semibold
            text-base-content
          "
        >
          {formatSystemdDate(
            task.next_run,
          )}
        </p>
      </div>
    </div>
  )
}


function TaskStatusIcon({
  status,
}: {
  status: AutomatedTaskStatus
}) {
  const config =
    getStatusConfig(
      status,
    )

  const Icon =
    config.icon

  return (
    <div
      className={[
        (
          'flex h-10 w-10 shrink-0 '
          + 'items-center justify-center '
          + 'rounded-xl'
        ),
        config.iconClassName,
      ].join(' ')}
    >
      <Icon
        size={19}
      />
    </div>
  )
}


function TaskStatusBadge({
  status,
}: {
  status: AutomatedTaskStatus
}) {
  const config =
    getStatusConfig(
      status,
    )

  return (
    <span
      className={[
        'badge badge-sm',
        config.badgeClassName,
      ].join(' ')}
    >
      {config.label}
    </span>
  )
}


function SummaryBadge({
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
      ? 'badge-success'
      : status === 'error'
        ? 'badge-error'
        : status === 'inactive'
          ? 'badge-warning'
          : 'badge-ghost'

  return (
    <span
      className={[
        'badge badge-sm font-medium',
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
      (task) =>
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
      (task) =>
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
      (task) =>
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
  icon:
    typeof CheckCircle2
} {
  if (status === 'ok') {
    return {
      label: 'OK',
      badgeClassName:
        'badge-success',
      iconClassName:
        'bg-success/10 text-success',
      icon:
        CheckCircle2,
    }
  }

  if (status === 'error') {
    return {
      label: 'Erreur',
      badgeClassName:
        'badge-error',
      iconClassName:
        'bg-error/10 text-error',
      icon:
        CircleAlert,
    }
  }

  if (status === 'inactive') {
    return {
      label: 'Inactive',
      badgeClassName:
        'badge-warning',
      iconClassName:
        'bg-warning/10 text-warning',
      icon:
        TimerOff,
    }
  }

  return {
    label: 'En attente',
    badgeClassName:
      'badge-ghost',
    iconClassName:
      (
        'bg-base-200 '
        + 'text-base-content/50'
      ),
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

  return value.replace(
    /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+/,
    '',
  )
}
