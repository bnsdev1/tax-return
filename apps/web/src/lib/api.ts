import type {
  TaxReturn,
  CreateTaxReturnRequest,
  ArtifactMetadata,
  CreateArtifactRequest,
  TaxReturnStatus,
} from '../types/api';
import type {
  ReviewPreviewResponse,
  ConfirmationRequest,
  ConfirmationResponse,
} from '../types/review';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_URL as string) || 'http://localhost:8000';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getTaxReturn: (id: number) => request<TaxReturn>(`/api/returns/${id}`),
  getTaxReturnStatus: (id: number) => request<TaxReturnStatus>(`/api/returns/${id}/status`),
  createTaxReturn: (data: CreateTaxReturnRequest) =>
    request<TaxReturn>(`/api/returns`, { method: 'POST', body: JSON.stringify(data) }),
  startBuildJob: (id: number) => request<unknown>(`/api/returns/${id}/build`, { method: 'POST' }),
  getArtifacts: (returnId: number) => request<ArtifactMetadata[]>(`/api/returns/${returnId}/artifacts`),
  createArtifact: (returnId: number, data: CreateArtifactRequest) =>
    request<ArtifactMetadata>(`/api/returns/${returnId}/artifacts`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  uploadFile: async (returnId: number, artifactId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE_URL}/api/returns/${returnId}/artifacts/${artifactId}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || response.statusText);
    }
    return (await response.json()) as ArtifactMetadata;
  },
  getReviewPreview: (returnId: number) => request<ReviewPreviewResponse>(`/api/returns/${returnId}/review/preview`),
  submitConfirmations: (returnId: number, data: ConfirmationRequest) =>
    request<ConfirmationResponse>(`/api/returns/${returnId}/review/confirm`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export type {
  TaxReturn,
  CreateTaxReturnRequest,
  ArtifactMetadata,
  CreateArtifactRequest,
  TaxReturnStatus,
  ReviewPreviewResponse,
  ConfirmationRequest,
  ConfirmationResponse,
};
