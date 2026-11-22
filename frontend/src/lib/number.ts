/** Convert an optional numeric form value into a finite number. */
export function parseOptionalNumber(value: string): number | undefined {
  const trimmedValue = value.trim()
  if (!trimmedValue) return undefined

  const parsedValue = Number(trimmedValue)
  return Number.isFinite(parsedValue) ? parsedValue : undefined
}
