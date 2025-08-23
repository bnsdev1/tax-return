// React Query hooks for API calls

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type {
  CreateTaxReturnRequest,
  CreateArtifactRequest,
} from '../types/api';

// Tax Returns
export function useTaxReturn(id: number) {
  return useQuery({
    queryKey: ['taxReturn', id],
    queryFn: () => apiClient.getTaxReturn(id),
    enabled: !!id,
  });
}

export function useTaxReturnStatus(id: number, enabled = true) {
  return useQuery({
    queryKey: ['taxReturnStatus', id],
    queryFn: () => apiClient.getTaxReturnStatus(id),
    enabled: enabled && !!id,
    refetchInterval: (query) => {
      // Poll every 2 seconds if status is in progress
      if (query.state.data?.status === 'in_progress') {
        return 2000;
      }
      return false;
    },
  });
}

export function useCreateTaxReturn() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateTaxReturnRequest) => apiClient.createTaxReturn(data),
    onSuccess: () => {
      // Invalidate any relevant queries
      queryClient.invalidateQueries({ queryKey: ['taxReturns'] });
    },
  });
}

export function useStartBuildJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (returnId: number) => apiClient.startBuildJob(returnId),
    onSuccess: (_, returnId) => {
      // Invalidate status query to start polling
      queryClient.invalidateQueries({ queryKey: ['taxReturnStatus', returnId] });
    },
  });
}

// Artifacts
export function useArtifacts(returnId: number) {
  return useQuery({
    queryKey: ['artifacts', returnId],
    queryFn: () => apiClient.getArtifacts(returnId),
    enabled: !!returnId,
  });
}

export function useCreateArtifact() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ returnId, data }: { returnId: number; data: CreateArtifactRequest }) =>
      apiClient.createArtifact(returnId, data),
    onSuccess: (_, { returnId }) => {
      queryClient.invalidateQueries({ queryKey: ['artifacts', returnId] });
    },
  });
}

export function useUploadFile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ returnId, artifactId, file }: { returnId: number; artifactId: number; file: File }) =>
      apiClient.uploadFile(returnId, artifactId, file),
    onSuccess: (_, { returnId }) => {
      queryClient.invalidateQueries({ queryKey: ['artifacts', returnId] });
    },
  });
}