import './core/modules'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import {
  ToastProvider,
} from './components/ui/ToastProvider'
import App from './App.tsx'
import { AuthGate } from './modules/auth'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <AuthGate>
        <App />
      </AuthGate>
    </ToastProvider>
  </StrictMode>,
)
