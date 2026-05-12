import { RobotOutlined, UserOutlined } from '@ant-design/icons'
import { Avatar, Button, Typography } from 'antd'
import { Bubble, Welcome } from '@ant-design/x'
import { useTranslation } from 'react-i18next'

import type { ChatMessage, Citation } from '../../types/gov'

type ChatThreadProps = {
  messages: ChatMessage[]
  onPromptClick: (prompt: string) => void
  onOpenExtraction: (citation: Citation) => void
  dark: boolean
}

const roles = {
  assistant: {
    placement: 'start' as const,
    avatar: (
      <Avatar
        size={32}
        icon={<RobotOutlined />}
        style={{ background: '#10a37f', color: '#fff' }}
      />
    ),
    typing: { effect: 'typing' as const, step: 4, interval: 28 },
  },
  user: {
    placement: 'end' as const,
    avatar: (
      <Avatar
        size={32}
        icon={<UserOutlined />}
        style={{ background: '#e5e7eb', color: '#111827' }}
      />
    ),
    variant: 'shadow' as const,
  },
}

type CitationListProps = {
  message: ChatMessage
  dark: boolean
  t: (key: string) => string
  onOpenExtraction: (citation: Citation) => void
}

function CitationList({ message, dark, t, onOpenExtraction }: CitationListProps) {
  if (!message.citations?.length) {
    return null
  }

  return (
    <div className="mt-3 space-y-2">
      <div className="text-[11px] uppercase tracking-[0.16em] text-[#8c8c8c]">{t('sourceTitle')}</div>
      {message.citations.map((citation) => (
        <div
          key={`${citation.id ?? citation.url}-${citation.publish_time}`}
          className={
            dark
              ? 'rounded-xl border border-white/10 bg-white/6 px-3 py-3'
              : 'rounded-xl border border-black/6 bg-[#f7f7f8] px-3 py-3'
          }
        >
          <a href={citation.url} target="_blank" rel="noreferrer" className="block">
            <div className={dark ? 'text-sm font-medium text-[#f3f4f6]' : 'text-sm font-medium text-[#111827]'}>
              {citation.title}
            </div>
            <div className={dark ? 'mt-1 text-xs text-[#9ca3af]' : 'mt-1 text-xs text-[#6b7280]'}>
              {citation.publish_time || t('unknownDate')} · {citation.issuer || t('unknownSource')}
            </div>
            {citation.snippet ? (
              <div className={dark ? 'mt-2 line-clamp-4 text-xs text-[#cbd5e1]' : 'mt-2 line-clamp-4 text-xs text-[#4b5563]'}>
                {citation.snippet}
              </div>
            ) : null}
          </a>
          {citation.id ? (
            <div className="mt-3 flex justify-end">
              <Button size="small" type="default" onClick={() => onOpenExtraction(citation)}>
                {t('viewStructured')}
              </Button>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  )
}

export function ChatThread({ messages, onPromptClick, onOpenExtraction, dark }: ChatThreadProps) {
  const { t } = useTranslation()
  const starterPrompts = [t('prompts.ai'), t('prompts.talent'), t('prompts.notice')]

  if (!messages.length) {
    return (
      <div className="flex h-full items-center justify-center px-6">
        <div className="w-full max-w-3xl">
          <Welcome
            variant="borderless"
            title={t('welcomeTitle')}
            description={t('welcomeDescription')}
            className={dark ? '!bg-transparent !px-0 !text-[#f3f4f6]' : '!bg-transparent !px-0'}
            extra={
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {starterPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => onPromptClick(prompt)}
                    className={
                      dark
                        ? 'rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-[#d1d5db] transition hover:bg-white/10'
                        : 'rounded-full border border-black/10 bg-white px-4 py-2 text-sm text-[#374151] transition hover:bg-[#f3f4f6]'
                    }
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            }
          />
        </div>
      </div>
    )
  }

  const items = messages.map((message) => ({
    key: message.id,
    role: message.role,
    content: (
      <div>
        <Typography.Paragraph className="!mb-0 !whitespace-pre-wrap !text-[15px] !leading-7 !text-inherit">
          {message.content}
        </Typography.Paragraph>
        <CitationList message={message} dark={dark} t={t} onOpenExtraction={onOpenExtraction} />
      </div>
    ),
    loading: message.pending && !message.content,
  }))

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6">
      <Bubble.List
        items={items}
        role={roles}
        className={`gov-bubble-list ${dark ? 'gov-bubble-list-dark' : 'gov-bubble-list-light'}`}
        autoScroll
      />
    </div>
  )
}
