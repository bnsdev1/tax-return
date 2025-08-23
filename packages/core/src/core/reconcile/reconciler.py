"""Data reconciliation engine for cross-referencing multiple data sources."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of data reconciliation process."""
    
    reconciled_data: Dict[str, Any]
    discrepancies: List[Dict[str, Any]]
    confidence_score: float
    warnings: List[str]
    metadata: Dict[str, Any]


class DataReconciler:
    """Reconciles data from multiple sources (prefill, AIS, bank statements, etc.)."""
    
    def __init__(self):
        self.tolerance = Decimal('0.01')  # ₹0.01 tolerance for amount matching
    
    def reconcile_sources(self, parsed_artifacts: Dict[str, Any]) -> ReconciliationResult:
        """Reconcile data from multiple parsed sources.
        
        Args:
            parsed_artifacts: Dictionary of parsed artifact data by type
            
        Returns:
            ReconciliationResult with reconciled data and discrepancies
        """
        logger.info("Starting data reconciliation process")
        
        reconciled_data = {}
        discrepancies = []
        warnings = []
        
        # Extract available sources
        prefill = parsed_artifacts.get('prefill', {})
        ais = parsed_artifacts.get('ais', {})
        bank_statements = parsed_artifacts.get('bank_csv', {})
        form16b = parsed_artifacts.get('form16b', {})
        
        # Reconcile personal information
        personal_info = self._reconcile_personal_info(prefill, ais, warnings)
        reconciled_data['personal_info'] = personal_info
        
        # Reconcile salary information
        salary_result = self._reconcile_salary(prefill, ais, warnings)
        reconciled_data['salary'] = salary_result['data']
        discrepancies.extend(salary_result['discrepancies'])
        
        # Reconcile interest income
        interest_result = self._reconcile_interest_income(prefill, ais, bank_statements, warnings)
        reconciled_data['interest_income'] = interest_result['data']
        discrepancies.extend(interest_result['discrepancies'])
        
        # Reconcile TDS information
        tds_result = self._reconcile_tds(prefill, ais, form16b, warnings)
        reconciled_data['tds'] = tds_result['data']
        discrepancies.extend(tds_result['discrepancies'])
        
        # Reconcile capital gains
        capital_gains_result = self._reconcile_capital_gains(prefill, ais, warnings)
        reconciled_data['capital_gains'] = capital_gains_result['data']
        discrepancies.extend(capital_gains_result['discrepancies'])
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(discrepancies, len(parsed_artifacts))
        
        logger.info(f"Reconciliation completed with {len(discrepancies)} discrepancies")
        
        return ReconciliationResult(
            reconciled_data=reconciled_data,
            discrepancies=discrepancies,
            confidence_score=confidence_score,
            warnings=warnings,
            metadata={
                'sources_processed': list(parsed_artifacts.keys()),
                'total_discrepancies': len(discrepancies),
                'reconciliation_timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            }
        )
    
    def _reconcile_personal_info(self, prefill: Dict, ais: Dict, warnings: List[str]) -> Dict[str, Any]:
        """Reconcile personal information across sources."""
        personal_info = {}
        
        # PAN reconciliation
        prefill_pan = prefill.get('personal_info', {}).get('pan')
        ais_pan = ais.get('statement_info', {}).get('pan')
        
        if prefill_pan and ais_pan:
            if prefill_pan != ais_pan:
                warnings.append(f"PAN mismatch: Prefill ({prefill_pan}) vs AIS ({ais_pan})")
                personal_info['pan'] = prefill_pan  # Prefer prefill
            else:
                personal_info['pan'] = prefill_pan
        else:
            personal_info['pan'] = prefill_pan or ais_pan
        
        # Name reconciliation
        prefill_name = prefill.get('personal_info', {}).get('name')
        personal_info['name'] = prefill_name or "Unknown"
        
        # Other personal details from prefill
        personal_info.update({
            'date_of_birth': prefill.get('personal_info', {}).get('date_of_birth'),
            'address': prefill.get('personal_info', {}).get('address'),
            'mobile': prefill.get('personal_info', {}).get('mobile'),
            'email': prefill.get('personal_info', {}).get('email'),
        })
        
        return personal_info
    
    def _reconcile_salary(self, prefill: Dict, ais: Dict, warnings: List[str]) -> Dict[str, Any]:
        """Reconcile salary information."""
        result = {'data': {}, 'discrepancies': []}
        
        # Extract salary data
        prefill_salary = prefill.get('income', {}).get('salary', {})
        ais_salary_details = ais.get('salary_details', [])
        
        # Get amounts
        prefill_gross = Decimal(str(prefill_salary.get('gross_salary', 0)))
        ais_total_salary = sum(Decimal(str(detail.get('gross_salary', 0))) for detail in ais_salary_details)
        
        # Reconcile gross salary
        if prefill_gross > 0 and ais_total_salary > 0:
            difference = abs(prefill_gross - ais_total_salary)
            if difference > self.tolerance:
                result['discrepancies'].append({
                    'field': 'gross_salary',
                    'prefill_value': float(prefill_gross),
                    'ais_value': float(ais_total_salary),
                    'difference': float(difference),
                    'severity': 'high' if difference > 10000 else 'medium'
                })
                warnings.append(f"Salary discrepancy: ₹{difference} difference between sources")
        
        # Use higher value or prefill if available
        reconciled_gross = max(prefill_gross, ais_total_salary) if both_exist(prefill_gross, ais_total_salary) else (prefill_gross or ais_total_salary)
        
        result['data'] = {
            'gross_salary': float(reconciled_gross),
            'allowances': prefill_salary.get('allowances', 0),
            'perquisites': prefill_salary.get('perquisites', 0),
            'employer_details': ais_salary_details[:3] if ais_salary_details else []  # Top 3 employers
        }
        
        return result
    
    def _reconcile_interest_income(self, prefill: Dict, ais: Dict, bank_statements: Dict, warnings: List[str]) -> Dict[str, Any]:
        """Reconcile interest income from multiple sources."""
        result = {'data': {}, 'discrepancies': []}
        
        # Extract interest data
        prefill_interest = Decimal(str(prefill.get('income', {}).get('other_sources', {}).get('interest_income', 0)))
        ais_interest_details = ais.get('interest_details', [])
        ais_total_interest = sum(Decimal(str(detail.get('interest_amount', 0))) for detail in ais_interest_details)
        
        # Bank statement interest (from categories)
        bank_interest = Decimal('0')
        if bank_statements:
            interest_category = bank_statements.get('categories', {}).get('interest', {})
            bank_interest = Decimal(str(interest_category.get('total_amount', 0)))
        
        # Find the best estimate
        sources = [
            ('prefill', prefill_interest),
            ('ais', ais_total_interest),
            ('bank', bank_interest)
        ]
        
        # Use AIS as primary source if available, otherwise prefill
        reconciled_interest = ais_total_interest if ais_total_interest > 0 else prefill_interest
        
        # Check for significant discrepancies
        for source_name, amount in sources:
            if amount > 0 and reconciled_interest > 0:
                difference = abs(amount - reconciled_interest)
                if difference > self.tolerance and difference > reconciled_interest * Decimal('0.1'):  # 10% threshold
                    result['discrepancies'].append({
                        'field': 'interest_income',
                        'source': source_name,
                        'value': float(amount),
                        'reconciled_value': float(reconciled_interest),
                        'difference': float(difference),
                        'severity': 'medium'
                    })
        
        result['data'] = {
            'total_interest': float(reconciled_interest),
            'bank_wise_details': ais_interest_details,
            'bank_statement_interest': float(bank_interest)
        }
        
        return result
    
    def _reconcile_tds(self, prefill: Dict, ais: Dict, form16b: Dict, warnings: List[str]) -> Dict[str, Any]:
        """Reconcile TDS information."""
        result = {'data': {}, 'discrepancies': []}
        
        # Extract TDS data
        prefill_tds = Decimal(str(prefill.get('taxes_paid', {}).get('tds', 0)))
        
        # AIS TDS (salary + interest)
        ais_salary_tds = sum(Decimal(str(detail.get('tds_deducted', 0))) for detail in ais.get('salary_details', []))
        ais_interest_tds = sum(Decimal(str(detail.get('tds_deducted', 0))) for detail in ais.get('interest_details', []))
        ais_total_tds = ais_salary_tds + ais_interest_tds
        
        # Form 16B TDS
        form16b_tds = Decimal(str(form16b.get('payment_details', {}).get('tds_amount', 0)))
        
        # Reconcile total TDS
        total_tds_sources = ais_total_tds + form16b_tds
        
        if prefill_tds > 0 and total_tds_sources > 0:
            difference = abs(prefill_tds - total_tds_sources)
            if difference > self.tolerance:
                result['discrepancies'].append({
                    'field': 'total_tds',
                    'prefill_value': float(prefill_tds),
                    'calculated_value': float(total_tds_sources),
                    'difference': float(difference),
                    'severity': 'high' if difference > 5000 else 'medium'
                })
        
        reconciled_tds = max(prefill_tds, total_tds_sources) if both_exist(prefill_tds, total_tds_sources) else (prefill_tds or total_tds_sources)
        
        result['data'] = {
            'total_tds': float(reconciled_tds),
            'salary_tds': float(ais_salary_tds),
            'interest_tds': float(ais_interest_tds),
            'property_tds': float(form16b_tds),
            'breakdown': {
                'salary': float(ais_salary_tds),
                'interest': float(ais_interest_tds),
                'property': float(form16b_tds)
            }
        }
        
        return result
    
    def _reconcile_capital_gains(self, prefill: Dict, ais: Dict, warnings: List[str]) -> Dict[str, Any]:
        """Reconcile capital gains information."""
        result = {'data': {}, 'discrepancies': []}
        
        # Extract capital gains data
        prefill_cg = prefill.get('income', {}).get('capital_gains', {})
        prefill_short_term = Decimal(str(prefill_cg.get('short_term', 0)))
        prefill_long_term = Decimal(str(prefill_cg.get('long_term', 0)))
        
        # AIS capital gains
        ais_cg_details = ais.get('capital_gains', [])
        ais_short_term = sum(Decimal(str(cg.get('amount', 0))) for cg in ais_cg_details if cg.get('gain_type') == 'short_term')
        ais_long_term = sum(Decimal(str(cg.get('amount', 0))) for cg in ais_cg_details if cg.get('gain_type') == 'long_term')
        
        # Reconcile short-term capital gains
        if prefill_short_term > 0 and ais_short_term > 0:
            difference = abs(prefill_short_term - ais_short_term)
            if difference > self.tolerance:
                result['discrepancies'].append({
                    'field': 'short_term_capital_gains',
                    'prefill_value': float(prefill_short_term),
                    'ais_value': float(ais_short_term),
                    'difference': float(difference),
                    'severity': 'medium'
                })
        
        # Reconcile long-term capital gains
        if prefill_long_term > 0 and ais_long_term > 0:
            difference = abs(prefill_long_term - ais_long_term)
            if difference > self.tolerance:
                result['discrepancies'].append({
                    'field': 'long_term_capital_gains',
                    'prefill_value': float(prefill_long_term),
                    'ais_value': float(ais_long_term),
                    'difference': float(difference),
                    'severity': 'medium'
                })
        
        result['data'] = {
            'short_term': float(max(prefill_short_term, ais_short_term)),
            'long_term': float(max(prefill_long_term, ais_long_term)),
            'transactions': ais_cg_details[:5]  # Top 5 transactions
        }
        
        return result
    
    def _calculate_confidence_score(self, discrepancies: List[Dict], num_sources: int) -> float:
        """Calculate confidence score based on discrepancies and data availability."""
        if num_sources == 0:
            return 0.0
        
        # Base score
        base_score = 0.8
        
        # Penalty for discrepancies
        high_severity_count = sum(1 for d in discrepancies if d.get('severity') == 'high')
        medium_severity_count = sum(1 for d in discrepancies if d.get('severity') == 'medium')
        
        penalty = (high_severity_count * 0.2) + (medium_severity_count * 0.1)
        
        # Bonus for multiple sources
        source_bonus = min(0.1 * (num_sources - 1), 0.2)
        
        confidence = max(0.0, min(1.0, base_score - penalty + source_bonus))
        return round(confidence, 2)


def both_exist(val1, val2) -> bool:
    """Check if both values exist and are greater than 0."""
    return val1 > 0 and val2 > 0