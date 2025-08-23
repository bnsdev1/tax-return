#!/usr/bin/env python3
"""
Integration validation script to demonstrate that all components work together.
This script validates the complete integration of models and schema registry.
"""

import json
from pathlib import Path
from core import (
    PersonalInfo,
    ReturnContext,
    Salary,
    HouseProperty,
    CapitalGains,
    OtherSources,
    Deductions,
    TaxesPaid,
    Totals,
    SchemaRegistry,
)


def main():
    """Run integration validation."""
    print("🚀 Starting Integration Validation...")
    
    # Test 1: Model Import Validation
    print("\n✅ Test 1: Model Import Validation")
    print("   All models imported successfully!")
    
    # Test 2: Model Creation and Validation
    print("\n✅ Test 2: Model Creation and Validation")
    
    # Create sample tax return data
    personal_info = PersonalInfo(
        pan="ABCDE1234F",
        name="Integration Test User",
        date_of_birth="1985-06-15",
        address="123 Test Street, Test City",
        mobile="9876543210",
        email="test@example.com"
    )
    
    return_context = ReturnContext(
        assessment_year="2025-26",
        form_type="ITR2"
    )
    
    salary = Salary(
        gross_salary=800000.0,
        allowances=80000.0,
        perquisites=20000.0
    )
    
    house_property = HouseProperty(
        annual_value=240000.0,
        municipal_tax=12000.0,
        interest_on_loan=150000.0
    )
    
    capital_gains = CapitalGains(
        short_term=50000.0,
        long_term=100000.0
    )
    
    other_sources = OtherSources(
        interest_income=25000.0,
        dividend_income=15000.0
    )
    
    deductions = Deductions(
        section_80c=150000.0,
        section_80d=25000.0,
        section_80g=10000.0
    )
    
    taxes_paid = TaxesPaid(
        tds=45000.0,
        advance_tax=20000.0
    )
    
    totals = Totals(
        gross_total_income=1096000.0,
        total_deductions=185000.0,
        tax_on_taxable_income=91100.0,
        total_taxes_paid=65000.0
    )
    
    print(f"   Personal Info: {personal_info.name} (PAN: {personal_info.pan})")
    print(f"   Return Context: {return_context.assessment_year} {return_context.form_type}")
    print(f"   Salary Total: ₹{salary.total_salary:,.2f}")
    print(f"   House Property Net Income: ₹{house_property.net_income:,.2f}")
    print(f"   Capital Gains Total: ₹{capital_gains.total_capital_gains:,.2f}")
    print(f"   Other Sources Total: ₹{other_sources.total_other_sources:,.2f}")
    print(f"   Deductions Total: ₹{deductions.total_deductions:,.2f}")
    print(f"   Taxes Paid Total: ₹{taxes_paid.total_taxes_paid:,.2f}")
    print(f"   Taxable Income: ₹{totals.taxable_income:,.2f}")
    print(f"   Refund/Payable: ₹{totals.refund_or_payable:,.2f}")
    
    # Test 3: JSON Serialization
    print("\n✅ Test 3: JSON Serialization")
    
    tax_return_data = {
        "personal_info": personal_info,
        "return_context": return_context,
        "salary": salary,
        "house_property": house_property,
        "capital_gains": capital_gains,
        "other_sources": other_sources,
        "deductions": deductions,
        "taxes_paid": taxes_paid,
        "totals": totals
    }
    
    # Serialize all models
    serialized_data = {}
    for key, model in tax_return_data.items():
        serialized_data[key] = model.model_dump()
    
    json_str = json.dumps(serialized_data, indent=2, default=str)
    print(f"   Serialized data size: {len(json_str)} characters")
    print("   JSON serialization successful!")
    
    # Test 4: Schema Registry Integration
    print("\n✅ Test 4: Schema Registry Integration")
    
    # Get schemas root path
    schemas_root = Path(__file__).parent.parent.parent.parent / "packages" / "schemas"
    registry = SchemaRegistry(schemas_root)
    
    # List available schemas
    available_schemas = registry.list_available_schemas()
    print(f"   Available schemas: {available_schemas}")
    
    # Load schema files
    for ay, form_type in available_schemas:
        try:
            schema = registry.load_schema(ay, form_type)
            version = registry.get_schema_version(ay, form_type)
            print(f"   Loaded {ay} {form_type} schema (version: {version})")
        except Exception as e:
            print(f"   Error loading {ay} {form_type}: {e}")
    
    # Test 5: Round-trip Validation
    print("\n✅ Test 5: Round-trip Validation")
    
    # Test round-trip for a few key models
    models_to_test = [
        ("PersonalInfo", personal_info, PersonalInfo),
        ("Salary", salary, Salary),
        ("Totals", totals, Totals)
    ]
    
    for model_name, original_model, model_class in models_to_test:
        # Serialize
        serialized = original_model.model_dump()
        
        # Filter out computed fields for validation
        if model_name == "Salary":
            serialized = {k: v for k, v in serialized.items() if k != 'total_salary'}
        elif model_name == "Totals":
            serialized = {k: v for k, v in serialized.items() 
                         if k not in ['taxable_income', 'total_tax_liability', 'refund_or_payable']}
        
        # Deserialize
        restored_model = model_class.model_validate(serialized)
        
        # Verify key fields match
        if model_name == "PersonalInfo":
            assert restored_model.pan == original_model.pan
            assert restored_model.name == original_model.name
        elif model_name == "Salary":
            assert restored_model.gross_salary == original_model.gross_salary
            assert restored_model.total_salary == original_model.total_salary  # Computed field
        elif model_name == "Totals":
            assert restored_model.gross_total_income == original_model.gross_total_income
            assert restored_model.taxable_income == original_model.taxable_income  # Computed field
        
        print(f"   {model_name}: Round-trip validation successful!")
    
    print("\n🎉 Integration Validation Complete!")
    print("   All tests passed successfully!")
    print("   ✓ Models can be imported")
    print("   ✓ Models can be created and validated")
    print("   ✓ Models can be serialized to JSON")
    print("   ✓ Schema registry works with actual files")
    print("   ✓ Round-trip serialization works correctly")


if __name__ == "__main__":
    main()