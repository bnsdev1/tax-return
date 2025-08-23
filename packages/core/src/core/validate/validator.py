"""Tax return validation engine for compliance and business rule checks."""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, date

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    
    rule_name: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    field_path: Optional[str] = None
    suggested_fix: Optional[str] = None
    blocking: bool = False


@dataclass
class ValidationResult:
    """Result of validation process."""
    
    is_valid: bool
    issues: List[ValidationIssue]
    warnings: List[ValidationIssue]
    blockers: List[ValidationIssue]
    metadata: Dict[str, Any]


class TaxValidator:
    """Validates tax return data for compliance and business rules."""
    
    def __init__(self, assessment_year: str = "2025-26", form_type: str = "ITR2"):
        self.assessment_year = assessment_year
        self.form_type = form_type
        self._load_validation_rules()
    
    def _load_validation_rules(self):
        """Load validation rules based on form type and assessment year."""
        # PAN validation pattern
        self.pan_pattern = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
        
        # Deduction limits for 2025-26
        self.deduction_limits = {
            'section_80c': 150000,
            'section_80d': 25000,  # For individuals below 60
            'section_80d_senior': 50000,  # For senior citizens
            'section_80g': 100000,  # Varies by donation type
        }
        
        # Income thresholds
        self.income_thresholds = {
            'basic_exemption_new': 300000,
            'basic_exemption_old': 250000,
            'surcharge_threshold': 5000000,
            'high_income_threshold': 10000000,
        }
    
    def validate(self, reconciled_data: Dict[str, Any], computed_totals: Dict[str, Any]) -> ValidationResult:
        """Validate tax return data comprehensively.
        
        Args:
            reconciled_data: Reconciled data from multiple sources
            computed_totals: Computed tax totals and liability
            
        Returns:
            ValidationResult with all validation issues
        """
        logger.info("Starting comprehensive tax return validation")
        
        issues = []
        
        # Personal information validation
        issues.extend(self._validate_personal_info(reconciled_data.get('personal_info', {})))
        
        # Income validation
        issues.extend(self._validate_income(reconciled_data, computed_totals))
        
        # Deduction validation
        issues.extend(self._validate_deductions(computed_totals.get('deductions_summary', {})))
        
        # Tax computation validation
        issues.extend(self._validate_tax_computation(computed_totals))
        
        # Cross-field validation
        issues.extend(self._validate_cross_fields(reconciled_data, computed_totals))
        
        # Compliance validation
        issues.extend(self._validate_compliance(reconciled_data, computed_totals))
        
        # Categorize issues
        warnings = [issue for issue in issues if issue.severity == 'warning']
        blockers = [issue for issue in issues if issue.blocking or issue.severity == 'error']
        
        is_valid = len(blockers) == 0
        
        logger.info(f"Validation completed: {len(issues)} total issues, {len(blockers)} blockers")
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            blockers=blockers,
            metadata={
                'total_issues': len(issues),
                'warnings_count': len(warnings),
                'blockers_count': len(blockers),
                'validation_timestamp': datetime.now().isoformat(),
                'form_type': self.form_type,
                'assessment_year': self.assessment_year
            }
        )
    
    def _validate_personal_info(self, personal_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate personal information."""
        issues = []
        
        # PAN validation
        pan = personal_info.get('pan', '')
        if not pan:
            issues.append(ValidationIssue(
                rule_name='pan_required',
                severity='error',
                message='PAN number is required',
                field_path='personal_info.pan',
                blocking=True
            ))
        elif not self.pan_pattern.match(pan):
            issues.append(ValidationIssue(
                rule_name='pan_format',
                severity='error',
                message=f'Invalid PAN format: {pan}',
                field_path='personal_info.pan',
                suggested_fix='PAN should be in format ABCDE1234F',
                blocking=True
            ))
        
        # Name validation
        name = personal_info.get('name', '')
        if not name or name.strip() == '':
            issues.append(ValidationIssue(
                rule_name='name_required',
                severity='error',
                message='Name is required',
                field_path='personal_info.name',
                blocking=True
            ))
        elif len(name.strip()) < 2:
            issues.append(ValidationIssue(
                rule_name='name_length',
                severity='warning',
                message='Name appears to be too short',
                field_path='personal_info.name'
            ))
        
        # Date of birth validation
        dob = personal_info.get('date_of_birth')
        if dob:
            try:
                if isinstance(dob, str):
                    dob_date = datetime.fromisoformat(dob.replace('Z', '+00:00')).date()
                else:
                    dob_date = dob
                
                today = date.today()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                
                if age < 18:
                    issues.append(ValidationIssue(
                        rule_name='age_validation',
                        severity='warning',
                        message=f'Taxpayer appears to be {age} years old',
                        field_path='personal_info.date_of_birth'
                    ))
                elif age > 120:
                    issues.append(ValidationIssue(
                        rule_name='age_validation',
                        severity='error',
                        message=f'Invalid age: {age} years',
                        field_path='personal_info.date_of_birth'
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    rule_name='dob_format',
                    severity='warning',
                    message='Invalid date of birth format',
                    field_path='personal_info.date_of_birth'
                ))
        
        return issues
    
    def _validate_income(self, reconciled_data: Dict[str, Any], computed_totals: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate income components."""
        issues = []
        
        gross_total_income = computed_totals.get('gross_total_income', 0)
        income_breakdown = computed_totals.get('income_breakdown', {})
        
        # Check for reasonable income levels
        if gross_total_income > 50000000:  # 5 Crores
            issues.append(ValidationIssue(
                rule_name='high_income_alert',
                severity='warning',
                message=f'Very high income reported: ₹{gross_total_income:,.2f}',
                field_path='income.gross_total_income'
            ))
        
        # Salary income validation
        salary_income = income_breakdown.get('salary', 0)
        if salary_income > 0:
            # Check for reasonable salary levels
            if salary_income > 10000000:  # 1 Crore
                issues.append(ValidationIssue(
                    rule_name='high_salary_alert',
                    severity='warning',
                    message=f'Very high salary income: ₹{salary_income:,.2f}',
                    field_path='income.salary'
                ))
        
        # Capital gains validation
        capital_gains = income_breakdown.get('capital_gains', 0)
        if capital_gains > 0:
            # Check if capital gains are properly supported
            cg_data = reconciled_data.get('capital_gains', {})
            transactions = cg_data.get('transactions', [])
            
            if capital_gains > 100000 and len(transactions) == 0:
                issues.append(ValidationIssue(
                    rule_name='capital_gains_documentation',
                    severity='warning',
                    message=f'Capital gains of ₹{capital_gains:,.2f} reported without transaction details',
                    field_path='income.capital_gains',
                    suggested_fix='Provide supporting transaction details'
                ))
        
        # Interest income validation
        other_sources = income_breakdown.get('other_sources', 0)
        if other_sources > 0:
            interest_data = reconciled_data.get('interest_income', {})
            bank_details = interest_data.get('bank_wise_details', [])
            
            if other_sources > 50000 and len(bank_details) == 0:
                issues.append(ValidationIssue(
                    rule_name='interest_documentation',
                    severity='warning',
                    message=f'Interest income of ₹{other_sources:,.2f} without bank-wise details',
                    field_path='income.other_sources'
                ))
        
        return issues
    
    def _validate_deductions(self, deductions_summary: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate deduction claims."""
        issues = []
        
        # Section 80C validation
        section_80c = deductions_summary.get('section_80c', 0)
        if section_80c > self.deduction_limits['section_80c']:
            issues.append(ValidationIssue(
                rule_name='section_80c_limit',
                severity='error',
                message=f'Section 80C deduction exceeds limit: ₹{section_80c:,.2f} > ₹{self.deduction_limits["section_80c"]:,.2f}',
                field_path='deductions.section_80c',
                suggested_fix=f'Reduce Section 80C deduction to ₹{self.deduction_limits["section_80c"]:,.2f}',
                blocking=True
            ))
        elif section_80c == self.deduction_limits['section_80c']:
            issues.append(ValidationIssue(
                rule_name='section_80c_max',
                severity='info',
                message='Section 80C deduction claimed at maximum limit',
                field_path='deductions.section_80c'
            ))
        
        # Section 80D validation
        section_80d = deductions_summary.get('section_80d', 0)
        if section_80d > self.deduction_limits['section_80d']:
            issues.append(ValidationIssue(
                rule_name='section_80d_limit',
                severity='error',
                message=f'Section 80D deduction exceeds limit: ₹{section_80d:,.2f} > ₹{self.deduction_limits["section_80d"]:,.2f}',
                field_path='deductions.section_80d',
                blocking=True
            ))
        
        return issues
    
    def _validate_tax_computation(self, computed_totals: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate tax computation logic."""
        issues = []
        
        gross_income = computed_totals.get('gross_total_income', 0)
        total_deductions = computed_totals.get('total_deductions', 0)
        taxable_income = computed_totals.get('taxable_income', 0)
        tax_liability = computed_totals.get('total_tax_liability', 0)
        
        # Validate taxable income calculation
        expected_taxable = max(0, gross_income - total_deductions)
        if abs(taxable_income - expected_taxable) > 1:  # Allow ₹1 rounding difference
            issues.append(ValidationIssue(
                rule_name='taxable_income_calculation',
                severity='error',
                message=f'Taxable income calculation error: Expected ₹{expected_taxable:,.2f}, got ₹{taxable_income:,.2f}',
                field_path='computation.taxable_income',
                blocking=True
            ))
        
        # Validate tax liability reasonableness
        if taxable_income > 0 and tax_liability == 0:
            if taxable_income > self.income_thresholds['basic_exemption_new']:
                issues.append(ValidationIssue(
                    rule_name='zero_tax_high_income',
                    severity='warning',
                    message=f'Zero tax liability on taxable income of ₹{taxable_income:,.2f}',
                    field_path='computation.tax_liability'
                ))
        
        # Validate effective tax rate
        if taxable_income > 0 and tax_liability > 0:
            effective_rate = (tax_liability / taxable_income) * 100
            if effective_rate > 45:  # Maximum possible rate with surcharge and cess
                issues.append(ValidationIssue(
                    rule_name='high_tax_rate',
                    severity='error',
                    message=f'Effective tax rate too high: {effective_rate:.2f}%',
                    field_path='computation.effective_rate',
                    blocking=True
                ))
        
        return issues
    
    def _validate_cross_fields(self, reconciled_data: Dict[str, Any], computed_totals: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate relationships between different fields."""
        issues = []
        
        # TDS vs Tax Liability validation
        total_tds = reconciled_data.get('tds', {}).get('total_tds', 0)
        tax_liability = computed_totals.get('total_tax_liability', 0)
        
        if total_tds > tax_liability * 2:  # TDS more than 2x tax liability
            issues.append(ValidationIssue(
                rule_name='excessive_tds',
                severity='warning',
                message=f'TDS (₹{total_tds:,.2f}) significantly exceeds tax liability (₹{tax_liability:,.2f})',
                field_path='taxes.tds_vs_liability'
            ))
        
        # Income vs TDS consistency
        salary_income = computed_totals.get('income_breakdown', {}).get('salary', 0)
        salary_tds = reconciled_data.get('tds', {}).get('salary_tds', 0)
        
        if salary_income > 0 and salary_tds > 0:
            tds_rate = (salary_tds / salary_income) * 100
            if tds_rate > 35:  # TDS rate too high
                issues.append(ValidationIssue(
                    rule_name='high_tds_rate',
                    severity='warning',
                    message=f'High TDS rate on salary: {tds_rate:.2f}%',
                    field_path='taxes.salary_tds_rate'
                ))
        
        return issues
    
    def _validate_compliance(self, reconciled_data: Dict[str, Any], computed_totals: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate compliance requirements."""
        issues = []
        
        gross_income = computed_totals.get('gross_total_income', 0)
        
        # ITR form type validation
        if self.form_type == 'ITR1':
            # ITR1 is for salary income only
            other_income = (
                computed_totals.get('income_breakdown', {}).get('capital_gains', 0) +
                computed_totals.get('income_breakdown', {}).get('house_property', 0)
            )
            
            if other_income > 0:
                issues.append(ValidationIssue(
                    rule_name='itr1_eligibility',
                    severity='error',
                    message='ITR1 not applicable for capital gains or house property income',
                    field_path='return.form_type',
                    suggested_fix='Use ITR2 for multiple income sources',
                    blocking=True
                ))
        
        # Audit threshold check
        if gross_income > 10000000:  # 1 Crore
            issues.append(ValidationIssue(
                rule_name='audit_threshold',
                severity='info',
                message=f'Income above ₹1 Crore may require tax audit',
                field_path='compliance.audit_requirement'
            ))
        
        # Advance tax requirement
        tax_liability = computed_totals.get('total_tax_liability', 0)
        if tax_liability > 10000:  # ₹10,000 threshold
            advance_tax = reconciled_data.get('advance_tax', 0)
            if advance_tax < tax_liability * 0.9:  # Less than 90% paid as advance tax
                issues.append(ValidationIssue(
                    rule_name='advance_tax_shortfall',
                    severity='warning',
                    message=f'Advance tax may be insufficient. Paid: ₹{advance_tax:,.2f}, Required: ~₹{tax_liability * 0.9:,.2f}',
                    field_path='taxes.advance_tax'
                ))
        
        return issues