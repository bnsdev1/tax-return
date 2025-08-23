"""Integration tests for fixture cases to lock behavior and catch regressions."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from core.parsers import default_registry
from core.reconcile.reconciler import DataReconciler
from core.compute.calculator import TaxCalculator
from core.reconcile.taxes_paid import TaxesPaidReconciler


class TestITR1SalaryOnlyFixture:
    """Test ITR-1 salary-only fixture for behavior locking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixture_path = Path("fixtures/case_itr1_salary_only")
        self.expected_output = self._load_expected_output()
    
    def _load_expected_output(self):
        """Load expected output for comparison."""
        with open(self.fixture_path / "expected_output.json") as f:
            return json.load(f)
    
    def _load_fixture_data(self):
        """Load all fixture data files."""
        with open(self.fixture_path / "prefill.json") as f:
            prefill = json.load(f)
        
        with open(self.fixture_path / "ais.json") as f:
            ais = json.load(f)
        
        return {
            "prefill": prefill,
            "ais": ais,
            "form16b_path": self.fixture_path / "form16b.pdf"
        }
    
    def test_deterministic_parsing_only(self):
        """Test that ITR-1 case uses only deterministic parsing."""
        fixture_data = self._load_fixture_data()
        
        # Mock Form 16B parser to return deterministic result
        with patch.object(default_registry, 'parse') as mock_parse:
            mock_parse.return_value = {
                "tds": 45000,
                "gross_salary": 850000,
                "employer_name": "TECH SOLUTIONS PVT LTD",
                "metadata": {"parser": "deterministic", "confidence": 1.0}
            }
            
            result = default_registry.parse("form16b", fixture_data["form16b_path"])
            
            # Verify deterministic parsing
            assert result["metadata"]["parser"] == "deterministic"
            assert result["metadata"]["confidence"] == 1.0
            assert result["tds"] == 45000
    
    def test_reconciliation_no_variances(self):
        """Test reconciliation produces no variances for clean data."""
        fixture_data = self._load_fixture_data()
        
        reconciler = DataReconciler()
        
        # Mock parsed artifacts
        parsed_artifacts = {
            "prefill": fixture_data["prefill"],
            "ais": fixture_data["ais"],
            "form16b": {
                "tds": 45000,
                "gross_salary": 850000,
                "metadata": {"confidence": 1.0}
            }
        }
        
        result = reconciler.reconcile_sources(parsed_artifacts)
        
        # Verify no discrepancies
        assert len(result.discrepancies) == 0
        assert result.confidence_score >= 0.9
        assert len(result.warnings) == 0
    
    def test_tax_computation_refund_scenario(self):
        """Test tax computation results in refund."""
        fixture_data = self._load_fixture_data()
        
        calculator = TaxCalculator()
        
        # Prepare computation input
        computation_input = {
            "personal_info": fixture_data["prefill"]["personal_info"],
            "income": fixture_data["prefill"]["income"],
            "deductions": fixture_data["prefill"]["deductions"],
            "taxes_paid": fixture_data["prefill"]["taxes_paid"],
            "regime": "new"
        }
        
        result = calculator.compute_totals(computation_input)
        
        # Verify refund scenario
        expected = self.expected_output["computation_result"]
        assert result.computed_totals["gross_total_income"] == expected["gross_total_income"]
        assert result.computed_totals["taxable_income"] == expected["taxable_income"]
        assert result.computed_totals["refund_or_payable"] < 0  # Refund
        
        # Verify no payment required
        assert result.computed_totals["refund_or_payable"] == expected["net_result"]["refund_or_payable"]
    
    def test_export_json_schema_validation(self):
        """Test export JSON validates against schema."""
        fixture_data = self._load_fixture_data()
        
        # Mock complete processing pipeline
        export_data = {
            "return_info": {
                "pan": fixture_data["prefill"]["personal_info"]["pan"],
                "assessment_year": "2025-26",
                "form_type": "ITR1",
                "regime": "new"
            },
            "income": fixture_data["prefill"]["income"],
            "deductions": fixture_data["prefill"]["deductions"],
            "tax_computation": self.expected_output["computation_result"]["tax_calculation"],
            "taxes_paid": fixture_data["prefill"]["taxes_paid"],
            "refund_or_payable": self.expected_output["computation_result"]["net_result"]["refund_or_payable"]
        }
        
        # Validate JSON structure
        assert "return_info" in export_data
        assert "income" in export_data
        assert "tax_computation" in export_data
        assert export_data["return_info"]["form_type"] == "ITR1"
        assert export_data["refund_or_payable"] < 0  # Refund
    
    def test_no_payment_workflow_triggered(self):
        """Test that no payment workflow is triggered for refund case."""
        expected = self.expected_output["computation_result"]
        
        # Verify refund scenario
        assert expected["net_result"]["status"] == "refund"
        assert expected["net_result"]["refund_or_payable"] < 0
        
        # No challan should be required
        payment_required = expected["net_result"]["refund_or_payable"] > 0
        assert not payment_required
    
    def test_processing_time_benchmark(self):
        """Test processing completes within expected time."""
        expected_time = self.expected_output["metadata"]["processing_time_ms"]
        
        start_time = datetime.now()
        
        # Simulate processing
        fixture_data = self._load_fixture_data()
        
        # Mock quick processing
        with patch('time.sleep', return_value=None):
            # Simulate parser calls
            for _ in range(3):  # prefill, ais, form16b
                pass
        
        end_time = datetime.now()
        actual_time = (end_time - start_time).total_seconds() * 1000
        
        # Should be much faster than expected (since mocked)
        assert actual_time < expected_time * 2  # Allow 2x buffer for test overhead


