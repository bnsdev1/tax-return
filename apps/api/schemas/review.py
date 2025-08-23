"""Review and confirmation schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Individual line item in a tax head."""
    
    id: str = Field(..., description="Unique line item identifier", example="salary_gross")
    label: str = Field(..., description="Display label", example="Gross Salary")
    amount: float = Field(..., description="Amount value", example=1200000.0)
    source: str = Field(..., description="Data source", example="prefill")
    needs_confirm: bool = Field(..., description="Requires user confirmation", example=True)
    editable: bool = Field(..., description="Can be edited by user", example=True)
    variance: Optional[Dict[str, Any]] = Field(None, description="Variance details if any")


class HeadVariance(BaseModel):
    """Variance in a tax head that needs attention."""
    
    field: str = Field(..., description="Field with variance", example="salary_gross")
    description: str = Field(..., description="Variance description", example="High salary amount detected")
    expected_range: Optional[str] = Field(None, description="Expected value range", example="₹500,000 - ₹1,000,000")
    actual_value: str = Field(..., description="Actual value found", example="₹1,200,000.00")
    severity: str = Field(..., description="Severity level", example="warning")
    blocking: bool = Field(..., description="Blocks proceeding if true", example=False)


class TaxHead(BaseModel):
    """Tax head with line items and variances."""
    
    head_name: str = Field(..., description="Head display name", example="Salary Income")
    total_amount: float = Field(..., description="Total amount for this head", example=1200000.0)
    line_items: List[LineItem] = Field(..., description="Line items in this head")
    variances: List[HeadVariance] = Field(default_factory=list, description="Variances requiring attention")
    needs_confirm: bool = Field(..., description="Head requires confirmation", example=True)


class ConfirmationStatus(BaseModel):
    """Overall confirmation status."""
    
    total_items: int = Field(..., description="Total items requiring confirmation", example=8)
    confirmed_items: int = Field(..., description="Items already confirmed", example=5)
    blocking_variances: int = Field(..., description="Number of blocking variances", example=0)
    can_proceed: bool = Field(..., description="Can proceed to next step", example=False)


class ReviewMetadata(BaseModel):
    """Review metadata."""
    
    generated_at: str = Field(..., description="Generation timestamp")
    pipeline_status: str = Field(..., description="Pipeline status", example="completed")


class ReviewPreviewResponse(BaseModel):
    """Review preview response with head-wise breakdown."""
    
    return_id: int = Field(..., description="Tax return ID", example=1)
    heads: Dict[str, TaxHead] = Field(..., description="Tax heads with line items")
    summary: Dict[str, float] = Field(..., description="Tax computation summary")
    confirmations: ConfirmationStatus = Field(..., description="Confirmation status")
    metadata: ReviewMetadata = Field(..., description="Review metadata")
    
    class Config:
        from_attributes = True


class LineItemEdit(BaseModel):
    """Edit to a line item."""
    
    line_item_id: str = Field(..., description="Line item ID to edit", example="salary_gross")
    new_amount: float = Field(..., description="New amount value", example=1150000.0)
    reason: Optional[str] = Field(None, description="Reason for edit", example="Corrected based on Form 16")


class ConfirmationRequest(BaseModel):
    """Request to confirm line items and submit edits."""
    
    confirmations: List[str] = Field(
        default_factory=list,
        description="List of line item IDs being confirmed",
        example=["salary_gross", "interest_savings"]
    )
    edits: List[LineItemEdit] = Field(
        default_factory=list,
        description="List of edits to apply"
    )


class ConfirmationResponse(BaseModel):
    """Response after processing confirmations."""
    
    return_id: int = Field(..., description="Tax return ID", example=1)
    confirmations_processed: int = Field(..., description="Number of confirmations processed", example=2)
    edits_applied: int = Field(..., description="Number of edits applied", example=1)
    remaining_confirmations: int = Field(..., description="Remaining items to confirm", example=3)
    blocking_variances: int = Field(..., description="Blocking variances remaining", example=0)
    can_proceed: bool = Field(..., description="Can proceed to next step", example=False)
    updated_summary: Dict[str, float] = Field(..., description="Updated tax summary after edits")
    message: str = Field(..., description="Response message", example="Confirmations processed successfully")
    
    class Config:
        from_attributes = True