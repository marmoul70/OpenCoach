import {
  useEffect,
} from 'react'

import {
  resetPushBadge,
} from './pushApi'


type BadgeNavigator = Navigator & {
  setAppBadge?: (
    contents?: number,
  ) => Promise<void>
  clearAppBadge?: () => Promise<void>
}


async function clearBadge() {
  const badgeNavigator =
    navigator as BadgeNavigator

  try {
    if (
      'serviceWorker'
      in navigator
    ) {
      const registration =
        await navigator
          .serviceWorker
          .ready

      const subscription =
        await registration
          .pushManager
          .getSubscription()

      if (subscription) {
        try {
          await resetPushBadge(
            subscription.endpoint,
          )
        } catch {
          /*
           * Une erreur réseau ne doit pas
           * bloquer OpenCoach.
           */
        }
      }
    }

    if (
      typeof badgeNavigator
        .clearAppBadge
      === 'function'
    ) {
      await badgeNavigator
        .clearAppBadge()

      return
    }

    if (
      typeof badgeNavigator
        .setAppBadge
      === 'function'
    ) {
      await badgeNavigator
        .setAppBadge(0)
    }
  } catch {
    /*
     * Le badge est une amélioration PWA.
     * Une erreur ne doit jamais bloquer
     * OpenCoach.
     */
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

    function handlePageShow() {
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

    window.addEventListener(
      'pageshow',
      handlePageShow,
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

      window.removeEventListener(
        'pageshow',
        handlePageShow,
      )
    }
  }, [])

  return null
}
