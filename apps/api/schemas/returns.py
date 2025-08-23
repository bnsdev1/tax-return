"""Tax return schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class TaxRegime(str, Enum):
    """Tax regime options."""
    OLD = "old"
    NEW = "new"


class ReturnStatus(str, Enum):
    """Tax return status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSED = "processed"
    REJECTED = "rejected"


class TaxReturnCreate(BaseModel):
    """Schema for creating a new tax return."""
    
    pan: str = Field(
        ...,
        description="PAN number of the taxpayer",
        example="ABCDE1234F",
        min_length=10,
        max_length=10
    )
    ay: str = Field(
        ...,
        description="Assessment year in YYYY-YY format",
        example="2025-26",
        alias="assessment_year"
    )
    form: str = Field(
        ...,
        description="ITR form type",
        example="ITR2",
        alias="form_type"
    )
    regime: TaxRegime = Field(
        TaxRegime.NEW,
        description="Tax regime (old or new)",
        example="new"
    )
    
    class Config:
        populate_by_name = True


class TaxReturnResponse(BaseModel):
    """Schema for tax return response."""
    
    id: int = Field(..., description="Unique tax return ID", example=1)
    taxpayer_id: int = Field(..., description="Taxpayer ID", example=1)
    assessment_year: str = Field(..., description="Assessment year", example="2025-26")
    form_type: str = Field(..., description="ITR form type", example="ITR2")
    regime: TaxRegime = Field(..., description="Tax regime", example="new")
    status: ReturnStatus = Field(..., description="Return status", example="draft")
    
    # Optional fields
    filing_date: Optional[datetime] = Field(None, description="Filing date")
    acknowledgment_number: Optional[str] = Field(None, description="Acknowledgment number")
    revised_return: bool = Field(False, description="Is this a revised return")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class TaxReturnStatus(str, Enum):
    """Build and processing status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationResult(BaseModel):
    """Validation result schema."""
    
    rule_name: str = Field(..., description="Validation rule name", example="pan_format")
    status: str = Field(..., description="Validation status", example="passed")
    message: Optional[str] = Field(None, description="Validation message")
    field_path: Optional[str] = Field(None, description="Field path if validation failed")


class TaxReturnStatusResponse(BaseModel):
    """Schema for tax return status response."""
    
    id: int = Field(..., description="Tax return ID", example=1)
    status: TaxReturnStatus = Field(..., description="Processing status", example="completed")
    
    # Progress information
    progress_percentage: int = Field(0, description="Progress percentage", example=85)
    current_step: str = Field("", description="Current processing step", example="Generating PDF")
    
    # Validation results
    validations: List[ValidationResult] = Field(
        default_factory=list,
        description="Validation results"
    )
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    class Config:
        from_attributes = True


# Preview Response Schemas
class SavingsInterest(BaseModel):
    """Savings interest details."""
    amount: float = Field(..., description="Total interest amount", example=45000.0)
    tds_deducted: float = Field(..., description="TDS deducted on interest", example=4500.0)
    bank_count: int = Field(..., description="Number of banks", example=2)


class TotalTdsTcs(BaseModel):
    """Total TDS/TCS details."""
    total_tds: float = Field(..., description="Total TDS amount", example=89500.0)
    salary_tds: float = Field(..., description="TDS on salary", example=85000.0)
    interest_tds: float = Field(..., description="TDS on interest", example=4500.0)
    property_tds: float = Field(..., description="TDS on property", example=0.0)
    breakdown: Dict[str, float] = Field(..., description="TDS breakdown by category")


class AdvanceTax(BaseModel):
    """Advance tax details."""
    amount: float = Field(..., description="Advance tax paid", example=15000.0)
    total_taxes_paid: float = Field(..., description="Total taxes paid", example=104500.0)


class CapitalGains(BaseModel):
    """Capital gains details."""
    short_term: float = Field(..., description="Short-term capital gains", example=25000.0)
    long_term: float = Field(..., description="Long-term capital gains", example=50000.0)
    total: float = Field(..., description="Total capital gains", example=75000.0)
    transaction_count: int = Field(..., description="Number of transactions", example=5)


class TaxSummary(BaseModel):
    """Tax computation summary."""
    gross_total_income: float = Field(..., description="Gross total income", example=1320000.0)
    total_deductions: float = Field(..., description="Total deductions", example=0.0)
    taxable_income: float = Field(..., description="Taxable income", example=1245000.0)
    tax_liability: float = Field(..., description="Tax liability", example=78000.0)
    refund_or_payable: float = Field(..., description="Refund or payable amount", example=-26500.0)


class KeyLines(BaseModel):
    """Key financial lines for preview."""
    savings_interest: SavingsInterest
    total_tds_tcs: TotalTdsTcs
    advance_tax: AdvanceTax
    capital_gains: CapitalGains


class Warning(BaseModel):
    """Warning or issue details."""
    type: str = Field(..., description="Warning type", example="validation")
    rule: Optional[str] = Field(None, description="Rule name", example="high_income_alert")
    message: str = Field(..., description="Warning message", example="Very high income reported")
    field: Optional[str] = Field(None, description="Field path", example="income.gross_total_income")
    severity: str = Field(..., description="Severity level", example="warning")


class Blocker(BaseModel):
    """Blocker or error details."""
    type: str = Field(..., description="Blocker type", example="validation")
    rule: Optional[str] = Field(None, description="Rule name", example="pan_required")
    message: str = Field(..., description="Blocker message", example="PAN number is required")
    field: Optional[str] = Field(None, description="Field path", example="personal_info.pan")
    severity: str = Field(..., description="Severity level", example="error")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix", example="Provide valid PAN number")


class PreviewMetadata(BaseModel):
    """Preview metadata."""
    generated_at: str = Field(..., description="Generation timestamp")
    pipeline_status: str = Field(..., description="Pipeline status", example="completed")
    total_warnings: int = Field(..., description="Total warnings count", example=2)
    total_blockers: int = Field(..., description="Total blockers count", example=0)


class PreviewResponse(BaseModel):
    """Preview response with key tax return highlights."""
    
    key_lines: KeyLines = Field(..., description="Key financial lines")
    summary: TaxSummary = Field(..., description="Tax computation summary")
    warnings: List[Warning] = Field(default_factory=list, description="List of warnings")
    blockers: List[Blocker] = Field(default_factory=list, description="List of blockers")
    metadata: PreviewMetadata = Field(..., description="Preview metadata")
    
    class Config:
        from_attributes = True