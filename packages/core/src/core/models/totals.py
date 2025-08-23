"""Totals model with calculated fields for tax liability."""

from pydantic import computed_field, field_validator, model_validator
from typing import Self
from .base import AmountModel


class Totals(AmountModel):
    """Model for calculated totals and tax liability."""
    
    # Income totals
    gross_total_income: float = 0.0
    total_deductions: float = 0.0
    
    # Tax calculations
    tax_on_taxable_income: float = 0.0
    total_taxes_paid: float = 0.0
    
    @computed_field
    @property
    def taxable_income(self) -> float:
        """Calculate taxable income after deductions."""
        taxable = self.gross_total_income - self.total_deductions
        return round(max(0, taxable), 2)  # Cannot be negative
    
    @computed_field
    @property
    def total_tax_liability(self) -> float:
        """Calculate total tax liability including cess and surcharge."""
        # Basic tax calculation (simplified)
        base_tax = self.tax_on_taxable_income
        
        # Add 4% Health and Education Cess
        cess = base_tax * 0.04
        
        # Add surcharge if applicable (simplified - 10% for income > 50L)
        surcharge = 0.0
        if self.taxable_income > 5000000:
            surcharge = base_tax * 0.10
        
        return round(base_tax + cess + surcharge, 2)
    
    @computed_field
    @property
    def refund_or_payable(self) -> float:
        """Calculate refund (negative) or additional tax payable (positive)."""
        return round(self.total_tax_liability - self.total_taxes_paid, 2)
    
    @field_validator('gross_total_income', 'total_deductions', 'tax_on_taxable_income', 'total_taxes_paid')
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        """Ensure all amounts are non-negative."""
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return round(v, 2)
    
    @model_validator(mode='after')
    def validate_tax_calculations(self) -> Self:
        """Cross-field validation for tax calculations."""
        # Validate that deductions don't exceed gross income (allow equal for edge cases)
        if self.total_deductions > self.gross_total_income:
            raise ValueError('Total deductions cannot exceed gross total income')
        
        # Validate tax calculation is reasonable for the taxable income
        if self.taxable_income > 250000 and self.tax_on_taxable_income == 0:
            # Allow zero tax for income below exemption limit (2.5L for individuals)
            raise ValueError('Tax on taxable income cannot be zero for income above exemption limit')
        
        # Validate tax rate is not unreasonably high (max ~42% including surcharge and cess)
        if self.taxable_income > 0 and self.tax_on_taxable_income > 0:
            effective_rate = (self.tax_on_taxable_income / self.taxable_income) * 100
            if effective_rate > 45:  # Allow some buffer for edge cases
                raise ValueError(f'Effective tax rate of {effective_rate:.1f}% seems unreasonably high')
        
        return self