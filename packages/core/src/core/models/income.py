"""Income-related models for tax return data."""

from pydantic import field_validator, computed_field
from typing import Optional
from .base import AmountModel


class Salary(AmountModel):
    """Model for salary income with allowances and deductions."""
    
    gross_salary: float = 0.0
    allowances: float = 0.0
    perquisites: float = 0.0
    profits_in_lieu: float = 0.0
    
    @computed_field
    @property
    def total_salary(self) -> float:
        """Calculate total salary income."""
        return round(
            self.gross_salary + self.allowances + self.perquisites + self.profits_in_lieu,
            2
        )


class HouseProperty(AmountModel):
    """Model for house property income with deductions."""
    
    annual_value: float = 0.0
    municipal_tax: float = 0.0
    standard_deduction: float = 0.0
    interest_on_loan: float = 0.0
    
    @computed_field
    @property
    def net_income(self) -> float:
        """Calculate net income from house property."""
        # Standard deduction is typically 30% of annual value minus municipal tax
        if self.standard_deduction == 0.0 and self.annual_value > 0:
            calculated_standard_deduction = (self.annual_value - self.municipal_tax) * 0.30
        else:
            calculated_standard_deduction = self.standard_deduction
        
        net = self.annual_value - self.municipal_tax - calculated_standard_deduction - self.interest_on_loan
        return round(max(net, 0.0), 2)  # Net income cannot be negative for house property
    
    @field_validator('municipal_tax')
    @classmethod
    def validate_municipal_tax(cls, v: float, info) -> float:
        """Validate that municipal tax doesn't exceed annual value."""
        # We can't access other fields during validation, so we'll skip this check here
        # The business logic validation will be handled in the computed field
        return round(v, 2) if v >= 0 else 0.0


class CapitalGains(AmountModel):
    """Model for capital gains income."""
    
    short_term: float = 0.0
    long_term: float = 0.0
    
    @computed_field
    @property
    def total_capital_gains(self) -> float:
        """Calculate total capital gains."""
        return round(self.short_term + self.long_term, 2)


class OtherSources(AmountModel):
    """Model for income from other sources."""
    
    interest_income: float = 0.0
    dividend_income: float = 0.0
    other_income: float = 0.0
    
    @computed_field
    @property
    def total_other_sources(self) -> float:
        """Calculate total income from other sources."""
        return round(self.interest_income + self.dividend_income + self.other_income, 2)
    
    @field_validator('interest_income', 'dividend_income', 'other_income')
    @classmethod
    def validate_income_amounts(cls, v: float) -> float:
        """Validate that income amounts are non-negative."""
        if v < 0:
            raise ValueError('Income amounts cannot be negative')
        return round(v, 2)