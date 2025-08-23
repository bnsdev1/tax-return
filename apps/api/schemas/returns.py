"""Tax return schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
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
        allow_population_by_field_name = True


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