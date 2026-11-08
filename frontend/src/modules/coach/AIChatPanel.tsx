import { useEffect, useState } from 'react'
import { Bot, Send, Sparkles, RotateCw } from 'lucide-react'
import { SidePanel } from '../../components/ui/SidePanel'

interface AIStatus {
  enabled: boolean
  provider: string
  model: string
  provider_check: string
}

interface AIReply {
  answer: string
  model: string
  context_used?: boolean
}

interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
}

export function AIChatPanel() {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<AIStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadStatus() {
    setStatusError(null)
    try {
      const response = await fetch('/api/ai/status', {
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
        cache: 'no-store',
      })
      if (!response.ok) {
        throw new Error(response.status === 401
          ? 'Session expirée : reconnecte-toi à OpenCoach.'
          : `Vérification IA impossible (HTTP ${response.status}).`)
      }
      setStatus(await response.json() as AIStatus)
    } catch (reason) {
      setStatusError(reason instanceof Error ? reason.message : 'Service IA indisponible.')
    }
  }

  useEffect(() => {
    void loadStatus()
  }, [])

  async function sendQuestion() {
    const normalized = question.trim()
    if (!normalized || sending || !status?.enabled) return

    const history = messages.slice(-8)
    setSending(true)
    setError(null)
    setMessages(current => [...current, { role: 'user', content: normalized }])
    setQuestion('')

    try {
      const response = await fetch('/api/ai/coach', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: normalized, history }),
      })
      const payload = await response.json() as AIReply | { detail?: string }
      if (!response.ok) {
        throw new Error('detail' in payload && payload.detail
          ? payload.detail
          : `Le moteur IA n’a pas pu répondre (HTTP ${response.status}).`)
      }
      const reply = payload as AIReply
      setMessages(current => [...current, { role: 'assistant', content: reply.answer }])
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Erreur lors de la requête IA.')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Ouvrir l’assistant IA"
        className="fixed bottom-20 right-5 z-[70] inline-flex h-12 items-center gap-2 rounded-full border border-violet-400/20 bg-violet-600 px-4 text-sm font-semibold text-white shadow-lg shadow-violet-950/15 transition hover:-translate-y-0.5 hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 lg:bottom-6"
      >
        <Bot className="h-5 w-5" />
        <span>Assistant IA</span>
      </button>

      <SidePanel
        open={open}
        eyebrow="OpenCoach · IA locale"
        title="Assistant personnel"
        onClose={() => setOpen(false)}
      >
        <div className="flex min-h-full flex-col gap-4">
          <div className="flex items-center gap-3 rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] p-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-500/10 text-violet-600 dark:text-violet-300">
              <Bot className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-[var(--oc-text)] dark:text-white">Assistant IA local</p>
              <p className="text-[10px] text-[var(--oc-muted)]">Données sportives en lecture seule · Ollama</p>
            </div>
            <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[9px] font-semibold text-emerald-700 dark:text-emerald-300">Local</span>
          </div>

          {statusError && (
            <div role="alert" className="flex items-center justify-between gap-3 rounded-xl bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-300">
              <span>{statusError}</span>
              <button type="button" onClick={() => void loadStatus()} className="inline-flex shrink-0 items-center gap-1 font-semibold">
                <RotateCw className="h-3.5 w-3.5" /> Réessayer
              </button>
            </div>
          )}

          {!status && !statusError && (
            <p className="text-xs text-[var(--oc-muted)]">Vérification du moteur IA…</p>
          )}

          {status && !status.enabled && (
            <div className="rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] p-4">
              <p className="text-sm font-semibold text-[var(--oc-text)] dark:text-white">Moteur IA désactivé</p>
              <p className="mt-1 text-xs leading-5 text-[var(--oc-muted)]">
                Le moteur local est installé mais reste désactivé dans la configuration serveur. Active-le lorsque nous aurons terminé les vérifications.
              </p>
              <p className="mt-2 text-[10px] text-[var(--oc-muted)]">Modèle configuré : {status.model}</p>
            </div>
          )}

          {status?.enabled && (
            <>
              <div className="flex items-start gap-2 rounded-lg bg-violet-500/[0.06] p-3 text-[11px] leading-5 text-[var(--oc-muted)]">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-violet-500" />
                L’assistant utilise un instantané sportif OpenCoach en lecture seule. Il peut expliquer tes données, mais ne modifie jamais ton planning ni COROS.
              </div>

              <div aria-live="polite" className="min-h-[180px] flex-1 space-y-3 rounded-xl bg-[var(--oc-surface-muted)] p-3">
                {messages.length === 0 && (
                  <div className="flex h-full min-h-[150px] flex-col items-center justify-center text-center">
                    <Bot className="h-8 w-8 text-violet-500/70" />
                    <p className="mt-3 text-sm font-semibold text-[var(--oc-text)] dark:text-white">Comment puis-je t’aider ?</p>
                    <p className="mt-1 max-w-[260px] text-xs leading-5 text-[var(--oc-muted)]">Interroge tes données d’entraînement, ta récupération ou ta charge récente.</p>
                  </div>
                )}
                {messages.map((message, index) => (
                  <div key={index} className={message.role === 'user' ? 'ml-5 rounded-xl bg-emerald-500/10 p-3' : 'mr-3 rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface)] p-3'}>
                    <p className="mb-1 text-[9px] font-bold uppercase tracking-wide text-[var(--oc-muted)]">
                      {message.role === 'user' ? 'Toi' : 'OpenCoach IA'}
                    </p>
                    <p className="whitespace-pre-wrap text-xs leading-5 text-[var(--oc-text)] dark:text-[var(--oc-text-secondary)]">{message.content}</p>
                  </div>
                ))}
                {sending && <p className="text-xs text-[var(--oc-muted)]">OpenCoach IA réfléchit…</p>}
              </div>

              {error && <p role="alert" className="rounded-lg bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-300">{error}</p>}

              <form
                className="sticky bottom-0 flex flex-col gap-2 border-t border-[var(--oc-border)] bg-[var(--oc-surface)] pt-3"
                onSubmit={event => {
                  event.preventDefault()
                  void sendQuestion()
                }}
              >
                <textarea
                  aria-label="Question à l’assistant IA"
                  value={question}
                  onChange={event => setQuestion(event.target.value)}
                  maxLength={4000}
                  rows={3}
                  placeholder="Écris ton message…"
                  className="min-h-[76px] w-full resize-y rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface)] px-3 py-2.5 text-xs text-[var(--oc-text)] outline-none transition focus:border-violet-500 dark:text-white"
                />
                <button
                  type="submit"
                  disabled={!question.trim() || sending}
                  className="inline-flex min-h-10 items-center justify-center gap-2 self-end rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {sending ? 'Analyse…' : 'Envoyer'}
                  <Send className="h-3.5 w-3.5" />
                </button>
                <p className="text-[9px] text-[var(--oc-muted)]">Conversation temporaire · les 8 derniers messages sont transmis au modèle. Aucun historique durable.</p>
              </form>
            </>
          )}
        </div>
      </SidePanel>
    </>
  )
}
