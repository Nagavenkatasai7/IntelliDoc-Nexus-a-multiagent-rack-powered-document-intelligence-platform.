import { useState, useCallback } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { streamChat, sendMessage } from '@/services/api'
import type { ChatMessage } from '@/types'

export function useChat() {
  const [error, setError] = useState<string | null>(null)

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

  const sendQuery = useCallback(
    async (query: string) => {
      if (!query.trim() || isStreaming) return
      setError(null)

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: query,
        created_at: new Date().toISOString(),
      }
      addMessage(userMessage)
      setIsStreaming(true)
      resetStreamContent()

      try {
        streamChat(
          query,
          currentSessionId || undefined,
          selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
          (text) => appendStreamContent(text),
          (sources) => {
            const content = useChatStore.getState().streamingContent
            addMessage({
              id: crypto.randomUUID(),
              role: 'assistant',
              content,
              sources,
              created_at: new Date().toISOString(),
            })
            resetStreamContent()
            setIsStreaming(false)
          },
          (_messageId) => {
            setIsStreaming(false)
          },
        )
      } catch {
        try {
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
        } catch (err) {
          setError('Failed to get response. Please try again.')
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            created_at: new Date().toISOString(),
          })
        }
        setIsStreaming(false)
      }
    },
    [
      isStreaming,
      currentSessionId,
      selectedDocumentIds,
      addMessage,
      setSessionId,
      setIsStreaming,
      appendStreamContent,
      resetStreamContent,
    ],
  )

  return {
    messages,
    isStreaming,
    streamingContent,
    error,
    sendQuery,
    clearChat,
  }
}
