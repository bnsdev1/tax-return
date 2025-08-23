"""Tests for income-related models."""

import pytest
from pydantic import ValidationError
from core.models.income import Salary, HouseProperty, CapitalGains, OtherSources


class TestSalary:
    """Test cases for Salary model."""
    
    def test_salary_creation_with_defaults(self):
        """Test creating salary with default values."""
        salary = Salary()
        assert salary.gross_salary == 0.0
        assert salary.allowances == 0.0
        assert salary.perquisites == 0.0
        assert salary.profits_in_lieu == 0.0
        assert salary.total_salary == 0.0
    
    def test_salary_creation_with_values(self):
        """Test creating salary with specific values."""
        salary = Salary(
            gross_salary=500000.0,
            allowances=50000.0,
            perquisites=10000.0,
            profits_in_lieu=5000.0
        )
        assert salary.gross_salary == 500000.0
        assert salary.allowances == 50000.0
        assert salary.perquisites == 10000.0
        assert salary.profits_in_lieu == 5000.0
        assert salary.total_salary == 565000.0
    
    def test_salary_total_calculation(self):
        """Test total salary calculation."""
        salary = Salary(
            gross_salary=100000.50,
            allowances=25000.25,
            perquisites=5000.10,
            profits_in_lieu=2500.15
        )
        expected_total = round(100000.50 + 25000.25 + 5000.10 + 2500.15, 2)
        assert salary.total_salary == expected_total
    
    def test_salary_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            Salary(gross_salary=-1000.0)
        
        with pytest.raises(ValidationError):
            Salary(allowances=-500.0)
    
    def test_salary_json_serialization(self):
        """Test JSON serialization and deserialization."""
        salary = Salary(
            gross_salary=600000.0,
            allowances=60000.0,
            perquisites=12000.0,
            profits_in_lieu=6000.0
        )
        
        # Test serialization
        json_data = salary.model_dump()
        assert json_data['gross_salary'] == 600000.0
        assert json_data['total_salary'] == 678000.0
        
        # Test deserialization (exclude computed fields)
        input_data = {k: v for k, v in json_data.items() if k != 'total_salary'}
        new_salary = Salary.model_validate(input_data)
        assert new_salary.gross_salary == salary.gross_salary
        assert new_salary.total_salary == salary.total_salary


class TestHouseProperty:
    """Test cases for HouseProperty model."""
    
    def test_house_property_creation_with_defaults(self):
        """Test creating house property with default values."""
        house = HouseProperty()
        assert house.annual_value == 0.0
        assert house.municipal_tax == 0.0
        assert house.standard_deduction == 0.0
        assert house.interest_on_loan == 0.0
        assert house.net_income == 0.0
    
    def test_house_property_creation_with_values(self):
        """Test creating house property with specific values."""
        house = HouseProperty(
            annual_value=200000.0,
            municipal_tax=5000.0,
            standard_deduction=58500.0,  # 30% of (200000-5000)
            interest_on_loan=150000.0
        )
        assert house.annual_value == 200000.0
        assert house.municipal_tax == 5000.0
        assert house.standard_deduction == 58500.0
        assert house.interest_on_loan == 150000.0
    
    def test_house_property_net_income_calculation(self):
        """Test net income calculation with explicit standard deduction."""
        house = HouseProperty(
            annual_value=300000.0,
            municipal_tax=10000.0,
            standard_deduction=87000.0,  # 30% of (300000-10000)
            interest_on_loan=100000.0
        )
        expected_net = 300000.0 - 10000.0 - 87000.0 - 100000.0
        assert house.net_income == expected_net
    
    def test_house_property_auto_standard_deduction(self):
        """Test automatic standard deduction calculation when not provided."""
        house = HouseProperty(
            annual_value=200000.0,
            municipal_tax=5000.0,
            # standard_deduction not provided, should auto-calculate
            interest_on_loan=50000.0
        )
        # Auto standard deduction = 30% of (200000 - 5000) = 58500
        expected_net = 200000.0 - 5000.0 - 58500.0 - 50000.0
        assert house.net_income == expected_net
    
    def test_house_property_negative_net_income_becomes_zero(self):
        """Test that negative net income becomes zero."""
        house = HouseProperty(
            annual_value=100000.0,
            municipal_tax=5000.0,
            standard_deduction=28500.0,  # 30% of (100000-5000)
            interest_on_loan=200000.0  # Very high interest
        )
        # This would result in negative net income, but should be 0
        assert house.net_income == 0.0
    
    def test_house_property_negative_values_handled(self):
        """Test handling of negative values."""
        with pytest.raises(ValidationError):
            HouseProperty(annual_value=-1000.0)
    
    def test_house_property_json_serialization(self):
        """Test JSON serialization and deserialization."""
        house = HouseProperty(
            annual_value=250000.0,
            municipal_tax=7500.0,
            standard_deduction=72750.0,
            interest_on_loan=80000.0
        )
        
        # Test serialization
        json_data = house.model_dump()
        assert json_data['annual_value'] == 250000.0
        assert json_data['net_income'] == 89750.0
        
        # Test deserialization (exclude computed fields)
        input_data = {k: v for k, v in json_data.items() if k != 'net_income'}
        new_house = HouseProperty.model_validate(input_data)
        assert new_house.annual_value == house.annual_value
        assert new_house.net_income == house.net_income


