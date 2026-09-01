import {
  useEffect,
  type ReactNode,
} from 'react'

import {
  X,
} from 'lucide-react'


interface ModalProps {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}


export function Modal({
  title,
  open,
  onClose,
  children,
}: ModalProps) {
  useEffect(() => {
    if (!open) {
      return
    }

    const previousOverflow =
      document.body.style.overflow

    document.body.style.overflow =
      'hidden'

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener(
      'keydown',
      handleKeyDown,
    )

    return () => {
      document.body.style.overflow =
        previousOverflow

      window.removeEventListener(
        'keydown',
        handleKeyDown,
      )
    }
  }, [
    open,
    onClose,
  ])


  if (!open) {
    return null
  }


  return (
    <div
      className="
        fixed
        inset-0
        z-[100]
        flex
        justify-center
                items-end
                justify-center
                sm:items-center
                sm:px-6
                sm:py-6
"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {/* BACKDROP */}

      <button
        type="button"
        aria-label="Fermer la fenêtre"
        onClick={onClose}
        className="
          absolute
          inset-0
          cursor-default
          bg-black/45
          backdrop-blur-[4px]
          dark:bg-black/55
        "
      />


      {/* SHEET */}

      <div
        className="
          relative
          z-10
          flex
          max-h-[82dvh]
          w-full
          flex-col
          overflow-hidden
          rounded-t-[20px]
          border
          border-black/[0.07]
          border-b-0
          bg-white
          shadow-[0_-20px_60px_rgba(15,23,42,0.18)]
          animate-[opencoach-sheet-in_220ms_cubic-bezier(0.22,1,0.36,1)]
                  sm:animate-[opencoach-modal-in_180ms_cubic-bezier(0.22,1,0.36,1)]
          dark:border-white/[0.08]
          dark:bg-[#151b1f]
          dark:shadow-[0_-22px_70px_rgba(0,0,0,0.42)]


          sm:max-h-[82vh]
          sm:max-w-[760px]
                  sm:border-b
          sm:rounded-[18px]

        "
      >

        {/* GRIP */}

        <div
          className="
            flex
            shrink-0
            justify-center
            pt-2
            sm:hidden
          "
        >
          <div
            className="
              h-1
              w-9
              rounded-full
              bg-slate-300
              dark:bg-white/[0.14]
            "
          />
        </div>


        {/* HEADER */}

        <div
          className="
            flex
            shrink-0
            items-center
            justify-between
            gap-4
            border-b
            border-black/[0.06]
            px-4
            py-3
            dark:border-white/[0.07]
            sm:px-5
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.13em]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              OpenCoach
            </p>

            <h2
              id="modal-title"
              className="
                mt-0.5
                truncate
                text-[16px]
                font-semibold
                tracking-[-0.02em]
                text-slate-950
                dark:text-white
              "
            >
              {title}
            </h2>
          </div>


          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="
              flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center
              rounded-[9px]
              text-slate-400
              transition
              hover:bg-slate-100
              hover:text-slate-900
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-emerald-500/30
              dark:hover:bg-white/[0.055]
              dark:hover:text-white
            "
          >
            <X
              className="
                h-4
                w-4
              "
            />
          </button>
        </div>


        {/* CONTENT */}

        <div
          className="
            min-h-0
            flex-1
            overflow-y-auto
            overscroll-contain
            px-4
            py-4
            sm:px-5
            sm:py-5
          "
        >
          {children}
        </div>
      </div>
    </div>
  )
}
