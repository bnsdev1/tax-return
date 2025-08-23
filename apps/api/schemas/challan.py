"""Challan schemas for API requests and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ChallanType(str, Enum):
    """Challan type options."""
    ADVANCE_TAX = "advance_tax"
    SELF_ASSESSMENT = "self_assessment"
    REGULAR_ASSESSMENT = "regular_assessment"


class ChallanStatus(str, Enum):
    """Challan status options."""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ChallanCreate(BaseModel):
    """Schema for creating a new challan."""
    
    challan_type: ChallanType = Field(
        ChallanType.SELF_ASSESSMENT,
        description="Type of challan",
        example="self_assessment"
    )
    amount: float = Field(
        ...,
        description="Challan amount",
        example=15000.0,
        gt=0
    )
    cin_crn: str = Field(
        ...,
        description="CIN/CRN number from challan",
        example="1234567890123456",
        min_length=16,
        max_length=16
    )
    bsr_code: str = Field(
        ...,
        description="BSR code of the bank",
        example="1234567",
        min_length=7,
        max_length=7
    )
    bank_reference: str = Field(
        ...,
        description="Bank reference number",
        example="REF123456789",
        max_length=50
    )
    payment_date: datetime = Field(
        ...,
        description="Date of payment",
        example="2025-08-23T00:00:00Z"
    )
    bank_name: Optional[str] = Field(
        None,
        description="Name of the bank",
        example="State Bank of India",
        max_length=100
    )
    remarks: Optional[str] = Field(
        None,
        description="Additional remarks",
        max_length=500
    )


class ChallanResponse(BaseModel):
    """Schema for challan response."""
    
    id: int = Field(..., description="Unique challan ID", example=1)
    tax_return_id: int = Field(..., description="Tax return ID", example=1)
    challan_number: Optional[str] = Field(None, description="System generated challan number")
    challan_type: ChallanType = Field(..., description="Type of challan")
    amount: float = Field(..., description="Challan amount", example=15000.0)
    
    # Payment details
    cin_crn: str = Field(..., description="CIN/CRN number")
    bsr_code: str = Field(..., description="BSR code")
    bank_reference: str = Field(..., description="Bank reference number")
    payment_date: datetime = Field(..., description="Date of payment")
    bank_name: Optional[str] = Field(None, description="Bank name")
    
    # Status and metadata
    status: ChallanStatus = Field(..., description="Challan status")
    assessment_year: str = Field(..., description="Assessment year")
    remarks: Optional[str] = Field(None, description="Remarks")
    
    # File information
    challan_file_path: Optional[str] = Field(None, description="Path to uploaded challan PDF")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ChallanUpdate(BaseModel):
    """Schema for updating challan."""
    
    status: Optional[ChallanStatus] = Field(None, description="Update challan status")
    remarks: Optional[str] = Field(None, description="Update remarks")


class ChallanSummary(BaseModel):
    """Summary of challans for a tax return."""
    
    total_challans: int = Field(..., description="Total number of challans")
    total_amount: float = Field(..., description="Total amount paid via challans")
    paid_challans: int = Field(..., description="Number of paid challans")
    pending_challans: int = Field(..., description="Number of pending challans")
    latest_payment_date: Optional[datetime] = Field(None, description="Latest payment date")