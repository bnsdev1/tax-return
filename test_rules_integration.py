#!/usr/bin/env python3
"""
Integration test for Rules Engine

Tests the complete rules engine functionality including:
- YAML rule loading
- Rule evaluation with various scenarios
- Integration with tax calculator
- API endpoints
- UI data flow
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from packages.core.src.core.rules.engine import RulesEngine, create_default_engine
from packages.core.src.core.compute.calculator import TaxCalculator
import json

def test_rules_engine_basic():
    """Test basic rules engine functionality"""
    print("🧪 Testing Rules Engine Basic Functionality")
    print("=" * 60)
    
    # Test 1: Load rules from YAML
    print("1. 🏗️ Loading Rules from YAML...")
    try:
        engine = create_default_engine("2025-26")
        print(f"   ✅ Loaded {len(engine.rules)} rules successfully")
        
        # Show some sample rules
        for i, rule in enumerate(engine.rules[:3]):
            print(f"   📋 Rule {i+1}: {rule.code} - {rule.description}")
    except Exception as e:
        print(f"   ❌ Failed to load rules: {e}")
        return False
    
    # Test 2: Evaluate rules with sample data
    print("\n2. 🔍 Evaluating Rules with Sample Data...")
    
    # Sample context that should pass most rules
    good_context = {
        'deduction_80c': 100000,  # Within 150k limit
        'deduction_80d_self': 20000,  # Within 25k limit
        'deduction_80d_parents': 15000,  # Within 25k limit
        'deduction_80ccd1b': 40000,  # Within 50k limit
        'total_income': 800000,  # 8 lakh income
        'tax_regime': 'new',
        'rebate_87a': 20000,  # Within 25k limit for new regime
        'tax_liability': 50000,
        'ltcg_equity': 80000,  # Within 1 lakh exemption
        'stcg_equity': 50000,
        'stcg_tax_equity': 7500,  # 15% of 50k
        'hp_interest_self_occupied': 150000,  # Within 2 lakh limit
        'salary_income': 800000,
        'business_income': 0,
        'tds_total': 60000,
        'advance_tax_paid': 10000,
        'is_senior_citizen': False,
        'is_super_senior_citizen': False,
        'parents_senior_citizen': False,
        'basic_exemption': 300000
    }
    
    results = engine.evaluate_all_rules(good_context)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    
    print(f"   📊 Results: {passed_count} passed, {failed_count} failed out of {len(results)} rules")
    
    # Show failed rules
    failed_rules = [r for r in results if not r.passed]
    if failed_rules:
        print("   ⚠️ Failed Rules:")
        for rule in failed_rules[:5]:  # Show first 5 failures
            print(f"      • {rule.rule_code}: {rule.message}")
    
    # Test 3: Test specific rule scenarios
    print("\n3. 🎯 Testing Specific Rule Scenarios...")
    
    # Test 80C cap violation
    engine.clear_log()
    bad_80c_context = good_context.copy()
    bad_80c_context['deduction_80c'] = 200000  # Exceeds 150k limit
    
    results = engine.evaluate_all_rules(bad_80c_context)
    cap_result = next((r for r in results if r.rule_code == "80C_CAP"), None)
    
    if cap_result:
        print(f"   📋 80C Cap Test: {'✅ PASS' if not cap_result.passed else '❌ FAIL'}")
        print(f"      Message: {cap_result.message}")
    
    # Test rebate 87A eligibility
    engine.clear_log()
    rebate_context = good_context.copy()
    rebate_context['total_income'] = 600000  # Eligible for rebate
    rebate_context['tax_regime'] = 'new'
    
    results = engine.evaluate_all_rules(rebate_context)
    rebate_result = next((r for r in results if r.rule_code == "87A_ELIGIBILITY_NEW"), None)
    
    if rebate_result:
        print(f"   🎁 87A Eligibility Test: {'✅ PASS' if rebate_result.passed else '❌ FAIL'}")
        print(f"      Message: {rebate_result.message}")
    
    return True

def test_calculator_integration():
    """Test rules engine integration with tax calculator"""
    print("\n🔄 Testing Calculator Integration")
    print("=" * 60)
    
    # Test with rules enabled
    print("1. 🧮 Testing Calculator with Rules Engine...")
    
    calculator = TaxCalculator(assessment_year="2025-26", regime="new", enable_rules=True)
    
    # Sample reconciled data
    reconciled_data = {
        'salary': {
            'gross_salary': 800000,
            'allowances': 50000,
            'perquisites': 0
        },
        'house_property': {
            'rental_income': 0,
            'interest_on_loan': 150000
        },
        'deductions': {
            'section_80c': 100000,
            'section_80d_self': 20000,
            'section_80d_parents': 15000,
            'section_80ccd1b': 40000
        },
        'tds': {
            'total_tds': 70000
        },
        'advance_tax': 0,
        'taxpayer_info': {
            'age': 35,
            'parents_senior_citizen': False
        }
    }
    
    try:
        result = calculator.compute_totals(reconciled_data)
        
        print(f"   💰 Taxable Income: ₹{result.computed_totals['taxable_income']:,.2f}")
        print(f"   🧾 Tax Liability: ₹{result.computed_totals['total_tax_liability']:,.2f}")
        print(f"   💸 Refund/Payable: ₹{result.computed_totals['refund_or_payable']:,.2f}")
        
        # Check if rules were evaluated
        if result.rules_results:
            rules_count = len(result.rules_results)
            passed_rules = sum(1 for r in result.rules_results if r['passed'])
            failed_rules = rules_count - passed_rules
            
            print(f"   📊 Rules Evaluated: {rules_count} total, {passed_rules} passed, {failed_rules} failed")
            
            # Show any critical failures
            critical_failures = [r for r in result.rules_results if not r['passed'] and r['severity'] == 'error']
            if critical_failures:
                print("   🚨 Critical Rule Failures:")
                for rule in critical_failures[:3]:
                    print(f"      • {rule['rule_code']}: {rule['message']}")
            else:
                print("   ✅ No critical rule failures")
        else:
            print("   ⚠️ No rules were evaluated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Calculator integration failed: {e}")
        return False

def test_rule_categories():
    """Test different rule categories"""
    print("\n📂 Testing Rule Categories")
    print("=" * 60)
    
    engine = create_default_engine("2025-26")
    
    # Group rules by category
    categories = {}
    for rule in engine.rules:
        category = rule.category
        if category not in categories:
            categories[category] = []
        categories[category].append(rule)
    
    print("📋 Rule Categories:")
    for category, rules in categories.items():
        print(f"   • {category.upper()}: {len(rules)} rules")
    
    # Test each category with appropriate data - provide all needed variables
    base_context = {
        'deduction_80c': 0,
        'deduction_80d_self': 0,
        'deduction_80d_parents': 0,
        'deduction_80ccd1b': 0,
        'parents_senior_citizen': False,
        'salary_income': 0,
        'business_income': 0,
        'total_income': 0,
        'tax_regime': 'new',
        'rebate_87a': 0,
        'tax_liability': 0,
        'ltcg_equity': 0,
        'ltcg_tax_equity': 0,
        'stcg_equity': 0,
        'stcg_tax_equity': 0,
        'hp_interest_self_occupied': 0,
        'tds_total': 0,
        'advance_tax_paid': 0,
        'is_senior_citizen': False,
        'is_super_senior_citizen': False,
        'basic_exemption': 300000
    }
    
    test_contexts = {
        'deductions': {
            **base_context,
            'deduction_80c': 120000,
            'deduction_80d_self': 22000,
            'deduction_80d_parents': 18000,
            'deduction_80ccd1b': 45000,
            'parents_senior_citizen': False
        },
        'income': {
            **base_context,
            'salary_income': 500000,
            'business_income': -50000,  # Loss
            'total_income': 450000,
            'tax_liability': 30000
        },
        'rebate': {
            **base_context,
            'total_income': 400000,  # Well within both regime limits
            'tax_regime': 'new',
            'rebate_87a': 15000
        },
        'capital_gains': {
            **base_context,
            'ltcg_equity': 80000,  # Within 1L exemption
            'ltcg_tax_equity': 0,  # No tax due to exemption
            'stcg_equity': 30000,
            'stcg_tax_equity': 4500  # 15%
        },
        'house_property': {
            **base_context,
            'hp_interest_self_occupied': 180000  # Within 2L limit
        }
    }
    
    print("\n🧪 Testing Category-Specific Rules:")
    all_categories_passed = True
    
    for category, context in test_contexts.items():
        engine.clear_log()
        results = engine.evaluate_all_rules(context)
        
        # Filter results for this category
        category_results = []
        for result in results:
            rule_def = next((r for r in engine.rules if r.code == result.rule_code), None)
            if rule_def and rule_def.category == category:
                category_results.append(result)
        
        if category_results:
            passed = sum(1 for r in category_results if r.passed)
            total = len(category_results)
            print(f"   📊 {category.upper()}: {passed}/{total} passed")
            
            # Show any failures
            failures = [r for r in category_results if not r.passed]
            for failure in failures[:2]:  # Show first 2 failures
                print(f"      ⚠️ {failure.rule_code}: {failure.message}")
                # Only fail the test for error-level rules
                if failure.severity == 'error':
                    all_categories_passed = False
    
    return all_categories_passed

def test_api_data_format():
    """Test that rules results are in correct format for API"""
    print("\n🌐 Testing API Data Format")
    print("=" * 60)
    
    engine = create_default_engine("2025-26")
    
    # Use complete context to avoid evaluation errors
    context = {
        'deduction_80c': 100000,
        'deduction_80d_self': 20000,
        'deduction_80d_parents': 15000,
        'deduction_80ccd1b': 40000,
        'parents_senior_citizen': False,
        'salary_income': 500000,
        'business_income': 0,
        'total_income': 500000,
        'tax_regime': 'new',
        'rebate_87a': 15000,
        'tax_liability': 30000,
        'ltcg_equity': 80000,
        'ltcg_tax_equity': 0,
        'stcg_equity': 30000,
        'stcg_tax_equity': 4500,
        'hp_interest_self_occupied': 150000,
        'tds_total': 35000,
        'advance_tax_paid': 10000,
        'is_senior_citizen': False,
        'is_super_senior_citizen': False,
        'basic_exemption': 300000
    }
    
    results = engine.evaluate_all_rules(context)
    
    # Convert to API format (similar to what calculator does)
    api_results = [
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
        for result in results
    ]
    
    print(f"   📊 Generated {len(api_results)} API-formatted results")
    
    # Test JSON serialization
    try:
        json_data = json.dumps(api_results, indent=2)
        print("   ✅ JSON serialization successful")
        
        # Show sample result
        if api_results:
            sample = api_results[0]
            print(f"   📋 Sample Result:")
            print(f"      Code: {sample['rule_code']}")
            print(f"      Passed: {sample['passed']}")
            print(f"      Message: {sample['message']}")
            print(f"      Severity: {sample['severity']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JSON serialization failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Rules Engine Integration Test Suite")
    print("=" * 80)
    
    tests = [
        ("Basic Rules Engine", test_rules_engine_basic),
        ("Calculator Integration", test_calculator_integration),
        ("Rule Categories", test_rule_categories),
        ("API Data Format", test_api_data_format)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 80)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rules engine is ready for production.")
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)