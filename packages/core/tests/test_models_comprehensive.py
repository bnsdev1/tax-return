"""Comprehensive unit tests for all Pydantic models.

This test file focuses on:
1. Round-trip serialization for all models
2. Field validation rules and constraints
3. Edge cases and invalid input handling
4. Calculated fields and business logic
5. Integration testing between models
"""

import pytest
import json
from datetime import date, timedelta
from pydantic import ValidationError

from core.models.base import TaxBaseModel, AmountModel, ValidationMixin
from core.models.personal import PersonalInfo, ReturnContext
from core.models.income import Salary, HouseProperty, CapitalGains, OtherSources
from core.models.deductions import Deductions
from core.models.taxes import TaxesPaid
from core.models.totals import Totals


class TestRoundTripSerialization:
    """Test round-trip JSON serialization for all models."""
    
    def test_personal_info_round_trip(self):
        """Test PersonalInfo round-trip serialization."""
        original = PersonalInfo(
            pan="ABCDE1234F",
            name="John Doe",
            father_name="Robert Doe",
            date_of_birth=date(1990, 5, 15),
            address="123 Main Street, City, State - 123456",
            mobile="9876543210",
            email="john.doe@example.com"
        )
        
        # Test JSON string round-trip
        json_str = original.model_dump_json()
        restored = PersonalInfo.model_validate_json(json_str)
        assert restored == original
        
        # Test dict round-trip
        data_dict = original.model_dump()
        restored_dict = PersonalInfo.model_validate(data_dict)
        assert restored_dict == original
    
    def test_return_context_round_trip(self):
        """Test ReturnContext round-trip serialization."""
        original = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1",
            filing_date=date(2024, 7, 31),
            revised_return=True,
            original_return_date=date(2024, 3, 31)
        )
        
        json_str = original.model_dump_json()
        restored = ReturnContext.model_validate_json(json_str)
        assert restored == original
    
    def test_salary_round_trip(self):
        """Test Salary round-trip serialization."""
        original = Salary(
            gross_salary=600000.0,
            allowances=60000.0,
            perquisites=12000.0,
            profits_in_lieu=6000.0
        )
        
        # Exclude computed fields for serialization
        data_dict = original.model_dump(exclude={'total_salary'})
        restored = Salary.model_validate(data_dict)
        
        assert restored.gross_salary == original.gross_salary
        assert restored.allowances == original.allowances
        assert restored.perquisites == original.perquisites
        assert restored.profits_in_lieu == original.profits_in_lieu
        assert restored.total_salary == original.total_salary
    
    def test_house_property_round_trip(self):
        """Test HouseProperty round-trip serialization."""
        original = HouseProperty(
            annual_value=250000.0,
            municipal_tax=7500.0,
            standard_deduction=72750.0,
            interest_on_loan=80000.0
        )
        
        data_dict = original.model_dump(exclude={'net_income'})
        restored = HouseProperty.model_validate(data_dict)
        
        assert restored.annual_value == original.annual_value
        assert restored.municipal_tax == original.municipal_tax
        assert restored.standard_deduction == original.standard_deduction
        assert restored.interest_on_loan == original.interest_on_loan
        assert restored.net_income == original.net_income
    
    def test_capital_gains_round_trip(self):
        """Test CapitalGains round-trip serialization."""
        original = CapitalGains(
            short_term=50000.0,
            long_term=100000.0
        )
        
        data_dict = original.model_dump(exclude={'total_capital_gains'})
        restored = CapitalGains.model_validate(data_dict)
        
        assert restored.short_term == original.short_term
        assert restored.long_term == original.long_term
        assert restored.total_capital_gains == original.total_capital_gains
    
    def test_other_sources_round_trip(self):
        """Test OtherSources round-trip serialization."""
        original = OtherSources(
            interest_income=25000.0,
            dividend_income=15000.0,
            other_income=10000.0
        )
        
        data_dict = original.model_dump(exclude={'total_other_sources'})
        restored = OtherSources.model_validate(data_dict)
        
        assert restored.interest_income == original.interest_income
        assert restored.dividend_income == original.dividend_income
        assert restored.other_income == original.other_income
        assert restored.total_other_sources == original.total_other_sources
    
    def test_deductions_round_trip(self):
        """Test Deductions round-trip serialization."""
        original = Deductions(
            section_80c=100000.0,
            section_80d=25000.0,
            section_80g=10000.0,
            other_deductions=5000.0
        )
        
        data_dict = original.model_dump(exclude={'total_deductions'})
        restored = Deductions.model_validate(data_dict)
        
        assert restored.section_80c == original.section_80c
        assert restored.section_80d == original.section_80d
        assert restored.section_80g == original.section_80g
        assert restored.other_deductions == original.other_deductions
        assert restored.total_deductions == original.total_deductions
    
    def test_taxes_paid_round_trip(self):
        """Test TaxesPaid round-trip serialization."""
        original = TaxesPaid(
            tds=50000.0,
            advance_tax=25000.0,
            self_assessment_tax=10000.0
        )
        
        data_dict = original.model_dump(exclude={'total_taxes_paid'})
        restored = TaxesPaid.model_validate(data_dict)
        
        assert restored.tds == original.tds
        assert restored.advance_tax == original.advance_tax
        assert restored.self_assessment_tax == original.self_assessment_tax
        assert restored.total_taxes_paid == original.total_taxes_paid
    
    def test_totals_round_trip(self):
        """Test Totals round-trip serialization."""
        original = Totals(
            gross_total_income=1000000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=150000.0,
            total_taxes_paid=100000.0
        )
        
        # Exclude computed fields
        data_dict = original.model_dump(exclude={
            'taxable_income', 'total_tax_liability', 'refund_or_payable'
        })
        restored = Totals.model_validate(data_dict)
        
        assert restored.gross_total_income == original.gross_total_income
        assert restored.total_deductions == original.total_deductions
        assert restored.tax_on_taxable_income == original.tax_on_taxable_income
        assert restored.total_taxes_paid == original.total_taxes_paid
        assert restored.taxable_income == original.taxable_income
        assert restored.total_tax_liability == original.total_tax_liability
        assert restored.refund_or_payable == original.refund_or_payable


