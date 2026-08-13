import { fitnessData } from './data'

interface FitnessWidgetProps {
  onClick: () => void
}

export function FitnessWidget({
  onClick,
}: FitnessWidgetProps) {
  const data = fitnessData

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            État de forme
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-900">
            {data.score}
            <span className="ml-1 text-base font-normal text-slate-400">
              / 100
            </span>
          </p>
        </div>

        <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
          {data.label}
        </span>
      </div>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${data.score}%` }}
        />
      </div>

      <p className="mt-4 text-sm text-slate-400">
        Cliquez pour voir les détails
      </p>
    </button>
  )
}