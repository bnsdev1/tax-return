from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from decimal import Decimal

class ChallanCreate(BaseModel):
    """Schema for creating a new challan record"""
    cin_crn: str = Field(..., description="Challan Identification Number (CIN) or Collection Receipt Number (CRN)")
    bsr_code: str = Field(..., description="Basic Statistical Return (BSR) code of the bank")
    bank_reference: str = Field(..., description="Bank reference number")
    payment_date: date = Field(..., description="Date of payment")
    amount_paid: Decimal = Field(..., gt=0, description="Amount paid in rupees")
    challan_file_path: Optional[str] = Field(None, description="Path to uploaded challan PDF file")
    
    class Config:
        json_encoders = {
            Decimal: str
        }

class ChallanResponse(BaseModel):
    """Schema for challan response"""
    id: int
    cin_crn: str
    bsr_code: str
    bank_reference: str
    payment_date: date
    amount: Decimal
    challan_file_path: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }

class TaxPaymentSummary(BaseModel):
    """Schema for tax payment summary"""
    total_tax_liability: Decimal
    tds_paid: Decimal
    advance_tax_paid: Decimal
    net_payable: Decimal
    interest_234a: Decimal
    interest_234b: Decimal
    interest_234c: Decimal
    total_interest: Decimal
    total_amount_due: Decimal
    challan_present: bool
    challan_amount: Optional[Decimal] = None
    remaining_balance: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            Decimal: str
        }