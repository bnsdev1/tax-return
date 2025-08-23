"""Tests for deductions model."""

import pytest
from pydantic import ValidationError
from core.models.deductions import Deductions


class TestDeductions:
    """Test cases for Deductions model."""
    
    def test_deductions_creation_with_defaults(self):
        """Test creating deductions with default values."""
        deductions = Deductions()
        assert deductions.section_80c == 0.0
        assert deductions.section_80d == 0.0
        assert deductions.section_80g == 0.0
        assert deductions.other_deductions == 0.0
        assert deductions.total_deductions == 0.0
    
    def test_deductions_creation_with_values(self):
        """Test creating deductions with specific values."""
        deductions = Deductions(
            section_80c=100000.0,
            section_80d=25000.0,
            section_80g=10000.0,
            other_deductions=5000.0
        )
        assert deductions.section_80c == 100000.0
        assert deductions.section_80d == 25000.0
        assert deductions.section_80g == 10000.0
        assert deductions.other_deductions == 5000.0
        assert deductions.total_deductions == 140000.0
    
    def test_total_deductions_calculation(self):
        """Test that total deductions is calculated correctly."""
        deductions = Deductions(
            section_80c=50000.0,
            section_80d=15000.0,
            section_80g=8000.0,
            other_deductions=2000.0
        )
        assert deductions.total_deductions == 75000.0
    
    def test_section_80c_limit_validation(self):
        """Test Section 80C limit validation."""
        with pytest.raises(ValidationError) as exc_info:
            Deductions(section_80c=200000.0)
        
        assert "Section 80C deduction cannot exceed Rs. 1,50,000" in str(exc_info.value)
    
    def test_section_80c_at_limit(self):
        """Test Section 80C at maximum limit."""
        deductions = Deductions(section_80c=150000.0)
        assert deductions.section_80c == 150000.0
    
    def test_section_80d_limit_validation(self):
        """Test Section 80D limit validation."""
        with pytest.raises(ValidationError) as exc_info:
            Deductions(section_80d=100000.0)
        
        assert "Section 80D deduction cannot exceed Rs. 75,000" in str(exc_info.value)
    
    def test_section_80d_at_limit(self):
        """Test Section 80D at maximum limit."""
        deductions = Deductions(section_80d=75000.0)
        assert deductions.section_80d == 75000.0
    
    def test_section_80g_reasonable_limit(self):
        """Test Section 80G reasonable limit validation."""
        with pytest.raises(ValidationError) as exc_info:
            Deductions(section_80g=1500000.0)
        
        assert "Section 80G deduction seems unreasonably high" in str(exc_info.value)
    
    def test_negative_values_validation(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            Deductions(section_80c=-1000.0)
        
        with pytest.raises(ValidationError):
            Deductions(section_80d=-500.0)
        
        with pytest.raises(ValidationError):
            Deductions(section_80g=-100.0)
        
        with pytest.raises(ValidationError):
            Deductions(other_deductions=-50.0)
    
    def test_decimal_rounding(self):
        """Test that decimal values are properly rounded."""
        deductions = Deductions(
            section_80c=100000.555,
            section_80d=25000.999,
            section_80g=10000.123,
            other_deductions=5000.456
        )
        assert deductions.section_80c == 100000.55
        assert deductions.section_80d == 25001.0
        assert deductions.section_80g == 10000.12
        assert deductions.other_deductions == 5000.46
        # Total should also be properly rounded
        assert deductions.total_deductions == 140002.13
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = Deductions(
            section_80c=100000.0,
            section_80d=25000.0,
            section_80g=10000.0,
            other_deductions=5000.0
        )
        
        # Serialize to JSON (exclude computed fields)
        json_data = original.model_dump(exclude={'total_deductions'})
        
        # Deserialize from JSON
        restored = Deductions(**json_data)
        
        assert restored.section_80c == original.section_80c
        assert restored.section_80d == original.section_80d
        assert restored.section_80g == original.section_80g
        assert restored.other_deductions == original.other_deductions
        assert restored.total_deductions == original.total_deductions
    
    def test_string_to_float_conversion(self):
        """Test that string values are converted to float."""
        deductions = Deductions(
            section_80c="100000.0",
            section_80d="25000.5",
            section_80g="10000",
            other_deductions="5000.25"
        )
        assert deductions.section_80c == 100000.0
        assert deductions.section_80d == 25000.5
        assert deductions.section_80g == 10000.0
        assert deductions.other_deductions == 5000.25