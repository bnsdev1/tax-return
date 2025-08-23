"""Tax calculation engine for computing totals and tax liability."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


@dataclass
class ComputationResult:
    """Result of tax computation process."""
    
    computed_totals: Dict[str, Any]
    tax_liability: Dict[str, Any]
    deductions_summary: Dict[str, Any]
    warnings: List[str]
    metadata: Dict[str, Any]


class TaxCalculator:
    """Calculates tax liability and totals from reconciled data."""
    
    def __init__(self, assessment_year: str = "2025-26", regime: str = "new"):
        self.assessment_year = assessment_year
        self.regime = regime
        self._load_tax_slabs()
    
    def _load_tax_slabs(self):
        """Load tax slabs based on assessment year and regime."""
        if self.regime == "new":
            # New tax regime slabs for 2025-26
            self.tax_slabs = [
                (300000, 0.0),    # Up to 3L - 0%
                (700000, 0.05),   # 3L to 7L - 5%
                (1000000, 0.10),  # 7L to 10L - 10%
                (1200000, 0.15),  # 10L to 12L - 15%
                (1500000, 0.20),  # 12L to 15L - 20%
                (float('inf'), 0.30)  # Above 15L - 30%
            ]
            self.standard_deduction = 75000  # New regime standard deduction
        else:
            # Old tax regime slabs
            self.tax_slabs = [
                (250000, 0.0),    # Up to 2.5L - 0%
                (500000, 0.05),   # 2.5L to 5L - 5%
                (1000000, 0.20),  # 5L to 10L - 20%
                (float('inf'), 0.30)  # Above 10L - 30%
            ]
            self.standard_deduction = 50000  # Old regime standard deduction
        
        # Common parameters
        self.cess_rate = 0.04  # 4% Health and Education Cess
        self.surcharge_threshold = 5000000  # 50L for surcharge
        self.surcharge_rate = 0.10  # 10% surcharge above 50L
    
    def compute_totals(self, reconciled_data: Dict[str, Any]) -> ComputationResult:
        """Compute tax totals and liability from reconciled data.
        
        Args:
            reconciled_data: Reconciled data from multiple sources
            
        Returns:
            ComputationResult with computed totals and tax liability
        """
        logger.info(f"Starting tax computation for {self.assessment_year} ({self.regime} regime)")
        
        warnings = []
        
        # Extract income components
        salary_income = self._compute_salary_income(reconciled_data, warnings)
        house_property_income = self._compute_house_property_income(reconciled_data, warnings)
        capital_gains_income = self._compute_capital_gains_income(reconciled_data, warnings)
        other_sources_income = self._compute_other_sources_income(reconciled_data, warnings)
        
        # Calculate gross total income (convert to Decimal for precision)
        gross_total_income = Decimal(str(
            salary_income['net_salary'] +
            house_property_income['net_income'] +
            capital_gains_income['total_gains'] +
            other_sources_income['total_income']
        ))
        
        # Compute deductions
        deductions_summary = self._compute_deductions(reconciled_data, warnings)
        total_deductions = Decimal(str(deductions_summary['total_deductions']))
        
        # Calculate taxable income
        taxable_income = max(Decimal('0'), gross_total_income - total_deductions)
        
        # Calculate tax liability
        tax_liability = self._calculate_tax_liability(taxable_income, warnings)
        
        # Compute refund/payable
        taxes_paid = Decimal(str(reconciled_data.get('tds', {}).get('total_tds', 0)))
        advance_tax = Decimal(str(reconciled_data.get('advance_tax', 0)))  # From prefill or other sources
        total_taxes_paid = taxes_paid + advance_tax
        
        refund_or_payable = Decimal(str(tax_liability['total_tax_liability'])) - total_taxes_paid
        
        # Prepare computed totals
        computed_totals = {
            'gross_total_income': float(gross_total_income),
            'total_deductions': float(total_deductions),
            'taxable_income': float(taxable_income),
            'tax_on_taxable_income': float(tax_liability['base_tax']),
            'total_tax_liability': float(tax_liability['total_tax_liability']),
            'total_taxes_paid': float(total_taxes_paid),
            'refund_or_payable': float(refund_or_payable),
            'income_breakdown': {
                'salary': float(salary_income['net_salary']),
                'house_property': float(house_property_income['net_income']),
                'capital_gains': float(capital_gains_income['total_gains']),
                'other_sources': float(other_sources_income['total_income'])
            }
        }
        
        logger.info(f"Tax computation completed. Taxable income: ₹{taxable_income:,.2f}")
        
        return ComputationResult(
            computed_totals=computed_totals,
            tax_liability=tax_liability,
            deductions_summary=deductions_summary,
            warnings=warnings,
            metadata={
                'assessment_year': self.assessment_year,
                'tax_regime': self.regime,
                'computation_timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'effective_tax_rate': float(Decimal(str(tax_liability['total_tax_liability'])) / taxable_income * 100) if taxable_income > 0 else 0.0
            }
        )
    
    def _compute_salary_income(self, data: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """Compute net salary income after standard deduction."""
        salary_data = data.get('salary', {})
        gross_salary = Decimal(str(salary_data.get('gross_salary', 0)))
        allowances = Decimal(str(salary_data.get('allowances', 0)))
        perquisites = Decimal(str(salary_data.get('perquisites', 0)))
        
        total_salary = gross_salary + allowances + perquisites
        
        # Apply standard deduction
        standard_deduction = min(Decimal(str(self.standard_deduction)), total_salary)
        net_salary = max(0, total_salary - standard_deduction)
        
        if total_salary > 0 and net_salary == 0:
            warnings.append("Salary income fully offset by standard deduction")
        
        return {
            'gross_salary': float(gross_salary),
            'allowances': float(allowances),
            'perquisites': float(perquisites),
            'total_salary': float(total_salary),
            'standard_deduction': float(standard_deduction),
            'net_salary': float(net_salary)
        }
    
    def _compute_house_property_income(self, data: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """Compute house property income."""
        # For now, return zero as house property data is not in reconciled format
        # In a real implementation, this would process house property details
        return {
            'annual_value': 0.0,
            'municipal_tax': 0.0,
            'standard_deduction': 0.0,
            'interest_on_loan': 0.0,
            'net_income': 0.0
        }
    
    def _compute_capital_gains_income(self, data: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """Compute capital gains income."""
        cg_data = data.get('capital_gains', {})
        short_term = Decimal(str(cg_data.get('short_term', 0)))
        long_term = Decimal(str(cg_data.get('long_term', 0)))
        
        # Apply exemptions and deductions (simplified)
        # In reality, this would be more complex with indexation, exemptions, etc.
        total_gains = short_term + long_term
        
        if total_gains > 100000:  # Threshold for reporting
            warnings.append(f"Significant capital gains of ₹{total_gains:,.2f} reported")
        
        return {
            'short_term': float(short_term),
            'long_term': float(long_term),
            'total_gains': float(total_gains)
        }
    
    def _compute_other_sources_income(self, data: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """Compute income from other sources."""
        interest_data = data.get('interest_income', {})
        total_interest = Decimal(str(interest_data.get('total_interest', 0)))
        
        # Apply exemptions (e.g., ₹10,000 for savings account interest in old regime)
        exemption = Decimal('10000') if self.regime == 'old' else Decimal('0')
        taxable_interest = max(0, total_interest - exemption)
        
        if total_interest > exemption and exemption > 0:
            warnings.append(f"Interest exemption of ₹{exemption} applied")
        
        return {
            'interest_income': float(total_interest),
            'exemption_applied': float(exemption),
            'taxable_interest': float(taxable_interest),
            'total_income': float(taxable_interest)
        }
    
    def _compute_deductions(self, data: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """Compute total deductions based on regime."""
        if self.regime == 'new':
            # New regime has limited deductions
            return {
                'section_80c': 0.0,
                'section_80d': 0.0,
                'section_80g': 0.0,
                'other_deductions': 0.0,
                'total_deductions': 0.0,
                'regime_note': 'New tax regime - most deductions not available'
            }
        else:
            # Old regime deductions (from prefill or other sources)
            # This would typically come from reconciled data
            section_80c = min(150000, 0)  # Placeholder - would come from data
            section_80d = min(25000, 0)   # Placeholder - would come from data
            section_80g = 0               # Placeholder - would come from data
            
            total_deductions = section_80c + section_80d + section_80g
            
            return {
                'section_80c': float(section_80c),
                'section_80d': float(section_80d),
                'section_80g': float(section_80g),
                'other_deductions': 0.0,
                'total_deductions': float(total_deductions)
            }
    
    def _calculate_tax_liability(self, taxable_income: Decimal, warnings: List[str]) -> Dict[str, Any]:
        """Calculate tax liability based on tax slabs."""
        if taxable_income <= 0:
            return {
                'base_tax': 0.0,
                'surcharge': 0.0,
                'cess': 0.0,
                'total_tax_liability': 0.0,
                'effective_rate': 0.0,
                'marginal_rate': 0.0
            }
        
        # Ensure taxable_income is Decimal
        taxable_income = Decimal(str(taxable_income))
        
        # Calculate base tax using slabs
        base_tax = Decimal('0')
        remaining_income = taxable_income
        previous_limit = Decimal('0')
        marginal_rate = 0.0
        
        for limit, rate in self.tax_slabs:
            if remaining_income <= 0:
                break
            
            limit_decimal = Decimal(str(limit))
            taxable_in_slab = min(remaining_income, limit_decimal - previous_limit)
            slab_tax = taxable_in_slab * Decimal(str(rate))
            base_tax += slab_tax
            
            if taxable_in_slab > 0:
                marginal_rate = rate
            
            remaining_income -= taxable_in_slab
            previous_limit = limit_decimal
        
        # Calculate surcharge
        surcharge = Decimal('0')
        if taxable_income > self.surcharge_threshold:
            surcharge = base_tax * Decimal(str(self.surcharge_rate))
            warnings.append(f"Surcharge of {self.surcharge_rate*100}% applied on income above ₹{self.surcharge_threshold:,}")
        
        # Calculate cess
        cess = (base_tax + surcharge) * Decimal(str(self.cess_rate))
        
        # Total tax liability
        total_tax_liability = base_tax + surcharge + cess
        
        # Effective tax rate
        effective_rate = float(total_tax_liability / taxable_income * 100) if taxable_income > 0 else 0.0
        
        return {
            'base_tax': float(base_tax),
            'surcharge': float(surcharge),
            'cess': float(cess),
            'total_tax_liability': float(total_tax_liability),
            'effective_rate': round(effective_rate, 2),
            'marginal_rate': marginal_rate * 100,
            'tax_breakdown': {
                'base_tax': float(base_tax),
                'surcharge': float(surcharge),
                'cess': float(cess)
            }
        }