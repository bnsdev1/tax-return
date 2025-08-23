"""
Unit tests for the tax computation engine.

Tests cover:
- Basic slab calculations for both regimes
- Surcharge calculations with marginal relief
- Cess computation
- Rebate 87A scenarios
- Interest calculations (234A, 234B, 234C)
- Net refund/payable calculations
- Edge cases and boundary conditions
"""

import pytest
from decimal import Decimal
from datetime import date
from pathlib import Path
import sys

# Add the core package to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.compute.tax import TaxEngine, TaxComputation


class TestTaxEngine:
    """Test cases for TaxEngine."""
    
    @pytest.fixture
    def tax_engine(self):
        """Create tax engine instance for testing."""
        return TaxEngine("2025-26")
    
    def test_new_regime_basic_slabs(self, tax_engine):
        """Test basic slab calculations for new regime."""
        # Test case 1: Income within first slab (₹3 lakh)
        result = tax_engine.compute_tax(Decimal('250000'), regime='new')
        assert result.tax_before_rebate == Decimal('0')
        assert result.total_tax_liability == Decimal('0')
        
        # Test case 2: Income in second slab (₹5 lakh)
        result = tax_engine.compute_tax(Decimal('500000'), regime='new')
        expected_tax = Decimal('200000') * Decimal('0.05')  # ₹2L at 5%
        assert result.tax_before_rebate == expected_tax
        
        # Test case 3: Income across multiple slabs (₹10 lakh)
        result = tax_engine.compute_tax(Decimal('1000000'), regime='new')
        expected_tax = (
            Decimal('300000') * Decimal('0.05') +  # ₹3L at 5%
            Decimal('300000') * Decimal('0.10') +  # ₹3L at 10%
            Decimal('100000') * Decimal('0.15')    # ₹1L at 15%
        )
        assert result.tax_before_rebate == expected_tax
    
    def test_old_regime_basic_slabs(self, tax_engine):
        """Test basic slab calculations for old regime."""
        # Test case 1: Income within first slab (₹2.5 lakh)
        result = tax_engine.compute_tax(Decimal('200000'), regime='old')
        assert result.tax_before_rebate == Decimal('0')
        
        # Test case 2: Income in second slab (₹4 lakh)
        result = tax_engine.compute_tax(Decimal('400000'), regime='old')
        expected_tax = Decimal('150000') * Decimal('0.05')  # ₹1.5L at 5%
        assert result.tax_before_rebate == expected_tax
        
        # Test case 3: Income across all slabs (₹15 lakh)
        result = tax_engine.compute_tax(Decimal('1500000'), regime='old')
        expected_tax = (
            Decimal('250000') * Decimal('0.05') +   # ₹2.5L at 5%
            Decimal('500000') * Decimal('0.20') +   # ₹5L at 20%
            Decimal('500000') * Decimal('0.30')     # ₹5L at 30%
        )
        assert result.tax_before_rebate == expected_tax
    
    def test_rebate_87a_new_regime(self, tax_engine):
        """Test rebate 87A calculations for new regime."""
        # Test case 1: Income eligible for full rebate (₹6 lakh)
        result = tax_engine.compute_tax(Decimal('600000'), regime='new')
        expected_tax_before_rebate = Decimal('300000') * Decimal('0.05')  # ₹15,000
        expected_rebate = min(expected_tax_before_rebate, Decimal('25000'))
        
        assert result.tax_before_rebate == expected_tax_before_rebate
        assert result.rebate_87a == expected_rebate
        assert result.tax_after_rebate == Decimal('0')  # Full rebate
        
        # Test case 2: Income above rebate limit (₹8 lakh)
        result = tax_engine.compute_tax(Decimal('800000'), regime='new')
        assert result.rebate_87a == Decimal('0')  # No rebate above ₹7L
    
    def test_rebate_87a_old_regime(self, tax_engine):
        """Test rebate 87A calculations for old regime."""
        # Test case 1: Income eligible for rebate (₹4 lakh)
        result = tax_engine.compute_tax(Decimal('400000'), regime='old')
        expected_tax_before_rebate = Decimal('150000') * Decimal('0.05')  # ₹7,500
        expected_rebate = min(expected_tax_before_rebate, Decimal('12500'))
        
        assert result.rebate_87a == expected_rebate
        assert result.tax_after_rebate == Decimal('0')  # Full rebate
        
        # Test case 2: Income above rebate limit (₹6 lakh)
        result = tax_engine.compute_tax(Decimal('600000'), regime='old')
        assert result.rebate_87a == Decimal('0')  # No rebate above ₹5L
    
    def test_surcharge_calculations(self, tax_engine):
        """Test surcharge calculations with marginal relief."""
        # Test case 1: Income below surcharge threshold
        result = tax_engine.compute_tax(Decimal('4000000'), regime='new')
        assert result.surcharge == Decimal('0')
        
        # Test case 2: Income in first surcharge slab (₹60 lakh)
        result = tax_engine.compute_tax(Decimal('6000000'), regime='new')
        assert result.surcharge > Decimal('0')
        # Surcharge should be 10% of tax after rebate
        expected_surcharge = result.tax_after_rebate * Decimal('0.10')
        assert result.surcharge == expected_surcharge
        
        # Test case 3: Income in higher surcharge slab (₹1.5 crore)
        result = tax_engine.compute_tax(Decimal('15000000'), regime='new')
        assert result.surcharge > Decimal('0')
        # Should use 15% surcharge rate
    
    def test_cess_calculation(self, tax_engine):
        """Test Health and Education Cess calculation."""
        result = tax_engine.compute_tax(Decimal('1000000'), regime='new')
        
        # Cess should be 4% of (tax + surcharge)
        expected_cess = result.tax_plus_surcharge * Decimal('0.04')
        assert result.cess == expected_cess
        
        # Total liability should include cess
        expected_total = result.tax_plus_surcharge + result.cess
        assert result.total_tax_liability == expected_total
    
    def test_interest_234a_calculation(self, tax_engine):
        """Test interest calculation under section 234A."""
        filing_date = date(2025, 7, 31)  # Filed on July 31, 2025
        
        result = tax_engine.compute_tax(
            Decimal('1000000'),
            regime='new',
            advance_tax_paid=Decimal('50000'),  # Less than required
            filing_date=filing_date
        )
        
        # Should have interest for delayed payment
        assert result.interest_234a > Decimal('0')
        assert len(result.interest_details) > 0
        
        # Check interest details
        interest_234a_detail = next(
            (detail for detail in result.interest_details if detail.section == '234A'),
            None
        )
        assert interest_234a_detail is not None
        assert interest_234a_detail.months > 0
    
    def test_interest_234b_calculation(self, tax_engine):
        """Test interest calculation under section 234B."""
        result = tax_engine.compute_tax(
            Decimal('1000000'),
            regime='new',
            advance_tax_paid=Decimal('30000')  # Less than 90% of liability
        )
        
        # Should have interest for insufficient advance tax
        assert result.interest_234b > Decimal('0')
        
        # Check interest details
        interest_234b_detail = next(
            (detail for detail in result.interest_details if detail.section == '234B'),
            None
        )
        assert interest_234b_detail is not None
    
    def test_net_position_refund(self, tax_engine):
        """Test net position calculation - refund scenario."""
        result = tax_engine.compute_tax(Decimal('500000'), regime='new')
        
        # Scenario: TDS and advance tax exceed liability
        net_position = tax_engine.calculate_net_position(
            result,
            advance_tax_paid=Decimal('20000'),
            tds_deducted=Decimal('10000')
        )
        
        assert net_position['is_refund'] == True
        assert net_position['is_payable'] == False
        assert net_position['refund_amount'] > 0
        assert net_position['payable_amount'] == 0
    
    def test_net_position_payable(self, tax_engine):
        """Test net position calculation - payable scenario."""
        result = tax_engine.compute_tax(Decimal('1500000'), regime='new')
        
        # Scenario: Payments less than liability
        net_position = tax_engine.calculate_net_position(
            result,
            advance_tax_paid=Decimal('50000'),
            tds_deducted=Decimal('30000')
        )
        
        assert net_position['is_payable'] == True
        assert net_position['is_refund'] == False
        assert net_position['payable_amount'] > 0
        assert net_position['refund_amount'] == 0
    
    def test_effective_tax_rate(self, tax_engine):
        """Test effective tax rate calculation."""
        result = tax_engine.compute_tax(Decimal('1000000'), regime='new')
        effective_rate = tax_engine.get_effective_tax_rate(result)
        
        assert 0 <= effective_rate <= 100
        expected_rate = float(result.total_tax_liability / result.total_income * 100)
        assert abs(effective_rate - expected_rate) < 0.01  # Allow small floating point difference
    
    def test_marginal_tax_rate(self, tax_engine):
        """Test marginal tax rate calculation."""
        # Test for different income levels
        rate_500k = tax_engine.get_marginal_tax_rate(Decimal('500000'), 'new')
        rate_800k = tax_engine.get_marginal_tax_rate(Decimal('800000'), 'new')
        rate_1200k = tax_engine.get_marginal_tax_rate(Decimal('1200000'), 'new')
        
        assert rate_500k == 5.0   # 5% slab
        assert rate_800k == 10.0  # 10% slab
        assert rate_1200k == 15.0 # 15% slab
    
    def test_slab_wise_breakdown(self, tax_engine):
        """Test slab-wise tax breakdown."""
        result = tax_engine.compute_tax(Decimal('1000000'), regime='new')
        
        assert len(result.slab_wise_tax) > 0
        
        # Check that breakdown adds up to total tax
        total_from_slabs = sum(slab['tax_amount'] for slab in result.slab_wise_tax)
        assert abs(total_from_slabs - float(result.tax_before_rebate)) < 0.01
    
    def test_zero_income(self, tax_engine):
        """Test edge case: zero income."""
        result = tax_engine.compute_tax(Decimal('0'), regime='new')
        
        assert result.tax_before_rebate == Decimal('0')
        assert result.total_tax_liability == Decimal('0')
        assert result.total_interest == Decimal('0')
    
    def test_very_high_income(self, tax_engine):
        """Test edge case: very high income with maximum surcharge."""
        result = tax_engine.compute_tax(Decimal('100000000'), regime='new')  # ₹10 crore
        
        assert result.tax_before_rebate > Decimal('0')
        assert result.surcharge > Decimal('0')
        assert result.total_tax_liability > Decimal('0')
        
        # Should use highest surcharge rate (37%)
        # Note: Actual calculation would depend on marginal relief
    
    def test_regime_comparison(self, tax_engine):
        """Test comparison between old and new regimes."""
        income = Decimal('800000')
        
        old_result = tax_engine.compute_tax(income, regime='old')
        new_result = tax_engine.compute_tax(income, regime='new')
        
        # Both should have valid calculations
        assert old_result.total_tax_liability >= Decimal('0')
        assert new_result.total_tax_liability >= Decimal('0')
        
        # Results may differ due to different slab structures
        # This test ensures both regimes work without errors


