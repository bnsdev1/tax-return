#!/usr/bin/env python3
"""Integration test for Form 26AS parsing system."""

import sys
from pathlib import Path

# Add packages to path
sys.path.append(str(Path(__file__).parent / "packages" / "core" / "src"))
sys.path.append(str(Path(__file__).parent / "packages" / "llm"))

from core.parsers.form26as import Form26ASParser, TDSRow, ChallanRow, Form26ASExtract
from core.reconcile.taxes_paid import TaxesPaidReconciler
import json


def test_form26as_parsing_workflow():
    """Test the complete Form 26AS parsing and reconciliation workflow."""
    
    print("🔍 Testing Form 26AS Parsing System")
    print("=" * 50)
    
    # 1. Test parser creation
    parser = Form26ASParser()
    print(f"✅ Created Form 26AS parser: {parser.name}")
    print(f"   Supported kinds: {parser.supported_kinds}")
    print(f"   Supported extensions: {parser.supported_extensions}")
    
    # 2. Test data models
    print("\n📋 Testing Data Models")
    
    # Test TDS row
    tds_row = TDSRow(
        tan="ABCD12345E",
        deductor="ABC Company Ltd",
        section="192",
        amount="₹85,000"  # Test amount parsing
    )
    print(f"✅ TDS Row: {tds_row.deductor} - ₹{tds_row.amount:,}")
    
    # Test Challan row
    challan_row = ChallanRow(
        kind="ADVANCE",
        bsr_code="1234567",
        challan_no="123456789",
        amount="₹15,000"
    )
    print(f"✅ Challan Row: {challan_row.kind} - ₹{challan_row.amount:,}")
    
    # 3. Test Form 26AS extract
    print("\n📄 Testing Form 26AS Extract")
    
    extract = Form26ASExtract(
        tds_salary=[
            TDSRow(tan="ABCD12345E", deductor="ABC Company", amount=85000),
            TDSRow(tan="EFGH67890I", deductor="XYZ Corp", amount=45000)
        ],
        tds_others=[
            TDSRow(tan="BANK12345E", deductor="State Bank", section="194A", amount=4500)
        ],
        tcs=[
            TDSRow(tan="ECOM12345E", deductor="E-commerce Platform", amount=2000)
        ],
        challans=[
            ChallanRow(kind="ADVANCE", bsr_code="1234567", amount=10000),
            ChallanRow(kind="ADVANCE", bsr_code="1234567", amount=5000),
            ChallanRow(kind="SELF_ASSESSMENT", bsr_code="7654321", amount=3000)
        ],
        totals={
            "tds_salary_total": 130000,
            "tds_others_total": 4500,
            "tcs_total": 2000,
            "advance_tax_total": 15000,
            "self_assessment_total": 3000
        }
    )
    
    print(f"✅ Form 26AS Extract created with:")
    print(f"   - TDS Salary entries: {len(extract.tds_salary)}")
    print(f"   - TDS Others entries: {len(extract.tds_others)}")
    print(f"   - TCS entries: {len(extract.tcs)}")
    print(f"   - Challan entries: {len(extract.challans)}")
    print(f"   - Confidence: {extract.confidence}")
    
    # 4. Test reconciliation
    print("\n🔄 Testing Taxes Paid Reconciliation")
    
    reconciler = TaxesPaidReconciler()
    
    # Mock Form 26AS data
    form26as_data = {
        "form26as_data": extract.model_dump(),
        "metadata": {"parser": "deterministic", "confidence": 1.0}
    }
    
    # Mock AIS data for cross-reference
    ais_data = {
        "salary_details": [
            {"tds_deducted": 85000, "employer": "ABC Company"},
            {"tds_deducted": 45000, "employer": "XYZ Corp"}
        ],
        "interest_details": [
            {"tds_deducted": 4500, "bank": "State Bank"}
        ]
    }
    
    # Mock Form 16 data
    form16_data = {
        "tds": 85000,
        "gross_salary": 1200000,
        "employer_name": "ABC Company",
        "metadata": {"parser": "deterministic", "confidence": 1.0}
    }
    
    # Perform reconciliation
    result = reconciler.reconcile_taxes_paid(
        form26as_data=form26as_data,
        ais_data=ais_data,
        form16_data=form16_data
    )
    
    print(f"✅ Reconciliation completed:")
    print(f"   - Total TDS: ₹{result.total_tds:,}")
    print(f"   - Total TCS: ₹{result.total_tcs:,}")
    print(f"   - Total Advance Tax: ₹{result.total_advance_tax:,}")
    print(f"   - Total Self Assessment: ₹{result.total_self_assessment:,}")
    print(f"   - Credits found: {len(result.credits)}")
    print(f"   - Warnings: {len(result.warnings)}")
    print(f"   - Confidence Score: {result.confidence_score}")
    
    # 5. Display credit details
    print("\n💳 Credit Details:")
    for i, credit in enumerate(result.credits, 1):
        print(f"   {i}. {credit.category}: ₹{credit.amount:,} (Source: {credit.source})")
        if credit.needs_confirm:
            print(f"      ⚠️  Needs confirmation")
    
    # 6. Display warnings if any
    if result.warnings:
        print("\n⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    # 7. Calculate total taxes paid
    total_taxes_paid = (
        result.total_tds + 
        result.total_tcs + 
        result.total_advance_tax + 
        result.total_self_assessment
    )
    
    print(f"\n💰 Summary:")
    print(f"   Total Taxes Paid: ₹{total_taxes_paid:,}")
    print(f"   Data Quality Score: {result.confidence_score:.2f}")
    
    # 8. Test JSON serialization
    print("\n📤 Testing Data Export")
    
    export_data = {
        "form26as_extract": extract.model_dump(),
        "reconciliation_result": {
            "total_tds": result.total_tds,
            "total_tcs": result.total_tcs,
            "total_advance_tax": result.total_advance_tax,
            "total_self_assessment": result.total_self_assessment,
            "confidence_score": result.confidence_score,
            "warnings_count": len(result.warnings),
            "credits_count": len(result.credits)
        }
    }
    
    json_output = json.dumps(export_data, indent=2, default=str)
    print(f"✅ JSON export successful ({len(json_output)} characters)")
    
    print("\n🎉 Form 26AS Integration Test Completed Successfully!")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    try:
        test_form26as_parsing_workflow()
        print("\n✅ All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)