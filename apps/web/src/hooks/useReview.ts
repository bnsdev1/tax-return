// React Query hooks for review API calls

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type {
  ReviewPreviewResponse,
  ConfirmationResponse,
} from '../types/review';

// Review Preview
export function useReviewPreview(returnId: number) {
  return useQuery<ReviewPreviewResponse>({
    queryKey: ['reviewPreview', returnId],
    queryFn: () => apiClient.getReviewPreview(returnId),
    enabled: !!returnId,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

// Submit Confirmations
export function useSubmitConfirmations() {
  const queryClient = useQueryClient();

  return useMutation<
    ConfirmationResponse,
    Error,
    { returnId: number; confirmations: string[]; edits: any[] }
  >({
    mutationFn: ({ returnId, confirmations, edits }) =>
      apiClient.submitConfirmations(returnId, { confirmations, edits }),
    onSuccess: (_, { returnId }) => {
      // Invalidate the review preview to get updated data
      queryClient.invalidateQueries({ queryKey: ['reviewPreview', returnId] });
    },
  });
}