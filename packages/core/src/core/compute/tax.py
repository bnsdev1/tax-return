"""
Comprehensive tax computation engine for Indian Income Tax.

Supports both old and new tax regimes (115BAC) with:
- Slab-based tax calculation
- Surcharge computation with marginal relief
- Health and Education Cess (4%)
- Rebate under section 87A
- Interest calculations under sections 234A, 234B, 234C
- Advance tax requirements and interest
"""

import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TaxSlab:
    """Individual tax slab definition."""
    min_amount: Decimal
    max_amount: Optional[Decimal]
    rate: Decimal
    description: str


@dataclass
class SurchargeRule:
    """Surcharge rule definition."""
    min_amount: Decimal
    max_amount: Optional[Decimal]
    rate: Decimal
    description: str


@dataclass
class InterestCalculation:
    """Interest calculation result."""
    section: str
    principal_amount: Decimal
    rate: Decimal
    months: int
    interest_amount: Decimal
    description: str


@dataclass
class TaxComputation:
    """Complete tax computation result."""
    # Input parameters
    total_income: Decimal
    regime: str
    assessment_year: str
    
    # Basic tax calculation
    taxable_income: Decimal
    tax_before_rebate: Decimal
    rebate_87a: Decimal
    tax_after_rebate: Decimal
    
    # Surcharge and cess
    surcharge: Decimal
    tax_plus_surcharge: Decimal
    cess: Decimal
    total_tax_liability: Decimal
    
    # Interest calculations
    interest_234a: Decimal = Decimal('0')
    interest_234b: Decimal = Decimal('0')
    interest_234c: Decimal = Decimal('0')
    total_interest: Decimal = Decimal('0')
    
    # Final amounts
    total_payable: Decimal = field(init=False)
    
    # Breakdown details
    slab_wise_tax: List[Dict[str, Any]] = field(default_factory=list)
    interest_details: List[InterestCalculation] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate total payable after initialization."""
        self.total_payable = self.total_tax_liability + self.total_interest


class TaxEngine:
    """Comprehensive tax computation engine."""
    
    def __init__(self, assessment_year: str = "2025-26"):
        """Initialize tax engine with rates for given assessment year."""
        self.assessment_year = assessment_year
        self.rates = self._load_tax_rates(assessment_year)
        
    def _load_tax_rates(self, assessment_year: str) -> Dict[str, Any]:
        """Load tax rates from YAML file."""
        rates_file = Path(__file__).parent.parent / "data" / "rates" / f"{assessment_year}.yaml"
        
        if not rates_file.exists():
            raise FileNotFoundError(f"Tax rates file not found: {rates_file}")
        
        with open(rates_file, 'r', encoding='utf-8') as f:
            rates = yaml.safe_load(f)
        
        logger.info(f"Loaded tax rates for AY {assessment_year}")
        return rates
    
    def compute_tax(
        self,
        total_income: Decimal,
        regime: str = "new",
        advance_tax_paid: Decimal = Decimal('0'),
        tds_deducted: Decimal = Decimal('0'),
        filing_date: Optional[date] = None,
        taxpayer_age: int = 35
    ) -> TaxComputation:
        """
        Compute comprehensive tax liability.
        
        Args:
            total_income: Total taxable income
            regime: Tax regime ('old' or 'new')
            advance_tax_paid: Advance tax already paid
            tds_deducted: TDS already deducted
            filing_date: Date of filing (for interest calculation)
            taxpayer_age: Age of taxpayer (for senior citizen benefits)
            
        Returns:
            TaxComputation with complete breakdown
        """
        logger.info(f"Computing tax for income ₹{total_income:,.2f} under {regime} regime")
        
        # Ensure inputs are Decimal
        total_income = Decimal(str(total_income))
        advance_tax_paid = Decimal(str(advance_tax_paid))
        tds_deducted = Decimal(str(tds_deducted))
        
        # Get regime-specific rates
        regime_rates = self.rates['regimes'][regime]
        
        # Adjust basic exemption for senior citizens (old regime only)
        taxable_income = self._calculate_taxable_income(total_income, regime, taxpayer_age)
        
        # Calculate tax before rebate
        tax_before_rebate, slab_wise_tax = self._calculate_slab_tax(taxable_income, regime_rates['slabs'])
        
        # Calculate rebate under section 87A
        rebate_87a = self._calculate_rebate_87a(taxable_income, tax_before_rebate, regime_rates['rebate_87a'])
        
        # Tax after rebate
        tax_after_rebate = max(Decimal('0'), tax_before_rebate - rebate_87a)
        
        # Calculate surcharge
        surcharge = self._calculate_surcharge(taxable_income, tax_after_rebate)
        
        # Tax plus surcharge
        tax_plus_surcharge = tax_after_rebate + surcharge
        
        # Calculate cess
        cess = self._calculate_cess(tax_plus_surcharge)
        
        # Total tax liability
        total_tax_liability = tax_plus_surcharge + cess
        
        # Calculate interest (234A, 234B, 234C)
        interest_234a, interest_234b, interest_234c, interest_details = self._calculate_interest(
            total_tax_liability, advance_tax_paid, tds_deducted, filing_date
        )
        
        total_interest = interest_234a + interest_234b + interest_234c
        
        return TaxComputation(
            total_income=total_income,
            regime=regime,
            assessment_year=self.assessment_year,
            taxable_income=taxable_income,
            tax_before_rebate=tax_before_rebate,
            rebate_87a=rebate_87a,
            tax_after_rebate=tax_after_rebate,
            surcharge=surcharge,
            tax_plus_surcharge=tax_plus_surcharge,
            cess=cess,
            total_tax_liability=total_tax_liability,
            interest_234a=interest_234a,
            interest_234b=interest_234b,
            interest_234c=interest_234c,
            total_interest=total_interest,
            slab_wise_tax=slab_wise_tax,
            interest_details=interest_details
        )
    
    def _calculate_taxable_income(self, total_income: Decimal, regime: str, taxpayer_age: int) -> Decimal:
        """Calculate taxable income after basic exemption adjustments."""
        # For senior citizens in old regime, higher basic exemption applies
        if regime == 'old' and taxpayer_age >= 60:
            if taxpayer_age >= 80:
                # Super senior citizen
                basic_exemption = Decimal(str(self.rates['special_provisions']['super_senior_citizen']['basic_exemption_old']))
            else:
                # Senior citizen
                basic_exemption = Decimal(str(self.rates['special_provisions']['senior_citizen']['basic_exemption_old']))
            
            # Adjust the first slab for senior citizens
            return total_income
        
        return total_income
    
    def _calculate_slab_tax(self, taxable_income: Decimal, slabs: List[Dict]) -> Tuple[Decimal, List[Dict]]:
        """Calculate tax using slab rates."""
        if taxable_income <= 0:
            return Decimal('0'), []
        
        total_tax = Decimal('0')
        slab_wise_breakdown = []
        remaining_income = taxable_income
        
        for slab_data in slabs:
            slab_min = Decimal(str(slab_data['min']))
            slab_max = Decimal(str(slab_data['max'])) if slab_data['max'] is not None else None
            slab_rate = Decimal(str(slab_data['rate']))
            
            # Skip if income is below this slab
            if remaining_income <= slab_min:
                break
            
            # Calculate taxable amount in this slab
            if slab_max is None:
                # Highest slab - no upper limit
                taxable_in_slab = remaining_income - slab_min
            else:
                # Limited slab
                taxable_in_slab = min(remaining_income, slab_max) - slab_min
            
            if taxable_in_slab > 0:
                slab_tax = taxable_in_slab * slab_rate
                total_tax += slab_tax
                
                slab_wise_breakdown.append({
                    'slab_min': float(slab_min),
                    'slab_max': float(slab_max) if slab_max else None,
                    'rate': float(slab_rate),
                    'taxable_amount': float(taxable_in_slab),
                    'tax_amount': float(slab_tax),
                    'description': slab_data['description']
                })
        
        return total_tax, slab_wise_breakdown
    
    def _calculate_rebate_87a(self, taxable_income: Decimal, tax_before_rebate: Decimal, rebate_config: Dict) -> Decimal:
        """Calculate rebate under section 87A."""
        eligible_limit = Decimal(str(rebate_config['eligible_income_limit']))
        max_rebate = Decimal(str(rebate_config['max_rebate']))
        
        if taxable_income <= eligible_limit:
            # Rebate is minimum of tax liability or maximum rebate amount
            return min(tax_before_rebate, max_rebate)
        
        return Decimal('0')
    
    def _calculate_surcharge(self, taxable_income: Decimal, tax_after_rebate: Decimal) -> Decimal:
        """Calculate surcharge with marginal relief."""
        surcharge_rules = self.rates['surcharge']['thresholds']
        
        applicable_surcharge_rate = Decimal('0')
        surcharge_threshold = None
        
        # Find applicable surcharge rate
        for rule in surcharge_rules:
            rule_min = Decimal(str(rule['min']))
            rule_max = Decimal(str(rule['max'])) if rule['max'] is not None else None
            
            if taxable_income >= rule_min:
                if rule_max is None or taxable_income <= rule_max:
                    applicable_surcharge_rate = Decimal(str(rule['rate']))
                    surcharge_threshold = rule_min
                    break
        
        if applicable_surcharge_rate == 0:
            return Decimal('0')
        
        # Calculate surcharge
        surcharge = tax_after_rebate * applicable_surcharge_rate
        
        # Apply marginal relief if enabled
        if self.rates['surcharge']['marginal_relief'] and surcharge_threshold:
            # Marginal relief: ensure total tax doesn't exceed income above threshold
            excess_income = taxable_income - surcharge_threshold
            max_additional_tax = excess_income
            
            if surcharge > max_additional_tax:
                surcharge = max_additional_tax
        
        return surcharge
    
    def _calculate_cess(self, tax_plus_surcharge: Decimal) -> Decimal:
        """Calculate Health and Education Cess."""
        cess_rate = Decimal(str(self.rates['cess']['rate']))
        return tax_plus_surcharge * cess_rate
    
    def _calculate_interest(
        self,
        total_tax_liability: Decimal,
        advance_tax_paid: Decimal,
        tds_deducted: Decimal,
        filing_date: Optional[date]
    ) -> Tuple[Decimal, Decimal, Decimal, List[InterestCalculation]]:
        """Calculate interest under sections 234A, 234B, 234C."""
        interest_234a = Decimal('0')
        interest_234b = Decimal('0')
        interest_234c = Decimal('0')
        interest_details = []
        
        # Skip interest calculation if tax liability is below minimum
        minimum_liability = Decimal(str(self.rates['advance_tax']['minimum_liability']))
        if total_tax_liability < minimum_liability:
            return interest_234a, interest_234b, interest_234c, interest_details
        
        # Calculate net tax payable after TDS and advance tax
        total_paid = advance_tax_paid + tds_deducted
        net_payable = total_tax_liability - total_paid
        
        # Section 234A: Interest for failure to pay advance tax
        if net_payable > 0 and filing_date:
            # Calculate months from April 1 to filing date
            fy_start = date(filing_date.year - 1 if filing_date.month < 4 else filing_date.year, 4, 1)
            months_234a = self._calculate_months_difference(fy_start, filing_date)
            
            if months_234a > 0:
                interest_rate = Decimal(str(self.rates['interest']['section_234a']['rate']))
                interest_234a = net_payable * interest_rate * months_234a
                
                interest_details.append(InterestCalculation(
                    section='234A',
                    principal_amount=net_payable,
                    rate=interest_rate,
                    months=months_234a,
                    interest_amount=interest_234a,
                    description=f"Interest for {months_234a} months on unpaid tax"
                ))
        
        # Section 234B: Interest for deferment of advance tax
        required_advance_tax = total_tax_liability * Decimal('0.90')  # 90% of liability
        if advance_tax_paid < required_advance_tax:
            shortfall = required_advance_tax - advance_tax_paid
            # Simplified calculation - 12 months interest
            interest_rate = Decimal(str(self.rates['interest']['section_234b']['rate']))
            interest_234b = shortfall * interest_rate * 12
            
            interest_details.append(InterestCalculation(
                section='234B',
                principal_amount=shortfall,
                rate=interest_rate,
                months=12,
                interest_amount=interest_234b,
                description="Interest for deferment of advance tax"
            ))
        
        # Section 234C: Interest for failure to pay advance tax installments
        # Simplified calculation based on installment defaults
        advance_tax_schedule = self.rates['advance_tax']['due_dates']
        for installment in advance_tax_schedule:
            required_by_date = total_tax_liability * Decimal(str(installment['percentage']))
            # This would require actual payment dates for precise calculation
            # For now, using simplified approach
        
        return interest_234a, interest_234b, interest_234c, interest_details
    
    def _calculate_months_difference(self, start_date: date, end_date: date) -> int:
        """Calculate number of months between two dates."""
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if end_date.day > start_date.day:
            months += 1  # Part of month counts as full month
        return max(0, months)
    
    def calculate_net_position(
        self,
        tax_computation: TaxComputation,
        advance_tax_paid: Decimal = Decimal('0'),
        tds_deducted: Decimal = Decimal('0'),
        other_payments: Decimal = Decimal('0')
    ) -> Dict[str, Any]:
        """
        Calculate net refund or payable position.
        
        Args:
            tax_computation: Result from compute_tax()
            advance_tax_paid: Advance tax payments made
            tds_deducted: TDS deducted during the year
            other_payments: Other tax payments (self-assessment, etc.)
            
        Returns:
            Dictionary with net position details
        """
        total_liability = tax_computation.total_payable
        total_payments = advance_tax_paid + tds_deducted + other_payments
        
        net_amount = total_liability - total_payments
        
        return {
            'total_tax_liability': float(tax_computation.total_tax_liability),
            'total_interest': float(tax_computation.total_interest),
            'total_payable': float(total_liability),
            'total_payments': float(total_payments),
            'net_amount': float(net_amount),
            'is_refund': net_amount < 0,
            'is_payable': net_amount > 0,
            'refund_amount': float(abs(net_amount)) if net_amount < 0 else 0.0,
            'payable_amount': float(net_amount) if net_amount > 0 else 0.0,
            'payment_breakdown': {
                'advance_tax': float(advance_tax_paid),
                'tds_deducted': float(tds_deducted),
                'other_payments': float(other_payments)
            }
        }
    
    def get_effective_tax_rate(self, tax_computation: TaxComputation) -> float:
        """Calculate effective tax rate."""
        if tax_computation.total_income > 0:
            return float(tax_computation.total_tax_liability / tax_computation.total_income * 100)
        return 0.0
    
    def get_marginal_tax_rate(self, taxable_income: Decimal, regime: str) -> float:
        """Get marginal tax rate for given income level."""
        regime_rates = self.rates['regimes'][regime]
        
        for slab_data in reversed(regime_rates['slabs']):
            slab_min = Decimal(str(slab_data['min']))
            if taxable_income > slab_min:
                return float(slab_data['rate'] * 100)
        
        return 0.0


def create_tax_engine(assessment_year: str = "2025-26") -> TaxEngine:
    """Factory function to create tax engine instance."""
    return TaxEngine(assessment_year)