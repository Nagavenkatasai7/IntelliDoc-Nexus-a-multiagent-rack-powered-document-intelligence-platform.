import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDocuments, uploadDocument, deleteDocument } from '@/services/api'

export function useDocuments(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['documents', page, pageSize],
    queryFn: () => listDocuments(page, pageSize),
    refetchInterval: 5000,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
