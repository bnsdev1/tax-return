"""Tests for challan API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import tempfile
import os

from main import app
from db.base import get_db
from db.models import TaxReturn, Taxpayer, Challan


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_tax_return(db_session):
    """Create a sample tax return for testing."""
    # Create taxpayer
    taxpayer = Taxpayer(
        pan="ABCDE1234F",
        name="Test Taxpayer",
        email="test@example.com"
    )
    db_session.add(taxpayer)
    db_session.commit()
    
    # Create tax return
    tax_return = TaxReturn(
        taxpayer_id=taxpayer.id,
        assessment_year="2025-26",
        form_type="ITR2",
        return_data='{"regime": "new"}'
    )
    db_session.add(tax_return)
    db_session.commit()
    
    return tax_return


def test_create_challan_success(client, sample_tax_return):
    """Test successful challan creation."""
    challan_data = {
        "challan_type": "self_assessment",
        "amount": 15000.0,
        "cin_crn": "1234567890123456",
        "bsr_code": "1234567",
        "bank_reference": "REF123456789",
        "payment_date": "2025-08-23T00:00:00Z",
        "bank_name": "State Bank of India",
        "remarks": "Self assessment tax payment"
    }
    
    response = client.post(
        f"/api/challans/{sample_tax_return.id}",
        data=challan_data
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["tax_return_id"] == sample_tax_return.id
    assert data["amount"] == 15000.0
    assert data["cin_crn"] == "1234567890123456"
    assert data["bsr_code"] == "1234567"
    assert data["bank_reference"] == "REF123456789"
    assert data["status"] == "paid"
    assert "challan_number" in data


def test_create_challan_with_file(client, sample_tax_return):
    """Test challan creation with PDF file upload."""
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b'%PDF-1.4 fake pdf content')
        tmp_file_path = tmp_file.name
    
    try:
        with open(tmp_file_path, 'rb') as pdf_file:
            response = client.post(
                f"/api/challans/{sample_tax_return.id}",
                data={
                    "challan_type": "self_assessment",
                    "amount": 15000.0,
                    "cin_crn": "1234567890123456",
                    "bsr_code": "1234567",
                    "bank_reference": "REF123456789",
                    "payment_date": "2025-08-23T00:00:00Z"
                },
                files={"challan_file": ("test_challan.pdf", pdf_file, "application/pdf")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["challan_file_path"] is not None
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_file_path)


def test_create_challan_invalid_data(client, sample_tax_return):
    """Test challan creation with invalid data."""
    # Missing required fields
    response = client.post(
        f"/api/challans/{sample_tax_return.id}",
        data={
            "challan_type": "self_assessment",
            "amount": 15000.0
            # Missing cin_crn, bsr_code, etc.
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_create_challan_invalid_return_id(client):
    """Test challan creation with non-existent return ID."""
    challan_data = {
        "challan_type": "self_assessment",
        "amount": 15000.0,
        "cin_crn": "1234567890123456",
        "bsr_code": "1234567",
        "bank_reference": "REF123456789",
        "payment_date": "2025-08-23T00:00:00Z"
    }
    
    response = client.post(
        "/api/challans/99999",  # Non-existent return ID
        data=challan_data
    )
    
    assert response.status_code == 404


def test_get_challans(client, sample_tax_return, db_session):
    """Test getting all challans for a tax return."""
    # Create a challan first
    challan = Challan(
        tax_return_id=sample_tax_return.id,
        challan_number="CH00000100001",
        challan_type="self_assessment",
        amount=15000.0,
        cin_crn="1234567890123456",
        bsr_code="1234567",
        bank_reference="REF123456789",
        payment_date=datetime(2025, 8, 23),
        assessment_year=sample_tax_return.assessment_year
    )
    db_session.add(challan)
    db_session.commit()
    
    response = client.get(f"/api/challans/{sample_tax_return.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 15000.0
    assert data[0]["cin_crn"] == "1234567890123456"


def test_get_challan_summary(client, sample_tax_return, db_session):
    """Test getting challan summary for a tax return."""
    # Create multiple challans
    challans = [
        Challan(
            tax_return_id=sample_tax_return.id,
            challan_number=f"CH00000100{i:03d}",
            challan_type="self_assessment",
            amount=10000.0 + i * 1000,
            cin_crn=f"123456789012345{i}",
            bsr_code="1234567",
            bank_reference=f"REF12345678{i}",
            payment_date=datetime(2025, 8, 23),
            assessment_year=sample_tax_return.assessment_year
        )
        for i in range(1, 4)
    ]
    
    for challan in challans:
        db_session.add(challan)
    db_session.commit()
    
    response = client.get(f"/api/challans/{sample_tax_return.id}/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_challans"] == 3
    assert data["total_amount"] == 36000.0  # 11000 + 12000 + 13000
    assert data["paid_challans"] == 0  # Default status is PENDING
    assert data["pending_challans"] == 3