import {
  HeartPulse,
  ShieldCheck,
} from 'lucide-react'

import {
  FeelingWidgets,
} from './FeelingWidgets'


export function FeelingPage() {
  return (
    <main
      className="
        min-h-screen
        bg-[#f5f7f6]
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          mx-auto
          max-w-[1120px]
          px-3
          py-4
          sm:px-5
          lg:py-5
        "
      >
        <header className="mb-4">
          <p
            className="
              text-[10px]
              font-bold
              uppercase
              tracking-[0.13em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Check-in quotidien
          </p>

          <h1
            className="
              mt-1
              text-[30px]
              font-bold
              tracking-[-0.04em]
              text-slate-950
              dark:text-white
            "
          >
            Ressenti
          </h1>

          <p
            className="
              mt-1
              text-[13px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Quelques secondes pour aider OpenCoach
            à adapter intelligemment ta journée.
          </p>
        </header>


        <section
          className="
            relative
            mb-3
            overflow-hidden
            rounded-[15px]
            border
            border-white/[0.07]
            bg-[#141917]
            p-5
            text-white
            shadow-[0_12px_38px_rgba(4,12,8,0.10)]
            sm:p-6
          "
        >
          <div
            className="
              pointer-events-none
              absolute
              -right-24
              -top-28
              h-64
              w-64
              rounded-full
              bg-emerald-500/[0.11]
              blur-3xl
            "
          />

          <div
            className="
              relative
              flex
              flex-col
              gap-5
              sm:flex-row
              sm:items-center
              sm:justify-between
            "
          >
            <div className="max-w-2xl">
              <div
                className="
                  flex
                  items-center
                  gap-2
                "
              >
                <div
                  className="
                    flex
                    h-8
                    w-8
                    items-center
                    justify-center
                    rounded-[9px]
                    bg-emerald-400/[0.10]
                    text-emerald-300
                  "
                >
                  <HeartPulse
                    className="
                      h-4
                      w-4
                    "
                  />
                </div>

                <span
                  className="
                    text-[9px]
                    font-bold
                    uppercase
                    tracking-[0.12em]
                    text-emerald-400
                  "
                >
                  État du jour
                </span>
              </div>

              <h2
                className="
                  mt-4
                  text-[22px]
                  font-bold
                  tracking-[-0.03em]
                  text-white
                  sm:text-[24px]
                "
              >
                Comment tu te sens aujourd’hui ?
              </h2>

              <p
                className="
                  mt-2
                  max-w-xl
                  text-[12px]
                  leading-5
                  text-white/45
                "
              >
                Ton énergie, ton confort et ta disponibilité
                complètent les données de récupération
                utilisées par le Coach.
              </p>


              <div
                className="
                  mt-4
                  flex
                  items-center
                  gap-2
                  border-t
                  border-white/[0.07]
                  pt-3
                  text-[10px]
                  text-white/40
                "
              >
                <ShieldCheck
                  className="
                    h-3.5
                    w-3.5
                    text-emerald-400
                  "
                />

                Les réponses sont enregistrées
                automatiquement.
              </div>
            </div>


            <div
              className="
                hidden
                h-20
                w-20
                shrink-0
                items-center
                justify-center
                rounded-full
                border
                border-white/[0.06]
                bg-white/[0.025]
                lg:flex
              "
            >
              <HeartPulse
                className="
                  h-8
                  w-8
                  text-emerald-400
                "
                strokeWidth={1.7}
              />
            </div>
          </div>
        </section>


        <FeelingWidgets />
      </div>
    </main>
  )
}
