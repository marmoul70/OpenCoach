import {
  HeartPulse,
} from 'lucide-react'

import {
  FeelingWidgets,
} from './FeelingWidgets'


export function FeelingPage() {
  return (
    <main className="min-h-screen bg-base-200">
      <div
        className="
          mx-auto
          max-w-5xl
          px-4
          py-6
          sm:px-6
          lg:py-8
        "
      >
        <header className="mb-6">
          <div
            className="
              flex
              items-start
              justify-between
              gap-6
            "
          >
            <div>
              <h1
                className="
                  text-3xl
                  font-bold
                  tracking-tight
                  text-base-content
                "
              >
                Ressenti
              </h1>

              <p
                className="
                  mt-1
                  text-sm
                  text-base-content/55
                "
              >
                Évaluez votre état du jour pour permettre
                à OpenCoach d&apos;adapter votre entraînement.
              </p>
            </div>

            <div
              className="
                flex
                size-11
                shrink-0
                items-center
                justify-center
                rounded-2xl
                bg-primary/10
                text-primary
              "
            >
              <HeartPulse
                size={24}
                strokeWidth={2}
              />
            </div>
          </div>
        </header>

        <FeelingWidgets />
      </div>
    </main>
  )
}
