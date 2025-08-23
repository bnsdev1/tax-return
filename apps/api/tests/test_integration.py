"""Integration tests for the storage layer."""

import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.base import Base
from repo import (
    TaxpayerRepository,
    TaxReturnRepository,
    ArtifactRepository,
    ValidationRepository,
    RulesLogRepository,
    ChallanRepository,
)
from db.models import TaxReturnStatus, ValidationStatus, ChallanStatus
from decimal import Decimal


class TestStorageLayerIntegration:
    """Integration tests for the complete storage layer."""
    
    @pytest.fixture(scope="function")
    def integration_db(self):
        """Create a test database for integration testing."""
        # Use a temporary file database
        db_path = "test_integration.db"
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        yield session
        
        # Cleanup
        session.close()
        engine.dispose()
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except PermissionError:
            # On Windows, sometimes the file is still locked
            pass
    
    def test_complete_tax_filing_workflow(self, integration_db):
        """Test a complete tax filing workflow using all repositories."""
        db = integration_db
        
        # Step 1: Create a taxpayer
        taxpayer_repo = TaxpayerRepository(db)
        taxpayer = taxpayer_repo.create_taxpayer(
            pan="ABCDE1234F",
            name="John Doe",
            email="john.doe@example.com",
            mobile="9876543210",
            address="123 Main Street, City"
        )
        
        assert taxpayer.id is not None
        assert taxpayer.pan == "ABCDE1234F"
        
        # Step 2: Create a tax return
        return_repo = TaxReturnRepository(db)
        tax_return = return_repo.create_tax_return(
            taxpayer_id=taxpayer.id,
            assessment_year="2025-26",
            form_type="ITR2",
            return_data='{"salary": 800000, "house_property": 240000}'
        )
        
        assert tax_return.id is not None
        assert tax_return.status == TaxReturnStatus.DRAFT
        
        # Step 3: Create artifacts
        artifact_repo = ArtifactRepository(db)
        
        # Create PDF form
        pdf_artifact = artifact_repo.create_artifact(
            tax_return_id=tax_return.id,
            name="ITR2_Form.pdf",
            artifact_type="pdf",
            description="Generated ITR2 form",
            tags="form,pdf,itr2",
            file_size=1024000
        )
        
        # Create XML data
        xml_artifact = artifact_repo.create_artifact(
            tax_return_id=tax_return.id,
            name="return_data.xml",
            artifact_type="xml",
            content="<ITR><PersonalInfo>...</PersonalInfo></ITR>",
            description="Tax return XML data",
            tags="data,xml"
        )
        
        assert len(artifact_repo.get_by_tax_return(tax_return.id)) == 2
        
        # Step 4: Run validations
        validation_repo = ValidationRepository(db)
        
        # Schema validation
        validation_repo.create_validation(
            tax_return_id=tax_return.id,
            validation_type="schema",
            rule_name="pan_format",
            status=ValidationStatus.PASSED,
            message="PAN format is valid"
        )
        
        # Business rule validation
        validation_repo.create_validation(
            tax_return_id=tax_return.id,
            validation_type="business_rule",
            rule_name="deduction_limit",
            status=ValidationStatus.WARNING,
            message="Deduction exceeds recommended limit",
            field_path="deductions.section_80c"
        )
        
        # Get validation summary
        summary = validation_repo.get_validation_summary(tax_return.id)
        assert summary["passed"] == 1
        assert summary["warning"] == 1
        
        # Step 5: Log rule executions
        rules_repo = RulesLogRepository(db)
        
        # Tax calculation rule
        rules_repo.create_rules_log(
            tax_return_id=tax_return.id,
            rule_name="calculate_income_tax",
            success=True,
            rule_category="calculation",
            input_data='{"taxable_income": 750000}',
            output_data='{"tax_liability": 75000}',
            execution_time_ms=250
        )
        
        # Deduction validation rule
        rules_repo.create_rules_log(
            tax_return_id=tax_return.id,
            rule_name="validate_deductions",
            success=True,
            rule_category="validation",
            execution_time_ms=100
        )
        
        # Get execution stats
        stats = rules_repo.get_execution_stats(tax_return.id)
        assert stats["total_executions"] == 2
        assert stats["successful"] == 2
        assert stats["failed"] == 0
        
        # Step 6: Create challans for tax payment
        challan_repo = ChallanRepository(db)
        
        # Advance tax challan
        advance_challan = challan_repo.create_challan(
            tax_return_id=tax_return.id,
            challan_type="advance_tax",
            amount=Decimal("50000.00"),
            assessment_year="2025-26",
            challan_number="CH2025260001",
            quarter="Q4"
        )
        
        # Self-assessment challan
        self_assessment_challan = challan_repo.create_challan(
            tax_return_id=tax_return.id,
            challan_type="self_assessment",
            amount=Decimal("25000.00"),
            assessment_year="2025-26",
            challan_number="CH2025260002"
        )
        
        # Mark advance tax as paid
        challan_repo.mark_as_paid(advance_challan.id, "RCP2025260001")
        
        # Check challan status
        paid_challans = challan_repo.get_paid_challans(tax_return.id)
        pending_challans = challan_repo.get_pending_challans(tax_return.id)
        
        assert len(paid_challans) == 1
        assert len(pending_challans) == 1
        
        # Get total amounts
        total_amount = challan_repo.get_total_amount_by_return(tax_return.id)
        paid_amount = challan_repo.get_paid_amount_by_return(tax_return.id)
        
        assert total_amount == Decimal("75000.00")
        assert paid_amount == Decimal("50000.00")
        
        # Step 7: Submit the tax return
        submitted_return = return_repo.submit_return(
            tax_return.id, 
            "ACK2025260123456789"
        )
        
        assert submitted_return.status == TaxReturnStatus.SUBMITTED
        assert submitted_return.acknowledgment_number == "ACK2025260123456789"
        assert submitted_return.filing_date is not None
        
        # Step 8: Verify complete data retrieval
        complete_return = return_repo.get_with_related_data(tax_return.id)
        
        assert complete_return is not None
        assert complete_return.taxpayer.pan == "ABCDE1234F"
        assert len(complete_return.artifacts) == 2
        assert len(complete_return.validations) == 2
        assert len(complete_return.rules_logs) == 2
        assert len(complete_return.challans) == 2
        
        print("✅ Complete tax filing workflow test passed!")
    
    def test_database_constraints_and_relationships(self, integration_db):
        """Test database constraints and relationships."""
        db = integration_db
        
        # Test unique constraints
        taxpayer_repo = TaxpayerRepository(db)
        
        # Create first taxpayer
        taxpayer1 = taxpayer_repo.create_taxpayer(
            pan="UNIQUE1234A",
            name="First Taxpayer",
            email="first@example.com"
        )
        
        # Try to create another with same PAN - should fail
        with pytest.raises(ValueError, match="already exists"):
            taxpayer_repo.create_taxpayer(
                pan="UNIQUE1234A",
                name="Second Taxpayer",
                email="second@example.com"
            )
        
        # Try to create another with same email - should fail
        with pytest.raises(ValueError, match="already exists"):
            taxpayer_repo.create_taxpayer(
                pan="UNIQUE5678B",
                name="Third Taxpayer",
                email="first@example.com"
            )
        
        # Test foreign key relationships
        return_repo = TaxReturnRepository(db)
        tax_return = return_repo.create_tax_return(
            taxpayer_id=taxpayer1.id,
            assessment_year="2025-26",
            form_type="ITR1"
        )
        
        # Create related records
        artifact_repo = ArtifactRepository(db)
        artifact_repo.create_artifact(
            tax_return_id=tax_return.id,
            name="test.pdf",
            artifact_type="pdf"
        )
        
        validation_repo = ValidationRepository(db)
        validation_repo.create_validation(
            tax_return_id=tax_return.id,
            validation_type="test",
            rule_name="test_rule",
            status=ValidationStatus.PASSED
        )
        
        # Verify relationships work
        taxpayer_with_returns = taxpayer_repo.get_with_returns(taxpayer1.id)
        assert len(taxpayer_with_returns.tax_returns) == 1
        
        return_with_data = return_repo.get_with_related_data(tax_return.id)
        assert len(return_with_data.artifacts) == 1
        assert len(return_with_data.validations) == 1
        
        print("✅ Database constraints and relationships test passed!")
    
    def test_data_integrity_and_transactions(self, integration_db):
        """Test data integrity and transaction handling."""
        db = integration_db
        
        # Test transaction rollback on error
        taxpayer_repo = TaxpayerRepository(db)
        
        # This should work
        taxpayer = taxpayer_repo.create_taxpayer(
            pan="TRANS1234A",
            name="Transaction Test",
            email="trans@example.com"
        )
        
        # Verify it was created
        found = taxpayer_repo.get_by_pan("TRANS1234A")
        assert found is not None
        
        # Test that invalid data doesn't corrupt the database
        try:
            # This should fail due to duplicate PAN
            taxpayer_repo.create_taxpayer(
                pan="TRANS1234A",  # Duplicate PAN
                name="Should Fail",
                email="fail@example.com"
            )
        except ValueError:
            pass  # Expected
        
        # Verify original data is still intact
        original = taxpayer_repo.get_by_pan("TRANS1234A")
        assert original.name == "Transaction Test"
        assert original.email == "trans@example.com"
        
        print("✅ Data integrity and transactions test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])