class TestCapitalGains:
    """Test cases for CapitalGains model."""
    
    def test_capital_gains_creation_with_defaults(self):
        """Test creating capital gains with default values."""
        cg = CapitalGains()
        assert cg.short_term == 0.0
        assert cg.long_term == 0.0
        assert cg.total_capital_gains == 0.0
    
    def test_capital_gains_creation_with_values(self):
        """Test creating capital gains with specific values."""
        cg = CapitalGains(
            short_term=50000.0,
            long_term=100000.0
        )
        assert cg.short_term == 50000.0
        assert cg.long_term == 100000.0
        assert cg.total_capital_gains == 150000.0
    
    def test_capital_gains_total_calculation(self):
        """Test total capital gains calculation."""
        cg = CapitalGains(
            short_term=25000.50,
            long_term=75000.75
        )
        expected_total = round(25000.50 + 75000.75, 2)
        assert cg.total_capital_gains == expected_total
    
    def test_capital_gains_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            CapitalGains(short_term=-1000.0)
        
        with pytest.raises(ValidationError):
            CapitalGains(long_term=-500.0)
    
    def test_capital_gains_json_serialization(self):
        """Test JSON serialization and deserialization."""
        cg = CapitalGains(
            short_term=30000.0,
            long_term=120000.0
        )
        
        # Test serialization
        json_data = cg.model_dump()
        assert json_data['short_term'] == 30000.0
        assert json_data['long_term'] == 120000.0
        assert json_data['total_capital_gains'] == 150000.0
        
        # Test deserialization (exclude computed fields)
        input_data = {k: v for k, v in json_data.items() if k != 'total_capital_gains'}
        new_cg = CapitalGains.model_validate(input_data)
        assert new_cg.short_term == cg.short_term
        assert new_cg.total_capital_gains == cg.total_capital_gains


class TestOtherSources:
    """Test cases for OtherSources model."""
    
    def test_other_sources_creation_with_defaults(self):
        """Test creating other sources with default values."""
        other = OtherSources()
        assert other.interest_income == 0.0
        assert other.dividend_income == 0.0
        assert other.other_income == 0.0
        assert other.total_other_sources == 0.0
    
    def test_other_sources_creation_with_values(self):
        """Test creating other sources with specific values."""
        other = OtherSources(
            interest_income=25000.0,
            dividend_income=15000.0,
            other_income=10000.0
        )
        assert other.interest_income == 25000.0
        assert other.dividend_income == 15000.0
        assert other.other_income == 10000.0
        assert other.total_other_sources == 50000.0
    
    def test_other_sources_total_calculation(self):
        """Test total other sources calculation."""
        other = OtherSources(
            interest_income=12500.25,
            dividend_income=7500.50,
            other_income=5000.75
        )
        expected_total = round(12500.25 + 7500.50 + 5000.75, 2)
        assert other.total_other_sources == expected_total
    
    def test_other_sources_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            OtherSources(interest_income=-1000.0)
        
        with pytest.raises(ValidationError):
            OtherSources(dividend_income=-500.0)
        
        with pytest.raises(ValidationError):
            OtherSources(other_income=-250.0)
    
    def test_other_sources_json_serialization(self):
        """Test JSON serialization and deserialization."""
        other = OtherSources(
            interest_income=20000.0,
            dividend_income=12000.0,
            other_income=8000.0
        )
        
        # Test serialization
        json_data = other.model_dump()
        assert json_data['interest_income'] == 20000.0
        assert json_data['dividend_income'] == 12000.0
        assert json_data['other_income'] == 8000.0
        assert json_data['total_other_sources'] == 40000.0
        
        # Test deserialization (exclude computed fields)
        input_data = {k: v for k, v in json_data.items() if k != 'total_other_sources'}
        new_other = OtherSources.model_validate(input_data)
        assert new_other.interest_income == other.interest_income
        assert new_other.total_other_sources == other.total_other_sources


class TestIncomeModelsIntegration:
    """Integration tests for income models."""
    
    def test_all_income_models_together(self):
        """Test using all income models together."""
        salary = Salary(gross_salary=600000.0, allowances=60000.0)
        house = HouseProperty(annual_value=200000.0, municipal_tax=5000.0)
        capital_gains = CapitalGains(short_term=50000.0, long_term=100000.0)
        other_sources = OtherSources(interest_income=25000.0, dividend_income=15000.0)
        
        # Calculate total income
        total_income = (
            salary.total_salary +
            house.net_income +
            capital_gains.total_capital_gains +
            other_sources.total_other_sources
        )
        
        # Verify individual calculations
        assert salary.total_salary == 660000.0
        assert house.net_income > 0  # Should have positive net income
        assert capital_gains.total_capital_gains == 150000.0
        assert other_sources.total_other_sources == 40000.0
        
        # Verify total is reasonable
        assert total_income > 800000.0
    
    def test_edge_case_zero_values(self):
        """Test edge case with all zero values."""
        salary = Salary()
        house = HouseProperty()
        capital_gains = CapitalGains()
        other_sources = OtherSources()
        
        assert salary.total_salary == 0.0
        assert house.net_income == 0.0
        assert capital_gains.total_capital_gains == 0.0
        assert other_sources.total_other_sources == 0.0