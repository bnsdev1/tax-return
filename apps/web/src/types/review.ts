// Review and confirmation types

export interface LineItem {
  id: string;
  label: string;
  amount: number;
  source: string;
  needs_confirm: boolean;
  editable: boolean;
  variance?: any;
}

export interface HeadVariance {
  field: string;
  description: string;
  expected_range?: string;
  actual_value: string;
  severity: string;
  blocking: boolean;
}

export interface TaxHead {
  head_name: string;
  total_amount: number;
  line_items: LineItem[];
  variances: HeadVariance[];
  needs_confirm: boolean;
}

export interface ConfirmationStatus {
  total_items: number;
  confirmed_items: number;
  blocking_variances: number;
  can_proceed: boolean;
}

export interface ReviewMetadata {
  generated_at: string;
  pipeline_status: string;
}

export interface ReviewPreviewResponse {
  return_id: number;
  heads: Record<string, TaxHead>;
  summary: Record<string, number>;
  confirmations: ConfirmationStatus;
  metadata: ReviewMetadata;
}

export interface LineItemEdit {
  line_item_id: string;
  new_amount: number;
  reason?: string;
}

export interface ConfirmationRequest {
  confirmations: string[];
  edits: LineItemEdit[];
}

export interface ConfirmationResponse {
  return_id: number;
  confirmations_processed: number;
  edits_applied: number;
  remaining_confirmations: number;
  blocking_variances: number;
  can_proceed: boolean;
  updated_summary: Record<string, number>;
  message: string;
}