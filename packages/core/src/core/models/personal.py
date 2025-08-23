"""Personal information models for tax returns."""

from datetime import date
from typing import Optional
from pydantic import field_validator, Field

from .base import TaxBaseModel, ValidationMixin


class PersonalInfo(TaxBaseModel, ValidationMixin):
    """Model for personal information in tax returns."""
    
    pan: str = Field(..., description="Permanent Account Number")
    name: str = Field(..., min_length=1, max_length=100, description="Full name as per PAN")
    father_name: Optional[str] = Field(None, max_length=100, description="Father's name")
    date_of_birth: date = Field(..., description="Date of birth")
    address: str = Field(..., min_length=10, max_length=500, description="Complete address")
    mobile: Optional[str] = Field(None, description="Mobile number (10 digits)")
    email: Optional[str] = Field(None, description="Email address")
    
    @field_validator('pan')
    @classmethod
    def validate_pan_field(cls, v: str) -> str:
        """Validate PAN format."""
        return cls.validate_pan(v)
    
    @field_validator('name', 'father_name')
    @classmethod
    def validate_name_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate name fields contain only letters, spaces, and common punctuation."""
        if not v:
            return v
        
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or only whitespace")
        
        # Allow letters, spaces, dots, hyphens, and apostrophes
        import re
        if not re.match(r"^[a-zA-Z\s.\-']+$", v):
            raise ValueError("Name can only contain letters, spaces, dots, hyphens, and apostrophes")
        
        return v.title()  # Convert to title case
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        """Validate date of birth is reasonable."""
        from datetime import date as dt_date
        
        today = dt_date.today()
        min_age_date = dt_date(today.year - 120, today.month, today.day)  # Max 120 years old
        max_age_date = dt_date(today.year - 18, today.month, today.day)   # Min 18 years old
        
        if v < min_age_date:
            raise ValueError("Date of birth cannot be more than 120 years ago")
        
        if v > max_age_date:
            raise ValueError("Person must be at least 18 years old")
        
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address_field(cls, v: str) -> str:
        """Validate address field."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Address must be at least 10 characters long")
        
        return v
    
    @field_validator('mobile')
    @classmethod
    def validate_mobile_field(cls, v: Optional[str]) -> Optional[str]:
        """Validate mobile number."""
        return cls.validate_mobile(v)
    
    @field_validator('email')
    @classmethod
    def validate_email_field(cls, v: Optional[str]) -> Optional[str]:
        """Validate email address."""
        return cls.validate_email(v)


class ReturnContext(TaxBaseModel, ValidationMixin):
    """Model for tax return context information."""
    
    assessment_year: str = Field(..., description="Assessment year (e.g., 2025-26)")
    form_type: str = Field(..., description="Form type (e.g., ITR1, ITR2)")
    filing_date: Optional[date] = Field(None, description="Date of filing")
    revised_return: bool = Field(False, description="Whether this is a revised return")
    original_return_date: Optional[date] = Field(None, description="Date of original return if revised")
    
    @field_validator('assessment_year')
    @classmethod
    def validate_assessment_year_field(cls, v: str) -> str:
        """Validate assessment year format."""
        return cls.validate_assessment_year(v)
    
    @field_validator('form_type')
    @classmethod
    def validate_form_type(cls, v: str) -> str:
        """Validate form type."""
        if not v:
            raise ValueError("Form type is required")
        
        v = v.upper().strip()
        valid_forms = ['ITR1', 'ITR2', 'ITR3', 'ITR4', 'ITR5', 'ITR6', 'ITR7']
        
        if v not in valid_forms:
            raise ValueError(f"Form type must be one of: {', '.join(valid_forms)}")
        
        return v
    
    @field_validator('filing_date', 'original_return_date')
    @classmethod
    def validate_filing_dates(cls, v: Optional[date]) -> Optional[date]:
        """Validate filing dates are not in the future."""
        if v is None:
            return v
        
        from datetime import date as dt_date
        
        today = dt_date.today()
        if v > today:
            raise ValueError("Filing date cannot be in the future")
        
        return v
    
    @field_validator('original_return_date')
    @classmethod
    def validate_original_return_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate original return date is before filing date if both are provided."""
        if v is None:
            return v
        
        # Get filing_date from the model data
        filing_date = info.data.get('filing_date')
        if filing_date and v >= filing_date:
            raise ValueError("Original return date must be before the current filing date")
        
        return v
    
    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        # Additional validation for revised returns
        if self.revised_return and not self.original_return_date:
            raise ValueError("Original return date is required for revised returns")
        
        if not self.revised_return and self.original_return_date:
            raise ValueError("Original return date should only be provided for revised returns")