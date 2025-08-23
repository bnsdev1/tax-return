#!/usr/bin/env python3
"""
Demonstration script for the storage layer.
Shows how to use the SQLAlchemy models and repository classes.
"""

from decimal import Decimal
from db.base import get_db
from db.models import TaxReturnStatus, ValidationStatus, ChallanStatus
from repo import (
    TaxpayerRepository,
    TaxReturnRepository,
    ArtifactRepository,
    ValidationRepository,
    RulesLogRepository,
    ChallanRepository,
)


def main():
    """Demonstrate the storage layer functionality."""
    print("🚀 Storage Layer Demonstration")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Step 1: Create a taxpayer
        print("\n📋 Step 1: Creating a taxpayer...")
        taxpayer_repo = TaxpayerRepository(db)
        
        taxpayer = taxpayer_repo.create_taxpayer(
            pan="DEMO12345A",
            name="Demo Taxpayer",
            email="demo@example.com",
            mobile="9876543210",
            address="123 Demo Street, Demo City"
        )
        
        print(f"   ✅ Created taxpayer: {taxpayer.name} (ID: {taxpayer.id}, PAN: {taxpayer.pan})")
        
        # Step 2: Create a tax return
        print("\n📄 Step 2: Creating a tax return...")
        return_repo = TaxReturnRepository(db)
        
        tax_return = return_repo.create_tax_return(
            taxpayer_id=taxpayer.id,
            assessment_year="2025-26",
            form_type="ITR2",
            return_data='{"salary": 800000, "house_property": 240000, "deductions": 185000}'
        )
        
        print(f"   ✅ Created tax return: {tax_return.assessment_year} {tax_return.form_type} (ID: {tax_return.id})")
        print(f"   📊 Status: {tax_return.status.value}")
        
        # Step 3: Create artifacts
        print("\n📁 Step 3: Creating artifacts...")
        artifact_repo = ArtifactRepository(db)
        
        # PDF form
        pdf_artifact = artifact_repo.create_artifact(
            tax_return_id=tax_return.id,
            name="ITR2_Form.pdf",
            artifact_type="pdf",
            description="Generated ITR2 form",
            tags="form,pdf,itr2",
            file_size=1024000
        )
        
        # XML data
        xml_artifact = artifact_repo.create_artifact(
            tax_return_id=tax_return.id,
            name="return_data.xml",
            artifact_type="xml",
            content="<ITR><PersonalInfo><PAN>DEMO12345A</PAN></PersonalInfo></ITR>",
            description="Tax return XML data"
        )
        
        print(f"   ✅ Created PDF artifact: {pdf_artifact.name} ({pdf_artifact.file_size} bytes)")
        print(f"   ✅ Created XML artifact: {xml_artifact.name}")
        
        # Step 4: Run validations
        print("\n✅ Step 4: Running validations...")
        validation_repo = ValidationRepository(db)
        
        # Schema validation
        schema_validation = validation_repo.create_validation(
            tax_return_id=tax_return.id,
            validation_type="schema",
            rule_name="pan_format",
            status=ValidationStatus.PASSED,
            message="PAN format is valid",
            execution_time_ms=50
        )
        
        # Business rule validation
        business_validation = validation_repo.create_validation(
            tax_return_id=tax_return.id,
            validation_type="business_rule",
            rule_name="deduction_limit",
            status=ValidationStatus.WARNING,
            message="Deduction exceeds recommended limit",
            field_path="deductions.section_80c",
            execution_time_ms=120
        )
        
        print(f"   ✅ Schema validation: {schema_validation.status.value}")
        print(f"   ⚠️  Business rule validation: {business_validation.status.value}")
        
        # Get validation summary
        summary = validation_repo.get_validation_summary(tax_return.id)
        print(f"   📊 Validation summary: {summary}")
        
        # Step 5: Log rule executions
        print("\n⚙️  Step 5: Logging rule executions...")
        rules_repo = RulesLogRepository(db)
        
        # Tax calculation
        calc_log = rules_repo.create_rules_log(
            tax_return_id=tax_return.id,
            rule_name="calculate_income_tax",
            success=True,
            rule_category="calculation",
            input_data='{"taxable_income": 855000}',
            output_data='{"tax_liability": 85500}',
            execution_time_ms=250
        )
        
        # Deduction validation
        deduction_log = rules_repo.create_rules_log(
            tax_return_id=tax_return.id,
            rule_name="validate_deductions",
            success=True,
            rule_category="validation",
            execution_time_ms=100
        )
        
        print(f"   ✅ Tax calculation rule executed successfully")
        print(f"   ✅ Deduction validation rule executed successfully")
        
        # Get execution stats
        stats = rules_repo.get_execution_stats(tax_return.id)
        print(f"   📊 Execution stats: {stats}")
        
        # Step 6: Create challans
        print("\n💰 Step 6: Creating tax payment challans...")
        challan_repo = ChallanRepository(db)
        
        # Advance tax
        advance_challan = challan_repo.create_challan(
            tax_return_id=tax_return.id,
            challan_type="advance_tax",
            amount=Decimal("60000.00"),
            assessment_year="2025-26",
            challan_number="CH2025260001",
            quarter="Q4"
        )
        
        # Self-assessment
        self_assessment_challan = challan_repo.create_challan(
            tax_return_id=tax_return.id,
            challan_type="self_assessment",
            amount=Decimal("25500.00"),
            assessment_year="2025-26",
            challan_number="CH2025260002"
        )
        
        print(f"   ✅ Created advance tax challan: ₹{advance_challan.amount}")
        print(f"   ✅ Created self-assessment challan: ₹{self_assessment_challan.amount}")
        
        # Mark advance tax as paid
        paid_challan = challan_repo.mark_as_paid(advance_challan.id, "RCP2025260001")
        print(f"   💳 Marked advance tax as paid (Receipt: {paid_challan.receipt_number})")
        
        # Get payment summary
        total_amount = challan_repo.get_total_amount_by_return(tax_return.id)
        paid_amount = challan_repo.get_paid_amount_by_return(tax_return.id)
        pending_amount = total_amount - paid_amount
        
        print(f"   📊 Payment summary:")
        print(f"      Total: ₹{total_amount}")
        print(f"      Paid: ₹{paid_amount}")
        print(f"      Pending: ₹{pending_amount}")
        
        # Step 7: Submit the tax return
        print("\n📤 Step 7: Submitting tax return...")
        submitted_return = return_repo.submit_return(
            tax_return.id,
            "ACK2025260123456789"
        )
        
        print(f"   ✅ Tax return submitted!")
        print(f"   📋 Acknowledgment: {submitted_return.acknowledgment_number}")
        print(f"   📅 Filing date: {submitted_return.filing_date}")
        print(f"   📊 Status: {submitted_return.status.value}")
        
        # Step 8: Retrieve complete data
        print("\n📊 Step 8: Retrieving complete tax return data...")
        complete_return = return_repo.get_with_related_data(tax_return.id)
        
        print(f"   👤 Taxpayer: {complete_return.taxpayer.name}")
        print(f"   📄 Return: {complete_return.assessment_year} {complete_return.form_type}")
        print(f"   📁 Artifacts: {len(complete_return.artifacts)} files")
        print(f"   ✅ Validations: {len(complete_return.validations)} checks")
        print(f"   ⚙️  Rules logs: {len(complete_return.rules_logs)} executions")
        print(f"   💰 Challans: {len(complete_return.challans)} payments")
        
        print("\n🎉 Storage layer demonstration completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()