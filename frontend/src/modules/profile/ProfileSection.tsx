import { useState, type ReactNode } from 'react'

interface ProfileSectionProps {
  title: string
  description?: string
  children: ReactNode
  defaultOpen?: boolean
}

export function ProfileSection({
  title,
  description,
  children,
  defaultOpen = false,
}: ProfileSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left transition hover:bg-slate-50"
        aria-expanded={open}
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {title}
          </h2>

          {description && (
            <p className="mt-1 text-sm text-slate-500">
              {description}
            </p>
          )}
        </div>

        <span
          className={[
            'text-xl text-slate-400 transition-transform',
            open ? 'rotate-180' : '',
          ].join(' ')}
          aria-hidden="true"
        >
          ↓
        </span>
      </button>

      {open && (
        <div className="border-t border-slate-100 px-6 py-5">
          {children}
        </div>
      )}
    </section>
  )
}
