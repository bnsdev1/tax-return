"""Base models for tax-related data structures."""

import re
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import date


class TaxBaseModel(BaseModel):
    """Base model for all tax-related models with common configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        use_enum_values=True,
        validate_default=True,
    )


class AmountModel(TaxBaseModel):
    """Base model for monetary amounts with validation."""
    
    amount: float = 0.0
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Validate that amount is non-negative and properly rounded."""
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return round(v, 2)
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_numeric_fields(cls, v, info):
        """Validate all numeric fields in amount-based models."""
        field_name = info.field_name
        
        # Skip validation for non-numeric fields
        if field_name == 'amount' or not isinstance(v, (int, float, str)):
            return v
            
        # Convert string numbers to float
        if isinstance(v, str):
            try:
                v = float(v)
            except ValueError:
                return v
        
        # Validate numeric fields are non-negative and round to 2 decimal places
        if isinstance(v, (int, float)):
            if v < 0:
                raise ValueError(f'{field_name} cannot be negative')
            return round(float(v), 2)
        
        return v


class ValidationMixin:
    """Mixin class with common validation methods for tax-related fields."""
    
    @staticmethod
    def validate_pan(pan: str) -> str:
        """Validate PAN format (AAAAA9999A)."""
        if not pan:
            raise ValueError("PAN is required")
        
        pan = pan.upper().strip()
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        
        if not re.match(pan_pattern, pan):
            raise ValueError("PAN must be in format AAAAA9999A (5 letters, 4 digits, 1 letter)")
        
        return pan
    
    @staticmethod
    def validate_assessment_year(ay: str) -> str:
        """Validate assessment year format (YYYY-YY)."""
        if not ay:
            raise ValueError("Assessment year is required")
        
        ay = ay.strip()
        ay_pattern = r'^20\d{2}-\d{2}$'
        
        if not re.match(ay_pattern, ay):
            raise ValueError("Assessment year must be in format YYYY-YY (e.g., 2025-26)")
        
        # Validate that the second year is exactly one more than the first
        start_year, end_year = ay.split('-')
        if int(end_year) != (int(start_year) + 1) % 100:
            raise ValueError("Assessment year format invalid - second year must be next year's last two digits")
        
        return ay
    
    @staticmethod
    def validate_mobile(mobile: Optional[str]) -> Optional[str]:
        """Validate mobile number format (10 digits)."""
        if not mobile:
            return mobile
        
        mobile = mobile.strip()
        mobile_pattern = r'^[6-9]\d{9}$'
        
        if not re.match(mobile_pattern, mobile):
            raise ValueError("Mobile number must be 10 digits starting with 6, 7, 8, or 9")
        
        return mobile
    
    @staticmethod
    def validate_email(email: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if not email:
            return email
        
        email = email.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email