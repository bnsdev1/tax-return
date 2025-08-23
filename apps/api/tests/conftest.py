"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base
from db.models import (
    Taxpayer,
    TaxReturn,
    Artifact,
    Validation,
    RulesLog,
    Challan,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_taxpayer_data():
    """Sample taxpayer data for testing."""
    return {
        "pan": "ABCDE1234F",
        "name": "Test Taxpayer",
        "email": "test@example.com",
        "mobile": "9876543210",
        "address": "123 Test Street, Test City",
    }


@pytest.fixture
def sample_tax_return_data():
    """Sample tax return data for testing."""
    return {
        "assessment_year": "2025-26",
        "form_type": "ITR1",
        "return_data": '{"gross_salary": 500000}',
    }