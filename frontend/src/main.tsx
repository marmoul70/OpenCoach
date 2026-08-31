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
import {
  BadgeDiagnostic,
} from './modules/pwa/BadgeDiagnostic'

registerServiceWorker()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <VersionWatcher />
      <AuthGate>
        <AppBadgeManager />
      <BadgeDiagnostic />
        <App />
      </AuthGate>
    </ToastProvider>
  </StrictMode>,
)
