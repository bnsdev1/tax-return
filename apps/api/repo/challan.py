"""Challan repository with specific CRUD operations."""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from db.models import Challan, ChallanStatus
from .base import BaseRepository


class ChallanRepository(BaseRepository[Challan]):
    """Repository for challan operations."""
    
    def __init__(self, db: Session):
        super().__init__(Challan, db)
    
    def get_by_tax_return(self, tax_return_id: int) -> List[Challan]:
        """Get all challans for a tax return."""
        return (
            self.db.query(Challan)
            .filter(Challan.tax_return_id == tax_return_id)
            .order_by(Challan.created_at.desc())
            .all()
        )
    
    def get_by_challan_number(self, challan_number: str) -> Optional[Challan]:
        """Get challan by challan number."""
        return (
            self.db.query(Challan)
            .filter(Challan.challan_number == challan_number)
            .first()
        )
    
    def get_by_status(
        self, 
        tax_return_id: int, 
        status: ChallanStatus
    ) -> List[Challan]:
        """Get challans by status for a tax return."""
        return (
            self.db.query(Challan)
            .filter(
                Challan.tax_return_id == tax_return_id,
                Challan.status == status
            )
            .all()
        )
    
    def get_by_type(self, tax_return_id: int, challan_type: str) -> List[Challan]:
        """Get challans by type for a tax return."""
        return (
            self.db.query(Challan)
            .filter(
                Challan.tax_return_id == tax_return_id,
                Challan.challan_type == challan_type
            )
            .all()
        )
    
    def get_by_assessment_year(
        self, 
        assessment_year: str, 
        status: Optional[ChallanStatus] = None
    ) -> List[Challan]:
        """Get challans by assessment year."""
        query = self.db.query(Challan).filter(
            Challan.assessment_year == assessment_year
        )
        
        if status:
            query = query.filter(Challan.status == status)
        
        return query.all()
    
    def get_pending_challans(self, tax_return_id: int) -> List[Challan]:
        """Get all pending challans for a tax return."""
        return self.get_by_status(tax_return_id, ChallanStatus.PENDING)
    
    def get_paid_challans(self, tax_return_id: int) -> List[Challan]:
        """Get all paid challans for a tax return."""
        return self.get_by_status(tax_return_id, ChallanStatus.PAID)
    
    def create_challan(
        self,
        tax_return_id: int,
        challan_type: str,
        amount: Decimal,
        assessment_year: str,
        challan_number: Optional[str] = None,
        bank_name: Optional[str] = None,
        branch_code: Optional[str] = None,
        quarter: Optional[str] = None,
        remarks: Optional[str] = None,
    ) -> Challan:
        """Create a new challan."""
        challan_data = {
            "tax_return_id": tax_return_id,
            "challan_type": challan_type,
            "amount": amount,
            "assessment_year": assessment_year,
            "challan_number": challan_number,
            "bank_name": bank_name,
            "branch_code": branch_code,
            "quarter": quarter,
            "remarks": remarks,
            "status": ChallanStatus.PENDING,
        }
        
        return self.create(challan_data)
    
    def mark_as_paid(
        self, 
        challan_id: int, 
        receipt_number: str,
        payment_date: Optional[str] = None
    ) -> Optional[Challan]:
        """Mark a challan as paid."""
        from datetime import datetime
        
        update_data = {
            "status": ChallanStatus.PAID,
            "receipt_number": receipt_number,
        }
        
        if payment_date:
            update_data["payment_date"] = datetime.fromisoformat(payment_date)
        else:
            update_data["payment_date"] = datetime.now()
        
        return self.update(challan_id, update_data)
    
    def get_total_amount_by_return(self, tax_return_id: int) -> Decimal:
        """Get total amount of all challans for a tax return."""
        from sqlalchemy import func
        result = (
            self.db.query(func.sum(Challan.amount))
            .filter(Challan.tax_return_id == tax_return_id)
            .scalar()
        )
        return result or Decimal('0.00')
    
    def get_paid_amount_by_return(self, tax_return_id: int) -> Decimal:
        """Get total paid amount for a tax return."""
        from sqlalchemy import func
        result = (
            self.db.query(func.sum(Challan.amount))
            .filter(
                Challan.tax_return_id == tax_return_id,
                Challan.status == ChallanStatus.PAID
            )
            .scalar()
        )
        return result or Decimal('0.00')