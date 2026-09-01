import './core/modules'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import {
  ToastProvider,
} from './components/ui/ToastProvider'
import App from './App.tsx'
import {
  AppBadgeManager,
  VersionWatcher,
  registerServiceWorker,
} from './modules/pwa'
import { AuthGate } from './modules/auth'
registerServiceWorker()


type InitialTheme =
  | 'light'
  | 'dark'
  | 'system'


function applyInitialTheme() {
  const savedTheme =
    localStorage.getItem(
      'opencoach-theme',
    ) as InitialTheme | null

  let resolvedTheme:
    'light'
    | 'dark'

  if (
    savedTheme === 'light'
    || savedTheme === 'dark'
  ) {
    resolvedTheme =
      savedTheme
  } else {
    resolvedTheme =
      window.matchMedia(
        '(prefers-color-scheme: dark)',
      ).matches
        ? 'dark'
        : 'light'
  }

  document.documentElement.setAttribute(
    'data-theme',
    resolvedTheme,
  )
}


/*
 * Le thème doit être appliqué AVANT le rendu React.
 *
 * AuthGate peut afficher LoginPage, le splash ou
 * l'écran hors ligne sans rendre App.tsx.
 */
applyInitialTheme()


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <VersionWatcher />
      <AuthGate>
        <AppBadgeManager />
        <App />
      </AuthGate>
    </ToastProvider>
  </StrictMode>,
)
