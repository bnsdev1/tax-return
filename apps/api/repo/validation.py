"""Validation repository with specific CRUD operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from db.models import Validation, ValidationStatus
from .base import BaseRepository


class ValidationRepository(BaseRepository[Validation]):
    """Repository for validation operations."""
    
    def __init__(self, db: Session):
        super().__init__(Validation, db)
    
    def get_by_tax_return(self, tax_return_id: int) -> List[Validation]:
        """Get all validations for a tax return."""
        return (
            self.db.query(Validation)
            .filter(Validation.tax_return_id == tax_return_id)
            .order_by(Validation.created_at.desc())
            .all()
        )
    
    def get_by_status(
        self, 
        tax_return_id: int, 
        status: ValidationStatus
    ) -> List[Validation]:
        """Get validations by status for a tax return."""
        return (
            self.db.query(Validation)
            .filter(
                Validation.tax_return_id == tax_return_id,
                Validation.status == status
            )
            .all()
        )
    
    def get_by_type(self, tax_return_id: int, validation_type: str) -> List[Validation]:
        """Get validations by type for a tax return."""
        return (
            self.db.query(Validation)
            .filter(
                Validation.tax_return_id == tax_return_id,
                Validation.validation_type == validation_type
            )
            .all()
        )
    
    def get_by_rule(self, tax_return_id: int, rule_name: str) -> List[Validation]:
        """Get validations by rule name for a tax return."""
        return (
            self.db.query(Validation)
            .filter(
                Validation.tax_return_id == tax_return_id,
                Validation.rule_name == rule_name
            )
            .all()
        )
    
    def get_failed_validations(self, tax_return_id: int) -> List[Validation]:
        """Get all failed validations for a tax return."""
        return self.get_by_status(tax_return_id, ValidationStatus.FAILED)
    
    def get_warnings(self, tax_return_id: int) -> List[Validation]:
        """Get all validation warnings for a tax return."""
        return self.get_by_status(tax_return_id, ValidationStatus.WARNING)
    
    def create_validation(
        self,
        tax_return_id: int,
        validation_type: str,
        rule_name: str,
        status: ValidationStatus,
        message: Optional[str] = None,
        details: Optional[str] = None,
        field_path: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ) -> Validation:
        """Create a new validation record."""
        validation_data = {
            "tax_return_id": tax_return_id,
            "validation_type": validation_type,
            "rule_name": rule_name,
            "status": status,
            "message": message,
            "details": details,
            "field_path": field_path,
            "execution_time_ms": execution_time_ms,
        }
        
        return self.create(validation_data)
    
    def get_validation_summary(self, tax_return_id: int) -> dict:
        """Get validation summary for a tax return."""
        from sqlalchemy import func
        
        summary = (
            self.db.query(
                Validation.status,
                func.count(Validation.id).label('count')
            )
            .filter(Validation.tax_return_id == tax_return_id)
            .group_by(Validation.status)
            .all()
        )
        
        return {status.value: count for status, count in summary}