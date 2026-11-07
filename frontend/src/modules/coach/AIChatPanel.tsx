import { useEffect, useState } from 'react'
import { Bot, Send, Sparkles } from 'lucide-react'

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
  const [status, setStatus] = useState<AIStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    void fetch('/api/ai/status', {
      headers: { Accept: 'application/json' },
    })
      .then(async response => {
        if (!response.ok) {
          throw new Error('Impossible de vérifier la configuration du moteur IA.')
        }
        return response.json() as Promise<AIStatus>
      })
      .then(data => {
        if (active) setStatus(data)
      })
      .catch(reason => {
        if (active) {
          setStatusError(reason instanceof Error ? reason.message : 'Service IA indisponible.')
        }
      })

    return () => {
      active = false
    }
  }, [])

  async function sendQuestion() {
    const normalized = question.trim()
    if (!normalized || sending || !status?.enabled) return

    setSending(true)
    setError(null)
    setMessages(current => [...current, { role: 'user', content: normalized }])
    setQuestion('')

    try {
      const response = await fetch('/api/ai/coach', {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: normalized,
          history: messages.slice(-8),
        }),
      })

      const payload = await response.json() as AIReply | { detail?: string }
      if (!response.ok) {
        throw new Error('detail' in payload && payload.detail
          ? payload.detail
          : 'Le moteur IA n’a pas pu répondre.')
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
    <section className="mt-6 overflow-hidden rounded-2xl border border-[var(--oc-border)] bg-[var(--oc-surface)] shadow-sm">
      <div className="flex items-center gap-3 border-b border-[var(--oc-border)] px-4 py-4 sm:px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-500/10 text-violet-600 dark:text-violet-300">
          <Bot className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-[var(--oc-text)] dark:text-white">Assistant IA local</h2>
          <p className="mt-0.5 text-[10px] text-[var(--oc-muted)]">Analyse tes données sportives en lecture seule</p>
        </div>
        <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[9px] font-semibold text-emerald-700 dark:text-emerald-300">
          Ollama · local
        </span>
      </div>

      <div className="space-y-3 p-4 sm:p-5">
        {statusError && (
          <p role="alert" className="rounded-lg bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-300">{statusError}</p>
        )}

        {status && !status.enabled && (
          <div className="rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] p-4">
            <p className="text-sm font-medium text-[var(--oc-text)] dark:text-white">Moteur IA désactivé</p>
            <p className="mt-1 text-xs leading-5 text-[var(--oc-muted)]">
              L’assistant est volontairement désactivé par défaut. Active-le côté serveur dans la configuration OpenCoach pour commencer à l’utiliser.
            </p>
          </div>
        )}

        {status?.enabled && (
          <>
            <div className="flex items-start gap-2 rounded-lg bg-violet-500/[0.06] p-3 text-[11px] leading-5 text-[var(--oc-muted)]">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-violet-500" />
              L’assistant reçoit un instantané sportif calculé par OpenCoach. Il peut l’expliquer, mais ne modifie jamais ton planning ni tes données COROS.
            </div>

            {messages.length > 0 && (
              <div aria-live="polite" className="max-h-[360px] space-y-3 overflow-y-auto rounded-xl bg-[var(--oc-surface-muted)] p-3">
                {messages.map((message, index) => (
                  <div key={index} className={message.role === 'user' ? 'ml-6 rounded-xl bg-emerald-500/10 p-3' : 'mr-6 rounded-xl bg-[var(--oc-surface)] p-3'}>
                    <p className="mb-1 text-[9px] font-bold uppercase tracking-wide text-[var(--oc-muted)]">
                      {message.role === 'user' ? 'Toi' : 'OpenCoach IA'}
                    </p>
                    <p className="whitespace-pre-wrap text-xs leading-5 text-[var(--oc-text)] dark:text-[var(--oc-text-secondary)]">{message.content}</p>
                  </div>
                ))}
              </div>
            )}

            {error && <p role="alert" className="text-xs text-rose-600 dark:text-rose-300">{error}</p>}

            <form
              className="flex flex-col gap-2 sm:flex-row"
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
                rows={2}
                placeholder="Ex. : Comment interpréter ma charge récente ?"
                className="min-h-[68px] flex-1 resize-y rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface)] px-3 py-2.5 text-xs text-[var(--oc-text)] outline-none transition focus:border-violet-500 dark:text-white"
              />
              <button
                type="submit"
                disabled={!question.trim() || sending}
                className="inline-flex min-h-10 items-center justify-center gap-2 self-end rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40 sm:self-stretch"
              >
                {sending ? 'Analyse…' : 'Envoyer'}
                <Send className="h-3.5 w-3.5" />
              </button>
            </form>
            <p className="text-[9px] text-[var(--oc-muted)]">Réponses générées localement · les 8 derniers messages sont transmis pour garder le fil de la conversation. L’historique n’est pas enregistré durablement.</p>
          </>
        )}
      </div>
    </section>
  )
}
