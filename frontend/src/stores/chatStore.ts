import { create } from 'zustand'
import type { ChatMessage, SourceReference } from '@/types'

interface ChatState {
  messages: ChatMessage[]
  currentSessionId: string | null
  selectedDocumentIds: string[]
  isStreaming: boolean
  streamingContent: string

  addMessage: (message: ChatMessage) => void
  setMessages: (messages: ChatMessage[]) => void
  setSessionId: (id: string | null) => void
  setSelectedDocuments: (ids: string[]) => void
  setIsStreaming: (streaming: boolean) => void
  appendStreamContent: (content: string) => void
  resetStreamContent: () => void
  clearChat: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  currentSessionId: null,
  selectedDocumentIds: [],
  isStreaming: false,
  streamingContent: '',

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setMessages: (messages) => set({ messages }),

  setSessionId: (id) => set({ currentSessionId: id }),

  setSelectedDocuments: (ids) => set({ selectedDocumentIds: ids }),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  appendStreamContent: (content) =>
    set((state) => ({ streamingContent: state.streamingContent + content })),

  resetStreamContent: () => set({ streamingContent: '' }),

  clearChat: () =>
    set({
      messages: [],
      currentSessionId: null,
      streamingContent: '',
      isStreaming: false,
    }),
}))
