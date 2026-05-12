import { EditOutlined, SearchOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { Conversations } from '@ant-design/x'
import { useTranslation } from 'react-i18next'

import type { ChatSession } from '../../types/gov'

type ConversationSidebarProps = {
  items: ChatSession[]
  activeKey: string
  onNewChat: () => void
  onChange: (key: string) => void
  dark: boolean
}

export function ConversationSidebar({
  items,
  activeKey,
  onNewChat,
  onChange,
  dark,
}: ConversationSidebarProps) {
  const { t } = useTranslation()

  return (
    <aside
      className={
        dark
          ? 'flex h-full w-[260px] shrink-0 flex-col border-r border-white/8 bg-[#171717] px-3 py-3 text-white'
          : 'flex h-full w-[260px] shrink-0 flex-col border-r border-black/6 bg-[#f0f2f5] px-3 py-3 text-[#111827]'
      }
    >
      <div className="mb-3 flex items-center justify-between px-2">
        <Button
          type="text"
          shape="circle"
          icon={<SearchOutlined />}
          className={dark ? '!text-[#bfbfbf]' : '!text-[#4b5563]'}
        />
        <Button
          type="text"
          shape="circle"
          icon={<EditOutlined />}
          className={dark ? '!text-[#bfbfbf]' : '!text-[#4b5563]'}
          onClick={onNewChat}
        />
      </div>

      <Button
        type="primary"
        block
        className={
          dark
            ? '!mb-4 !h-10 !rounded-xl !border-0 !bg-[#303030] !text-white !shadow-none hover:!bg-[#3a3a3a]'
            : '!mb-4 !h-10 !rounded-xl !border-0 !bg-[#111827] !text-white !shadow-none hover:!bg-[#1f2937]'
        }
        icon={<EditOutlined />}
        onClick={onNewChat}
      >
        {t('newChat')}
      </Button>

      <Conversations
        items={items}
        activeKey={activeKey}
        onActiveChange={(key) => onChange(String(key))}
        className={`gov-conversations ${dark ? 'gov-conversations-dark' : 'gov-conversations-light'} flex-1 overflow-y-auto`}
      />
    </aside>
  )
}
