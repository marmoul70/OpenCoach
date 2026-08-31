import {
  useState,
} from 'react'


type BadgeStatus =
  | 'idle'
  | 'success'
  | 'unsupported'
  | 'error'


type BadgeNavigator = {
  setAppBadge?: (
    contents?: number,
  ) => Promise<void>
}


export function BadgeDiagnostic() {
  const [
    status,
    setStatus,
  ] = useState<BadgeStatus>(
    'idle',
  )

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string>(
    '',
  )


  const badgeNavigator =
    navigator as Navigator
    & BadgeNavigator


  async function testBadge() {
    setErrorMessage(
      '',
    )


    if (
      typeof badgeNavigator
        .setAppBadge
      !== 'function'
    ) {
      setStatus(
        'unsupported',
      )

      return
    }


    try {
      await badgeNavigator
        .setAppBadge(
          7,
        )

      setStatus(
        'success',
      )
    } catch (error) {
      console.error(
        '[OpenCoach Badge Diagnostic]',
        error,
      )

      setStatus(
        'error',
      )


      if (
        error
        instanceof Error
      ) {
        setErrorMessage(
          `${error.name}: ${error.message}`,
        )
      } else {
        setErrorMessage(
          String(
            error,
          ),
        )
      }
    }
  }


  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        right: '20px',
        zIndex: 99999,
        padding: '16px',
        background: '#111827',
        color: '#ffffff',
        borderRadius: '14px',
        boxShadow:
          '0 10px 30px rgba(0,0,0,0.35)',
        fontSize: '14px',
      }}
    >
      <div
        style={{
          fontWeight: 700,
          marginBottom: '10px',
        }}
      >
        OpenCoach Badge Diagnostic
      </div>

      <div>
        Permission : {
          typeof Notification
          !== 'undefined'
            ? Notification.permission
            : 'indisponible'
        }
      </div>

      <div>
        API badge : {
          typeof badgeNavigator
            .setAppBadge
          === 'function'
            ? 'OUI'
            : 'NON'
        }
      </div>

      <div>
        Résultat : {status}
      </div>

      {
        errorMessage
        && (
          <div
            style={{
              marginTop: '8px',
              wordBreak: 'break-word',
            }}
          >
            Erreur : {errorMessage}
          </div>
        )
      }

      <button
        type="button"
        onClick={() => {
          void testBadge()
        }}
        style={{
          marginTop: '12px',
          width: '100%',
          padding: '12px',
          border: '0',
          borderRadius: '10px',
          fontWeight: 700,
          cursor: 'pointer',
        }}
      >
        TEST BADGE 7
      </button>
    </div>
  )
}
