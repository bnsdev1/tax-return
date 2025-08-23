"""Tests for base models."""

import pytest
from pydantic import ValidationError

from core.models.base import TaxBaseModel, AmountModel, ValidationMixin


class TestTaxBaseModel:
    """Test the base tax model."""
    
    def test_base_model_creation(self):
        """Test basic model creation."""
        
        class TestModel(TaxBaseModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42
    
    def test_string_whitespace_stripping(self):
        """Test that whitespace is stripped from strings."""
        
        class TestModel(TaxBaseModel):
            name: str
        
        model = TestModel(name="  test  ")
        assert model.name == "test"
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        
        class TestModel(TaxBaseModel):
            name: str
        
        with pytest.raises(ValidationError):
            TestModel(name="test", extra_field="not allowed")


class TestAmountModel:
    """Test the amount model."""
    
    def test_amount_model_creation(self):
        """Test basic amount model creation."""
        model = AmountModel(amount=100.50)
        assert model.amount == 100.50
    
    def test_amount_default_zero(self):
        """Test that amount defaults to zero."""
        model = AmountModel()
        assert model.amount == 0.0
    
    def test_amount_rounding(self):
        """Test that amounts are rounded to 2 decimal places."""
        model = AmountModel(amount=100.567)
        assert model.amount == 100.57
    
    def test_negative_amount_validation(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AmountModel(amount=-100.0)
        
        assert "Amount cannot be negative" in str(exc_info.value)
    
    def test_amount_model_with_additional_fields(self):
        """Test amount model with additional numeric fields."""
        
        class TestAmountModel(AmountModel):
            gross_amount: float = 0.0
            net_amount: float = 0.0
        
        model = TestAmountModel(
            amount=100.567,
            gross_amount=200.123,
            net_amount=150.999
        )
        
        assert model.amount == 100.57
        assert model.gross_amount == 200.12
        assert model.net_amount == 151.00
    
    def test_negative_additional_fields_validation(self):
        """Test that negative values in additional fields are rejected."""
        
        class TestAmountModel(AmountModel):
            gross_amount: float = 0.0
        
        with pytest.raises(ValidationError) as exc_info:
            TestAmountModel(amount=100.0, gross_amount=-50.0)
        
        assert "gross_amount cannot be negative" in str(exc_info.value)
    
    def test_string_to_float_conversion(self):
        """Test that string numbers are converted to float."""
        
        class TestAmountModel(AmountModel):
            gross_amount: float = 0.0
        
        model = TestAmountModel(amount="100.50", gross_amount="200.75")
        assert model.amount == 100.50
        assert model.gross_amount == 200.75
    
    def test_invalid_string_conversion(self):
        """Test that invalid string numbers raise validation error."""
        
        class TestAmountModel(AmountModel):
            text_field: str = ""
        
        # This should work - non-numeric string fields should pass through
        model = TestAmountModel(amount=100.0, text_field="not a number")
        assert model.text_field == "not a number"


class TestValidationMixin:
    """Test the validation mixin methods."""
    
    def test_validate_pan_valid(self):
        """Test valid PAN validation."""
        
        valid_pans = ["ABCDE1234F", "XYZAB9876C", "abcde1234f"]
        
        for pan in valid_pans:
            result = ValidationMixin.validate_pan(pan)
            assert result == pan.upper()
    
    def test_validate_pan_invalid(self):
        """Test invalid PAN validation."""
        
        invalid_pans = [
            "",
            "ABCD1234F",  # Too short
            "ABCDE12345F",  # Too long
            "12345ABCDF",  # Numbers first
            "ABCDE1234",  # Missing last letter
            "ABCDE123AF",  # Letter in number position
        ]
        
        for pan in invalid_pans:
            with pytest.raises(ValueError):
                ValidationMixin.validate_pan(pan)
    
    def test_validate_assessment_year_valid(self):
        """Test valid assessment year validation."""
        
        valid_years = ["2024-25", "2025-26", "2023-24"]
        
        for year in valid_years:
            result = ValidationMixin.validate_assessment_year(year)
            assert result == year
    
    def test_validate_assessment_year_invalid(self):
        """Test invalid assessment year validation."""
        
        invalid_years = [
            "",
            "2024-26",  # Wrong sequence
            "24-25",  # Wrong format
            "2024-2025",  # Full year format
            "2024",  # Missing second year
            "2024-",  # Missing second year
        ]
        
        for year in invalid_years:
            with pytest.raises(ValueError):
                ValidationMixin.validate_assessment_year(year)
    
    def test_validate_mobile_valid(self):
        """Test valid mobile number validation."""
        
        valid_mobiles = ["9876543210", "8123456789", "7000000000", "6999999999"]
        
        for mobile in valid_mobiles:
            result = ValidationMixin.validate_mobile(mobile)
            assert result == mobile
        
        # Test None/empty
        assert ValidationMixin.validate_mobile(None) is None
        assert ValidationMixin.validate_mobile("") == ""
    
    def test_validate_mobile_invalid(self):
        """Test invalid mobile number validation."""
        
        invalid_mobiles = [
            "123456789",  # Too short
            "12345678901",  # Too long
            "5123456789",  # Starts with 5
            "0123456789",  # Starts with 0
            "abcdefghij",  # Letters
        ]
        
        for mobile in invalid_mobiles:
            with pytest.raises(ValueError):
                ValidationMixin.validate_mobile(mobile)
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.in",
            "TEST@EXAMPLE.COM",  # Should be converted to lowercase
        ]
        
        for email in valid_emails:
            result = ValidationMixin.validate_email(email)
            assert result == email.lower()
        
        # Test None/empty
        assert ValidationMixin.validate_email(None) is None
        assert ValidationMixin.validate_email("") == ""
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError):
                ValidationMixin.validate_email(email)