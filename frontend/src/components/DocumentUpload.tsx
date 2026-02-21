import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { uploadDocument } from '@/services/api'
import { formatFileSize } from '@/lib/utils'

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
}

interface UploadStatus {
  file: File
  status: 'uploading' | 'processing' | 'success' | 'error'
  error?: string
}

export default function DocumentUpload() {
  const [uploads, setUploads] = useState<UploadStatus[]>([])
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        setUploads((prev) => [...prev, { file, status: 'uploading' }])

        // Show "processing" state after 3s to indicate embedding is happening
        const processingTimer = setTimeout(() => {
          setUploads((prev) =>
            prev.map((u) =>
              u.file === file && u.status === 'uploading'
                ? { ...u, status: 'processing' }
                : u,
            ),
          )
        }, 3000)

        try {
          await mutation.mutateAsync(file)
          clearTimeout(processingTimer)
          setUploads((prev) =>
            prev.map((u) => (u.file === file ? { ...u, status: 'success' } : u)),
          )
        } catch (err) {
          clearTimeout(processingTimer)
          const raw = err instanceof Error ? err.message : 'Upload failed'
          const message = raw.includes('timeout')
            ? 'Upload timed out — file may be too large. Try a smaller document.'
            : raw.includes('413')
              ? 'File exceeds maximum size limit (100MB)'
              : raw
          setUploads((prev) =>
            prev.map((u) =>
              u.file === file ? { ...u, status: 'error', error: message } : u,
            ),
          )
        }
      }

      // Clear completed uploads after delay
      setTimeout(() => {
        setUploads((prev) => prev.filter((u) => u.status === 'uploading' || u.status === 'processing'))
      }, 5000)
    },
    [mutation],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: 100 * 1024 * 1024,
  })

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
        {isDragActive ? (
          <p className="text-primary font-medium">Drop files here...</p>
        ) : (
          <>
            <p className="font-medium">Drag & drop documents here</p>
            <p className="text-sm text-muted-foreground mt-1">
              PDF, DOCX, TXT, or images (max 100MB)
            </p>
          </>
        )}
      </div>

      {uploads.length > 0 && (
        <div className="space-y-2">
          {uploads.map((upload, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50"
            >
              <FileText className="h-4 w-4 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{upload.file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(upload.file.size)}
                </p>
              </div>
              {upload.status === 'uploading' && (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-muted-foreground">Uploading</span>
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                </div>
              )}
              {upload.status === 'processing' && (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-muted-foreground">Processing</span>
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                </div>
              )}
              {upload.status === 'success' && (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              )}
              {upload.status === 'error' && (
                <div className="flex flex-col items-end">
                  <XCircle className="h-4 w-4 text-destructive" />
                  {upload.error && (
                    <span className="text-xs text-destructive mt-0.5 max-w-[200px] text-right">
                      {upload.error}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
