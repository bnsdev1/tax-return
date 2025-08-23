// API types based on the backend schemas

export interface TaxReturn {
  id: number;
  taxpayer_id: number;
  assessment_year: string;
  form_type: string;
  regime: 'old' | 'new';
  status: 'draft' | 'submitted' | 'processed' | 'rejected';
  filing_date?: string;
  acknowledgment_number?: string;
  revised_return: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CreateTaxReturnRequest {
  pan: string;
  assessment_year: string;
  form_type: string;
  regime: 'old' | 'new';
}

export interface ArtifactMetadata {
  id: number;
  name: string;
  artifact_type: 'pdf' | 'xml' | 'json' | 'excel' | 'image' | 'other';
  file_size?: number;
  upload_status: 'pending' | 'completed' | 'failed';
  created_at: string;
}

export interface CreateArtifactRequest {
  name: string;
  artifact_type: 'pdf' | 'xml' | 'json' | 'excel' | 'image' | 'other';
  description?: string;
  tags?: string;
  file_size?: number;
  mime_type?: string;
  metadata?: Record<string, any>;
}

export interface BuildJobResponse {
  job_id: string;
  tax_return_id: number;
  job_type: 'build_return';
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_step: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_completion?: string;
  result?: Record<string, any>;
  error_message?: string;
  error_details?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface TaxReturnStatus {
  id: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress_percentage: number;
  current_step: string;
  validations: ValidationResult[];
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface ValidationResult {
  rule_name: string;
  status: 'passed' | 'warning' | 'failed';
  message?: string;
  field_path?: string;
}