import axios from 'axios'
import type { DocumentListResponse, ChatResponse, ChatSession, SearchResult } from '@/types'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60_000, // 60s default timeout
})

// Documents
export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300_000, // 5 min timeout for large files (embedding takes time)
  })
  return data
}

export async function listDocuments(page = 1, pageSize = 20): Promise<DocumentListResponse> {
  const { data } = await api.get('/documents', { params: { page, page_size: pageSize } })
  return data
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`)
}

// Chat
export async function sendMessage(
  query: string,
  sessionId?: string,
  documentIds?: string[],
): Promise<ChatResponse> {
  const { data } = await api.post('/chat', {
    query,
    session_id: sessionId,
    document_ids: documentIds,
    stream: false,
  })
  return data
}

export async function streamChat(
  query: string,
  sessionId?: string,
  documentIds?: string[],
  onChunk?: (text: string) => void,
  onSources?: (sources: ChatResponse['sources']) => void,
  onDone?: (messageId: string) => void,
  onError?: (error: string) => void,
): Promise<void> {
  const body = JSON.stringify({
    query,
    session_id: sessionId,
    document_ids: documentIds,
    stream: true,
  })

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000) // 2 min timeout

  try {
    const response = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      signal: controller.signal,
    })

    if (!response.ok) {
      const errText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Server error (${response.status}): ${errText}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) throw new Error('No response stream available')

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'text') onChunk?.(event.content)
            else if (event.type === 'sources') onSources?.(event.sources)
            else if (event.type === 'done') onDone?.(event.message_id)
          } catch {
            // Skip malformed events
          }
        }
      }
    }
  } catch (err) {
    const message = err instanceof Error
      ? (err.name === 'AbortError' ? 'Request timed out' : err.message)
      : 'Streaming failed'
    onError?.(message)
    throw err
  } finally {
    clearTimeout(timeout)
  }
}

// Sessions
export async function listSessions(): Promise<{ sessions: ChatSession[]; total: number }> {
  const { data } = await api.get('/sessions')
  return data
}

export async function getSession(id: string): Promise<ChatSession> {
  const { data } = await api.get(`/sessions/${id}`)
  return data
}

// Search
export async function searchDocuments(
  query: string,
  documentIds?: string[],
  topK = 10,
): Promise<{ results: SearchResult[]; total: number }> {
  const { data } = await api.post('/search', {
    query,
    document_ids: documentIds,
    top_k: topK,
  })
  return data
}

export default api