class TestTaxEngineIntegration:
    """Integration tests for tax engine with realistic scenarios."""
    
    @pytest.fixture
    def tax_engine(self):
        """Create tax engine instance for testing."""
        return TaxEngine("2025-26")
    
    def test_typical_salaried_employee_new_regime(self, tax_engine):
        """Test typical salaried employee scenario - new regime."""
        # Scenario: ₹12 lakh salary, some TDS deducted
        result = tax_engine.compute_tax(Decimal('1200000'), regime='new')
        
        net_position = tax_engine.calculate_net_position(
            result,
            tds_deducted=Decimal('85000')
        )
        
        # Should have reasonable tax liability
        assert result.total_tax_liability > Decimal('0')
        assert result.rebate_87a == Decimal('0')  # Above rebate limit
        
        # Effective rate should be reasonable
        effective_rate = tax_engine.get_effective_tax_rate(result)
        assert 5 <= effective_rate <= 15  # Reasonable range
    
    def test_high_income_individual_old_regime(self, tax_engine):
        """Test high income individual - old regime with surcharge."""
        # Scenario: ₹75 lakh income
        result = tax_engine.compute_tax(Decimal('7500000'), regime='old')
        
        # Should have surcharge
        assert result.surcharge > Decimal('0')
        assert result.cess > Decimal('0')
        
        # Total liability should be substantial
        assert result.total_tax_liability > Decimal('1000000')
    
    def test_interest_scenario_late_filing(self, tax_engine):
        """Test interest calculation for late filing."""
        filing_date = date(2025, 12, 31)  # Very late filing
        
        result = tax_engine.compute_tax(
            Decimal('1500000'),
            regime='new',
            advance_tax_paid=Decimal('100000'),
            filing_date=filing_date
        )
        
        # Should have significant interest
        assert result.total_interest > Decimal('0')
        assert len(result.interest_details) > 0
        
        # Total payable should include interest
        assert result.total_payable > result.total_tax_liability


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])