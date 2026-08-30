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
          toast
          toast-end
          toast-bottom
          z-[100]
          w-full
          max-w-sm
          pointer-events-none
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
  return (
    <div
      role={
        toast.type === 'error'
          ? 'alert'
          : 'status'
      }
      className={`
        alert
        ${getToastClass(toast.type)}
        pointer-events-auto
        shadow-lg
      `}
    >
      <ToastIcon
        type={toast.type}
      />

      <div className="min-w-0 flex-1">
        <p className="font-semibold">
          {toast.title}
        </p>

        {toast.message && (
          <p className="mt-0.5 text-sm opacity-80">
            {toast.message}
          </p>
        )}
      </div>

      {toast.actionLabel && toast.onAction && (
        <button
          type="button"
          className="
            btn
            btn-sm
            btn-ghost
            shrink-0
          "
          onClick={() => {
            toast.onAction?.()
            onClose()
          }}
        >
          {toast.actionLabel}
        </button>
      )}

      <button
        type="button"
        className="btn btn-ghost btn-circle btn-xs"
        onClick={onClose}
        aria-label="Fermer la notification"
      >
        <X className="h-4 w-4" />
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
      <CheckCircle2 className="h-5 w-5 shrink-0" />
    )
  }

  if (type === 'warning') {
    return (
      <AlertTriangle className="h-5 w-5 shrink-0" />
    )
  }

  if (type === 'error') {
    return (
      <AlertCircle className="h-5 w-5 shrink-0" />
    )
  }

  return (
    <Info className="h-5 w-5 shrink-0" />
  )
}


function getToastClass(
  type: ToastType,
): string {
  if (type === 'success') {
    return 'alert-success'
  }

  if (type === 'warning') {
    return 'alert-warning'
  }

  if (type === 'error') {
    return 'alert-error'
  }

  return 'alert-info'
}
