import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Trash2, Loader2, Clock, CheckCircle2, XCircle } from 'lucide-react'
import { listDocuments, deleteDocument } from '@/services/api'
import { formatFileSize, formatDate } from '@/lib/utils'
import { useChatStore } from '@/stores/chatStore'
import type { Document } from '@/types'

const STATUS_ICONS = {
  pending: <Clock className="h-4 w-4 text-yellow-500" />,
  processing: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
  completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-destructive" />,
}

export default function DocumentList() {
  const queryClient = useQueryClient()
  const { selectedDocumentIds, setSelectedDocuments } = useChatStore()

  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => listDocuments(),
    refetchInterval: 5000,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const toggleDocument = (id: string) => {
    setSelectedDocuments(
      selectedDocumentIds.includes(id)
        ? selectedDocumentIds.filter((d) => d !== id)
        : [...selectedDocumentIds, id],
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const documents = data?.documents || []

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <FileText className="h-10 w-10 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No documents uploaded yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {documents.map((doc: Document) => (
        <div
          key={doc.id}
          className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
            selectedDocumentIds.includes(doc.id)
              ? 'bg-primary/10 border border-primary/20'
              : 'hover:bg-secondary/50'
          }`}
          onClick={() => toggleDocument(doc.id)}
        >
          <div className="shrink-0">{STATUS_ICONS[doc.status]}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{doc.original_filename}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(doc.file_size)}
              {doc.page_count && ` · ${doc.page_count} pages`}
              {doc.chunk_count > 0 && ` · ${doc.chunk_count} chunks`}
            </p>
          </div>
          <button
            className="shrink-0 p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
            onClick={(e) => {
              e.stopPropagation()
              deleteMutation.mutate(doc.id)
            }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}
