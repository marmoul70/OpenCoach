import {
  useEffect,
  useRef,
  useState,
} from 'react'

import type {
  ReactNode,
} from 'react'

import {
  X,
} from 'lucide-react'


interface SidePanelProps {
  open: boolean
  title?: string
  eyebrow?: string
  onClose: () => void
  children: ReactNode
}


const SIDE_PANEL_ANIMATION_MS = 280


export function SidePanel({
  open,
  title,
  eyebrow = 'Détail',
  onClose,
  children,
}: SidePanelProps) {
  const [
    mounted,
    setMounted,
  ] = useState(open)

  const [
    visible,
    setVisible,
  ] = useState(false)

  const closeTimerRef =
    useRef<number | null>(
      null,
    )

  const frameRef =
    useRef<number | null>(
      null,
    )


  useEffect(() => {
    /*
     * Toujours annuler les timers / frames
     * d'une transition précédente.
     */
    if (
      closeTimerRef.current
      !== null
    ) {
      window.clearTimeout(
        closeTimerRef.current,
      )

      closeTimerRef.current = null
    }

    if (
      frameRef.current
      !== null
    ) {
      window.cancelAnimationFrame(
        frameRef.current,
      )

      frameRef.current = null
    }


    if (open) {
      /*
       * Étape 1 :
       * monter le panneau avec visible=false.
       *
       * Son état initial est donc :
       * translateX(100%).
       */
      setMounted(
        true,
      )

      setVisible(
        false,
      )


      /*
       * Étape 2 :
       * attendre deux frames.
       *
       * Frame 1 :
       * React monte réellement le SidePanel.
       *
       * Frame 2 :
       * le navigateur a eu le temps de peindre
       * translateX(100%), puis on passe à
       * translateX(0).
       *
       * Cela garantit l'animation d'ouverture.
       */
      frameRef.current =
        window.requestAnimationFrame(
          () => {
            frameRef.current =
              window.requestAnimationFrame(
                () => {
                  frameRef.current = null

                  setVisible(
                    true,
                  )
                },
              )
          },
        )

      return
    }


    /*
     * Fermeture :
     * visible=false déclenche immédiatement
     * translateX(100%).
     */
    setVisible(
      false,
    )


    /*
     * On garde le composant monté pendant
     * toute la durée de l'animation.
     */
    closeTimerRef.current =
      window.setTimeout(
        () => {
          closeTimerRef.current = null

          setMounted(
            false,
          )
        },
        SIDE_PANEL_ANIMATION_MS,
      )
  }, [
    open,
  ])


  useEffect(() => {
    if (!mounted) {
      return
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (
        event.key === 'Escape'
        && visible
      ) {
        requestClose()
      }
    }

    document.addEventListener(
      'keydown',
      handleKeyDown,
    )

    return () => {
      document.removeEventListener(
        'keydown',
        handleKeyDown,
      )
    }
  })


  useEffect(() => {
    return () => {
      if (closeTimerRef.current !== null) {
        window.clearTimeout(
          closeTimerRef.current,
        )
      }

      if (frameRef.current !== null) {
        window.cancelAnimationFrame(
          frameRef.current,
        )
      }
    }
  }, [])


  function requestClose() {
    if (!visible) {
      return
    }

    /*
     * L'animation de fermeture démarre
     * immédiatement.
     */
    setVisible(
      false,
    )

    if (closeTimerRef.current !== null) {
      window.clearTimeout(
        closeTimerRef.current,
      )
    }

    /*
     * Le parent est réellement fermé
     * seulement après la translation.
     */
    closeTimerRef.current =
      window.setTimeout(
        () => {
          closeTimerRef.current = null

          onClose()
        },
        SIDE_PANEL_ANIMATION_MS,
      )
  }


  if (!mounted) {
    return null
  }


  return (
    <div
      className="
        fixed
        inset-0
        z-[80]
      "
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <button
        type="button"
        aria-label="Fermer"
        onClick={
          requestClose
        }
        className={[
          (
            'absolute inset-0 '
            + 'bg-slate-950/15 '
            + 'backdrop-blur-[1px] '
            + 'transition-opacity '
            + 'duration-[280ms] '
            + 'dark:bg-black/30'
          ),
          visible
            ? 'opacity-100'
            : 'opacity-0',
        ].join(' ')}
      />


      <aside
        className={[
          (
            'absolute inset-y-0 right-0 '
            + 'flex w-full flex-col '
            + 'border-l border-black/[0.07] '
            + 'bg-[#f8faf9] '
            + 'shadow-[-16px_0_45px_rgba(15,23,42,0.10)] '
            + 'dark:border-white/[0.08] '
            + 'dark:bg-[#0f1519] '
            + 'md:w-[38vw] '
            + 'md:min-w-[420px] '
            + 'md:max-w-[560px] '
            + 'lg:w-[34vw] '
            + 'transform-gpu '
            + 'transition-transform '
            + 'duration-[280ms] '
            + 'ease-[cubic-bezier(0.22,1,0.36,1)]'
          ),
          visible
            ? 'translate-x-0'
            : 'translate-x-full',
        ].join(' ')}
      >
        <header
          className="
            flex
            min-h-[58px]
            shrink-0
            items-center
            justify-between
            gap-3

            border-b
            border-black/[0.06]

            bg-white/90

            px-4

            backdrop-blur-xl

            dark:border-white/[0.07]
            dark:bg-[#141a1e]/95

            sm:px-5
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.12em]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              {eyebrow}
            </p>

            {title && (
              <h2
                className="
                  mt-0.5
                  truncate
                  text-[14px]
                  font-semibold
                  text-slate-800
                  dark:text-slate-100
                "
              >
                {title}
              </h2>
            )}
          </div>


          <button
            type="button"
            onClick={
              requestClose
            }
            aria-label="Fermer le détail"
            className="
              flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center

              rounded-[9px]

              border
              border-black/[0.07]

              bg-white

              text-slate-500

              transition

              hover:border-black/[0.12]
              hover:bg-slate-50
              hover:text-slate-800

              dark:border-white/[0.08]
              dark:bg-white/[0.035]
              dark:text-slate-400
              dark:hover:bg-white/[0.06]
              dark:hover:text-slate-200
            "
          >
            <X
              className="
                h-4
                w-4
              "
            />
          </button>
        </header>


        <div
          className="
            min-h-0
            flex-1
            overflow-y-auto

            px-3
            py-3

            sm:px-4
            sm:py-4
          "
        >
          {children}
        </div>
      </aside>
    </div>
  )
}
