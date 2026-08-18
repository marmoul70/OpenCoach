interface FormFieldProps {
  label: string
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
    <fieldset className="fieldset">
      <label className="fieldset-legend">
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        className="input input-bordered w-full"
      />
    </fieldset>
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
    <div className="flex flex-wrap items-center justify-end gap-3 border-t border-base-300 pt-5">
      {saved && (
        <div className="alert alert-success mr-auto w-auto py-2 text-sm">
          <span>Paramètres enregistrés.</span>
        </div>
      )}

      <button
        type="button"
        onClick={onReset}
        className="btn btn-ghost"
      >
        Annuler
      </button>

      <button
        type="button"
        onClick={onSave}
        className="btn btn-primary"
      >
        Enregistrer
      </button>
    </div>
  )
}

export function parseOptionalNumber(
  value: string,
): number | undefined {
  const trimmedValue = value.trim()

  if (!trimmedValue) {
    return undefined
  }

  const parsedValue = Number(trimmedValue)

  return Number.isFinite(parsedValue)
    ? parsedValue
    : undefined
}
