import { MessageSquarePlus, PanelLeft, Search, ShieldCheck } from 'lucide-react'

import type { ChatMessage } from '../../types/gov'
import { cn } from '../../lib/utils'

type ChatSidebarProps = {
  messages: ChatMessage[]
  online: boolean
}

function summarize(message: ChatMessage) {
  const single = message.content.replace(/\s+/g, ' ').trim()
  return single.length > 34 ? `${single.slice(0, 34)}...` : single
}

export function ChatSidebar({ messages, online }: ChatSidebarProps) {
  const history = messages.filter((message) => message.role === 'user').slice(-8).reverse()

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-black/10 bg-[#171717] text-[#ececec] lg:flex">
      <div className="flex items-center justify-between px-4 py-4">
        <button
          type="button"
          className="flex size-9 items-center justify-center rounded-lg text-[#b4b4b4] transition hover:bg-white/8 hover:text-white"
        >
          <PanelLeft className="size-4" />
        </button>
        <button
          type="button"
          className="flex size-9 items-center justify-center rounded-lg text-[#b4b4b4] transition hover:bg-white/8 hover:text-white"
        >
          <Search className="size-4" />
        </button>
      </div>

      <div className="px-3">
        <button
          type="button"
          className="flex w-full items-center gap-3 rounded-xl border border-white/10 bg-white/6 px-3 py-3 text-sm text-white transition hover:bg-white/10"
        >
          <MessageSquarePlus className="size-4" />
          New chat
        </button>
      </div>

      <div className="mt-6 flex-1 overflow-y-auto px-2 pb-4">
        <p className="px-3 pb-2 text-[11px] uppercase tracking-[0.18em] text-[#8b8b8b]">
          Recent
        </p>
        <div className="space-y-1">
          {history.length === 0 ? (
            <div className="px-3 py-2 text-sm text-[#8b8b8b]">No conversation yet</div>
          ) : (
            history.map((message) => (
              <button
                key={message.id}
                type="button"
                className="w-full rounded-xl px-3 py-2 text-left text-sm text-[#d5d5d5] transition hover:bg-white/8 hover:text-white"
              >
                {summarize(message)}
              </button>
            ))
          )}
        </div>
      </div>

      <div className="border-t border-white/8 p-3">
        <div
          className={cn(
            'flex items-center gap-2 rounded-xl px-3 py-2 text-sm',
            online ? 'bg-[#1f352a] text-[#d5f7df]' : 'bg-[#2d2222] text-[#ffd0d0]',
          )}
        >
          <ShieldCheck className="size-4" />
          {online ? 'Backend connected' : 'Backend offline'}
        </div>
      </div>
    </aside>
  )
}
