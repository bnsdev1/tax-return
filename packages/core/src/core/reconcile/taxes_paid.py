"""Taxes paid reconciliation module for Form 26AS, AIS, and Form 16 data."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import date
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaxCredit:
    """Represents a tax credit with provenance information."""
    amount: int
    source: str  # "26AS", "AIS", "FORM16", "LLM_FALLBACK"
    confidence: float
    category: str  # "TDS_SALARY", "TDS_OTHERS", "TCS", "ADVANCE_TAX", "SELF_ASSESSMENT"
    details: Dict[str, Any]
    needs_confirm: bool = False


@dataclass
class TaxesReconciliationResult:
    """Result of taxes paid reconciliation."""
    total_tds: int
    total_tcs: int
    total_advance_tax: int
    total_self_assessment: int
    credits: List[TaxCredit]
    warnings: List[str]
    blockers: List[str]
    confidence_score: float


class TaxesPaidReconciler:
    """Reconciles taxes paid from Form 26AS, AIS, and Form 16 sources."""
    
    def __init__(self):
        self.salary_tds_threshold = 100  # ₹100 threshold for salary TDS variance
        self.others_tds_threshold = 500  # ₹500 threshold for non-salary TDS variance
    
    def reconcile_taxes_paid(
        self,
        form26as_data: Optional[Dict[str, Any]] = None,
        ais_data: Optional[Dict[str, Any]] = None,
        form16_data: Optional[Dict[str, Any]] = None
    ) -> TaxesReconciliationResult:
        """
        Reconcile taxes paid from multiple sources.
        
        Args:
            form26as_data: Parsed Form 26AS data
            ais_data: Parsed AIS data
            form16_data: Parsed Form 16 data
            
        Returns:
            TaxesReconciliationResult with reconciled data and warnings
        """
        logger.info("Starting taxes paid reconciliation")
        
        credits = []
        warnings = []
        blockers = []
        
        # Extract data from sources
        form26as_extract = self._extract_form26as_data(form26as_data)
        ais_extract = self._extract_ais_data(ais_data)
        form16_extract = self._extract_form16_data(form16_data)
        
        # Reconcile TDS (Salary)
        salary_tds_result = self._reconcile_salary_tds(
            form26as_extract, ais_extract, form16_extract
        )
        credits.extend(salary_tds_result['credits'])
        warnings.extend(salary_tds_result['warnings'])
        
        # Reconcile TDS (Others)
        others_tds_result = self._reconcile_others_tds(
            form26as_extract, ais_extract
        )
        credits.extend(others_tds_result['credits'])
        warnings.extend(others_tds_result['warnings'])
        
        # Reconcile TCS
        tcs_result = self._reconcile_tcs(form26as_extract, ais_extract)
        credits.extend(tcs_result['credits'])
        warnings.extend(tcs_result['warnings'])
        
        # Reconcile Advance Tax and Self-Assessment
        challan_result = self._reconcile_challans(form26as_extract)
        credits.extend(challan_result['credits'])
        warnings.extend(challan_result['warnings'])
        blockers.extend(challan_result['blockers'])
        
        # Calculate totals
        totals = self._calculate_totals(credits)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(credits, warnings, blockers)
        
        logger.info(f"Taxes paid reconciliation completed with {len(warnings)} warnings and {len(blockers)} blockers")
        
        return TaxesReconciliationResult(
            total_tds=totals['tds'],
            total_tcs=totals['tcs'],
            total_advance_tax=totals['advance_tax'],
            total_self_assessment=totals['self_assessment'],
            credits=credits,
            warnings=warnings,
            blockers=blockers,
            confidence_score=confidence_score
        )
    
    def _extract_form26as_data(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant data from Form 26AS."""
        if not data or 'form26as_data' not in data:
            return {}
        
        form26as = data['form26as_data']
        confidence = data.get('metadata', {}).get('confidence', 1.0)
        source = "26AS" if data.get('metadata', {}).get('parser') == 'deterministic' else "LLM_FALLBACK"
        
        return {
            'tds_salary': form26as.get('tds_salary', []),
            'tds_others': form26as.get('tds_others', []),
            'tcs': form26as.get('tcs', []),
            'challans': form26as.get('challans', []),
            'totals': form26as.get('totals', {}),
            'confidence': confidence,
            'source': source
        }
    
    def _extract_ais_data(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant data from AIS."""
        if not data:
            return {}
        
        return {
            'salary_details': data.get('salary_details', []),
            'interest_details': data.get('interest_details', []),
            'capital_gains': data.get('capital_gains', []),
            'confidence': 1.0,
            'source': 'AIS'
        }
    
    def _extract_form16_data(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant data from Form 16."""
        if not data:
            return {}
        
        confidence = data.get('metadata', {}).get('confidence', 1.0)
        source = "FORM16" if data.get('metadata', {}).get('parser') == 'deterministic' else "LLM_FALLBACK"
        
        return {
            'tds': data.get('tds', 0),
            'gross_salary': data.get('gross_salary', 0),
            'employer_name': data.get('employer_name', ''),
            'confidence': confidence,
            'source': source
        }
    
    def _reconcile_salary_tds(
        self,
        form26as: Dict[str, Any],
        ais: Dict[str, Any],
        form16: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconcile salary TDS from multiple sources."""
        credits = []
        warnings = []
        
        # Form 26AS salary TDS
        form26as_salary_tds = sum(row.get('amount', 0) for row in form26as.get('tds_salary', []))
        
        # AIS salary TDS
        ais_salary_tds = sum(detail.get('tds_deducted', 0) for detail in ais.get('salary_details', []))
        
        # Form 16 TDS
        form16_tds = form16.get('tds', 0)
        
        # Use Form 26AS as primary source if available
        if form26as_salary_tds > 0:
            primary_amount = form26as_salary_tds
            primary_source = form26as.get('source', '26AS')
            primary_confidence = form26as.get('confidence', 1.0)
            
            # Cross-check with Form 16
            if form16_tds > 0:
                variance = abs(form26as_salary_tds - form16_tds)
                if variance > self.salary_tds_threshold:
                    warnings.append(
                        f"Salary TDS variance: Form 26AS (₹{form26as_salary_tds:,}) vs "
                        f"Form 16 (₹{form16_tds:,}) - difference ₹{variance:,}"
                    )
            
            # Cross-check with AIS
            if ais_salary_tds > 0:
                variance = abs(form26as_salary_tds - ais_salary_tds)
                if variance > self.salary_tds_threshold:
                    warnings.append(
                        f"Salary TDS variance: Form 26AS (₹{form26as_salary_tds:,}) vs "
                        f"AIS (₹{ais_salary_tds:,}) - difference ₹{variance:,}"
                    )
        
        elif ais_salary_tds > 0:
            # Use AIS as fallback
            primary_amount = ais_salary_tds
            primary_source = 'AIS'
            primary_confidence = 1.0
            
            # Cross-check with Form 16
            if form16_tds > 0:
                variance = abs(ais_salary_tds - form16_tds)
                if variance > self.salary_tds_threshold:
                    warnings.append(
                        f"Salary TDS variance: AIS (₹{ais_salary_tds:,}) vs "
                        f"Form 16 (₹{form16_tds:,}) - difference ₹{variance:,}"
                    )
        
        elif form16_tds > 0:
            # Use Form 16 as last resort
            primary_amount = form16_tds
            primary_source = form16.get('source', 'FORM16')
            primary_confidence = form16.get('confidence', 1.0)
        
        else:
            primary_amount = 0
            primary_source = 'NONE'
            primary_confidence = 1.0
        
        # Create credit entry
        if primary_amount > 0:
            credits.append(TaxCredit(
                amount=primary_amount,
                source=primary_source,
                confidence=primary_confidence,
                category="TDS_SALARY",
                details={
                    'form26as_amount': form26as_salary_tds,
                    'ais_amount': ais_salary_tds,
                    'form16_amount': form16_tds,
                    'employer_details': form26as.get('tds_salary', [])
                },
                needs_confirm=primary_source == 'LLM_FALLBACK'
            ))
        
        return {'credits': credits, 'warnings': warnings}
    
    def _reconcile_others_tds(
        self,
        form26as: Dict[str, Any],
        ais: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconcile non-salary TDS from multiple sources."""
        credits = []
        warnings = []
        
        # Form 26AS others TDS
        form26as_others_tds = sum(row.get('amount', 0) for row in form26as.get('tds_others', []))
        
        # AIS interest TDS (primary source for non-salary TDS)
        ais_interest_tds = sum(detail.get('tds_deducted', 0) for detail in ais.get('interest_details', []))
        
        # Use Form 26AS as primary source if available
        if form26as_others_tds > 0:
            primary_amount = form26as_others_tds
            primary_source = form26as.get('source', '26AS')
            primary_confidence = form26as.get('confidence', 1.0)
            
            # Cross-check with AIS
            if ais_interest_tds > 0:
                variance = abs(form26as_others_tds - ais_interest_tds)
                if variance > self.others_tds_threshold:
                    warnings.append(
                        f"Non-salary TDS variance: Form 26AS (₹{form26as_others_tds:,}) vs "
                        f"AIS (₹{ais_interest_tds:,}) - difference ₹{variance:,}"
                    )
        
        elif ais_interest_tds > 0:
            # Use AIS as fallback
            primary_amount = ais_interest_tds
            primary_source = 'AIS'
            primary_confidence = 1.0
        
        else:
            primary_amount = 0
            primary_source = 'NONE'
            primary_confidence = 1.0
        
        # Create credit entry
        if primary_amount > 0:
            credits.append(TaxCredit(
                amount=primary_amount,
                source=primary_source,
                confidence=primary_confidence,
                category="TDS_OTHERS",
                details={
                    'form26as_amount': form26as_others_tds,
                    'ais_amount': ais_interest_tds,
                    'deductor_details': form26as.get('tds_others', [])
                },
                needs_confirm=primary_source == 'LLM_FALLBACK'
            ))
        
        return {'credits': credits, 'warnings': warnings}
    
    def _reconcile_tcs(
        self,
        form26as: Dict[str, Any],
        ais: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconcile TCS from multiple sources."""
        credits = []
        warnings = []
        
        # Form 26AS TCS
        form26as_tcs = sum(row.get('amount', 0) for row in form26as.get('tcs', []))
        
        # Create credit entry if TCS exists
        if form26as_tcs > 0:
            credits.append(TaxCredit(
                amount=form26as_tcs,
                source=form26as.get('source', '26AS'),
                confidence=form26as.get('confidence', 1.0),
                category="TCS",
                details={
                    'form26as_amount': form26as_tcs,
                    'collector_details': form26as.get('tcs', [])
                },
                needs_confirm=form26as.get('source') == 'LLM_FALLBACK'
            ))
        
        return {'credits': credits, 'warnings': warnings}
    
    def _reconcile_challans(self, form26as: Dict[str, Any]) -> Dict[str, Any]:
        """Reconcile challan payments from Form 26AS."""
        credits = []
        warnings = []
        blockers = []
        
        challans = form26as.get('challans', [])
        
        # Group challans by type
        advance_tax_challans = []
        self_assessment_challans = []
        
        for challan in challans:
            if challan.get('kind') == 'ADVANCE':
                advance_tax_challans.append(challan)
            elif challan.get('kind') == 'SELF_ASSESSMENT':
                self_assessment_challans.append(challan)
        
        # Process advance tax challans
        advance_tax_total = 0
        advance_tax_details = []
        
        for challan in advance_tax_challans:
            amount = challan.get('amount', 0)
            advance_tax_total += amount
            
            # Check for duplicates (same BSR code + date + amount)
            duplicate_key = (
                challan.get('bsr_code'),
                challan.get('paid_on'),
                amount
            )
            
            advance_tax_details.append({
                'bsr_code': challan.get('bsr_code'),
                'challan_no': challan.get('challan_no'),
                'paid_on': challan.get('paid_on'),
                'amount': amount,
                'duplicate_key': duplicate_key
            })
        
        # Check for duplicates in advance tax
        seen_keys = set()
        for detail in advance_tax_details:
            if detail['duplicate_key'] in seen_keys:
                warnings.append(
                    f"Potential duplicate advance tax challan: BSR {detail['bsr_code']}, "
                    f"Date {detail['paid_on']}, Amount ₹{detail['amount']:,}"
                )
            seen_keys.add(detail['duplicate_key'])
        
        # Create advance tax credit
        if advance_tax_total > 0:
            credits.append(TaxCredit(
                amount=advance_tax_total,
                source=form26as.get('source', '26AS'),
                confidence=form26as.get('confidence', 1.0),
                category="ADVANCE_TAX",
                details={
                    'total_amount': advance_tax_total,
                    'challan_count': len(advance_tax_challans),
                    'challans': advance_tax_details
                },
                needs_confirm=form26as.get('source') == 'LLM_FALLBACK'
            ))
        
        # Process self-assessment challans
        self_assessment_total = 0
        self_assessment_details = []
        
        for challan in self_assessment_challans:
            amount = challan.get('amount', 0)
            self_assessment_total += amount
            
            self_assessment_details.append({
                'bsr_code': challan.get('bsr_code'),
                'challan_no': challan.get('challan_no'),
                'paid_on': challan.get('paid_on'),
                'amount': amount
            })
        
        # Create self-assessment credit
        if self_assessment_total > 0:
            credits.append(TaxCredit(
                amount=self_assessment_total,
                source=form26as.get('source', '26AS'),
                confidence=form26as.get('confidence', 1.0),
                category="SELF_ASSESSMENT",
                details={
                    'total_amount': self_assessment_total,
                    'challan_count': len(self_assessment_challans),
                    'challans': self_assessment_details
                },
                needs_confirm=form26as.get('source') == 'LLM_FALLBACK'
            ))
        
        return {'credits': credits, 'warnings': warnings, 'blockers': blockers}
    
    def _calculate_totals(self, credits: List[TaxCredit]) -> Dict[str, int]:
        """Calculate total amounts by category."""
        totals = {
            'tds': 0,
            'tcs': 0,
            'advance_tax': 0,
            'self_assessment': 0
        }
        
        for credit in credits:
            if credit.category in ['TDS_SALARY', 'TDS_OTHERS']:
                totals['tds'] += credit.amount
            elif credit.category == 'TCS':
                totals['tcs'] += credit.amount
            elif credit.category == 'ADVANCE_TAX':
                totals['advance_tax'] += credit.amount
            elif credit.category == 'SELF_ASSESSMENT':
                totals['self_assessment'] += credit.amount
        
        return totals
    
    def _calculate_confidence_score(
        self,
        credits: List[TaxCredit],
        warnings: List[str],
        blockers: List[str]
    ) -> float:
        """Calculate overall confidence score for taxes paid reconciliation."""
        if not credits:
            return 0.0
        
        # Base score from credit confidences
        total_amount = sum(credit.amount for credit in credits)
        if total_amount == 0:
            return 0.0
        
        weighted_confidence = sum(
            credit.confidence * credit.amount for credit in credits
        ) / total_amount
        
        # Penalty for warnings and blockers
        warning_penalty = min(len(warnings) * 0.05, 0.2)  # Max 20% penalty
        blocker_penalty = min(len(blockers) * 0.1, 0.3)   # Max 30% penalty
        
        # Penalty for LLM fallback sources
        llm_credits = [c for c in credits if c.source == 'LLM_FALLBACK']
        llm_penalty = min(len(llm_credits) * 0.1, 0.2)    # Max 20% penalty
        
        final_confidence = max(0.0, weighted_confidence - warning_penalty - blocker_penalty - llm_penalty)
        
        return round(final_confidence, 2)