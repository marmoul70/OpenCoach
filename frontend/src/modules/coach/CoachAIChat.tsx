import { useState, type FormEvent } from 'react'
import { Brain, Check, LoaderCircle, Send, X } from 'lucide-react'

import {
  askAICoach,
  confirmAIDataProposal,
  rejectAIDataProposal,
} from '../../core/coach/aiApi'
import type {
  AIChatMessage,
  AIDataProposal,
} from '../../core/coach/aiApi'

interface DisplayMessage extends AIChatMessage {
  proposals?: AIDataProposal[]
}

const FIELD_LABELS: Record<string, string> = {
  height_cm: 'Taille',
  weight_kg: 'Poids',
  max_heart_rate: 'Fréquence cardiaque maximale',
  resting_heart_rate: 'Fréquence cardiaque au repos',
  vma: 'VMA',
  threshold_heart_rate_1: 'Seuil SV1',
  threshold_heart_rate_2: 'Seuil SV2',
  weekly_sessions: 'Séances par semaine',
  weekly_duration_minutes: 'Durée hebdomadaire',
  weekly_distance_km: 'Distance hebdomadaire',
  carbohydrates_per_hour: 'Glucides par heure',
  fluids_per_hour: 'Hydratation par heure',
  sodium_per_hour: 'Sodium par heure',
  fatigue_threshold: 'Seuil de fatigue',
}

export function CoachAIChat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      role: 'assistant',
      content: 'Je peux analyser tes données OpenCoach, répondre à tes questions et t’aider à compléter ton profil. Si une information importante manque, je te la demanderai.',
    },
  ])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeProposal, setActiveProposal] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = question.trim()
    if (!value || loading) return

    const history = messages.slice(-8).map(({ role, content }) => ({
      role,
      content,
    }))
    setMessages((current) => [...current, { role: 'user', content: value }])
    setQuestion('')
    setLoading(true)
    setError(null)

    try {
      const response = await askAICoach(value, history)
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.answer,
          proposals: response.data_proposals,
        },
      ])
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Impossible de contacter le coach IA.')
    } finally {
      setLoading(false)
    }
  }

  async function handleProposal(
    proposal: AIDataProposal,
    action: 'confirm' | 'reject',
  ) {
    if (activeProposal) return
    setActiveProposal(proposal.id)
    setError(null)
    try {
      const updated = action === 'confirm'
        ? await confirmAIDataProposal(proposal.id)
        : await rejectAIDataProposal(proposal.id)
      setMessages((current) => current.map((message) => ({
        ...message,
        proposals: message.proposals?.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      })))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La proposition n’a pas pu être traitée.')
    } finally {
      setActiveProposal(null)
    }
  }

  return (
    <section className="mb-4 overflow-hidden rounded-[16px] border border-[var(--oc-border)] bg-[var(--oc-surface)] shadow-[0_1px_3px_rgba(15,23,42,0.04)]">
      <div className="flex items-center gap-3 border-b border-[var(--oc-border)] px-4 py-3 sm:px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <Brain className="h-4.5 w-4.5" />
        </div>
        <div className="min-w-0">
          <h2 className="text-[13px] font-semibold text-[var(--oc-text)] dark:text-white">Coach IA</h2>
          <p className="text-[10px] text-[var(--oc-muted)]">Analyse ton profil et collecte les informations manquantes</p>
        </div>
        <span className="ml-auto rounded-full border border-emerald-500/20 bg-emerald-500/[0.06] px-2 py-1 text-[9px] font-semibold text-emerald-700 dark:text-emerald-400">Local</span>
      </div>

      <div className="max-h-[420px] space-y-3 overflow-y-auto px-4 py-4 sm:px-5">
        {messages.map((message, index) => (
          <div key={index} className={message.role === 'user' ? 'ml-auto max-w-[88%]' : 'mr-auto max-w-[94%]'}>
            <div className={message.role === 'user'
              ? 'rounded-2xl rounded-br-md bg-emerald-600 px-3.5 py-2.5 text-[12px] leading-5 text-white'
              : 'rounded-2xl rounded-bl-md bg-[var(--oc-surface-muted)] px-3.5 py-2.5 text-[12px] leading-5 text-[var(--oc-text)] dark:text-[var(--oc-text-secondary)]'}>
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
            {message.proposals?.map((proposal) => (
              <div key={proposal.id} className="mt-2 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.035] p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-semibold text-[var(--oc-text)] dark:text-white">Proposition de sauvegarde</p>
                  <span className={proposal.status === 'confirmed'
                    ? 'text-[9px] font-semibold text-emerald-600'
                    : proposal.status === 'pending'
                      ? 'text-[9px] font-semibold text-amber-600'
                      : 'text-[9px] font-semibold text-[var(--oc-muted)]'}>
                    {proposal.status === 'confirmed' ? 'Enregistrée' : proposal.status === 'pending' ? 'À confirmer' : proposal.status === 'rejected' ? 'Refusée' : proposal.status === 'expired' ? 'Expirée' : 'Conflit'}
                  </span>
                </div>
                <p className="mt-2 text-[12px] font-semibold text-[var(--oc-text)] dark:text-white">
                  {FIELD_LABELS[proposal.field_key] ?? proposal.field_key}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[var(--oc-muted)]">
                  {proposal.existing_value !== null && (
                    <span>Actuel : {proposal.existing_value} {proposal.unit}</span>
                  )}
                  <span>Nouveau : <strong className="text-[var(--oc-text)] dark:text-white">{proposal.value} {proposal.unit}</strong></span>
                </div>
                {proposal.status === 'pending' && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={activeProposal !== null}
                      onClick={() => void handleProposal(proposal, 'confirm')}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-[10px] font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                    >
                      {activeProposal === proposal.id ? <LoaderCircle className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                      Confirmer
                    </button>
                    <button
                      type="button"
                      disabled={activeProposal !== null}
                      onClick={() => void handleProposal(proposal, 'reject')}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--oc-border)] px-3 py-2 text-[10px] font-semibold text-[var(--oc-muted)] hover:bg-[var(--oc-surface-muted)] disabled:opacity-50"
                    >
                      <X className="h-3 w-3" />
                      Refuser
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-[11px] text-[var(--oc-muted)]">
            <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
            Le coach analyse ta demande…
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="mx-4 mb-3 rounded-lg border border-red-500/20 bg-red-500/[0.05] px-3 py-2 text-[10px] text-red-600 sm:mx-5">
          {error}
        </p>
      )}

      <form onSubmit={sendMessage} className="flex items-end gap-2 border-t border-[var(--oc-border)] p-3 sm:px-5">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
          rows={2}
          maxLength={4000}
          placeholder="Pose une question à ton coach…"
          aria-label="Message au coach IA"
          className="min-h-[42px] max-h-28 flex-1 resize-y rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] px-3 py-2.5 text-[12px] text-[var(--oc-text)] outline-none placeholder:text-[var(--oc-muted-soft)] focus:border-emerald-500/50 dark:text-white"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          aria-label="Envoyer le message"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </section>
  )
}