class TestFieldValidationEdgeCases:
    """Test edge cases and boundary conditions for field validation."""
    
    def test_pan_edge_cases(self):
        """Test PAN validation edge cases."""
        base_data = {
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Test case sensitivity
        personal_info = PersonalInfo(pan="abcde1234f", **base_data)
        assert personal_info.pan == "ABCDE1234F"
        
        # Test whitespace handling
        personal_info = PersonalInfo(pan="  ABCDE1234F  ", **base_data)
        assert personal_info.pan == "ABCDE1234F"
        
        # Test boundary cases for invalid PANs
        invalid_pans = [
            "ABCDE123F",   # Missing digit
            "ABCDE12345F", # Extra digit
            "1BCDE1234F",  # Number in first position
            "ABCDE1234",   # Missing last letter
            "ABCDE123A4F", # Letter in number position
        ]
        
        for invalid_pan in invalid_pans:
            with pytest.raises(ValidationError):
                PersonalInfo(pan=invalid_pan, **base_data)
    
    def test_date_of_birth_boundary_cases(self):
        """Test date of birth boundary validation."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "address": "Test Address 123456"
        }
        
        today = date.today()
        
        # Test exactly 18 years old (should pass)
        exactly_18 = date(today.year - 18, today.month, today.day)
        personal_info = PersonalInfo(date_of_birth=exactly_18, **base_data)
        assert personal_info.date_of_birth == exactly_18
        
        # Test exactly 120 years old (should pass)
        exactly_120 = date(today.year - 120, today.month, today.day)
        personal_info = PersonalInfo(date_of_birth=exactly_120, **base_data)
        assert personal_info.date_of_birth == exactly_120
        
        # Test one day under 18 (should fail)
        under_18 = exactly_18 + timedelta(days=1)
        with pytest.raises(ValidationError):
            PersonalInfo(date_of_birth=under_18, **base_data)
        
        # Test over 120 years (should fail)
        over_120 = exactly_120 - timedelta(days=1)
        with pytest.raises(ValidationError):
            PersonalInfo(date_of_birth=over_120, **base_data)
    
    def test_mobile_number_edge_cases(self):
        """Test mobile number validation edge cases."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Test boundary valid numbers
        valid_mobiles = [
            "6000000000",  # Starts with 6
            "7999999999",  # Starts with 7
            "8000000000",  # Starts with 8
            "9999999999",  # Starts with 9
        ]
        
        for mobile in valid_mobiles:
            personal_info = PersonalInfo(mobile=mobile, **base_data)
            assert personal_info.mobile == mobile
        
        # Test boundary invalid numbers
        invalid_mobiles = [
            "5999999999",  # Starts with 5
            "0123456789",  # Starts with 0
            "1234567890",  # Starts with 1
        ]
        
        for mobile in invalid_mobiles:
            with pytest.raises(ValidationError):
                PersonalInfo(mobile=mobile, **base_data)
    
    def test_assessment_year_edge_cases(self):
        """Test assessment year validation edge cases."""
        base_data = {"form_type": "ITR1"}
        
        # Test valid edge cases
        valid_years = [
            "2000-01",  # Y2K era
            "2099-00",  # Century boundary
            "2024-25",  # Current typical year
        ]
        
        for year in valid_years:
            context = ReturnContext(assessment_year=year, **base_data)
            assert context.assessment_year == year
        
        # Test invalid edge cases
        invalid_years = [
            "2024-24",  # Same year
            "2024-26",  # Skip a year
            "2024-23",  # Previous year
            "1999-00",  # Before 2000
        ]
        
        for year in invalid_years:
            with pytest.raises(ValidationError):
                ReturnContext(assessment_year=year, **base_data)
    
    def test_amount_precision_edge_cases(self):
        """Test amount precision and rounding edge cases."""
        # Test various precision scenarios
        test_cases = [
            (100.001, 100.0),    # Round down
            (100.004, 100.0),    # Round down (Python uses banker's rounding)
            (100.006, 100.01),   # Round up
            (100.999, 101.0),    # Round up
            (0.001, 0.0),        # Very small amount
            (999999.999, 1000000.0),  # Large amount rounding
        ]
        
        for input_amount, expected in test_cases:
            salary = Salary(gross_salary=input_amount)
            assert salary.gross_salary == expected
    
    def test_deduction_limit_edge_cases(self):
        """Test deduction limit edge cases."""
        # Test exactly at limits
        deductions = Deductions(
            section_80c=150000.0,  # Exactly at limit
            section_80d=75000.0,   # Exactly at limit
            section_80g=999999.0   # Just under reasonable limit
        )
        assert deductions.section_80c == 150000.0
        assert deductions.section_80d == 75000.0
        assert deductions.section_80g == 999999.0
        
        # Test just over limits
        with pytest.raises(ValidationError):
            Deductions(section_80c=150000.01)
        
        with pytest.raises(ValidationError):
            Deductions(section_80d=75000.01)
        
        with pytest.raises(ValidationError):
            Deductions(section_80g=1000000.01)


class TestCalculatedFieldsBusinessLogic:
    """Test calculated fields and business logic validation."""
    
    def test_salary_total_calculation_precision(self):
        """Test salary total calculation with various precision scenarios."""
        test_cases = [
            # (gross, allowances, perquisites, profits, expected_total)
            (100000.33, 25000.33, 5000.33, 2500.33, 132501.32),
            (0.01, 0.01, 0.01, 0.01, 0.04),
            (999999.99, 0.01, 0.0, 0.0, 1000000.0),
        ]
        
        for gross, allowances, perquisites, profits, expected in test_cases:
            salary = Salary(
                gross_salary=gross,
                allowances=allowances,
                perquisites=perquisites,
                profits_in_lieu=profits
            )
            assert salary.total_salary == expected
    
    def test_house_property_auto_standard_deduction_logic(self):
        """Test house property automatic standard deduction calculation."""
        # Test auto calculation when standard_deduction is 0
        house = HouseProperty(
            annual_value=200000.0,
            municipal_tax=10000.0,
            # standard_deduction not provided (defaults to 0)
            interest_on_loan=50000.0
        )
        
        # Auto standard deduction = 30% of (200000 - 10000) = 57000
        expected_net = 200000.0 - 10000.0 - 57000.0 - 50000.0
        assert house.net_income == expected_net
        
        # Test explicit standard deduction overrides auto calculation
        house_explicit = HouseProperty(
            annual_value=200000.0,
            municipal_tax=10000.0,
            standard_deduction=40000.0,  # Explicit value
            interest_on_loan=50000.0
        )
        
        expected_net_explicit = 200000.0 - 10000.0 - 40000.0 - 50000.0
        assert house_explicit.net_income == expected_net_explicit
    
    def test_house_property_negative_net_income_handling(self):
        """Test house property negative net income becomes zero."""
        # Create scenario where net income would be negative
        house = HouseProperty(
            annual_value=100000.0,
            municipal_tax=5000.0,
            standard_deduction=28500.0,  # 30% of (100000-5000)
            interest_on_loan=200000.0    # Very high interest
        )
        
        # Net would be: 100000 - 5000 - 28500 - 200000 = -133500
        # But should be clamped to 0
        assert house.net_income == 0.0
    
    def test_totals_tax_liability_calculation_scenarios(self):
        """Test various tax liability calculation scenarios."""
        # Test no surcharge scenario (income <= 50L)
        totals_no_surcharge = Totals(
            gross_total_income=3000000.0,  # 30L
            total_deductions=300000.0,
            tax_on_taxable_income=400000.0,
            total_taxes_paid=350000.0
        )
        
        # Tax liability = 400000 + (400000 * 0.04) = 416000
        expected_liability = 400000.0 + (400000.0 * 0.04)
        assert totals_no_surcharge.total_tax_liability == expected_liability
        
        # Test with surcharge scenario (income > 50L)
        totals_with_surcharge = Totals(
            gross_total_income=6000000.0,  # 60L
            total_deductions=500000.0,
            tax_on_taxable_income=1500000.0,
            total_taxes_paid=1400000.0
        )
        
        # Tax liability = 1500000 + (1500000 * 0.10) + (1500000 * 0.04) = 1710000
        base_tax = 1500000.0
        surcharge = base_tax * 0.10
        cess = base_tax * 0.04
        expected_liability_surcharge = base_tax + surcharge + cess
        assert totals_with_surcharge.total_tax_liability == expected_liability_surcharge
    
    def test_totals_refund_vs_payable_scenarios(self):
        """Test refund vs additional payable calculation scenarios."""
        # Refund scenario (taxes paid > liability)
        totals_refund = Totals(
            gross_total_income=500000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=50000.0,
            total_taxes_paid=60000.0
        )
        
        # Liability = 50000 + (50000 * 0.04) = 52000
        # Refund = 52000 - 60000 = -8000 (negative means refund)
        expected_refund = 52000.0 - 60000.0
        assert totals_refund.refund_or_payable == expected_refund
        
        # Additional payable scenario (liability > taxes paid)
        totals_payable = Totals(
            gross_total_income=1000000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=150000.0,
            total_taxes_paid=100000.0
        )
        
        # Liability = 150000 + (150000 * 0.04) = 156000
        # Additional payable = 156000 - 100000 = 56000
        expected_payable = 156000.0 - 100000.0
        assert totals_payable.refund_or_payable == expected_payable


class TestInvalidInputHandling:
    """Test handling of various invalid inputs and error scenarios."""
    
    def test_string_conversion_edge_cases(self):
        """Test string to number conversion edge cases."""
        # Test valid string conversions
        salary = Salary(
            gross_salary="100000.50",
            allowances="25000",
            perquisites="5000.0",
            profits_in_lieu="0"
        )
        assert salary.gross_salary == 100000.50
        assert salary.allowances == 25000.0
        assert salary.perquisites == 5000.0
        assert salary.profits_in_lieu == 0.0
        
        # Test invalid string conversions should raise ValidationError
        with pytest.raises(ValidationError):
            Salary(gross_salary="not_a_number")
    
    def test_extreme_values(self):
        """Test handling of extreme values."""
        # Test very large amounts
        large_salary = Salary(gross_salary=99999999.99)
        assert large_salary.gross_salary == 99999999.99
        
        # Test very small amounts
        small_salary = Salary(gross_salary=0.01)
        assert small_salary.gross_salary == 0.01
        
        # Test zero amounts
        zero_salary = Salary(gross_salary=0.0)
        assert zero_salary.gross_salary == 0.0
    
    def test_none_and_empty_string_handling(self):
        """Test handling of None and empty string values."""
        # Test optional fields with None
        personal_info = PersonalInfo(
            pan="ABCDE1234F",
            name="Test User",
            date_of_birth=date(1990, 1, 1),
            address="Test Address 123456",
            mobile=None,
            email=None,
            father_name=None
        )
        assert personal_info.mobile is None
        assert personal_info.email is None
        assert personal_info.father_name is None
        
        # Test empty strings for optional fields
        personal_info_empty = PersonalInfo(
            pan="ABCDE1234F",
            name="Test User",
            date_of_birth=date(1990, 1, 1),
            address="Test Address 123456",
            mobile="",
            email=""
        )
        assert personal_info_empty.mobile == ""
        assert personal_info_empty.email == ""
    
    def test_whitespace_handling(self):
        """Test whitespace stripping and validation."""
        # Test whitespace stripping in string fields
        personal_info = PersonalInfo(
            pan="  ABCDE1234F  ",
            name="  John Doe  ",
            date_of_birth=date(1990, 1, 1),
            address="  123 Main Street  ",
            mobile="  9876543210  ",
            email="  john@example.com  "
        )
        
        assert personal_info.pan == "ABCDE1234F"
        assert personal_info.name == "John Doe"
        assert personal_info.address == "123 Main Street"
        assert personal_info.mobile == "9876543210"
        assert personal_info.email == "john@example.com"
    
    def test_type_coercion_failures(self):
        """Test scenarios where type coercion should fail."""
        # Test invalid date formats
        with pytest.raises(ValidationError):
            PersonalInfo(
                pan="ABCDE1234F",
                name="Test User",
                date_of_birth="invalid_date",
                address="Test Address"
            )
        
        # Test invalid boolean values for revised_return
        with pytest.raises(ValidationError):
            ReturnContext(
                assessment_year="2025-26",
                form_type="ITR1",
                revised_return="maybe"  # Should be boolean
            )


class TestModelIntegration:
    """Test integration scenarios between different models."""
    
    def test_complete_tax_return_scenario(self):
        """Test a complete tax return scenario with all models."""
        # Create personal info
        personal_info = PersonalInfo(
            pan="ABCDE1234F",
            name="John Doe",
            date_of_birth=date(1985, 6, 15),
            address="123 Main Street, City, State - 123456",
            mobile="9876543210",
            email="john.doe@example.com"
        )
        
        # Create return context
        return_context = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1",
            filing_date=date(2024, 7, 31)
        )
        
        # Create income sources
        salary = Salary(
            gross_salary=800000.0,
            allowances=80000.0,
            perquisites=20000.0
        )
        
        house_property = HouseProperty(
            annual_value=300000.0,
            municipal_tax=15000.0,
            interest_on_loan=200000.0
        )
        
        other_sources = OtherSources(
            interest_income=30000.0,
            dividend_income=20000.0
        )
        
        # Create deductions
        deductions = Deductions(
            section_80c=150000.0,
            section_80d=25000.0,
            section_80g=10000.0
        )
        
        # Create taxes paid
        taxes_paid = TaxesPaid(
            tds=75000.0,
            advance_tax=25000.0
        )
        
        # Calculate totals
        gross_total_income = (
            salary.total_salary +
            house_property.net_income +
            other_sources.total_other_sources
        )
        
        totals = Totals(
            gross_total_income=gross_total_income,
            total_deductions=deductions.total_deductions,
            tax_on_taxable_income=120000.0,  # Calculated tax
            total_taxes_paid=taxes_paid.total_taxes_paid
        )
        
        # Verify all calculations are consistent
        assert salary.total_salary == 900000.0
        # House property net income calculation:
        # 300000 - 15000 - (285000 * 0.30) - 200000 = 300000 - 15000 - 85500 - 200000 = -500
        # But net income is clamped to 0, so it should be 0
        assert house_property.net_income == 0.0  # Net income is 0 due to high interest
        assert other_sources.total_other_sources == 50000.0
        assert deductions.total_deductions == 185000.0
        assert taxes_paid.total_taxes_paid == 100000.0
        
        # Verify totals calculations
        assert totals.taxable_income == gross_total_income - deductions.total_deductions
        assert totals.total_tax_liability > totals.tax_on_taxable_income  # Due to cess
        
        # Verify all models can be serialized
        models = [
            personal_info, return_context, salary, house_property,
            other_sources, deductions, taxes_paid, totals
        ]
        
        for model in models:
            json_str = model.model_dump_json()
            assert json_str is not None
            assert len(json_str) > 0
    
    def test_model_compatibility_with_json_schemas(self):
        """Test that models are compatible with expected JSON schema structure."""
        # Create a comprehensive model instance
        salary = Salary(
            gross_salary=600000.0,
            allowances=60000.0,
            perquisites=12000.0,
            profits_in_lieu=6000.0
        )
        
        # Test that serialized data has expected structure
        data = salary.model_dump()
        
        # Verify all expected fields are present
        expected_fields = ['gross_salary', 'allowances', 'perquisites', 'profits_in_lieu', 'total_salary']
        for field in expected_fields:
            assert field in data
        
        # Verify data types
        assert isinstance(data['gross_salary'], float)
        assert isinstance(data['allowances'], float)
        assert isinstance(data['perquisites'], float)
        assert isinstance(data['profits_in_lieu'], float)
        assert isinstance(data['total_salary'], float)
        
        # Verify computed field is calculated correctly
        expected_total = data['gross_salary'] + data['allowances'] + data['perquisites'] + data['profits_in_lieu']
        assert data['total_salary'] == expected_total
    
    def test_cross_model_validation_scenarios(self):
        """Test validation scenarios that involve multiple models."""
        # Test scenario where deductions exceed income (should be caught in Totals)
        with pytest.raises(ValidationError):
            Totals(
                gross_total_income=100000.0,
                total_deductions=150000.0,  # Exceeds income
                tax_on_taxable_income=0.0,
                total_taxes_paid=0.0
            )
        
        # Test scenario with inconsistent tax calculations
        with pytest.raises(ValidationError):
            Totals(
                gross_total_income=1000000.0,
                total_deductions=100000.0,
                tax_on_taxable_income=0.0,  # Zero tax for high income
                total_taxes_paid=0.0
            )


