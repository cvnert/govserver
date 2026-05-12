import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import type { ThemeMode } from '../../App'
import { createSource, discoverSource, fetchPolicyExtraction, pingHealth, streamGovernmentKnowledge } from '../../lib/gov-api'
import type { ChatMessage, ChatSession, Citation, PolicyExtraction, SourceCreateRequest } from '../../types/gov'
import { ChatSender } from './chat-sender'
import { ChatShell } from './chat-shell'
import { ChatThread } from './chat-thread'
import { PolicyExtractionDrawer } from './policy-extraction-drawer'
import { SourceCreateModal } from './source-create-modal'

const DEFAULT_SESSION_KEY = 'default'
const DEFAULT_SESSION_LABEL = 'newChat'

type GovChatPageProps = {
  themeMode: ThemeMode
  onThemeModeChange: (mode: ThemeMode) => void
}

export function GovChatPage({ themeMode, onThemeModeChange }: GovChatPageProps) {
  const { t } = useTranslation()
  const dark = themeMode === 'dark'
  const [messagesBySession, setMessagesBySession] = useState<Record<string, ChatMessage[]>>({
    [DEFAULT_SESSION_KEY]: [],
  })
  const [sessions, setSessions] = useState<ChatSession[]>([
    { key: DEFAULT_SESSION_KEY, label: t(DEFAULT_SESSION_LABEL) },
  ])
  const [activeSessionKey, setActiveSessionKey] = useState(DEFAULT_SESSION_KEY)
  const [submitting, setSubmitting] = useState(false)
  const [bootError, setBootError] = useState('')
  const [presetPrompt, setPresetPrompt] = useState<string | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerLoading, setDrawerLoading] = useState(false)
  const [drawerError, setDrawerError] = useState('')
  const [extraction, setExtraction] = useState<PolicyExtraction | null>(null)
  const [sourceModalOpen, setSourceModalOpen] = useState(false)
  const [sourceSaving, setSourceSaving] = useState(false)
  const listRef = useRef<HTMLDivElement | null>(null)

  const messages = messagesBySession[activeSessionKey] ?? []

  useEffect(() => {
    let active = true

    void pingHealth()
      .then((ok) => {
        if (!ok && active) {
          setBootError(t('backendUnreachable'))
        }
      })
      .catch(() => {
        if (active) {
          setBootError(t('backendUnreachable'))
        }
      })

    return () => {
      active = false
    }
  }, [t])

  useEffect(() => {
    setSessions((current) =>
      current.map((session) =>
        session.label === 'New chat' || session.label === '新对话'
          ? { ...session, label: t(DEFAULT_SESSION_LABEL) }
          : session,
      ),
    )
  }, [t])

  useEffect(() => {
    if (!listRef.current) {
      return
    }

    listRef.current.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages])

  function updateSessionTitle(question: string) {
    const title = question.length > 28 ? `${question.slice(0, 28)}...` : question
    setSessions((current) =>
      current.map((session) =>
        session.key === activeSessionKey && session.label === t(DEFAULT_SESSION_LABEL)
          ? { ...session, label: title }
          : session,
      ),
    )
  }

  async function handleSubmit(question: string) {
    const sessionKey = activeSessionKey
    const history = (messagesBySession[sessionKey] ?? [])
      .filter((message) => !message.pending && !message.error && message.content.trim())
      .slice(-6)
      .map((message) => ({
        role: message.role,
        content: message.content,
      }))

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
    }
    const pendingMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      pending: true,
    }

    setMessagesBySession((current) => ({
      ...current,
      [sessionKey]: [...(current[sessionKey] ?? []), userMessage, pendingMessage],
    }))
    setSubmitting(true)
    setBootError('')
    setPresetPrompt(null)
    updateSessionTitle(question)

    try {
      await streamGovernmentKnowledge(question, history, (event) => {
        if (event.type === 'delta') {
          setMessagesBySession((current) => ({
            ...current,
            [sessionKey]: (current[sessionKey] ?? []).map((message) =>
              message.id === pendingMessage.id
                ? {
                    ...message,
                    content: `${message.content}${event.content}`,
                    pending: false,
                  }
                : message,
            ),
          }))
          return
        }

        if (event.type === 'citations') {
          setMessagesBySession((current) => ({
            ...current,
            [sessionKey]: (current[sessionKey] ?? []).map((message) =>
              message.id === pendingMessage.id
                ? {
                    ...message,
                    citations: event.citations,
                    pending: false,
                  }
                : message,
            ),
          }))
          return
        }

        if (event.type === 'error') {
          setMessagesBySession((current) => ({
            ...current,
            [sessionKey]: (current[sessionKey] ?? []).map((message) =>
              message.id === pendingMessage.id
                ? {
                    ...message,
                    content: event.message,
                    pending: false,
                    error: true,
                  }
                : message,
            ),
          }))
          return
        }

        if (event.type === 'done') {
          setMessagesBySession((current) => ({
            ...current,
            [sessionKey]: (current[sessionKey] ?? []).map((message) =>
              message.id === pendingMessage.id
                ? {
                    ...message,
                    pending: false,
                  }
                : message,
            ),
          }))
        }
      })
    } catch (error) {
      setMessagesBySession((current) => ({
        ...current,
        [sessionKey]: (current[sessionKey] ?? []).map((message) =>
          message.id === pendingMessage.id
            ? {
                ...message,
                content: error instanceof Error ? error.message : t('requestFailed'),
                pending: false,
                error: true,
              }
            : message,
        ),
      }))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleOpenExtraction(citation: Citation) {
    if (!citation.id) {
      return
    }

    setDrawerOpen(true)
    setDrawerLoading(true)
    setDrawerError('')
    setExtraction(null)

    try {
      const result = await fetchPolicyExtraction(citation.id)
      setExtraction(result)
    } catch (error) {
      setDrawerError(error instanceof Error ? error.message : t('requestFailed'))
    } finally {
      setDrawerLoading(false)
    }
  }

  function handleNewChat() {
    const key = crypto.randomUUID()
    setMessagesBySession((current) => ({ ...current, [key]: [] }))
    setSessions((current) => [{ key, label: t(DEFAULT_SESSION_LABEL) }, ...current])
    setActiveSessionKey(key)
    setPresetPrompt(null)
  }

  async function handleCreateSource(values: SourceCreateRequest) {
    setSourceSaving(true)
    try {
      await createSource(values)
      setSourceModalOpen(false)
    } catch (error) {
      setBootError(error instanceof Error ? error.message : t('requestFailed'))
      throw error
    } finally {
      setSourceSaving(false)
    }
  }

  const sessionItems = useMemo(() => sessions, [sessions])

  return (
    <>
      <ChatShell
        sessions={sessionItems}
        activeSessionKey={activeSessionKey}
        onSessionChange={setActiveSessionKey}
        onNewChat={handleNewChat}
        onAddSource={() => setSourceModalOpen(true)}
        themeMode={themeMode}
        onThemeModeChange={onThemeModeChange}
      >
        <section className={dark ? 'flex min-h-0 flex-1 flex-col bg-[#212121]' : 'flex min-h-0 flex-1 flex-col bg-[#ffffff]'}>
          <div ref={listRef} className={dark ? 'flex-1 overflow-y-auto bg-[#212121]' : 'flex-1 overflow-y-auto bg-[#ffffff]'}>
            {bootError ? (
              <div className={dark ? 'mx-auto mt-4 max-w-3xl rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200' : 'mx-auto mt-4 max-w-3xl rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700'}>
                {bootError}
              </div>
            ) : null}

            <ChatThread
              messages={messages}
              onPromptClick={setPresetPrompt}
              onOpenExtraction={handleOpenExtraction}
              dark={dark}
            />
          </div>

          <div className={dark ? 'border-t border-white/8 bg-[#212121] px-4 pb-5 pt-4 sm:px-6' : 'border-t border-black/6 bg-[#ffffff] px-4 pb-5 pt-4 sm:px-6'}>
            <ChatSender disabled={submitting} preset={presetPrompt} onSubmit={handleSubmit} dark={dark} />
          </div>
        </section>
      </ChatShell>

      <PolicyExtractionDrawer
        open={drawerOpen}
        dark={dark}
        loading={drawerLoading}
        error={drawerError}
        data={extraction}
        onClose={() => setDrawerOpen(false)}
      />
      <SourceCreateModal
        open={sourceModalOpen}
        loading={sourceSaving}
        dark={dark}
        onClose={() => setSourceModalOpen(false)}
        onDiscover={discoverSource}
        onSubmit={handleCreateSource}
      />
    </>
  )
}
