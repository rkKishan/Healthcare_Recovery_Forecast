import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import { Icon, VisuallyHidden } from './ui'

/**
 * The assistant panel.
 *
 * A slide-over available on every signed-in page. It renders nothing at all
 * when the server reports the assistant unconfigured -- a launcher that only
 * produces an error when pressed is worse than no launcher.
 *
 * Conversation state is deliberately local and unpersisted. The server
 * reconstructs tool calls from scratch on every turn and only accepts plain
 * user/assistant text back, so nothing here is load-bearing; a refresh
 * starting a clean thread is the honest behaviour rather than a limitation.
 */

const SUGGESTIONS = {
  doctor: [
    'Who on my caseload is overdue?',
    'Which of my patients are due out in the next 48 hours?',
    'What drives a long stay for an elderly emergency admission?',
  ],
  analyst: [
    'How is bed occupancy looking over the next two weeks?',
    'Is the model still accurate enough to trust?',
    'Which features matter most for length of stay?',
  ],
  admin: [
    'How is bed occupancy looking over the next two weeks?',
    'Who on my caseload is overdue?',
    'Is the model still accurate enough to trust?',
  ],
}

/** Tool names as a clinician would describe them. */
const TOOL_LABELS = {
  score_admission: 'scored the admission',
  my_caseload: 'read your caseload',
  cohort_overview: 'read the cohort forecast',
  model_metrics: 'checked model metrics',
  global_drivers: 'read feature importance',
  list_datasets: 'listed your uploads',
}

export default function Assistant() {
  const [config, setConfig] = useState(null)
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)

  const listRef = useRef(null)
  const inputRef = useRef(null)
  const launcherRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    api
      .chatConfig()
      .then((value) => {
        if (!cancelled) setConfig(value)
      })
      .catch(() => {
        // An assistant that cannot report on itself is simply absent.
        if (!cancelled) setConfig({ enabled: false })
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Keep the newest turn in view as the conversation grows.
  useEffect(() => {
    const node = listRef.current
    if (node) node.scrollTop = node.scrollHeight
  }, [messages, pending])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // Escape closes and hands focus back to the launcher that opened it.
  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = (event) => {
      if (event.key !== 'Escape') return
      event.preventDefault()
      setOpen(false)
      launcherRef.current?.focus()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open])

  if (!config?.enabled) return null

  const suggestions = SUGGESTIONS[config.role] ?? SUGGESTIONS.doctor

  async function send(text) {
    const trimmed = text.trim()
    if (!trimmed || pending) return

    // The history sent is the state *before* this turn -- the server appends
    // the new message itself.
    const history = messages.map(({ role, content }) => ({ role, content }))

    setMessages((prior) => [...prior, { role: 'user', content: trimmed }])
    setDraft('')
    setError(null)
    setPending(true)

    try {
      const result = await api.chat(trimmed, history)
      setMessages((prior) => [
        ...prior,
        {
          role: 'assistant',
          content: result.reply,
          tools: result.tools_used ?? [],
        },
      ])
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err
          : new ApiError('Something went wrong talking to the assistant.'),
      )
      // Drop the unanswered question so retrying does not duplicate it.
      setMessages((prior) => prior.slice(0, -1))
      setDraft(trimmed)
    } finally {
      setPending(false)
    }
  }

  return (
    <>
      <button
        className="assist-launcher"
        ref={launcherRef}
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="assistant-panel"
      >
        <Icon name="inbox" size={18} />
        <VisuallyHidden>
          {open ? 'Close the assistant' : 'Open the assistant'}
        </VisuallyHidden>
      </button>

      <aside
        className={`assist-panel${open ? ' open' : ''}`}
        id="assistant-panel"
        aria-label="Assistant"
        hidden={!open}
      >
        <header className="assist-head">
          <div>
            <div className="assist-title">Assistant</div>
            <div className="assist-sub">
              Answers from your data — not a clinical adviser
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setOpen(false)
              launcherRef.current?.focus()
            }}
            aria-label="Close the assistant"
          >
            <Icon name="close" />
          </button>
        </header>

        <div className="assist-log" ref={listRef} role="log" aria-live="polite">
          {messages.length === 0 && (
            <div className="assist-intro">
              <p>
                Ask about the forecast, your caseload, or the model behind it.
                Every figure comes from a live lookup — nothing here is
                estimated by the assistant.
              </p>
              <div className="assist-suggestions">
                {suggestions.map((text) => (
                  <button key={text} onClick={() => send(text)}>
                    {text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div className={`assist-msg assist-${message.role}`} key={index}>
              <div className="assist-bubble">{message.content}</div>
              {message.tools?.length > 0 && (
                <div className="assist-tools">
                  <Icon name="check" size={12} />
                  {message.tools
                    .map((name) => TOOL_LABELS[name] ?? name)
                    .join(' · ')}
                </div>
              )}
            </div>
          ))}

          {pending && (
            <div className="assist-msg assist-assistant">
              <div className="assist-bubble assist-thinking">
                <span />
                <span />
                <span />
                <VisuallyHidden>Working on it</VisuallyHidden>
              </div>
            </div>
          )}

          {error && (
            <div className="assist-error" role="alert">
              <strong>{error.message}</strong>
              {error.hint && <div className="assist-hint">{error.hint}</div>}
            </div>
          )}
        </div>

        <form
          className="assist-composer"
          onSubmit={(event) => {
            event.preventDefault()
            send(draft)
          }}
        >
          <label htmlFor="assist-input">
            <VisuallyHidden>Message the assistant</VisuallyHidden>
          </label>
          <textarea
            id="assist-input"
            ref={inputRef}
            value={draft}
            rows={1}
            maxLength={2000}
            placeholder="Ask about a forecast…"
            onChange={(event) => setDraft(event.target.value)}
            /* Enter sends; Shift+Enter is a newline. */
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                send(draft)
              }
            }}
          />
          <button
            className="btn btn-primary btn-sm"
            type="submit"
            disabled={pending || !draft.trim()}
          >
            <Icon name="arrow-right" size={15} />
            <VisuallyHidden>Send</VisuallyHidden>
          </button>
        </form>
      </aside>
    </>
  )
}
