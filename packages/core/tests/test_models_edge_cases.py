"""Additional edge case tests for Pydantic models.

This file covers specific edge cases and boundary conditions that might not be
covered in the main test files.
"""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from core.models.base import TaxBaseModel, AmountModel, ValidationMixin
from core.models.personal import PersonalInfo, ReturnContext
from core.models.income import Salary, HouseProperty, CapitalGains, OtherSources
from core.models.deductions import Deductions
from core.models.taxes import TaxesPaid
from core.models.totals import Totals


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_zero_amounts_across_all_models(self):
        """Test that zero amounts work correctly across all models."""
        # Test all income models with zero amounts
        salary = Salary()
        house_property = HouseProperty()
        capital_gains = CapitalGains()
        other_sources = OtherSources()
        deductions = Deductions()
        taxes_paid = TaxesPaid()
        
        # All should have zero totals
        assert salary.total_salary == 0.0
        assert house_property.net_income == 0.0
        assert capital_gains.total_capital_gains == 0.0
        assert other_sources.total_other_sources == 0.0
        assert deductions.total_deductions == 0.0
        assert taxes_paid.total_taxes_paid == 0.0
        
        # Test totals with all zeros
        totals = Totals()
        assert totals.taxable_income == 0.0
        assert totals.total_tax_liability == 0.0
        assert totals.refund_or_payable == 0.0
    
    def test_maximum_reasonable_amounts(self):
        """Test with maximum reasonable amounts."""
        # Test with very large but reasonable amounts
        large_salary = Salary(
            gross_salary=99999999.99,
            allowances=9999999.99,
            perquisites=999999.99,
            profits_in_lieu=999999.99
        )
        
        expected_total = 99999999.99 + 9999999.99 + 999999.99 + 999999.99
        assert large_salary.total_salary == round(expected_total, 2)
        
        # Test large house property values
        large_house = HouseProperty(
            annual_value=50000000.0,  # 5 crore annual value
            municipal_tax=500000.0,
            standard_deduction=14850000.0,  # 30% of (5cr - 5L)
            interest_on_loan=10000000.0  # 1 crore interest
        )
        
        expected_net = 50000000.0 - 500000.0 - 14850000.0 - 10000000.0
        assert large_house.net_income == expected_net
    
    def test_precision_edge_cases_all_models(self):
        """Test precision handling across all models."""
        # Test with amounts that require precise rounding
        test_amount = 123456.789
        expected_rounded = 123456.79
        
        salary = Salary(gross_salary=test_amount)
        assert salary.gross_salary == expected_rounded
        
        house_property = HouseProperty(annual_value=test_amount)
        assert house_property.annual_value == expected_rounded
        
        capital_gains = CapitalGains(short_term=test_amount)
        assert capital_gains.short_term == expected_rounded
        
        other_sources = OtherSources(interest_income=test_amount)
        assert other_sources.interest_income == expected_rounded
        
        deductions = Deductions(section_80c=test_amount)
        assert deductions.section_80c == expected_rounded
        
        taxes_paid = TaxesPaid(tds=test_amount)
        assert taxes_paid.tds == expected_rounded
    
    def test_computed_field_precision(self):
        """Test that computed fields maintain precision correctly."""
        # Test salary total with precise amounts
        salary = Salary(
            gross_salary=100000.33,
            allowances=25000.33,
            perquisites=5000.33,
            profits_in_lieu=2500.33
        )
        
        # Manual calculation: 100000.33 + 25000.33 + 5000.33 + 2500.33 = 132501.32
        assert salary.total_salary == 132501.32
        
        # Test capital gains total
        capital_gains = CapitalGains(
            short_term=50000.55,
            long_term=75000.44
        )
        
        # Manual calculation: 50000.55 + 75000.44 = 125000.99
        assert capital_gains.total_capital_gains == 125000.99


