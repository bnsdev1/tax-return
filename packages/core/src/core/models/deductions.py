"""Deductions model for tax return data."""

from pydantic import field_validator, computed_field
from .base import AmountModel


class Deductions(AmountModel):
    """Model for tax deductions under various sections."""
    
    # Section 80C deductions (investments, insurance, etc.)
    section_80c: float = 0.0
    
    # Section 80D deductions (medical insurance)
    section_80d: float = 0.0
    
    # Section 80G deductions (donations)
    section_80g: float = 0.0
    
    # Other deductions (80E, 80TTA, etc.)
    other_deductions: float = 0.0
    
    @computed_field
    @property
    def total_deductions(self) -> float:
        """Calculate total deductions across all sections."""
        return round(
            self.section_80c + 
            self.section_80d + 
            self.section_80g + 
            self.other_deductions, 
            2
        )
    
    @field_validator('section_80c')
    @classmethod
    def validate_section_80c(cls, v: float) -> float:
        """Validate Section 80C deduction limit."""
        if v > 150000:
            raise ValueError('Section 80C deduction cannot exceed Rs. 1,50,000')
        return round(v, 2)
    
    @field_validator('section_80d')
    @classmethod
    def validate_section_80d(cls, v: float) -> float:
        """Validate Section 80D deduction limit."""
        if v > 75000:
            raise ValueError('Section 80D deduction cannot exceed Rs. 75,000')
        return round(v, 2)
    
    @field_validator('section_80g')
    @classmethod
    def validate_section_80g(cls, v: float) -> float:
        """Validate Section 80G deduction (no specific limit but must be reasonable)."""
        if v > 1000000:  # Reasonable upper limit
            raise ValueError('Section 80G deduction seems unreasonably high')
        return round(v, 2)