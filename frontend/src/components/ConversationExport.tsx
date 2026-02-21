import { useState } from 'react'
import { Download, FileText, Copy, Check } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import type { ChatMessage } from '@/types'

export default function ConversationExport() {
  const { messages, currentSessionId } = useChatStore()
  const [copied, setCopied] = useState(false)

  if (messages.length === 0) return null

  const toMarkdown = (msgs: ChatMessage[]): string => {
    const lines = ['# IntelliDoc Nexus Conversation\n']
    for (const msg of msgs) {
      const role = msg.role === 'user' ? '**You**' : '**IntelliDoc**'
      lines.push(`### ${role}`)
      lines.push(msg.content)
      if (msg.sources?.length) {
        lines.push('\n**Sources:**')
        for (const src of msg.sources) {
          const page = src.page_number ? ` (Page ${src.page_number})` : ''
          lines.push(`- Source ${src.source_index}${page}`)
        }
      }
      lines.push('')
    }
    return lines.join('\n')
  }

  const handleCopy = async () => {
    const md = toMarkdown(messages)
    await navigator.clipboard.writeText(md)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const md = toMarkdown(messages)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `intellidoc-conversation-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={handleCopy}
        className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        title="Copy as Markdown"
      >
        {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
      </button>
      <button
        onClick={handleDownload}
        className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        title="Download as Markdown"
      >
        <Download className="h-4 w-4" />
      </button>
    </div>
  )
}