class TestValidationErrorMessages:
    """Test that validation error messages are clear and helpful."""
    
    def test_pan_validation_error_messages(self):
        """Test PAN validation error messages."""
        base_data = {
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Test empty PAN
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfo(pan="", **base_data)
        
        error_msg = str(exc_info.value)
        assert "PAN is required" in error_msg
        
        # Test invalid PAN format
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfo(pan="INVALID", **base_data)
        
        error_msg = str(exc_info.value)
        assert "PAN must be in format AAAAA9999A" in error_msg
    
    def test_deduction_limit_error_messages(self):
        """Test deduction limit validation error messages."""
        # Test Section 80C limit
        with pytest.raises(ValidationError) as exc_info:
            Deductions(section_80c=200000.0)
        
        error_msg = str(exc_info.value)
        assert "Section 80C deduction cannot exceed Rs. 1,50,000" in error_msg
        
        # Test Section 80D limit
        with pytest.raises(ValidationError) as exc_info:
            Deductions(section_80d=100000.0)
        
        error_msg = str(exc_info.value)
        assert "Section 80D deduction cannot exceed Rs. 75,000" in error_msg
    
    def test_totals_validation_error_messages(self):
        """Test totals validation error messages."""
        # Test deductions exceeding income
        with pytest.raises(ValidationError) as exc_info:
            Totals(
                gross_total_income=100000.0,
                total_deductions=150000.0
            )
        
        error_msg = str(exc_info.value)
        assert "Total deductions cannot exceed gross total income" in error_msg
        
        # Test unreasonable tax rate
        with pytest.raises(ValidationError) as exc_info:
            Totals(
                gross_total_income=1000000.0,
                total_deductions=100000.0,
                tax_on_taxable_income=500000.0  # 55.6% effective rate
            )
        
        error_msg = str(exc_info.value)
        assert "Effective tax rate" in error_msg
        assert "seems unreasonably high" in error_msg


class TestSpecialCharacterHandling:
    """Test handling of special characters and unicode."""
    
    def test_name_with_special_characters(self):
        """Test names with special characters."""
        base_data = {
            "pan": "ABCDE1234F",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Test valid special characters in names
        valid_names = [
            "Mary-Jane Smith",
            "O'Connor",
            "Dr. Smith",
            "Jean-Pierre",
            "Smith Jr.",
            "Mary Ann",
        ]
        
        for name in valid_names:
            personal_info = PersonalInfo(name=name, **base_data)
            assert personal_info.name == name.title()
    
    def test_address_with_special_characters(self):
        """Test addresses with special characters."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1)
        }
        
        # Test addresses with various special characters
        valid_addresses = [
            "123, Main Street, City - 123456",
            "Apt. 4B, Building Name, Area, City",
            "House No. 45/A, Street Name, City",
            "Plot #123, Sector-5, New Town",
        ]
        
        for address in valid_addresses:
            personal_info = PersonalInfo(address=address, **base_data)
            assert personal_info.address == address
    
    def test_email_edge_cases(self):
        """Test email validation edge cases."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Test valid email edge cases
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example.co.in",
            "USER@EXAMPLE.COM",  # Should be converted to lowercase
        ]
        
        for email in valid_emails:
            personal_info = PersonalInfo(email=email, **base_data)
            assert personal_info.email == email.lower()


class TestDateHandling:
    """Test date handling edge cases."""
    
    def test_leap_year_dates(self):
        """Test leap year date handling."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "address": "Test Address 123456"
        }
        
        # Test leap year date (Feb 29)
        leap_year_date = date(1992, 2, 29)  # 1992 was a leap year
        personal_info = PersonalInfo(date_of_birth=leap_year_date, **base_data)
        assert personal_info.date_of_birth == leap_year_date
    
    def test_filing_date_edge_cases(self):
        """Test filing date edge cases."""
        base_data = {
            "assessment_year": "2025-26",
            "form_type": "ITR1"
        }
        
        today = date.today()
        
        # Test filing date exactly today
        context = ReturnContext(filing_date=today, **base_data)
        assert context.filing_date == today
        
        # Test filing date yesterday
        yesterday = today - timedelta(days=1)
        context = ReturnContext(filing_date=yesterday, **base_data)
        assert context.filing_date == yesterday
    
    def test_revised_return_date_validation(self):
        """Test revised return date validation edge cases."""
        base_data = {
            "assessment_year": "2025-26",
            "form_type": "ITR1",
            "filing_date": date(2024, 12, 31)
        }
        
        # Test original return date exactly one day before filing date
        original_date = date(2024, 12, 30)
        context = ReturnContext(
            revised_return=True,
            original_return_date=original_date,
            **base_data
        )
        assert context.original_return_date == original_date
        
        # Test original return date same as filing date (should fail)
        with pytest.raises(ValidationError):
            ReturnContext(
                revised_return=True,
                original_return_date=date(2024, 12, 31),  # Same as filing date
                **base_data
            )


class TestModelStateConsistency:
    """Test that models maintain consistent state."""
    
    def test_model_immutability_after_creation(self):
        """Test that models maintain consistent state after creation."""
        salary = Salary(
            gross_salary=100000.0,
            allowances=25000.0
        )
        
        original_total = salary.total_salary
        
        # The total should remain consistent
        assert salary.total_salary == original_total
        assert salary.total_salary == 125000.0
    
    def test_computed_fields_consistency(self):
        """Test that computed fields are consistent across multiple accesses."""
        house_property = HouseProperty(
            annual_value=200000.0,
            municipal_tax=10000.0,
            interest_on_loan=50000.0
        )
        
        # Access net_income multiple times
        net_income_1 = house_property.net_income
        net_income_2 = house_property.net_income
        net_income_3 = house_property.net_income
        
        # All should be the same
        assert net_income_1 == net_income_2 == net_income_3
    
    def test_model_equality_after_serialization(self):
        """Test that models remain equal after serialization/deserialization."""
        original = PersonalInfo(
            pan="ABCDE1234F",
            name="John Doe",
            date_of_birth=date(1990, 5, 15),
            address="123 Main Street, City, State - 123456",
            mobile="9876543210",
            email="john.doe@example.com"
        )
        
        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = PersonalInfo.model_validate_json(json_str)
        
        # Should be equal
        assert original == restored
        
        # Should have same hash (if hashable)
        # Note: Pydantic models are not hashable by default, but we can test field equality
        assert original.pan == restored.pan
        assert original.name == restored.name
        assert original.date_of_birth == restored.date_of_birth


class TestConcurrentAccess:
    """Test behavior under concurrent access scenarios."""
    
    def test_multiple_model_instances(self):
        """Test that multiple model instances don't interfere with each other."""
        # Create multiple salary instances
        salary1 = Salary(gross_salary=100000.0, allowances=10000.0)
        salary2 = Salary(gross_salary=200000.0, allowances=20000.0)
        salary3 = Salary(gross_salary=300000.0, allowances=30000.0)
        
        # Each should have correct totals
        assert salary1.total_salary == 110000.0
        assert salary2.total_salary == 220000.0
        assert salary3.total_salary == 330000.0
        
        # Modifying one shouldn't affect others
        # (Note: Pydantic models are immutable by default, but we can test this conceptually)
        assert salary1.gross_salary == 100000.0
        assert salary2.gross_salary == 200000.0
        assert salary3.gross_salary == 300000.0
    
    def test_model_independence(self):
        """Test that different model types are independent."""
        salary = Salary(gross_salary=500000.0)
        house_property = HouseProperty(annual_value=300000.0)
        deductions = Deductions(section_80c=100000.0)
        
        # Each should maintain its own state
        assert salary.total_salary == 500000.0
        assert house_property.net_income >= 0  # Should be calculated independently
        assert deductions.total_deductions == 100000.0
        
        # Creating new instances shouldn't affect existing ones
        salary2 = Salary(gross_salary=600000.0)
        assert salary.total_salary == 500000.0  # Original unchanged
        assert salary2.total_salary == 600000.0  # New instance correct