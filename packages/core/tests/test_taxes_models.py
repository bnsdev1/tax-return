"""Tests for taxes model."""

import pytest
from pydantic import ValidationError
from core.models.taxes import TaxesPaid


class TestTaxesPaid:
    """Test cases for TaxesPaid model."""
    
    def test_taxes_paid_creation_with_defaults(self):
        """Test creating taxes paid with default values."""
        taxes = TaxesPaid()
        assert taxes.tds == 0.0
        assert taxes.advance_tax == 0.0
        assert taxes.self_assessment_tax == 0.0
        assert taxes.total_taxes_paid == 0.0
    
    def test_taxes_paid_creation_with_values(self):
        """Test creating taxes paid with specific values."""
        taxes = TaxesPaid(
            tds=50000.0,
            advance_tax=25000.0,
            self_assessment_tax=10000.0
        )
        assert taxes.tds == 50000.0
        assert taxes.advance_tax == 25000.0
        assert taxes.self_assessment_tax == 10000.0
        assert taxes.total_taxes_paid == 85000.0
    
    def test_total_taxes_paid_calculation(self):
        """Test that total taxes paid is calculated correctly."""
        taxes = TaxesPaid(
            tds=30000.0,
            advance_tax=15000.0,
            self_assessment_tax=5000.0
        )
        assert taxes.total_taxes_paid == 50000.0
    
    def test_only_tds_payment(self):
        """Test with only TDS payment."""
        taxes = TaxesPaid(tds=75000.0)
        assert taxes.tds == 75000.0
        assert taxes.advance_tax == 0.0
        assert taxes.self_assessment_tax == 0.0
        assert taxes.total_taxes_paid == 75000.0
    
    def test_only_advance_tax_payment(self):
        """Test with only advance tax payment."""
        taxes = TaxesPaid(advance_tax=40000.0)
        assert taxes.tds == 0.0
        assert taxes.advance_tax == 40000.0
        assert taxes.self_assessment_tax == 0.0
        assert taxes.total_taxes_paid == 40000.0
    
    def test_only_self_assessment_payment(self):
        """Test with only self-assessment tax payment."""
        taxes = TaxesPaid(self_assessment_tax=20000.0)
        assert taxes.tds == 0.0
        assert taxes.advance_tax == 0.0
        assert taxes.self_assessment_tax == 20000.0
        assert taxes.total_taxes_paid == 20000.0
    
    def test_negative_values_validation(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            TaxesPaid(tds=-1000.0)
        
        with pytest.raises(ValidationError):
            TaxesPaid(advance_tax=-500.0)
        
        with pytest.raises(ValidationError):
            TaxesPaid(self_assessment_tax=-100.0)
    
    def test_decimal_rounding(self):
        """Test that decimal values are properly rounded."""
        taxes = TaxesPaid(
            tds=50000.555,
            advance_tax=25000.999,
            self_assessment_tax=10000.123
        )
        assert taxes.tds == 50000.56
        assert taxes.advance_tax == 25001.0
        assert taxes.self_assessment_tax == 10000.12
        # Total should also be properly rounded
        assert taxes.total_taxes_paid == 85001.68
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = TaxesPaid(
            tds=50000.0,
            advance_tax=25000.0,
            self_assessment_tax=10000.0
        )
        
        # Serialize to JSON (exclude computed fields)
        json_data = original.model_dump(exclude={'total_taxes_paid'})
        
        # Deserialize from JSON
        restored = TaxesPaid(**json_data)
        
        assert restored.tds == original.tds
        assert restored.advance_tax == original.advance_tax
        assert restored.self_assessment_tax == original.self_assessment_tax
        assert restored.total_taxes_paid == original.total_taxes_paid
    
    def test_string_to_float_conversion(self):
        """Test that string values are converted to float."""
        taxes = TaxesPaid(
            tds="50000.0",
            advance_tax="25000.5",
            self_assessment_tax="10000"
        )
        assert taxes.tds == 50000.0
        assert taxes.advance_tax == 25000.5
        assert taxes.self_assessment_tax == 10000.0
        assert taxes.total_taxes_paid == 85000.5
    
    def test_large_amounts(self):
        """Test with large tax amounts."""
        taxes = TaxesPaid(
            tds=1000000.0,
            advance_tax=500000.0,
            self_assessment_tax=250000.0
        )
        assert taxes.total_taxes_paid == 1750000.0