export interface Document {
  id: string
  filename: string
  original_filename: string
  file_type: 'pdf' | 'docx' | 'txt' | 'image'
  file_size: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  page_count: number | null
  chunk_count: number
  processing_time_ms: number | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  page_size: number
}

export interface SourceReference {
  source_index: number
  document_id: string
  document_name: string
  chunk_id: string
  chunk_index?: number
  content_preview: string
  page_number: number | null
  section_title?: string
  relevance_score: number
  score?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources?: SourceReference[]
  created_at: string
}

export interface ChatSession {
  id: string
  title: string | null
  is_shared: boolean
  document_ids: string[] | null
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

export interface ChatRequest {
  query: string
  session_id?: string
  document_ids?: string[]
  stream?: boolean
}

export interface ChatResponse {
  session_id: string
  message_id: string
  content: string
  sources: SourceReference[]
  latency_ms: number
}

export interface SearchResult {
  document_id: string
  document_name: string
  chunk_id: string
  content: string
  page_number: number | null
  score: number
}
