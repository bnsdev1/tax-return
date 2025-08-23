"""SQLAlchemy models for the tax planning application."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Numeric,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from .base import Base


class TaxReturnStatus(str, Enum):
    """Tax return status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSED = "processed"
    REJECTED = "rejected"


class ValidationStatus(str, Enum):
    """Validation status enumeration."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class ChallanStatus(str, Enum):
    """Challan status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Taxpayer(Base):
    """Taxpayer model representing individual taxpayers."""
    
    __tablename__ = "taxpayers"
    
    id = Column(Integer, primary_key=True, index=True)
    pan = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    mobile = Column(String(15))
    date_of_birth = Column(DateTime)
    address = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tax_returns = relationship("TaxReturn", back_populates="taxpayer", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Taxpayer(id={self.id}, pan='{self.pan}', name='{self.name}')>"


class TaxReturn(Base):
    """Tax return model representing filed tax returns."""
    
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True, index=True)
    taxpayer_id = Column(Integer, ForeignKey("taxpayers.id"), nullable=False)
    assessment_year = Column(String(7), nullable=False)  # Format: "2025-26"
    form_type = Column(String(10), nullable=False)  # ITR1, ITR2, etc.
    status = Column(SQLEnum(TaxReturnStatus), default=TaxReturnStatus.DRAFT)
    
    # Return data (stored as JSON text)
    return_data = Column(Text)  # JSON string of the complete return
    
    # Filing information
    filing_date = Column(DateTime)
    acknowledgment_number = Column(String(50), unique=True)
    revised_return = Column(Boolean, default=False)
    original_return_id = Column(Integer, ForeignKey("returns.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    taxpayer = relationship("Taxpayer", back_populates="tax_returns")
    original_return = relationship("TaxReturn", remote_side=[id])
    artifacts = relationship("Artifact", back_populates="tax_return", cascade="all, delete-orphan")
    validations = relationship("Validation", back_populates="tax_return", cascade="all, delete-orphan")
    rules_logs = relationship("RulesLog", back_populates="tax_return", cascade="all, delete-orphan")
    challans = relationship("Challan", back_populates="tax_return", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<TaxReturn(id={self.id}, taxpayer_id={self.taxpayer_id}, ay='{self.assessment_year}', form='{self.form_type}')>"


class Artifact(Base):
    """Artifact model for storing generated documents and files."""
    
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    
    # Artifact metadata
    name = Column(String(255), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # pdf, xml, json, etc.
    file_path = Column(String(500))  # Path to stored file
    file_size = Column(Integer)  # Size in bytes
    checksum = Column(String(64))  # SHA-256 checksum
    
    # Content (for small artifacts, can store directly)
    content = Column(Text)  # For small text-based artifacts
    
    # Metadata
    description = Column(Text)
    tags = Column(String(500))  # Comma-separated tags
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tax_return = relationship("TaxReturn", back_populates="artifacts")
    
    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name='{self.name}', type='{self.artifact_type}')>"


class Validation(Base):
    """Validation model for storing validation results."""
    
    __tablename__ = "validations"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    
    # Validation details
    validation_type = Column(String(50), nullable=False)  # schema, business_rule, etc.
    rule_name = Column(String(100), nullable=False)
    status = Column(SQLEnum(ValidationStatus), nullable=False)
    
    # Results
    message = Column(Text)
    details = Column(Text)  # JSON string with detailed results
    field_path = Column(String(200))  # Path to the field that failed validation
    
    # Execution info
    execution_time_ms = Column(Integer)  # Execution time in milliseconds
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tax_return = relationship("TaxReturn", back_populates="validations")
    
    def __repr__(self) -> str:
        return f"<Validation(id={self.id}, type='{self.validation_type}', rule='{self.rule_name}', status='{self.status}')>"


class RulesLog(Base):
    """Rules log model for tracking business rule executions."""
    
    __tablename__ = "rules_log"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    
    # Rule execution details
    rule_name = Column(String(100), nullable=False)
    rule_version = Column(String(20))
    rule_category = Column(String(50))  # calculation, validation, transformation
    
    # Execution context
    input_data = Column(Text)  # JSON string of input data
    output_data = Column(Text)  # JSON string of output data
    execution_time_ms = Column(Integer)
    
    # Results
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    warnings = Column(Text)  # JSON array of warning messages
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tax_return = relationship("TaxReturn", back_populates="rules_logs")
    
    def __repr__(self) -> str:
        return f"<RulesLog(id={self.id}, rule='{self.rule_name}', success={self.success})>"


class Challan(Base):
    """Challan model for tax payment challans."""
    
    __tablename__ = "challans"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    
    # Challan details
    challan_number = Column(String(50), unique=True)
    challan_type = Column(String(20), nullable=False)  # advance_tax, self_assessment, etc.
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Payment details
    bank_name = Column(String(100))
    branch_code = Column(String(20))
    payment_date = Column(DateTime)
    status = Column(SQLEnum(ChallanStatus), default=ChallanStatus.PENDING)
    
    # Tax period
    assessment_year = Column(String(7), nullable=False)
    quarter = Column(String(2))  # Q1, Q2, Q3, Q4 for advance tax
    
    # Additional details
    remarks = Column(Text)
    receipt_number = Column(String(50))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tax_return = relationship("TaxReturn", back_populates="challans")
    
    def __repr__(self) -> str:
        return f"<Challan(id={self.id}, number='{self.challan_number}', amount={self.amount}, status='{self.status}')>"