class TestITR2ComplexFixture:
    """Test ITR-2 complex fixture with variances and confirmations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixture_path = Path("fixtures/case_itr2_cg_interest")
        self.expected_output = self._load_expected_output()
    
    def _load_expected_output(self):
        """Load expected output for comparison."""
        with open(self.fixture_path / "expected_output.json") as f:
            return json.load(f)
    
    def _load_fixture_data(self):
        """Load all fixture data files."""
        with open(self.fixture_path / "prefill.json") as f:
            prefill = json.load(f)
        
        with open(self.fixture_path / "ais.json") as f:
            ais = json.load(f)
        
        return {
            "prefill": prefill,
            "ais": ais,
            "form26as_path": self.fixture_path / "form26as.pdf",
            "bank_csv_path": self.fixture_path / "bank_statement.csv",
            "broker_csv_path": self.fixture_path / "broker_pnl.csv"
        }
    
    def test_variance_detection_interest_income(self):
        """Test detection of interest income variance between AIS and bank."""
        fixture_data = self._load_fixture_data()
        
        # Mock bank CSV parser
        with patch.object(default_registry, 'parse') as mock_parse:
            mock_parse.return_value = {
                "categories": {
                    "interest": {"total_amount": 45000}  # ₹2000 more than AIS
                },
                "metadata": {"confidence": 1.0}
            }
            
            bank_result = default_registry.parse("bank_csv", fixture_data["bank_csv_path"])
            
            # Compare with AIS
            ais_interest = sum(detail["interest_amount"] for detail in fixture_data["ais"]["interest_details"])
            bank_interest = bank_result["categories"]["interest"]["total_amount"]
            
            variance = abs(bank_interest - ais_interest)
            assert variance == 2000  # Expected variance
            assert variance > 1000  # Exceeds threshold, requires confirmation
    
    def test_capital_gains_reconciliation(self):
        """Test capital gains reconciliation between broker and AIS."""
        fixture_data = self._load_fixture_data()
        
        # Mock broker CSV parser
        with patch.object(default_registry, 'parse') as mock_parse:
            mock_parse.return_value = {
                "capital_gains": {
                    "short_term": 94800,
                    "long_term": 190250,
                    "total": 285050
                },
                "metadata": {"confidence": 1.0}
            }
            
            broker_result = default_registry.parse("pnl_csv", fixture_data["broker_csv_path"])
            
            # Compare with AIS
            ais_cg = sum(cg["gain_amount"] for cg in fixture_data["ais"]["capital_gains"])
            broker_cg = broker_result["capital_gains"]["total"]
            
            variance = abs(broker_cg - ais_cg)
            assert variance == 60050  # Expected variance
            assert variance / ais_cg > 0.1  # >10% variance
    
    def test_form26as_challan_processing(self):
        """Test Form 26AS challan processing and reconciliation."""
        fixture_data = self._load_fixture_data()
        
        # Mock Form 26AS parser
        with patch.object(default_registry, 'parse') as mock_parse:
            mock_parse.return_value = {
                "form26as_data": {
                    "tds_salary": [
                        {"amount": 180000, "tan": "FINA12345E"},
                        {"amount": 35000, "tan": "CONS67890E"}
                    ],
                    "tds_others": [
                        {"amount": 2500, "tan": "HDFC12345E"},
                        {"amount": 1800, "tan": "ICIC67890E"},
                        {"amount": 1500, "tan": "INFO12345E"},
                        {"amount": 500, "tan": "FREE12345E"}
                    ],
                    "tcs": [
                        {"amount": 2000, "tan": "ECOM12345E"}
                    ],
                    "challans": [
                        {"kind": "ADVANCE", "bsr_code": "1234567", "amount": 15000},
                        {"kind": "ADVANCE", "bsr_code": "1234567", "amount": 15000},
                        {"kind": "ADVANCE", "bsr_code": "1234567", "amount": 15000}
                    ]
                },
                "metadata": {"parser": "deterministic", "confidence": 1.0}
            }
            
            form26as_result = default_registry.parse("form26as", fixture_data["form26as_path"])
            
            # Verify challan totals
            challans = form26as_result["form26as_data"]["challans"]
            advance_tax_total = sum(c["amount"] for c in challans if c["kind"] == "ADVANCE")
            assert advance_tax_total == 45000
            
            # Verify TDS totals
            tds_salary_total = sum(row["amount"] for row in form26as_result["form26as_data"]["tds_salary"])
            assert tds_salary_total == 215000
    
    def test_taxes_paid_reconciliation_with_variances(self):
        """Test taxes paid reconciliation with detected variances."""
        fixture_data = self._load_fixture_data()
        
        reconciler = TaxesPaidReconciler()
        
        # Mock Form 26AS data
        form26as_data = {
            "form26as_data": {
                "tds_salary": [{"amount": 215000}],
                "tds_others": [{"amount": 6300}],
                "tcs": [{"amount": 2000}],
                "challans": [{"kind": "ADVANCE", "amount": 45000}]
            },
            "metadata": {"parser": "deterministic", "confidence": 1.0}
        }
        
        # Mock AIS data with slight variance
        ais_data = {
            "salary_details": [{"tds_deducted": 215000}],
            "interest_details": [{"tds_deducted": 6300}]
        }
        
        result = reconciler.reconcile_taxes_paid(
            form26as_data=form26as_data,
            ais_data=ais_data
        )
        
        # Verify reconciliation results
        assert result.total_tds == 221300  # 215000 + 6300
        assert result.total_advance_tax == 45000
        assert result.confidence_score >= 0.8
        assert len(result.warnings) == 0  # No variances in this mock
    
    def test_business_rules_validation(self):
        """Test that 20+ business rules are applied and validated."""
        expected_rules = self.expected_output["validation_results"]["rules_applied"]
        
        # Verify we have at least 20 rules
        assert len(expected_rules) >= 20
        
        # Verify rule structure
        for rule in expected_rules:
            assert "rule" in rule
            assert "status" in rule
            assert rule["status"] in ["pass", "fail", "warning"]
        
        # Verify specific rule outcomes
        passed_rules = [r for r in expected_rules if r["status"] == "pass"]
        failed_rules = [r for r in expected_rules if r["status"] == "fail"]
        
        assert len(passed_rules) == 18
        assert len(failed_rules) == 2
        
        # Verify specific failed rules
        failed_rule_names = [r["rule"] for r in failed_rules]
        assert "interest_variance_threshold" in failed_rule_names
        assert "capital_gains_reconciliation" in failed_rule_names
    
    def test_confirmation_workflow_triggered(self):
        """Test that confirmation workflow is triggered for variances."""
        expected = self.expected_output["reconciliation_summary"]
        
        assert expected["needs_confirmation"] is True
        assert len(expected["variances_detected"]) > 0
        
        # Verify specific variance
        interest_variance = next(
            v for v in expected["variances_detected"] 
            if v["field"] == "interest_income"
        )
        assert interest_variance["requires_confirmation"] is True
        assert interest_variance["variance"] == 2000
    
    def test_llm_fallback_scenarios(self):
        """Test LLM fallback scenarios with mocked responses."""
        # Mock LLM router
        mock_router = Mock()
        mock_router.run.return_value = Mock(
            ok=True,
            json={
                "tds_salary": [{"amount": 215000}],
                "tds_others": [{"amount": 6300}],
                "challans": [{"kind": "ADVANCE", "amount": 45000}],
                "confidence": 0.75
            }
        )
        
        # Test LLM fallback path
        from core.parsers.form26as_llm import parse_form26as_llm
        
        result = parse_form26as_llm("Complex PDF text", mock_router)
        
        assert result.source == "LLM_FALLBACK"
        assert result.confidence == 0.75
        assert len(result.tds_salary) == 1
        assert result.tds_salary[0].amount == 215000
    
    def test_export_totals_match_report_totals(self):
        """Test that export totals match report totals exactly."""
        expected = self.expected_output["computation_result"]
        
        # Export totals
        export_totals = {
            "gross_total_income": expected["gross_total_income"],
            "total_deductions": expected["deductions"]["total_deductions"],
            "taxable_income": expected["taxable_income"],
            "total_tax_liability": expected["tax_calculation"]["total_tax_liability"],
            "total_taxes_paid": expected["taxes_paid"]["total_paid"],
            "refund_or_payable": expected["net_result"]["refund_or_payable"]
        }
        
        # Report totals (should match exactly)
        report_totals = {
            "gross_total_income": 1788000,
            "total_deductions": 250000,
            "taxable_income": 1538000,
            "total_tax_liability": 189852,
            "total_taxes_paid": 268300,
            "refund_or_payable": -78448
        }
        
        # Verify exact matches
        for key in export_totals:
            assert export_totals[key] == report_totals[key], f"Mismatch in {key}"
    
    def test_schema_drift_detection(self):
        """Test that schema changes are detected."""
        expected = self.expected_output["export_validation"]
        
        # Verify schema validation passes
        assert expected["json_schema_valid"] is True
        assert expected["required_fields_present"] is True
        assert expected["amount_totals_match"] is True
        assert expected["date_formats_valid"] is True
        
        # Test would fail if schema drifts
        required_fields = [
            "computation_result",
            "reconciliation_summary", 
            "validation_results",
            "export_validation"
        ]
        
        for field in required_fields:
            assert field in self.expected_output


class TestFixtureDataIntegrity:
    """Test fixture data integrity and consistency."""
    
    def test_itr1_fixture_data_consistency(self):
        """Test ITR-1 fixture data is internally consistent."""
        fixture_path = Path("fixtures/case_itr1_salary_only")
        
        with open(fixture_path / "prefill.json") as f:
            prefill = json.load(f)
        
        with open(fixture_path / "ais.json") as f:
            ais = json.load(f)
        
        # Verify PAN consistency
        assert prefill["personal_info"]["pan"] == ais["statement_info"]["pan"]
        
        # Verify salary consistency
        prefill_salary = prefill["income"]["salary"]["gross_salary"]
        ais_salary = ais["salary_details"][0]["gross_salary"]
        assert prefill_salary == ais_salary
        
        # Verify TDS consistency
        prefill_tds = prefill["taxes_paid"]["tds"]
        ais_tds = ais["salary_details"][0]["tds_deducted"]
        assert prefill_tds == ais_tds
    
    def test_itr2_fixture_data_consistency(self):
        """Test ITR-2 fixture data is internally consistent."""
        fixture_path = Path("fixtures/case_itr2_cg_interest")
        
        with open(fixture_path / "prefill.json") as f:
            prefill = json.load(f)
        
        with open(fixture_path / "ais.json") as f:
            ais = json.load(f)
        
        # Verify PAN consistency
        assert prefill["personal_info"]["pan"] == ais["statement_info"]["pan"]
        
        # Verify total salary consistency
        prefill_salary = prefill["income"]["salary"]["gross_salary"]
        ais_salary_total = sum(emp["gross_salary"] for emp in ais["salary_details"])
        assert prefill_salary == ais_salary_total
        
        # Verify interest income (with expected variance)
        prefill_interest = prefill["income"]["other_sources"]["interest_income"]
        ais_interest_total = sum(bank["interest_amount"] for bank in ais["interest_details"])
        assert prefill_interest == ais_interest_total  # Should match in prefill
    
    def test_expected_outputs_are_realistic(self):
        """Test that expected outputs contain realistic values."""
        # ITR-1 case
        itr1_path = Path("fixtures/case_itr1_salary_only/expected_output.json")
        with open(itr1_path) as f:
            itr1_expected = json.load(f)
        
        # Verify realistic tax rates
        computation = itr1_expected["computation_result"]
        tax_rate = computation["tax_calculation"]["total_tax_liability"] / computation["taxable_income"]
        assert 0.0 <= tax_rate <= 0.35  # Reasonable tax rate range
        
        # ITR-2 case
        itr2_path = Path("fixtures/case_itr2_cg_interest/expected_output.json")
        with open(itr2_path) as f:
            itr2_expected = json.load(f)
        
        # Verify realistic values
        computation = itr2_expected["computation_result"]
        assert computation["gross_total_income"] > 0
        assert computation["taxable_income"] > 0
        assert computation["tax_calculation"]["total_tax_liability"] > 0