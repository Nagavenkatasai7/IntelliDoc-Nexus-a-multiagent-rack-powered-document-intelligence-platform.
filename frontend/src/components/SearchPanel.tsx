import { useState } from 'react'
import { Search, FileText, Loader2, AlertCircle } from 'lucide-react'
import { searchDocuments } from '@/services/api'
import { useChatStore } from '@/stores/chatStore'
import type { SearchResult } from '@/types'
import { truncate } from '@/lib/utils'

export default function SearchPanel() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { selectedDocumentIds } = useChatStore()

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    setError(null)

    try {
      const data = await searchDocuments(
        query,
        selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
        10,
      )
      setResults(data.results)
    } catch (err) {
      setResults([])
      const msg = err instanceof Error ? err.message : ''
      if (msg.includes('500') || msg.includes('PINECONE')) {
        setError('Search service is temporarily unavailable. Documents may need to be re-indexed.')
      } else if (msg.includes('Network') || msg.includes('ERR_')) {
        setError('Could not connect to the search service. Please check the backend is running.')
      } else {
        setError('Search failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold mb-3">Semantic Search</h2>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search across all documents..."
              className="w-full rounded-lg border bg-background px-4 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
          </button>
        </div>
        {selectedDocumentIds.length > 0 && (
          <p className="text-xs text-muted-foreground mt-2">
            Searching {selectedDocumentIds.length} selected document(s)
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loading && error && (
          <div className="text-center py-12">
            <AlertCircle className="h-10 w-10 mx-auto mb-3 text-destructive opacity-60" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {!loading && searched && !error && results.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Search className="h-10 w-10 mx-auto mb-3 opacity-40" />
            <p className="text-sm">No results found for "{query}"</p>
            <p className="text-xs mt-1 opacity-70">
              Make sure documents are uploaded and have finished processing.
            </p>
          </div>
        )}

        {!loading &&
          results.map((result, i) => (
            <div
              key={`${result.chunk_id}-${i}`}
              className="p-4 rounded-lg border bg-card hover:border-primary/30 transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-primary" />
                {result.document_name && (
                  <span className="text-xs font-medium truncate max-w-[180px]">
                    {result.document_name}
                  </span>
                )}
                <span className="text-xs font-medium text-primary">
                  Score: {(result.score * 100).toFixed(1)}%
                </span>
                {result.page_number && (
                  <span className="text-xs text-muted-foreground">
                    Page {result.page_number}
                  </span>
                )}
              </div>
              <p className="text-sm leading-relaxed">{truncate(result.content, 400)}</p>
            </div>
          ))}
      </div>
    </div>
  )
}
