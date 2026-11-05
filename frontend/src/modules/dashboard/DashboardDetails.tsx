export function DashboardDetails() {
  return (
    <div className="space-y-4">
      <p className="text-[var(--oc-text-secondary)]">
        Bienvenue dans OpenCoach.
      </p>

      <div className="rounded-xl bg-[var(--oc-surface-muted)] p-4">
        <p className="text-sm text-[var(--oc-muted)]">
          État du système
        </p>

        <p className="mt-1 font-medium text-[var(--oc-text)]">
          Le Dashboard est opérationnel.
        </p>
      </div>

      <p className="text-sm text-[var(--oc-muted)]">
        Les données d'entraînement, de récupération,
        de nutrition et de matériel seront progressivement
        intégrées ici.
      </p>
    </div>
  )
}
