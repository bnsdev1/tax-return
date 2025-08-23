"""Tests for taxes paid reconciliation module."""

import pytest
from datetime import date
from unittest.mock import Mock, patch

from core.reconcile.taxes_paid import (
    TaxesPaidReconciler,
    TaxCredit,
    TaxesReconciliationResult
)


class TestTaxesPaidReconciler:
    """Test cases for taxes paid reconciliation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reconciler = TaxesPaidReconciler()
    
    def test_reconcile_taxes_paid_form26as_primary(self):
        """Test reconciliation with Form 26AS as primary source."""
        form26as_data = {
            "form26as_data": {
                "tds_salary": [
                    {"tan": "ABCD12345E", "deductor": "ABC Company", "amount": 85000}
                ],
                "tds_others": [
                    {"tan": "BANK12345E", "deductor": "XYZ Bank", "amount": 4500}
                ],
                "tcs": [],
                "challans": [
                    {"kind": "ADVANCE", "bsr_code": "1234567", "amount": 15000}
                ],
                "totals": {"tds_salary_total": 85000, "tds_others_total": 4500}
            },
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        ais_data = {
            "salary_details": [
                {"tds_deducted": 85000}
            ],
            "interest_details": [
                {"tds_deducted": 4500}
            ]
        }
        
        result = self.reconciler.reconcile_taxes_paid(
            form26as_data=form26as_data,
            ais_data=ais_data
        )
        
        assert isinstance(result, TaxesReconciliationResult)
        assert result.total_tds == 89500  # 85000 + 4500
        assert result.total_advance_tax == 15000
        assert len(result.credits) == 3  # TDS salary, TDS others, Advance tax
        assert len(result.warnings) == 0  # No variance
        assert result.confidence_score > 0.8
    
    def test_reconcile_taxes_paid_with_variance_warnings(self):
        """Test reconciliation with variance warnings."""
        form26as_data = {
            "form26as_data": {
                "tds_salary": [{"amount": 85000}],
                "tds_others": [{"amount": 4500}],
                "tcs": [],
                "challans": []
            },
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        # AIS data with variance
        ais_data = {
            "salary_details": [
                {"tds_deducted": 86000}  # ₹1000 variance
            ],
            "interest_details": [
                {"tds_deducted": 5500}   # ₹1000 variance
            ]
        }
        
        # Form 16 data with variance
        form16_data = {
            "tds": 84000,  # ₹1000 variance
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        result = self.reconciler.reconcile_taxes_paid(
            form26as_data=form26as_data,
            ais_data=ais_data,
            form16_data=form16_data
        )
        
        # Should have warnings for variances
        assert len(result.warnings) >= 2  # Salary and others TDS variances
        assert any("variance" in warning.lower() for warning in result.warnings)
        assert result.confidence_score < 1.0  # Reduced due to warnings
    
    def test_reconcile_taxes_paid_ais_fallback(self):
        """Test reconciliation using AIS as fallback when Form 26AS unavailable."""
        ais_data = {
            "salary_details": [
                {"tds_deducted": 85000}
            ],
            "interest_details": [
                {"tds_deducted": 4500}
            ]
        }
        
        result = self.reconciler.reconcile_taxes_paid(ais_data=ais_data)
        
        assert result.total_tds == 89500
        assert len(result.credits) == 2  # TDS salary and others from AIS
        
        # Check source attribution
        salary_credit = next(c for c in result.credits if c.category == "TDS_SALARY")
        assert salary_credit.source == "AIS"
        assert salary_credit.confidence == 1.0
    
    def test_reconcile_taxes_paid_llm_fallback_needs_confirm(self):
        """Test reconciliation with LLM fallback requiring confirmation."""
        form26as_data = {
            "form26as_data": {
                "tds_salary": [{"amount": 85000}],
                "challans": [{"kind": "ADVANCE", "amount": 15000}]
            },
            "metadata": {"parser": "llm_fallback", "confidence": 0.7}
        }
        
        result = self.reconciler.reconcile_taxes_paid(form26as_data=form26as_data)
        
        # Credits from LLM should need confirmation
        llm_credits = [c for c in result.credits if c.source == "LLM_FALLBACK"]
        assert len(llm_credits) > 0
        assert all(c.needs_confirm for c in llm_credits)
        assert result.confidence_score < 0.8  # Reduced due to LLM source
    
    def test_reconcile_salary_tds_form26as_primary(self):
        """Test salary TDS reconciliation with Form 26AS as primary."""
        form26as = {
            "tds_salary": [{"amount": 85000}],
            "source": "26AS",
            "confidence": 1.0
        }
        ais = {"salary_details": [{"tds_deducted": 85000}]}
        form16 = {"tds": 85000, "source": "FORM16", "confidence": 1.0}
        
        result = self.reconciler._reconcile_salary_tds(form26as, ais, form16)
        
        assert len(result["credits"]) == 1
        credit = result["credits"][0]
        assert credit.amount == 85000
        assert credit.source == "26AS"
        assert credit.category == "TDS_SALARY"
        assert len(result["warnings"]) == 0
    
    def test_reconcile_salary_tds_with_variance(self):
        """Test salary TDS reconciliation with variance warnings."""
        form26as = {
            "tds_salary": [{"amount": 85000}],
            "source": "26AS",
            "confidence": 1.0
        }
        ais = {"salary_details": [{"tds_deducted": 85000}]}
        form16 = {"tds": 84500, "source": "FORM16", "confidence": 1.0}  # ₹500 variance
        
        result = self.reconciler._reconcile_salary_tds(form26as, ais, form16)
        
        assert len(result["warnings"]) == 1
        assert "variance" in result["warnings"][0].lower()
        assert "₹500" in result["warnings"][0]
    
    def test_reconcile_challans_advance_tax(self):
        """Test challan reconciliation for advance tax."""
        form26as = {
            "challans": [
                {
                    "kind": "ADVANCE",
                    "bsr_code": "1234567",
                    "challan_no": "123456789",
                    "paid_on": date(2024, 6, 15),
                    "amount": 10000
                },
                {
                    "kind": "ADVANCE",
                    "bsr_code": "1234567",
                    "challan_no": "987654321",
                    "paid_on": date(2024, 9, 15),
                    "amount": 5000
                }
            ],
            "source": "26AS",
            "confidence": 1.0
        }
        
        result = self.reconciler._reconcile_challans(form26as)
        
        assert len(result["credits"]) == 1
        credit = result["credits"][0]
        assert credit.amount == 15000  # Total advance tax
        assert credit.category == "ADVANCE_TAX"
        assert credit.details["challan_count"] == 2
    
    def test_reconcile_challans_self_assessment(self):
        """Test challan reconciliation for self-assessment."""
        form26as = {
            "challans": [
                {
                    "kind": "SELF_ASSESSMENT",
                    "bsr_code": "7654321",
                    "amount": 8000
                }
            ],
            "source": "26AS",
            "confidence": 1.0
        }
        
        result = self.reconciler._reconcile_challans(form26as)
        
        assert len(result["credits"]) == 1
        credit = result["credits"][0]
        assert credit.amount == 8000
        assert credit.category == "SELF_ASSESSMENT"
    
    def test_reconcile_challans_duplicate_detection(self):
        """Test duplicate challan detection."""
        form26as = {
            "challans": [
                {
                    "kind": "ADVANCE",
                    "bsr_code": "1234567",
                    "paid_on": date(2024, 6, 15),
                    "amount": 10000
                },
                {
                    "kind": "ADVANCE",
                    "bsr_code": "1234567",  # Same BSR
                    "paid_on": date(2024, 6, 15),  # Same date
                    "amount": 10000  # Same amount - potential duplicate
                }
            ],
            "source": "26AS",
            "confidence": 1.0
        }
        
        result = self.reconciler._reconcile_challans(form26as)
        
        assert len(result["warnings"]) == 1
        assert "duplicate" in result["warnings"][0].lower()
    
    def test_calculate_totals(self):
        """Test total calculation from credits."""
        credits = [
            TaxCredit(amount=85000, source="26AS", confidence=1.0, category="TDS_SALARY", details={}),
            TaxCredit(amount=4500, source="26AS", confidence=1.0, category="TDS_OTHERS", details={}),
            TaxCredit(amount=2000, source="26AS", confidence=1.0, category="TCS", details={}),
            TaxCredit(amount=15000, source="26AS", confidence=1.0, category="ADVANCE_TAX", details={}),
            TaxCredit(amount=3000, source="26AS", confidence=1.0, category="SELF_ASSESSMENT", details={})
        ]
        
        totals = self.reconciler._calculate_totals(credits)
        
        assert totals["tds"] == 89500  # 85000 + 4500
        assert totals["tcs"] == 2000
        assert totals["advance_tax"] == 15000
        assert totals["self_assessment"] == 3000
    
    def test_calculate_confidence_score_high_confidence(self):
        """Test confidence score calculation with high-quality data."""
        credits = [
            TaxCredit(amount=85000, source="26AS", confidence=1.0, category="TDS_SALARY", details={}),
            TaxCredit(amount=15000, source="26AS", confidence=1.0, category="ADVANCE_TAX", details={})
        ]
        warnings = []
        blockers = []
        
        score = self.reconciler._calculate_confidence_score(credits, warnings, blockers)
        
        assert score == 1.0
    
    def test_calculate_confidence_score_with_penalties(self):
        """Test confidence score calculation with warnings and LLM sources."""
        credits = [
            TaxCredit(amount=85000, source="LLM_FALLBACK", confidence=0.8, category="TDS_SALARY", details={}),
            TaxCredit(amount=15000, source="26AS", confidence=1.0, category="ADVANCE_TAX", details={})
        ]
        warnings = ["Variance detected", "Low confidence"]
        blockers = []
        
        score = self.reconciler._calculate_confidence_score(credits, warnings, blockers)
        
        # Should be reduced due to warnings and LLM source
        assert score < 0.8
    
    def test_calculate_confidence_score_no_credits(self):
        """Test confidence score calculation with no credits."""
        score = self.reconciler._calculate_confidence_score([], [], [])
        assert score == 0.0
    
    def test_extract_form26as_data(self):
        """Test Form 26AS data extraction."""
        data = {
            "form26as_data": {
                "tds_salary": [{"amount": 85000}],
                "totals": {"tds_salary_total": 85000}
            },
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        extracted = self.reconciler._extract_form26as_data(data)
        
        assert extracted["source"] == "26AS"
        assert extracted["confidence"] == 1.0
        assert len(extracted["tds_salary"]) == 1
    
    def test_extract_form26as_data_llm_fallback(self):
        """Test Form 26AS data extraction from LLM fallback."""
        data = {
            "form26as_data": {"tds_salary": []},
            "metadata": {"parser": "llm_fallback", "confidence": 0.7}
        }
        
        extracted = self.reconciler._extract_form26as_data(data)
        
        assert extracted["source"] == "LLM_FALLBACK"
        assert extracted["confidence"] == 0.7
    
    def test_extract_ais_data(self):
        """Test AIS data extraction."""
        data = {
            "salary_details": [{"tds_deducted": 85000}],
            "interest_details": [{"tds_deducted": 4500}]
        }
        
        extracted = self.reconciler._extract_ais_data(data)
        
        assert extracted["source"] == "AIS"
        assert extracted["confidence"] == 1.0
        assert len(extracted["salary_details"]) == 1
    
    def test_extract_form16_data(self):
        """Test Form 16 data extraction."""
        data = {
            "tds": 85000,
            "gross_salary": 1200000,
            "employer_name": "ABC Company",
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        extracted = self.reconciler._extract_form16_data(data)
        
        assert extracted["source"] == "FORM16"
        assert extracted["confidence"] == 1.0
        assert extracted["tds"] == 85000
    
    def test_reconcile_tcs(self):
        """Test TCS reconciliation."""
        form26as = {
            "tcs": [
                {"amount": 2000, "deductor": "E-commerce Platform"}
            ],
            "source": "26AS",
            "confidence": 1.0
        }
        ais = {}
        
        result = self.reconciler._reconcile_tcs(form26as, ais)
        
        assert len(result["credits"]) == 1
        credit = result["credits"][0]
        assert credit.amount == 2000
        assert credit.category == "TCS"
        assert credit.source == "26AS"
    
    def test_reconcile_others_tds_form26as_primary(self):
        """Test non-salary TDS reconciliation with Form 26AS primary."""
        form26as = {
            "tds_others": [{"amount": 4500}],
            "source": "26AS",
            "confidence": 1.0
        }
        ais = {"interest_details": [{"tds_deducted": 4500}]}
        
        result = self.reconciler._reconcile_others_tds(form26as, ais)
        
        assert len(result["credits"]) == 1
        credit = result["credits"][0]
        assert credit.amount == 4500
        assert credit.category == "TDS_OTHERS"
        assert credit.source == "26AS"
    
    def test_reconcile_others_tds_ais_fallback(self):
        """Test non-salary TDS reconciliation with AIS fallback."""
        form26as = {"tds_others": [], "source": "26AS", "confidence": 1.0}
        ais = {"interest_details": [{"tds_deducted": 4500}]}
        
        result = self.reconciler._reconcile_others_tds(form26as, ais)
        
        assert len(result["credits"]) == 1
        credit = result["credits"][0]
        assert credit.amount == 4500
        assert credit.source == "AIS"


class TestTaxCredit:
    """Test cases for TaxCredit dataclass."""
    
    def test_tax_credit_creation(self):
        """Test TaxCredit creation."""
        credit = TaxCredit(
            amount=85000,
            source="26AS",
            confidence=1.0,
            category="TDS_SALARY",
            details={"employer": "ABC Company"},
            needs_confirm=False
        )
        
        assert credit.amount == 85000
        assert credit.source == "26AS"
        assert credit.confidence == 1.0
        assert credit.category == "TDS_SALARY"
        assert not credit.needs_confirm
    
    def test_tax_credit_defaults(self):
        """Test TaxCredit with default values."""
        credit = TaxCredit(
            amount=85000,
            source="26AS",
            confidence=1.0,
            category="TDS_SALARY",
            details={}
        )
        
        assert not credit.needs_confirm  # Default value


class TestTaxesReconciliationResult:
    """Test cases for TaxesReconciliationResult dataclass."""
    
    def test_reconciliation_result_creation(self):
        """Test reconciliation result creation."""
        credits = [
            TaxCredit(amount=85000, source="26AS", confidence=1.0, category="TDS_SALARY", details={})
        ]
        
        result = TaxesReconciliationResult(
            total_tds=85000,
            total_tcs=0,
            total_advance_tax=15000,
            total_self_assessment=0,
            credits=credits,
            warnings=["Test warning"],
            blockers=[],
            confidence_score=0.95
        )
        
        assert result.total_tds == 85000
        assert result.total_advance_tax == 15000
        assert len(result.credits) == 1
        assert len(result.warnings) == 1
        assert result.confidence_score == 0.95


class TestIntegrationScenarios:
    """Integration test scenarios for taxes paid reconciliation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reconciler = TaxesPaidReconciler()
    
    def test_complete_reconciliation_scenario(self):
        """Test complete reconciliation with all data sources."""
        # Form 26AS data (primary source)
        form26as_data = {
            "form26as_data": {
                "tds_salary": [
                    {"tan": "ABCD12345E", "deductor": "ABC Company", "amount": 85000}
                ],
                "tds_others": [
                    {"tan": "BANK12345E", "deductor": "XYZ Bank", "amount": 4500}
                ],
                "tcs": [
                    {"tan": "ECOM12345E", "deductor": "E-commerce", "amount": 2000}
                ],
                "challans": [
                    {"kind": "ADVANCE", "bsr_code": "1234567", "amount": 10000},
                    {"kind": "ADVANCE", "bsr_code": "1234567", "amount": 5000},
                    {"kind": "SELF_ASSESSMENT", "bsr_code": "7654321", "amount": 3000}
                ]
            },
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        # AIS data (cross-reference)
        ais_data = {
            "salary_details": [{"tds_deducted": 85000}],
            "interest_details": [{"tds_deducted": 4500}]
        }
        
        # Form 16 data (cross-reference)
        form16_data = {
            "tds": 85000,
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        result = self.reconciler.reconcile_taxes_paid(
            form26as_data=form26as_data,
            ais_data=ais_data,
            form16_data=form16_data
        )
        
        # Verify totals
        assert result.total_tds == 89500  # 85000 + 4500
        assert result.total_tcs == 2000
        assert result.total_advance_tax == 15000  # 10000 + 5000
        assert result.total_self_assessment == 3000
        
        # Verify credits
        assert len(result.credits) == 5  # TDS salary, TDS others, TCS, Advance, Self-assessment
        
        # Verify no warnings (perfect match)
        assert len(result.warnings) == 0
        assert len(result.blockers) == 0
        
        # High confidence score
        assert result.confidence_score >= 0.9
    
    def test_partial_data_scenario(self):
        """Test reconciliation with partial data availability."""
        # Only AIS data available
        ais_data = {
            "salary_details": [{"tds_deducted": 85000}],
            "interest_details": [{"tds_deducted": 4500}]
        }
        
        result = self.reconciler.reconcile_taxes_paid(ais_data=ais_data)
        
        assert result.total_tds == 89500
        assert result.total_advance_tax == 0  # No challan data
        assert len(result.credits) == 2  # Only TDS credits
        
        # All credits should be from AIS
        assert all(credit.source == "AIS" for credit in result.credits)
    
    def test_conflicting_data_scenario(self):
        """Test reconciliation with conflicting data from multiple sources."""
        form26as_data = {
            "form26as_data": {
                "tds_salary": [{"amount": 85000}],
                "tds_others": [{"amount": 4500}]
            },
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        # Conflicting AIS data
        ais_data = {
            "salary_details": [{"tds_deducted": 90000}],  # ₹5000 difference
            "interest_details": [{"tds_deducted": 6000}]  # ₹1500 difference
        }
        
        # Conflicting Form 16 data
        form16_data = {
            "tds": 80000,  # ₹5000 difference
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        result = self.reconciler.reconcile_taxes_paid(
            form26as_data=form26as_data,
            ais_data=ais_data,
            form16_data=form16_data
        )
        
        # Should prefer Form 26AS values
        assert result.total_tds == 89500  # Form 26AS values
        
        # Should have multiple warnings for variances
        assert len(result.warnings) >= 3  # Salary vs AIS, Salary vs Form16, Others vs AIS
        
        # Confidence should be reduced due to conflicts
        assert result.confidence_score < 0.8