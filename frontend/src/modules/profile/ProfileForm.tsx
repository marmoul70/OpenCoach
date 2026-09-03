import type { ReactNode } from 'react'

/* oxlint-disable react/only-export-components */

interface FormFieldProps {
  label: ReactNode
  value: string
  onChange: (value: string) => void
  placeholder?: string
  type?: string
  min?: string
  max?: string
  step?: string
}


export function FormField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  min,
  max,
  step,
}: FormFieldProps) {
  return (
    <label className="block">
      <span
        className="
          mb-1.5
          block
          text-[10px]
          font-semibold
          text-slate-500
          dark:text-slate-400
        "
      >
        {label}
      </span>

      <input
        type={type}
        value={value}
        onChange={
          (event) =>
            onChange(
              event.target.value,
            )
        }
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        className="
          h-10
          w-full
          rounded-[9px]
          border
          border-black/[0.07]
          bg-white
          px-3
          text-[11px]
          font-medium
          text-slate-700
          outline-none
          transition
          placeholder:text-slate-400
          hover:border-black/[0.11]
          focus:border-emerald-500/35
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-[#171d21]
          dark:text-slate-200
          dark:placeholder:text-slate-500
          dark:hover:border-white/[0.11]
          dark:focus:border-emerald-400/30
          dark:focus:ring-emerald-400/[0.08]
        "
      />
    </label>
  )
}


interface SectionActionsProps {
  saved: boolean
  onReset: () => void
  onSave: () => void | Promise<void>
}


export function SectionActions({
  saved,
  onReset,
  onSave,
}: SectionActionsProps) {
  return (
    <div
      className="
        flex
        flex-wrap
        items-center
        justify-end
        gap-2.5
        border-t
        border-black/[0.06]
        pt-4
        dark:border-white/[0.07]
      "
    >
      {saved && (
        <div
          className="
            mr-auto
            inline-flex
            items-center
            gap-2
            rounded-[9px]
            border
            border-emerald-500/15
            bg-emerald-500/[0.06]
            px-3
            py-2
            text-[10.5px]
            font-medium
            text-emerald-700
            dark:border-emerald-400/15
            dark:bg-emerald-400/[0.06]
            dark:text-emerald-300
          "
        >
          <span
            className="
              h-1.5
              w-1.5
              rounded-full
              bg-emerald-500
              dark:bg-emerald-400
            "
          />

          Paramètres enregistrés.
        </div>
      )}

      <button
        type="button"
        onClick={onReset}
        className="
          inline-flex
          h-9
          items-center
          justify-center
          rounded-[9px]
          border
          border-black/[0.06]
          bg-white/70
          px-3.5
          text-[10.5px]
          font-semibold
          text-slate-600
          transition
          hover:border-black/[0.10]
          hover:bg-slate-100
          dark:border-white/[0.07]
          dark:bg-white/[0.025]
          dark:text-slate-300
          dark:hover:border-white/[0.11]
          dark:hover:bg-white/[0.05]
        "
      >
        Annuler
      </button>

      <button
        type="button"
        onClick={onSave}
        className="
          inline-flex
          h-9
          items-center
          justify-center
          rounded-[9px]
          border
          border-emerald-500/15
          bg-emerald-500/[0.09]
          px-3.5
          text-[10.5px]
          font-semibold
          text-emerald-700
          transition
          hover:border-emerald-500/25
          hover:bg-emerald-500/[0.14]
          dark:border-emerald-400/15
          dark:bg-emerald-400/[0.08]
          dark:text-emerald-300
          dark:hover:bg-emerald-400/[0.13]
        "
      >
        Enregistrer
      </button>
    </div>
  )
}


export function parseOptionalNumber(
  value: string,
): number | undefined {
  const trimmedValue =
    value.trim()

  if (!trimmedValue) {
    return undefined
  }

  const parsedValue =
    Number(
      trimmedValue,
    )

  return Number.isFinite(
    parsedValue,
  )
    ? parsedValue
    : undefined
}
