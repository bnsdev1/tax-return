"""
Unit tests for the Rules Engine

Tests rule evaluation, logging, and various rule scenarios.
"""

import pytest
from decimal import Decimal
from packages.core.src.core.rules.engine import RulesEngine, RuleDefinition, RuleResult
import tempfile
import yaml
import os

class TestRulesEngine:
    """Test cases for the Rules Engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = RulesEngine()
        
        # Sample test rules
        self.test_rules = [
            RuleDefinition(
                code="TEST_80C_CAP",
                description="Test 80C cap rule",
                expression="deduction_80c <= 150000",
                severity="error",
                message_pass="80C within limit",
                message_fail="80C exceeds limit",
                category="deductions"
            ),
            RuleDefinition(
                code="TEST_INCOME_POSITIVE",
                description="Test income positive rule",
                expression="total_income >= 0",
                severity="error",
                message_pass="Income is positive",
                message_fail="Income cannot be negative",
                category="income"
            ),
            RuleDefinition(
                code="TEST_TAX_RATE",
                description="Test tax rate reasonableness",
                expression="total_income == 0 or (tax_liability / total_income) <= 0.45",
                severity="warning",
                message_pass="Tax rate reasonable",
                message_fail="Tax rate too high",
                category="tax"
            )
        ]
        
        self.engine.rules = self.test_rules
    
    def test_rule_evaluation_pass(self):
        """Test rule evaluation that passes"""
        context = {
            'deduction_80c': 100000,
            'total_income': 500000,
            'tax_liability': 50000
        }
        
        results = self.engine.evaluate_all_rules(context)
        
        assert len(results) == 3
        assert all(result.passed for result in results)
        assert len(self.engine.rules_log) == 3
    
    def test_rule_evaluation_fail(self):
        """Test rule evaluation that fails"""
        context = {
            'deduction_80c': 200000,  # Exceeds 150000 limit
            'total_income': 500000,
            'tax_liability': 50000
        }
        
        results = self.engine.evaluate_all_rules(context)
        
        assert len(results) == 3
        assert not results[0].passed  # 80C cap should fail
        assert results[1].passed     # Income positive should pass
        assert results[2].passed     # Tax rate should pass
    
    def test_rule_evaluation_negative_income(self):
        """Test rule evaluation with negative income"""
        context = {
            'deduction_80c': 100000,
            'total_income': -50000,  # Negative income
            'tax_liability': 0
        }
        
        results = self.engine.evaluate_all_rules(context)
        
        assert len(results) == 3
        assert results[0].passed     # 80C cap should pass
        assert not results[1].passed # Income positive should fail
        assert results[2].passed     # Tax rate should pass (division by zero handled)
    
    def test_expression_evaluation(self):
        """Test expression evaluation with various operators"""
        context = {'a': 10, 'b': 5, 'c': 0}
        
        # Test arithmetic
        result, inputs = self.engine.evaluate_expression("a + b", context)
        assert result == 15
        assert inputs == {'a': 10, 'b': 5}
        
        # Test comparison
        result, inputs = self.engine.evaluate_expression("a > b", context)
        assert result == True
        assert inputs == {'a': 10, 'b': 5}
        
        # Test logical
        result, inputs = self.engine.evaluate_expression("a > 0 and b > 0", context)
        assert result == True
        assert inputs == {'a': 10, 'b': 5}
        
        # Test functions
        result, inputs = self.engine.evaluate_expression("max(a, b)", context)
        assert result == 10
        assert inputs == {'a': 10, 'b': 5}
    
    def test_yaml_loading(self):
        """Test loading rules from YAML file"""
        # Create temporary YAML file
        rules_data = {
            'rules': [
                {
                    'code': 'YAML_TEST',
                    'description': 'Test rule from YAML',
                    'expression': 'value <= 1000',
                    'severity': 'error',
                    'message_pass': 'Value OK',
                    'message_fail': 'Value too high',
                    'category': 'test'
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(rules_data, f)
            temp_file = f.name
        
        try:
            engine = RulesEngine(temp_file)
            assert len(engine.rules) == 1
            assert engine.rules[0].code == 'YAML_TEST'
            assert engine.rules[0].description == 'Test rule from YAML'
        finally:
            os.unlink(temp_file)
    
    def test_rules_log_filtering(self):
        """Test filtering of rules log"""
        context = {
            'deduction_80c': 200000,  # Will fail
            'total_income': 500000,
            'tax_liability': 250000   # High tax rate - will trigger warning
        }
        
        self.engine.evaluate_all_rules(context)
        
        # Test filtering by severity
        errors = self.engine.get_rules_log(severity='error')
        warnings = self.engine.get_rules_log(severity='warning')
        
        assert len(errors) == 1  # 80C cap failure
        assert len(warnings) == 1  # High tax rate
        
        # Test filtering by pass/fail
        failed = self.engine.get_rules_log(passed=False)
        passed = self.engine.get_rules_log(passed=True)
        
        assert len(failed) == 2  # 80C cap and tax rate
        assert len(passed) == 1  # Income positive
    
    def test_rule_summary(self):
        """Test rule summary statistics"""
        context = {
            'deduction_80c': 200000,  # Will fail
            'total_income': 500000,
            'tax_liability': 250000   # High tax rate - will trigger warning
        }
        
        self.engine.evaluate_all_rules(context)
        summary = self.engine.get_rule_summary()
        
        assert summary['total_rules'] == 3
        assert summary['passed'] == 1
        assert summary['failed'] == 2
        assert summary['by_severity']['error'] == 1
        assert summary['by_severity']['warning'] == 1
    
    def test_disabled_rule(self):
        """Test that disabled rules are skipped"""
        disabled_rule = RuleDefinition(
            code="DISABLED_TEST",
            description="Disabled test rule",
            expression="False",  # Would always fail
            enabled=False,
            category="test"
        )
        
        self.engine.rules.append(disabled_rule)
        
        context = {'total_income': 500000}
        results = self.engine.evaluate_all_rules(context)
        
        # Should have 4 results (3 original + 1 disabled)
        assert len(results) == 4
        
        # Disabled rule should pass with "Rule disabled" message
        disabled_result = next(r for r in results if r.rule_code == "DISABLED_TEST")
        assert disabled_result.passed
        assert disabled_result.message == "Rule disabled"
    
    def test_section_80c_cap_rule(self):
        """Test specific 80C cap rule from YAML"""
        # Load actual rules
        try:
            self.engine.load_rules("2025-26/rules.yaml")
        except:
            pytest.skip("Rules file not found")
        
        # Test 80C within limit
        context = {'deduction_80c': 100000}
        results = self.engine.evaluate_all_rules(context)
        
        cap_result = next((r for r in results if r.rule_code == "80C_CAP"), None)
        assert cap_result is not None
        assert cap_result.passed
        
        # Clear log and test 80C exceeding limit
        self.engine.clear_log()
        context = {'deduction_80c': 200000}
        results = self.engine.evaluate_all_rules(context)
        
        cap_result = next((r for r in results if r.rule_code == "80C_CAP"), None)
        assert cap_result is not None
        assert not cap_result.passed
    
    def test_section_87a_rebate_rules(self):
        """Test 87A rebate eligibility rules"""
        try:
            self.engine.load_rules("2025-26/rules.yaml")
        except:
            pytest.skip("Rules file not found")
        
        # Test new regime eligibility
        context = {
            'total_income': 600000,
            'tax_regime': 'new',
            'rebate_87a': 20000
        }
        
        results = self.engine.evaluate_all_rules(context)
        
        # Check new regime eligibility
        eligibility_result = next((r for r in results if r.rule_code == "87A_ELIGIBILITY_NEW"), None)
        assert eligibility_result is not None
        assert eligibility_result.passed
        
        # Check rebate amount limit
        amount_result = next((r for r in results if r.rule_code == "87A_AMOUNT_NEW"), None)
        assert amount_result is not None
        assert amount_result.passed
    
    def test_house_property_interest_cap(self):
        """Test house property interest cap rule"""
        try:
            self.engine.load_rules("2025-26/rules.yaml")
        except:
            pytest.skip("Rules file not found")
        
        # Test within limit
        context = {'hp_interest_self_occupied': 150000}
        results = self.engine.evaluate_all_rules(context)
        
        hp_result = next((r for r in results if r.rule_code == "HP_INTEREST_SELF_OCCUPIED"), None)
        assert hp_result is not None
        assert hp_result.passed
        
        # Clear log and test exceeding limit
        self.engine.clear_log()
        context = {'hp_interest_self_occupied': 250000}
        results = self.engine.evaluate_all_rules(context)
        
        hp_result = next((r for r in results if r.rule_code == "HP_INTEREST_SELF_OCCUPIED"), None)
        assert hp_result is not None
        assert not hp_result.passed
    
    def test_capital_gains_rules(self):
        """Test capital gains rules (112A and 111A)"""
        try:
            self.engine.load_rules("2025-26/rules.yaml")
        except:
            pytest.skip("Rules file not found")
        
        # Test LTCG within exemption
        context = {
            'ltcg_equity': 80000,
            'ltcg_tax_equity': 0
        }
        
        results = self.engine.evaluate_all_rules(context)
        
        ltcg_result = next((r for r in results if r.rule_code == "112A_EXEMPTION"), None)
        assert ltcg_result is not None
        assert ltcg_result.passed
        
        # Test STCG tax calculation
        context = {
            'stcg_equity': 50000,
            'stcg_tax_equity': 7500  # 15% of 50000
        }
        
        self.engine.clear_log()
        results = self.engine.evaluate_all_rules(context)
        
        stcg_result = next((r for r in results if r.rule_code == "111A_TAX_RATE"), None)
        assert stcg_result is not None
        assert stcg_result.passed

if __name__ == "__main__":
    pytest.main([__file__])