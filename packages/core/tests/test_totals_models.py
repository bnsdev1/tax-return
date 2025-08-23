"""Tests for totals model."""

import pytest
from pydantic import ValidationError
from core.models.totals import Totals


class TestTotals:
    """Test cases for Totals model."""
    
    def test_totals_creation_with_defaults(self):
        """Test creating totals with default values."""
        totals = Totals()
        assert totals.gross_total_income == 0.0
        assert totals.total_deductions == 0.0
        assert totals.tax_on_taxable_income == 0.0
        assert totals.total_taxes_paid == 0.0
        assert totals.taxable_income == 0.0
        assert totals.total_tax_liability == 0.0
        assert totals.refund_or_payable == 0.0
    
    def test_taxable_income_calculation(self):
        """Test taxable income calculation."""
        totals = Totals(
            gross_total_income=500000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=50000.0  # Provide tax for income above exemption
        )
        assert totals.taxable_income == 400000.0
    
    def test_taxable_income_cannot_be_negative(self):
        """Test that taxable income cannot be negative."""
        totals = Totals(
            gross_total_income=100000.0,
            total_deductions=100000.0,  # Equal to income to avoid validation error
            tax_on_taxable_income=0.0
        )
        # Should not raise error and taxable income should be 0
        assert totals.taxable_income == 0.0
    
    def test_total_tax_liability_with_cess(self):
        """Test total tax liability calculation with cess."""
        totals = Totals(
            gross_total_income=1000000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=100000.0
        )
        # Base tax: 100000, Cess (4%): 4000, No surcharge
        expected_liability = 100000.0 + (100000.0 * 0.04)
        assert totals.total_tax_liability == expected_liability
    
    def test_total_tax_liability_with_surcharge(self):
        """Test total tax liability calculation with surcharge for high income."""
        totals = Totals(
            gross_total_income=6000000.0,  # 60L income
            total_deductions=500000.0,
            tax_on_taxable_income=1500000.0
        )
        # Base tax: 1500000, Surcharge (10%): 150000, Cess (4% of base+surcharge): 66000
        base_tax = 1500000.0
        surcharge = base_tax * 0.10
        cess = base_tax * 0.04
        expected_liability = base_tax + surcharge + cess
        assert totals.total_tax_liability == expected_liability
    
    def test_refund_calculation(self):
        """Test refund calculation when taxes paid exceed liability."""
        totals = Totals(
            gross_total_income=500000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=50000.0,
            total_taxes_paid=60000.0
        )
        # Tax liability with cess: 50000 + 2000 = 52000
        # Refund: 52000 - 60000 = -8000 (negative means refund)
        expected_refund = 52000.0 - 60000.0
        assert totals.refund_or_payable == expected_refund
    
    def test_additional_tax_payable(self):
        """Test additional tax payable when liability exceeds taxes paid."""
        totals = Totals(
            gross_total_income=1000000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=150000.0,
            total_taxes_paid=100000.0
        )
        # Tax liability with cess: 150000 + 6000 = 156000
        # Additional payable: 156000 - 100000 = 56000
        expected_payable = 156000.0 - 100000.0
        assert totals.refund_or_payable == expected_payable
    
    def test_negative_values_validation(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            Totals(gross_total_income=-1000.0)
        
        with pytest.raises(ValidationError):
            Totals(total_deductions=-500.0)
        
        with pytest.raises(ValidationError):
            Totals(tax_on_taxable_income=-100.0)
        
        with pytest.raises(ValidationError):
            Totals(total_taxes_paid=-50.0)
    
    def test_deductions_exceed_income_validation(self):
        """Test validation when deductions exceed gross income."""
        with pytest.raises(ValidationError) as exc_info:
            Totals(
                gross_total_income=100000.0,
                total_deductions=150000.0
            )
        
        assert "Total deductions cannot exceed gross total income" in str(exc_info.value)
    
    def test_zero_tax_for_low_income(self):
        """Test that zero tax is allowed for income below exemption limit."""
        totals = Totals(
            gross_total_income=200000.0,
            total_deductions=50000.0,
            tax_on_taxable_income=0.0
        )
        # Should not raise error for income below 2.5L
        assert totals.tax_on_taxable_income == 0.0
    
    def test_zero_tax_validation_for_high_income(self):
        """Test validation when tax is zero for high income."""
        with pytest.raises(ValidationError) as exc_info:
            Totals(
                gross_total_income=1000000.0,
                total_deductions=100000.0,
                tax_on_taxable_income=0.0
            )
        
        assert "Tax on taxable income cannot be zero for income above exemption limit" in str(exc_info.value)
    
    def test_unreasonable_tax_rate_validation(self):
        """Test validation for unreasonably high tax rates."""
        with pytest.raises(ValidationError) as exc_info:
            Totals(
                gross_total_income=1000000.0,
                total_deductions=100000.0,
                tax_on_taxable_income=500000.0  # 55.6% effective rate
            )
        
        assert "Effective tax rate" in str(exc_info.value)
        assert "seems unreasonably high" in str(exc_info.value)
    
    def test_reasonable_high_tax_rate(self):
        """Test that reasonable high tax rates are accepted."""
        totals = Totals(
            gross_total_income=2000000.0,
            total_deductions=200000.0,
            tax_on_taxable_income=600000.0  # 33.3% effective rate
        )
        # Should not raise error for reasonable tax rate
        assert totals.tax_on_taxable_income == 600000.0
    
    def test_decimal_rounding(self):
        """Test that decimal values are properly rounded."""
        totals = Totals(
            gross_total_income=1000000.555,
            total_deductions=100000.999,
            tax_on_taxable_income=150000.123,
            total_taxes_paid=100000.456
        )
        assert totals.gross_total_income == 1000000.56
        assert totals.total_deductions == 100001.0
        assert totals.tax_on_taxable_income == 150000.12
        assert totals.total_taxes_paid == 100000.46
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = Totals(
            gross_total_income=1000000.0,
            total_deductions=100000.0,
            tax_on_taxable_income=150000.0,
            total_taxes_paid=100000.0
        )
        
        # Serialize to JSON (exclude computed fields)
        json_data = original.model_dump(exclude={'taxable_income', 'total_tax_liability', 'refund_or_payable'})
        
        # Deserialize from JSON
        restored = Totals(**json_data)
        
        assert restored.gross_total_income == original.gross_total_income
        assert restored.total_deductions == original.total_deductions
        assert restored.tax_on_taxable_income == original.tax_on_taxable_income
        assert restored.total_taxes_paid == original.total_taxes_paid
        assert restored.taxable_income == original.taxable_income
        assert restored.total_tax_liability == original.total_tax_liability
        assert restored.refund_or_payable == original.refund_or_payable
    
    def test_complex_calculation_scenario(self):
        """Test a complex real-world scenario."""
        totals = Totals(
            gross_total_income=1500000.0,  # 15L income
            total_deductions=200000.0,     # 2L deductions
            tax_on_taxable_income=195000.0, # Tax on 13L (approx 15% effective)
            total_taxes_paid=180000.0      # 1.8L paid
        )
        
        # Taxable income: 15L - 2L = 13L
        assert totals.taxable_income == 1300000.0
        
        # Tax liability: 195000 + (195000 * 0.04) = 202800
        expected_liability = 195000.0 + (195000.0 * 0.04)
        assert totals.total_tax_liability == expected_liability
        
        # Additional payable: 202800 - 180000 = 22800
        expected_payable = expected_liability - 180000.0
        assert totals.refund_or_payable == expected_payable