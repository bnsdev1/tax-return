"""Tax payment models for tax return data."""

from pydantic import computed_field
from .base import AmountModel


class TaxesPaid(AmountModel):
    """Model for taxes paid through various modes."""
    
    # Tax Deducted at Source
    tds: float = 0.0
    
    # Advance tax paid during the year
    advance_tax: float = 0.0
    
    # Self-assessment tax paid
    self_assessment_tax: float = 0.0
    
    @computed_field
    @property
    def total_taxes_paid(self) -> float:
        """Calculate total taxes paid across all modes."""
        return round(
            self.tds + 
            self.advance_tax + 
            self.self_assessment_tax, 
            2
        )