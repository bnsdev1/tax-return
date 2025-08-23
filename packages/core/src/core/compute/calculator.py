"""Tax calculation engine for computing totals and tax liability."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from .tax import TaxEngine, create_tax_engine
from ..rules.engine import create_default_engine, RulesEngine

logger = logging.getLogger(__name__)


@dataclass
class ComputationResult:
    """Result of tax computation process."""
    
    computed_totals: Dict[str, Any]
    tax_liability: Dict[str, Any]
    deductions_summary: Dict[str, Any]
    warnings: List[str]
    metadata: Dict[str, Any]
    rules_results: Optional[List[Dict[str, Any]]] = None


class TaxCalculator:
    """Calculates tax liability and totals from reconciled data using the comprehensive tax engine."""
    
    def __init__(self, assessment_year: str = "2025-26", regime: str = "new", enable_rules: bool = True):
        self.assessment_year = assessment_year
        self.regime = regime
        self.enable_rules = enable_rules
        self.tax_engine = create_tax_engine(assessment_year)
        
        # Standard deduction amount (₹50,000 for AY 2025-26)
        self.standard_deduction = 50000
        
        # Initialize rules engine if enabled
        self.rules_engine = None
        if enable_rules:
            try:
                self.rules_engine = create_default_engine(assessment_year)
                logger.info(f"Rules engine initialized with {len(self.rules_engine.rules)} rules")
            except Exception as e:
                logger.warning(f"Failed to initialize rules engine: {e}")
                self.rules_engine = None
        
        logger.info(f"Initialized TaxCalculator for AY {assessment_year} ({regime} regime)")
    

    
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
        
        # Calculate tax liability using the comprehensive tax engine
        tax_computation = self.tax_engine.compute_tax(
            total_income=taxable_income,
            regime=self.regime,
            advance_tax_paid=Decimal(str(reconciled_data.get('advance_tax', 0))),
            tds_deducted=Decimal(str(reconciled_data.get('tds', {}).get('total_tds', 0))),
            filing_date=None,  # Would be provided in real scenario
            taxpayer_age=35    # Default age, would be from taxpayer data
        )
        
        # Convert tax computation to legacy format
        tax_liability = {
            'base_tax': float(tax_computation.tax_before_rebate),
            'rebate_87a': float(tax_computation.rebate_87a),
            'tax_after_rebate': float(tax_computation.tax_after_rebate),
            'surcharge': float(tax_computation.surcharge),
            'cess': float(tax_computation.cess),
            'total_tax_liability': float(tax_computation.total_tax_liability),
            'interest_234a': float(tax_computation.interest_234a),
            'interest_234b': float(tax_computation.interest_234b),
            'interest_234c': float(tax_computation.interest_234c),
            'total_interest': float(tax_computation.total_interest),
            'total_payable': float(tax_computation.total_payable),
            'effective_rate': self.tax_engine.get_effective_tax_rate(tax_computation),
            'marginal_rate': self.tax_engine.get_marginal_tax_rate(taxable_income, self.regime),
            'slab_wise_breakdown': tax_computation.slab_wise_tax,
            'interest_details': [
                {
                    'section': detail.section,
                    'principal_amount': float(detail.principal_amount),
                    'rate': float(detail.rate),
                    'months': detail.months,
                    'interest_amount': float(detail.interest_amount),
                    'description': detail.description
                }
                for detail in tax_computation.interest_details
            ]
        }
        
        # Calculate net position using tax engine
        net_position = self.tax_engine.calculate_net_position(
            tax_computation,
            advance_tax_paid=Decimal(str(reconciled_data.get('advance_tax', 0))),
            tds_deducted=Decimal(str(reconciled_data.get('tds', {}).get('total_tds', 0))),
            other_payments=Decimal('0')
        )
        
        refund_or_payable = Decimal(str(net_position['net_amount']))
        
        # Prepare computed totals
        computed_totals = {
            'gross_total_income': float(gross_total_income),
            'total_deductions': float(total_deductions),
            'taxable_income': float(taxable_income),
            'tax_on_taxable_income': float(tax_liability['base_tax']),
            'total_tax_liability': float(tax_liability['total_tax_liability']),
            'total_taxes_paid': float(net_position['total_payments']),
            'refund_or_payable': float(refund_or_payable),
            'income_breakdown': {
                'salary': float(salary_income['net_salary']),
                'house_property': float(house_property_income['net_income']),
                'capital_gains': float(capital_gains_income['total_gains']),
                'other_sources': float(other_sources_income['total_income'])
            }
        }
        
        # Evaluate rules if enabled
        rules_results = None
        if self.rules_engine:
            try:
                # Prepare context for rules evaluation
                rules_context = self._prepare_rules_context(
                    computed_totals, tax_liability, deductions_summary, reconciled_data
                )
                
                # Evaluate all rules
                rule_evaluations = self.rules_engine.evaluate_all_rules(rules_context)
                
                # Convert to serializable format
                rules_results = [
                    {
                        'rule_code': result.rule_code,
                        'description': result.description,
                        'input_values': result.input_values,
                        'output_value': result.output_value,
                        'passed': result.passed,
                        'message': result.message,
                        'severity': result.severity,
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in rule_evaluations
                ]
                
                # Add rules summary to warnings if there are failures
                failed_rules = [r for r in rule_evaluations if not r.passed and r.severity == 'error']
                if failed_rules:
                    warnings.append(f"{len(failed_rules)} critical rule(s) failed validation")
                
                logger.info(f"Rules evaluation completed: {len(rule_evaluations)} rules evaluated")
                
            except Exception as e:
                logger.error(f"Rules evaluation failed: {e}")
                warnings.append("Rules evaluation failed - please review manually")
        
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
                'effective_tax_rate': tax_liability['effective_rate'],
                'marginal_tax_rate': tax_liability['marginal_rate'],
                'net_position': net_position
            },
            rules_results=rules_results
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
    
    def _prepare_rules_context(self, computed_totals: Dict[str, Any], 
                              tax_liability: Dict[str, Any], 
                              deductions_summary: Dict[str, Any],
                              reconciled_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context data for rules evaluation."""
        
        # Extract relevant data for rules evaluation
        context = {
            # Income components
            'salary_income': computed_totals['income_breakdown']['salary'],
            'business_income': 0,  # Would come from reconciled_data if available
            'total_income': computed_totals['taxable_income'],
            
            # Deductions
            'deduction_80c': deductions_summary.get('section_80c', 0),
            'deduction_80d_self': 0,  # Would be extracted from detailed deductions
            'deduction_80d_parents': 0,  # Would be extracted from detailed deductions
            'deduction_80ccd1b': 0,  # Would be extracted from detailed deductions
            'parents_senior_citizen': False,  # Would come from taxpayer data
            
            # Tax regime and calculations
            'tax_regime': self.regime,
            'tax_liability': tax_liability['total_tax_liability'],
            'rebate_87a': tax_liability['rebate_87a'],
            
            # Capital gains
            'ltcg_equity': computed_totals['income_breakdown'].get('capital_gains', 0),
            'ltcg_tax_equity': 0,  # Would be calculated separately
            'stcg_equity': 0,  # Would be calculated separately
            'stcg_tax_equity': 0,  # Would be calculated separately
            
            # House property
            'hp_interest_self_occupied': 0,  # Would come from house property data
            
            # TDS and payments
            'tds_total': reconciled_data.get('tds', {}).get('total_tds', 0),
            'advance_tax_paid': reconciled_data.get('advance_tax', 0),
            
            # Age-based flags
            'is_senior_citizen': False,  # Would come from taxpayer data
            'is_super_senior_citizen': False,  # Would come from taxpayer data
            'basic_exemption': 250000 if self.regime == 'old' else 300000,  # Basic exemption limit
        }
        
        # Add any additional context from reconciled data
        if 'house_property' in reconciled_data:
            hp_data = reconciled_data['house_property']
            context['hp_interest_self_occupied'] = hp_data.get('interest_on_loan', 0)
        
        if 'deductions' in reconciled_data:
            deductions_data = reconciled_data['deductions']
            context.update({
                'deduction_80c': deductions_data.get('section_80c', 0),
                'deduction_80d_self': deductions_data.get('section_80d_self', 0),
                'deduction_80d_parents': deductions_data.get('section_80d_parents', 0),
                'deduction_80ccd1b': deductions_data.get('section_80ccd1b', 0),
            })
        
        if 'taxpayer_info' in reconciled_data:
            taxpayer_data = reconciled_data['taxpayer_info']
            age = taxpayer_data.get('age', 35)
            context.update({
                'is_senior_citizen': age >= 60,
                'is_super_senior_citizen': age >= 80,
                'parents_senior_citizen': taxpayer_data.get('parents_senior_citizen', False)
            })
        
        return context
    
