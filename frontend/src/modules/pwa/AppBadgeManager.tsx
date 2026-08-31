import {
  useEffect,
} from 'react'


async function clearBadge() {
  if (
    'clearAppBadge'
    in navigator
  ) {
    try {
      await navigator
        .clearAppBadge()
    } catch {
      // Le badge ne doit jamais bloquer OpenCoach.
    }
  }
}


export function AppBadgeManager() {
  useEffect(() => {
    void clearBadge()

    function handleVisibilityChange() {
      if (
        document.visibilityState
        === 'visible'
      ) {
        void clearBadge()
      }
    }

    function handleFocus() {
      void clearBadge()
    }

    document.addEventListener(
      'visibilitychange',
      handleVisibilityChange,
    )

    window.addEventListener(
      'focus',
      handleFocus,
    )

    return () => {
      document.removeEventListener(
        'visibilitychange',
        handleVisibilityChange,
      )

      window.removeEventListener(
        'focus',
        handleFocus,
      )
    }
  }, [])

  return null
}