class TestPerformanceAndMemory:
    """Test performance characteristics and memory usage."""
    
    def test_large_dataset_serialization(self):
        """Test serialization performance with larger datasets."""
        # Create multiple model instances
        models = []
        for i in range(100):
            salary = Salary(
                gross_salary=500000.0 + i,
                allowances=50000.0 + i,
                perquisites=10000.0 + i,
                profits_in_lieu=5000.0 + i
            )
            models.append(salary)
        
        # Test batch serialization
        serialized_data = []
        for model in models:
            data = model.model_dump()
            serialized_data.append(data)
        
        assert len(serialized_data) == 100
        
        # Test batch deserialization
        restored_models = []
        for data in serialized_data:
            # Exclude computed fields for restoration
            input_data = {k: v for k, v in data.items() if k != 'total_salary'}
            model = Salary.model_validate(input_data)
            restored_models.append(model)
        
        assert len(restored_models) == 100
        
        # Verify data integrity
        for original, restored in zip(models, restored_models):
            assert original.gross_salary == restored.gross_salary
            assert original.total_salary == restored.total_salary
    
    def test_model_memory_efficiency(self):
        """Test that models don't consume excessive memory."""
        # Create a model with all fields populated
        personal_info = PersonalInfo(
            pan="ABCDE1234F",
            name="John Doe",
            father_name="Robert Doe",
            date_of_birth=date(1990, 5, 15),
            address="123 Main Street, City, State - 123456",
            mobile="9876543210",
            email="john.doe@example.com"
        )
        
        # Test that model dict representation is reasonable
        data = personal_info.model_dump()
        json_str = personal_info.model_dump_json()  # Use Pydantic's JSON serialization
        
        # Verify JSON string is not excessively large
        assert len(json_str) < 1000  # Reasonable size limit
        
        # Verify all data is preserved
        restored = PersonalInfo.model_validate_json(json_str)
        assert restored == personal_info