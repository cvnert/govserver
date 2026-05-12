import type { ReactNode } from 'react'
import { BulbOutlined, MoonOutlined } from '@ant-design/icons'
import { Button, Segmented } from 'antd'
import { useTranslation } from 'react-i18next'

import { ConversationSidebar } from './conversation-sidebar'
import type { ChatSession } from '../../types/gov'
import type { ThemeMode } from '../../App'

type ChatShellProps = {
  children: ReactNode
  sessions: ChatSession[]
  activeSessionKey: string
  onSessionChange: (key: string) => void
  onNewChat: () => void
  onAddSource: () => void
  themeMode: ThemeMode
  onThemeModeChange: (mode: ThemeMode) => void
}

export function ChatShell({
  children,
  sessions,
  activeSessionKey,
  onSessionChange,
  onNewChat,
  onAddSource,
  themeMode,
  onThemeModeChange,
}: ChatShellProps) {
  const { t, i18n } = useTranslation()
  const dark = themeMode === 'dark'

  return (
    <main
      className={dark ? 'h-screen bg-[#212121] text-[#ececec]' : 'h-screen bg-[#f7f7f8] text-[#111827]'}
    >
      <div className="flex h-full">
        <div className="hidden lg:block">
          <ConversationSidebar
            items={sessions}
            activeKey={activeSessionKey}
            onNewChat={onNewChat}
            onChange={onSessionChange}
            dark={dark}
          />
        </div>
        <section className={dark ? 'flex min-w-0 flex-1 flex-col bg-[#212121]' : 'flex min-w-0 flex-1 flex-col bg-[#ffffff]'}>
          <header
            className={
              dark
                ? 'flex items-center justify-between border-b border-white/8 px-4 py-3 text-[#ececec] lg:px-6'
                : 'flex items-center justify-between border-b border-black/6 px-4 py-3 text-[#111827] lg:px-6'
            }
          >
            <div className="flex items-center gap-3">
              <p className="text-sm font-medium">{t('appName')}</p>
            </div>

            <div className="flex items-center gap-2">
              <Button type="default" onClick={onAddSource}>
                {t('addSource')}
              </Button>
              <Button
                type="text"
                icon={dark ? <BulbOutlined /> : <MoonOutlined />}
                onClick={() => onThemeModeChange(dark ? 'light' : 'dark')}
                className={dark ? '!text-[#bfbfbf]' : '!text-[#4b5563]'}
              >
                {dark ? t('themeLight') : t('themeDark')}
              </Button>
              <Segmented
                size="small"
                value={i18n.language}
                onChange={(value) => void i18n.changeLanguage(String(value))}
                options={[
                  { label: t('langZh'), value: 'zh' },
                  { label: t('langEn'), value: 'en' },
                ]}
              />
            </div>
          </header>

          {children}
        </section>
      </div>
    </main>
  )
}
