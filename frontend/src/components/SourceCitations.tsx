import { useState } from 'react'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'
import type { SourceReference } from '@/types'
import { truncate } from '@/lib/utils'

interface Props {
  sources: SourceReference[]
}

export default function SourceCitations({ sources }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (!sources.length) return null

  return (
    <div className="mt-3 border-t border-border/50 pt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <FileText className="h-3 w-3" />
        <span>{sources.length} source(s)</span>
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {expanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, i) => (
            <div
              key={i}
              className="text-xs p-2 rounded bg-background/50 border border-border/30"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-primary">[Source {source.source_index}]</span>
                {source.page_number && (
                  <span className="text-muted-foreground">Page {source.page_number}</span>
                )}
                {(source.relevance_score || source.score) != null && (
                  <span className="text-muted-foreground">
                    Score: {(((source.relevance_score || source.score) ?? 0) * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <p className="text-muted-foreground leading-relaxed">
                {truncate(source.content_preview, 200)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
