"""Test cases for repository classes."""

import pytest
from decimal import Decimal
from datetime import datetime
from db.models import TaxReturnStatus, ValidationStatus, ChallanStatus
from repo import (
    TaxpayerRepository,
    TaxReturnRepository,
    ArtifactRepository,
    ValidationRepository,
    RulesLogRepository,
    ChallanRepository,
)


class TestTaxpayerRepository:
    """Test cases for TaxpayerRepository."""
    
    def test_create_taxpayer(self, db_session, sample_taxpayer_data):
        """Test creating a new taxpayer."""
        repo = TaxpayerRepository(db_session)
        taxpayer = repo.create_taxpayer(**sample_taxpayer_data)
        
        assert taxpayer.id is not None
        assert taxpayer.pan == sample_taxpayer_data["pan"]
        assert taxpayer.name == sample_taxpayer_data["name"]
        assert taxpayer.email == sample_taxpayer_data["email"]
    
    def test_get_by_pan(self, db_session, sample_taxpayer_data):
        """Test getting taxpayer by PAN."""
        repo = TaxpayerRepository(db_session)
        created_taxpayer = repo.create_taxpayer(**sample_taxpayer_data)
        
        found_taxpayer = repo.get_by_pan(sample_taxpayer_data["pan"])
        assert found_taxpayer is not None
        assert found_taxpayer.id == created_taxpayer.id
    
    def test_get_by_email(self, db_session, sample_taxpayer_data):
        """Test getting taxpayer by email."""
        repo = TaxpayerRepository(db_session)
        created_taxpayer = repo.create_taxpayer(**sample_taxpayer_data)
        
        found_taxpayer = repo.get_by_email(sample_taxpayer_data["email"])
        assert found_taxpayer is not None
        assert found_taxpayer.id == created_taxpayer.id
    
    def test_duplicate_pan_raises_error(self, db_session, sample_taxpayer_data):
        """Test that creating taxpayer with duplicate PAN raises error."""
        repo = TaxpayerRepository(db_session)
        repo.create_taxpayer(**sample_taxpayer_data)
        
        with pytest.raises(ValueError, match="already exists"):
            repo.create_taxpayer(**sample_taxpayer_data)
    
    def test_search_by_name(self, db_session):
        """Test searching taxpayers by name pattern."""
        repo = TaxpayerRepository(db_session)
        
        # Create multiple taxpayers
        repo.create_taxpayer("ABCDE1234F", "John Doe", "john@example.com")
        repo.create_taxpayer("FGHIJ5678K", "Jane Doe", "jane@example.com")
        repo.create_taxpayer("KLMNO9012P", "Bob Smith", "bob@example.com")
        
        # Search for "Doe"
        results = repo.search_by_name("Doe")
        assert len(results) == 2
        assert all("Doe" in tp.name for tp in results)


