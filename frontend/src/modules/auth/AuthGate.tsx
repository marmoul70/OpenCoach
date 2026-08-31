import {
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  checkSession,
} from './api'

import {
  LoginPage,
} from './LoginPage'


export function AuthGate({
  children,
}: {
  children: ReactNode
}) {
  const [
    authenticated,
    setAuthenticated,
  ] = useState<
    boolean | null
  >(null)


  useEffect(() => {
    let cancelled = false

    void checkSession()
      .then((result) => {
        if (!cancelled) {
          setAuthenticated(
            result,
          )
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAuthenticated(
            false,
          )
        }
      })

    return () => {
      cancelled = true
    }
  }, [])


  if (
    authenticated === null
  ) {
    return (
      <main
        className="
          flex
          min-h-screen
          items-center
          justify-center
          bg-base-200
        "
      >
        <span
          className="
            loading
            loading-spinner
            loading-lg
            text-primary
          "
        />
      </main>
    )
  }


  if (!authenticated) {
    return (
      <LoginPage
        onAuthenticated={() => {
          setAuthenticated(
            true,
          )
        }}
      />
    )
  }


  return children
}
