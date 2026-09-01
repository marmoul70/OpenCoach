interface OpenCoachLoadingScreenProps {
  message?: string
}


export function OpenCoachLoadingScreen({
  message = 'Préparation de votre espace…',
}: OpenCoachLoadingScreenProps) {
  return (
    <main
      className="
        pwa-safe-screen
        relative
        flex
        min-h-[100dvh]
        items-center
        justify-center
        overflow-hidden
        bg-[#f5f7f6]
        px-6
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          left-1/2
          top-1/3
          h-72
          w-72
          -translate-x-1/2
          rounded-full
          bg-emerald-500/[0.055]
          blur-3xl
        "
      />

      <div
        className="
          relative
          flex
          flex-col
          items-center
          text-center
        "
      >
        <img
          src="/opencoach-logo.png"
          alt="OpenCoach"
          className="
            h-[76px]
            w-[76px]
            object-contain
            sm:h-20
            sm:w-20
          "
        />

        <div
          className="
            mt-6
            flex
            h-9
            w-9
            items-center
            justify-center
          "
          aria-label="Chargement"
          role="status"
        >
          <span
            className="
              h-7
              w-7
              animate-spin
              rounded-full
              border-[2.5px]
              border-slate-200
              border-t-emerald-500
              dark:border-white/10
              dark:border-t-emerald-400
            "
          />
        </div>

        <p
          className="
            mt-3
            text-[12px]
            font-medium
            text-slate-500
            dark:text-slate-400
          "
        >
          {message}
        </p>

        <p
          className="
            mt-1
            text-[9px]
            font-semibold
            uppercase
            tracking-[0.16em]
            text-slate-300
            dark:text-slate-700
          "
        >
          OpenCoach
        </p>
      </div>
    </main>
  )
}
