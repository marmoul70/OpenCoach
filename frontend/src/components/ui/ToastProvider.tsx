/* oxlint-disable react/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'

import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Info,
  X,
} from 'lucide-react'


type ToastType =
  | 'success'
  | 'info'
  | 'warning'
  | 'error'


interface ToastInput {
  type?: ToastType
  title: string
  message?: string
  duration?: number | null

  actionLabel?: string
  onAction?: () => void
}


interface ToastItem extends ToastInput {
  id: number
  type: ToastType
  duration: number | null
}


interface ToastContextValue {
  toast: (
    input: ToastInput,
  ) => void
}


const ToastContext =
  createContext<ToastContextValue | null>(
    null,
  )


let nextToastId = 1


export function ToastProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const [
    toasts,
    setToasts,
  ] = useState<ToastItem[]>([])

  const removeToast =
    useCallback(
      (
        id: number,
      ) => {
        setToasts(
          (current) =>
            current.filter(
              (toast) =>
                toast.id !== id,
            ),
        )
      },
      [],
    )

  const toast =
    useCallback(
      (
        input: ToastInput,
      ) => {
        const id =
          nextToastId++

        const item: ToastItem = {
          id,
          type:
            input.type
            ?? 'info',
          title:
            input.title,
          message:
            input.message,
          duration:
            input.duration !== undefined
              ? input.duration
              : 5000,

          actionLabel:
            input.actionLabel,

          onAction:
            input.onAction,
        }

        setToasts(
          (current) => [
            ...current,
            item,
          ],
        )

        if (item.duration !== null) {
          window.setTimeout(
            () => {
              removeToast(id)
            },
            item.duration,
          )
        }
      },
      [
        removeToast,
      ],
    )

  const value =
    useMemo(
      () => ({
        toast,
      }),
      [
        toast,
      ],
    )

  return (
    <ToastContext.Provider
      value={value}
    >
      {children}

      <div
        className="
          pointer-events-none
          fixed
          bottom-4
          right-4
          z-[100]
          flex
          w-[calc(100%-2rem)]
          max-w-[370px]
          flex-col
          gap-2.5
          sm:bottom-5
          sm:right-5
        "
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map(
          (item) => (
            <ToastNotification
              key={item.id}
              toast={item}
              onClose={
                () =>
                  removeToast(
                    item.id,
                  )
              }
            />
          ),
        )}
      </div>
    </ToastContext.Provider>
  )
}


export function useToast(): ToastContextValue {
  const context =
    useContext(
      ToastContext,
    )

  if (!context) {
    throw new Error(
      'useToast doit être utilisé dans ToastProvider.',
    )
  }

  return context
}


function ToastNotification({
  toast,
  onClose,
}: {
  toast: ToastItem
  onClose: () => void
}) {
  const tone =
    getToastTone(
      toast.type,
    )

  return (
    <div
      role={
        toast.type === 'error'
          ? 'alert'
          : 'status'
      }
      className="
        pointer-events-auto
        relative
        flex
        items-start
        gap-3
        overflow-hidden
        rounded-[13px]
        border
        border-black/[0.07]
        bg-white/[0.97]
        p-3.5
        pr-10
        text-slate-800
        shadow-[0_12px_35px_rgba(15,23,42,0.12)]
        backdrop-blur-xl
        dark:border-white/[0.08]
        dark:bg-[#171d21]/[0.97]
        dark:text-slate-100
        dark:shadow-[0_16px_40px_rgba(0,0,0,0.30)]
      "
    >
      <div
        className={[
          'flex',
          'h-8',
          'w-8',
          'shrink-0',
          'items-center',
          'justify-center',
          'rounded-[9px]',
          tone.iconBackground,
          tone.iconColor,
        ].join(' ')}
      >
        <ToastIcon
          type={toast.type}
        />
      </div>

      <div className="min-w-0 flex-1 pt-0.5">
        <p
          className="
            text-[12.5px]
            font-semibold
            leading-[1.35]
            tracking-[-0.01em]
            text-slate-800
            dark:text-slate-100
          "
        >
          {toast.title}
        </p>

        {toast.message && (
          <p
            className="
              mt-1
              text-[10.5px]
              leading-[1.55]
              text-slate-500
              dark:text-slate-400
            "
          >
            {toast.message}
          </p>
        )}

        {toast.actionLabel && toast.onAction && (
          <button
            type="button"
            className={[
              'mt-2.5',
              'inline-flex',
              'h-7',
              'items-center',
              'justify-center',
              'rounded-[8px]',
              'border',
              'px-2.5',
              'text-[10.5px]',
              'font-semibold',
              'outline-none',
              'transition',
              'active:scale-[0.98]',
              tone.action,
            ].join(' ')}
            onClick={() => {
              toast.onAction?.()
              onClose()
            }}
          >
            {toast.actionLabel}
          </button>
        )}
      </div>

      <button
        type="button"
        className="
          absolute
          right-2.5
          top-2.5
          inline-flex
          h-6
          w-6
          items-center
          justify-center
          rounded-[7px]
          text-slate-400
          outline-none
          transition
          hover:bg-slate-100
          hover:text-slate-600
          focus-visible:ring-2
          focus-visible:ring-slate-300/60
          dark:text-slate-500
          dark:hover:bg-white/[0.06]
          dark:hover:text-slate-300
          dark:focus-visible:ring-white/10
        "
        onClick={onClose}
        aria-label="Fermer la notification"
      >
        <X
          className="h-3.5 w-3.5"
          strokeWidth={2}
        />
      </button>
    </div>
  )
}


function ToastIcon({
  type,
}: {
  type: ToastType
}) {
  if (type === 'success') {
    return (
      <CheckCircle2
        className="h-4 w-4"
        strokeWidth={2}
      />
    )
  }

  if (type === 'warning') {
    return (
      <AlertTriangle
        className="h-4 w-4"
        strokeWidth={2}
      />
    )
  }

  if (type === 'error') {
    return (
      <AlertCircle
        className="h-4 w-4"
        strokeWidth={2}
      />
    )
  }

  return (
    <Info
      className="h-4 w-4"
      strokeWidth={2}
    />
  )
}


function getToastTone(
  type: ToastType,
): {
  iconBackground: string
  iconColor: string
  action: string
} {
  if (type === 'success') {
    return {
      iconBackground:
        'bg-emerald-500/[0.10] dark:bg-emerald-400/[0.10]',
      iconColor:
        'text-emerald-600 dark:text-emerald-400',
      action:
        'border-emerald-500/15 bg-emerald-500/[0.08] '
        + 'text-emerald-700 hover:bg-emerald-500/[0.13] '
        + 'dark:border-emerald-400/15 '
        + 'dark:bg-emerald-400/[0.08] '
        + 'dark:text-emerald-300',
    }
  }

  if (type === 'warning') {
    return {
      iconBackground:
        'bg-amber-500/[0.10] dark:bg-amber-400/[0.10]',
      iconColor:
        'text-amber-600 dark:text-amber-400',
      action:
        'border-amber-500/15 bg-amber-500/[0.08] '
        + 'text-amber-700 hover:bg-amber-500/[0.13] '
        + 'dark:border-amber-400/15 '
        + 'dark:bg-amber-400/[0.08] '
        + 'dark:text-amber-300',
    }
  }

  if (type === 'error') {
    return {
      iconBackground:
        'bg-rose-500/[0.09] dark:bg-rose-400/[0.10]',
      iconColor:
        'text-rose-600 dark:text-rose-400',
      action:
        'border-rose-500/15 bg-rose-500/[0.07] '
        + 'text-rose-700 hover:bg-rose-500/[0.12] '
        + 'dark:border-rose-400/15 '
        + 'dark:bg-rose-400/[0.08] '
        + 'dark:text-rose-300',
    }
  }

  return {
    iconBackground:
      'bg-sky-500/[0.09] dark:bg-sky-400/[0.10]',
    iconColor:
      'text-sky-600 dark:text-sky-400',
    action:
      'border-sky-500/15 bg-sky-500/[0.07] '
      + 'text-sky-700 hover:bg-sky-500/[0.12] '
      + 'dark:border-sky-400/15 '
      + 'dark:bg-sky-400/[0.08] '
      + 'dark:text-sky-300',
  }
}