class TestTaxReturnRepository:
    """Test cases for TaxReturnRepository."""
    
    def test_create_tax_return(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test creating a new tax return."""
        # Create taxpayer first
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        # Create tax return
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(
            taxpayer_id=taxpayer.id,
            **sample_tax_return_data
        )
        
        assert tax_return.id is not None
        assert tax_return.taxpayer_id == taxpayer.id
        assert tax_return.status == TaxReturnStatus.DRAFT
    
    def test_get_by_taxpayer(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test getting tax returns by taxpayer."""
        # Create taxpayer
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        # Create multiple tax returns
        return_repo = TaxReturnRepository(db_session)
        return1 = return_repo.create_tax_return(taxpayer.id, "2024-25", "ITR1")
        return2 = return_repo.create_tax_return(taxpayer.id, "2025-26", "ITR2")
        
        # Get returns by taxpayer
        returns = return_repo.get_by_taxpayer(taxpayer.id)
        assert len(returns) == 2
        assert returns[0].assessment_year == "2025-26"  # Should be ordered by year desc
    
    def test_submit_return(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test submitting a tax return."""
        # Create taxpayer and return
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Submit return
        ack_number = "ACK123456789"
        submitted_return = return_repo.submit_return(tax_return.id, ack_number)
        
        assert submitted_return.status == TaxReturnStatus.SUBMITTED
        assert submitted_return.acknowledgment_number == ack_number
        assert submitted_return.filing_date is not None


class TestArtifactRepository:
    """Test cases for ArtifactRepository."""
    
    def test_create_artifact(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test creating a new artifact."""
        # Setup taxpayer and return
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create artifact
        artifact_repo = ArtifactRepository(db_session)
        artifact = artifact_repo.create_artifact(
            tax_return_id=tax_return.id,
            name="ITR1_Form.pdf",
            artifact_type="pdf",
            description="Generated ITR1 form",
            tags="form,pdf,itr1"
        )
        
        assert artifact.id is not None
        assert artifact.tax_return_id == tax_return.id
        assert artifact.name == "ITR1_Form.pdf"
    
    def test_get_by_type(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test getting artifacts by type."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create artifacts of different types
        artifact_repo = ArtifactRepository(db_session)
        artifact_repo.create_artifact(tax_return.id, "form.pdf", "pdf")
        artifact_repo.create_artifact(tax_return.id, "data.xml", "xml")
        artifact_repo.create_artifact(tax_return.id, "receipt.pdf", "pdf")
        
        # Get PDF artifacts
        pdf_artifacts = artifact_repo.get_by_type(tax_return.id, "pdf")
        assert len(pdf_artifacts) == 2
        assert all(art.artifact_type == "pdf" for art in pdf_artifacts)


class TestValidationRepository:
    """Test cases for ValidationRepository."""
    
    def test_create_validation(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test creating a new validation."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create validation
        validation_repo = ValidationRepository(db_session)
        validation = validation_repo.create_validation(
            tax_return_id=tax_return.id,
            validation_type="schema",
            rule_name="pan_format",
            status=ValidationStatus.PASSED,
            message="PAN format is valid"
        )
        
        assert validation.id is not None
        assert validation.tax_return_id == tax_return.id
        assert validation.status == ValidationStatus.PASSED
    
    def test_get_validation_summary(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test getting validation summary."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create validations with different statuses
        validation_repo = ValidationRepository(db_session)
        validation_repo.create_validation(tax_return.id, "schema", "rule1", ValidationStatus.PASSED)
        validation_repo.create_validation(tax_return.id, "schema", "rule2", ValidationStatus.PASSED)
        validation_repo.create_validation(tax_return.id, "business", "rule3", ValidationStatus.FAILED)
        validation_repo.create_validation(tax_return.id, "business", "rule4", ValidationStatus.WARNING)
        
        # Get summary
        summary = validation_repo.get_validation_summary(tax_return.id)
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["warning"] == 1


class TestRulesLogRepository:
    """Test cases for RulesLogRepository."""
    
    def test_create_rules_log(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test creating a new rules log entry."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create rules log
        rules_repo = RulesLogRepository(db_session)
        rules_log = rules_repo.create_rules_log(
            tax_return_id=tax_return.id,
            rule_name="calculate_tax",
            success=True,
            rule_category="calculation",
            execution_time_ms=150
        )
        
        assert rules_log.id is not None
        assert rules_log.tax_return_id == tax_return.id
        assert rules_log.success is True
    
    def test_get_execution_stats(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test getting execution statistics."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create rules logs
        rules_repo = RulesLogRepository(db_session)
        rules_repo.create_rules_log(tax_return.id, "rule1", True, execution_time_ms=100)
        rules_repo.create_rules_log(tax_return.id, "rule2", True, execution_time_ms=200)
        rules_repo.create_rules_log(tax_return.id, "rule3", False, execution_time_ms=50)
        
        # Get stats
        stats = rules_repo.get_execution_stats(tax_return.id)
        assert stats["total_executions"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert abs(stats["avg_execution_time"] - 116.67) < 0.01  # (100+200+50)/3


class TestChallanRepository:
    """Test cases for ChallanRepository."""
    
    def test_create_challan(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test creating a new challan."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create challan
        challan_repo = ChallanRepository(db_session)
        challan = challan_repo.create_challan(
            tax_return_id=tax_return.id,
            challan_type="advance_tax",
            amount=Decimal("50000.00"),
            assessment_year="2025-26",
            challan_number="CH123456789"
        )
        
        assert challan.id is not None
        assert challan.tax_return_id == tax_return.id
        assert challan.amount == Decimal("50000.00")
        assert challan.status == ChallanStatus.PENDING
    
    def test_mark_as_paid(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test marking a challan as paid."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create and pay challan
        challan_repo = ChallanRepository(db_session)
        challan = challan_repo.create_challan(
            tax_return.id, "advance_tax", Decimal("50000.00"), "2025-26"
        )
        
        paid_challan = challan_repo.mark_as_paid(challan.id, "RCP123456789")
        
        assert paid_challan.status == ChallanStatus.PAID
        assert paid_challan.receipt_number == "RCP123456789"
        assert paid_challan.payment_date is not None
    
    def test_get_total_amount_by_return(self, db_session, sample_taxpayer_data, sample_tax_return_data):
        """Test getting total amount of challans for a return."""
        # Setup
        taxpayer_repo = TaxpayerRepository(db_session)
        taxpayer = taxpayer_repo.create_taxpayer(**sample_taxpayer_data)
        
        return_repo = TaxReturnRepository(db_session)
        tax_return = return_repo.create_tax_return(taxpayer.id, **sample_tax_return_data)
        
        # Create multiple challans
        challan_repo = ChallanRepository(db_session)
        challan_repo.create_challan(tax_return.id, "advance_tax", Decimal("30000.00"), "2025-26")
        challan_repo.create_challan(tax_return.id, "self_assessment", Decimal("20000.00"), "2025-26")
        
        # Get total amount
        total = challan_repo.get_total_amount_by_return(tax_return.id)
        assert total == Decimal("50000.00")


class TestBaseRepositoryOperations:
    """Test cases for base repository operations."""
    
    def test_crud_operations(self, db_session, sample_taxpayer_data):
        """Test basic CRUD operations."""
        repo = TaxpayerRepository(db_session)
        
        # Create
        taxpayer = repo.create_taxpayer(**sample_taxpayer_data)
        assert taxpayer.id is not None
        
        # Read
        found = repo.get(taxpayer.id)
        assert found is not None
        assert found.pan == sample_taxpayer_data["pan"]
        
        # Update
        updated = repo.update(taxpayer.id, {"name": "Updated Name"})
        assert updated.name == "Updated Name"
        
        # Delete
        deleted = repo.delete(taxpayer.id)
        assert deleted is True
        
        # Verify deletion
        not_found = repo.get(taxpayer.id)
        assert not_found is None
    
    def test_get_multi_with_filters(self, db_session):
        """Test getting multiple records with filters."""
        repo = TaxpayerRepository(db_session)
        
        # Create multiple taxpayers
        repo.create_taxpayer("ABCDE1234F", "John Doe", "john@example.com")
        repo.create_taxpayer("FGHIJ5678K", "Jane Smith", "jane@example.com")
        repo.create_taxpayer("KLMNO9012P", "Bob Johnson", "bob@example.com")
        
        # Get all
        all_taxpayers = repo.get_multi()
        assert len(all_taxpayers) == 3
        
        # Get with limit
        limited = repo.get_multi(limit=2)
        assert len(limited) == 2
        
        # Get with skip
        skipped = repo.get_multi(skip=1, limit=2)
        assert len(skipped) == 2
    
    def test_count_and_exists(self, db_session, sample_taxpayer_data):
        """Test count and exists operations."""
        repo = TaxpayerRepository(db_session)
        
        # Initially empty
        assert repo.count() == 0
        
        # Create taxpayer
        taxpayer = repo.create_taxpayer(**sample_taxpayer_data)
        
        # Count should be 1
        assert repo.count() == 1
        
        # Should exist
        assert repo.exists(taxpayer.id) is True
        
        # Non-existent ID should not exist
        assert repo.exists(999) is False