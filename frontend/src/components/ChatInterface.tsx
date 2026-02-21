import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, RotateCcw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChatStore } from '@/stores/chatStore'
import { streamChat, sendMessage } from '@/services/api'
import type { ChatMessage, SourceReference } from '@/types'
import SourceCitations from './SourceCitations'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const {
    messages,
    currentSessionId,
    selectedDocumentIds,
    isStreaming,
    streamingContent,
    addMessage,
    setSessionId,
    setIsStreaming,
    appendStreamContent,
    resetStreamContent,
    clearChat,
  } = useChatStore()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSubmit = async () => {
    const query = input.trim()
    if (!query || isStreaming) return

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    }
    addMessage(userMessage)
    setInput('')
    setIsStreaming(true)
    resetStreamContent()

    let pendingSources: ChatMessage['sources'] = undefined

    try {
      await streamChat(
        query,
        currentSessionId || undefined,
        selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
        (text) => {
          appendStreamContent(text)
        },
        (sources) => {
          pendingSources = sources
        },
        (messageId) => {
          const finalContent = useChatStore.getState().streamingContent
          addMessage({
            id: messageId || crypto.randomUUID(),
            role: 'assistant',
            content: finalContent,
            sources: pendingSources,
            created_at: new Date().toISOString(),
          })
          resetStreamContent()
          setIsStreaming(false)
        },
        (errorMsg) => {
          // Error callback from stream — will also throw, caught below
        },
      )
    } catch {
      // If streaming errored out, check if we had partial content
      const partialContent = useChatStore.getState().streamingContent
      resetStreamContent()
      setIsStreaming(false)

      if (partialContent) {
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: partialContent + '\n\n*(Response was interrupted)*',
          sources: pendingSources,
          created_at: new Date().toISOString(),
        })
      } else {
        // Fallback to non-streaming
        try {
          setIsStreaming(true)
          const response = await sendMessage(
            query,
            currentSessionId || undefined,
            selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
          )
          setSessionId(response.session_id)
          addMessage({
            id: response.message_id,
            role: 'assistant',
            content: response.content,
            sources: response.sources,
            created_at: new Date().toISOString(),
          })
        } catch {
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'Sorry, I encountered an error processing your request. Please try again.',
            created_at: new Date().toISOString(),
          })
        }
        setIsStreaming(false)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <div className="text-4xl mb-4">📄</div>
            <h2 className="text-xl font-semibold mb-2">IntelliDoc Nexus</h2>
            <p className="text-sm text-center max-w-md">
              Upload documents and ask questions. I'll find relevant information
              and provide answers with source citations.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              )}
              {msg.sources && msg.sources.length > 0 && (
                <SourceCitations sources={msg.sources} />
              )}
            </div>
          </div>
        ))}

        {/* Streaming content */}
        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-3 bg-secondary">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
              </div>
              <Loader2 className="h-4 w-4 animate-spin mt-2 text-muted-foreground" />
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && (
          <div className="flex justify-start">
            <div className="rounded-lg px-4 py-3 bg-secondary">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t p-4">
        <div className="flex items-end gap-2">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="p-2 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
              title="New conversation"
            >
              <RotateCcw className="h-5 w-5" />
            </button>
          )}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              className="w-full resize-none rounded-lg border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[48px] max-h-[200px]"
              rows={1}
              disabled={isStreaming}
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isStreaming}
              className="absolute right-2 bottom-2 p-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
        {selectedDocumentIds.length > 0 && (
          <p className="text-xs text-muted-foreground mt-2">
            Searching {selectedDocumentIds.length} selected document(s)
          </p>
        )}
      </div>
    </div>
  )
}
