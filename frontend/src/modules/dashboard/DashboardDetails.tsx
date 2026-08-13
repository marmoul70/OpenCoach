export function DashboardDetails() {
  return (
    <div className="space-y-4">
      <p className="text-slate-600">
        Bienvenue dans OpenCoach.
      </p>

      <div className="rounded-xl bg-slate-50 p-4">
        <p className="text-sm text-slate-500">
          État du système
        </p>

        <p className="mt-1 font-medium text-slate-900">
          Le Dashboard est opérationnel.
        </p>
      </div>

      <p className="text-sm text-slate-500">
        Les données d'entraînement, de récupération,
        de nutrition et de matériel seront progressivement
        intégrées ici.
      </p>
    </div>
  )
}
