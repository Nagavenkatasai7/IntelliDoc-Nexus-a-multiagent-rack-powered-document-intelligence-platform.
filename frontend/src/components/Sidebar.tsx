import { useState } from 'react'
import { MessageSquare, Plus, PanelLeftClose, PanelLeft } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useChatStore } from '@/stores/chatStore'
import { listSessions } from '@/services/api'
import DocumentUpload from './DocumentUpload'
import DocumentList from './DocumentList'
import { formatDate, truncate } from '@/lib/utils'

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { clearChat, setSessionId, setMessages } = useChatStore()

  const { data: sessionsData } = useQuery({
    queryKey: ['sessions'],
    queryFn: listSessions,
    refetchInterval: 10000,
  })

  const sessions = sessionsData?.sessions || []

  if (collapsed) {
    return (
      <aside className="w-12 border-r bg-card flex flex-col items-center py-3 gap-2">
        <button
          onClick={() => setCollapsed(false)}
          className="p-2 rounded-lg hover:bg-secondary transition-colors"
          title="Expand sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
        <button
          onClick={clearChat}
          className="p-2 rounded-lg hover:bg-secondary transition-colors"
          title="New conversation"
        >
          <Plus className="h-4 w-4" />
        </button>
      </aside>
    )
  }

  return (
    <aside className="w-80 border-r bg-card flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h1 className="text-lg font-bold bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
          IntelliDoc Nexus
        </h1>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      {/* New Chat */}
      <div className="p-3 border-b">
        <button
          onClick={clearChat}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed hover:bg-secondary hover:border-primary/30 transition-colors text-sm"
        >
          <Plus className="h-4 w-4" />
          New Conversation
        </button>
      </div>

      {/* Document Upload */}
      <div className="p-3 border-b">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Upload Documents
        </h2>
        <DocumentUpload />
      </div>

      {/* Document List */}
      <div className="p-3 border-b flex-shrink-0 max-h-[220px] overflow-y-auto">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Your Documents
        </h2>
        <DocumentList />
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-3">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Chat History
        </h2>
        {sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground py-2">No conversations yet</p>
        ) : (
          <div className="space-y-0.5">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => {
                  setSessionId(session.id)
                  setMessages(session.messages)
                }}
                className="w-full text-left p-2.5 rounded-lg hover:bg-secondary transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary shrink-0" />
                  <span className="text-sm truncate">
                    {truncate(session.title || 'Untitled', 28)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground ml-[22px] mt-0.5">
                  {formatDate(session.updated_at)} · {session.messages.length} msgs
                </p>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
