import type { ReactNode } from 'react'

interface ModalProps {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}

export function Modal({
  title,
  open,
  onClose,
  children,
}: ModalProps) {
  if (!open) {
    return null
  }

  return (
    <div
      className="modal modal-open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal-box max-h-[calc(100vh-2rem)] max-w-2xl overflow-hidden p-0">
        <div className="flex items-center justify-between gap-4 border-b border-base-300 px-6 py-4">
          <h2
            id="modal-title"
            className="text-xl font-semibold"
          >
            {title}
          </h2>

          <button
            type="button"
            onClick={onClose}
            className="btn btn-sm btn-circle btn-ghost"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>

        <div className="max-h-[calc(100vh-7rem)] overflow-y-auto px-6 py-5">
          {children}
        </div>
      </div>

      <div
        className="modal-backdrop"
        onClick={onClose}
      />
    </div>
  )
}