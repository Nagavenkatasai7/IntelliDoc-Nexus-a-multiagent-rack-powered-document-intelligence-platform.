import { useState } from 'react'
import { X, FileText, ChevronLeft, ChevronRight } from 'lucide-react'
import type { Document } from '@/types'
import { formatFileSize, formatDate } from '@/lib/utils'

interface Props {
  document: Document
  onClose: () => void
}

export default function DocumentViewer({ document: doc, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-card border rounded-xl shadow-2xl w-[90vw] max-w-3xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-primary" />
            <div>
              <h3 className="font-semibold">{doc.original_filename}</h3>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(doc.file_size)}
                {doc.page_count && ` · ${doc.page_count} pages`}
                {doc.chunk_count > 0 && ` · ${doc.chunk_count} chunks`}
                {' · '}Uploaded {formatDate(doc.created_at)}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-secondary transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground mb-2">Document Info</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Type</p>
                  <p className="font-medium uppercase">{doc.file_type}</p>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Status</p>
                  <p className="font-medium capitalize">{doc.status}</p>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Processing Time</p>
                  <p className="font-medium">
                    {doc.processing_time_ms ? `${doc.processing_time_ms}ms` : 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Chunks</p>
                  <p className="font-medium">{doc.chunk_count}</p>
                </div>
              </div>
            </div>

            {doc.error_message && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{doc.error_message}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
