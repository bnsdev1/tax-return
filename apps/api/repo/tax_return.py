"""Tax return repository with specific CRUD operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from db.models import TaxReturn, TaxReturnStatus
from .base import BaseRepository


class TaxReturnRepository(BaseRepository[TaxReturn]):
    """Repository for tax return operations."""
    
    def __init__(self, db: Session):
        super().__init__(TaxReturn, db)
    
    def get_by_taxpayer(self, taxpayer_id: int) -> List[TaxReturn]:
        """Get all tax returns for a taxpayer."""
        return (
            self.db.query(TaxReturn)
            .filter(TaxReturn.taxpayer_id == taxpayer_id)
            .order_by(TaxReturn.assessment_year.desc())
            .all()
        )
    
    def get_by_assessment_year(
        self, 
        taxpayer_id: int, 
        assessment_year: str
    ) -> List[TaxReturn]:
        """Get tax returns for a specific assessment year."""
        return (
            self.db.query(TaxReturn)
            .filter(
                TaxReturn.taxpayer_id == taxpayer_id,
                TaxReturn.assessment_year == assessment_year
            )
            .all()
        )
    
    def get_by_acknowledgment_number(self, ack_number: str) -> Optional[TaxReturn]:
        """Get tax return by acknowledgment number."""
        return (
            self.db.query(TaxReturn)
            .filter(TaxReturn.acknowledgment_number == ack_number)
            .first()
        )
    
    def get_by_status(self, status: TaxReturnStatus) -> List[TaxReturn]:
        """Get tax returns by status."""
        return (
            self.db.query(TaxReturn)
            .filter(TaxReturn.status == status)
            .all()
        )
    
    def get_with_related_data(self, return_id: int) -> Optional[TaxReturn]:
        """Get tax return with all related data (artifacts, validations, etc.)."""
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(TaxReturn)
            .options(
                joinedload(TaxReturn.taxpayer),
                joinedload(TaxReturn.artifacts),
                joinedload(TaxReturn.validations),
                joinedload(TaxReturn.rules_logs),
                joinedload(TaxReturn.challans),
            )
            .filter(TaxReturn.id == return_id)
            .first()
        )
    
    def create_tax_return(
        self,
        taxpayer_id: int,
        assessment_year: str,
        form_type: str,
        return_data: Optional[str] = None,
        revised_return: bool = False,
        original_return_id: Optional[int] = None,
    ) -> TaxReturn:
        """Create a new tax return."""
        tax_return_data = {
            "taxpayer_id": taxpayer_id,
            "assessment_year": assessment_year,
            "form_type": form_type,
            "return_data": return_data,
            "revised_return": revised_return,
            "original_return_id": original_return_id,
            "status": TaxReturnStatus.DRAFT,
        }
        
        return self.create(tax_return_data)
    
    def update_status(self, return_id: int, status: TaxReturnStatus) -> Optional[TaxReturn]:
        """Update tax return status."""
        return self.update(return_id, {"status": status})
    
    def submit_return(
        self, 
        return_id: int, 
        acknowledgment_number: str
    ) -> Optional[TaxReturn]:
        """Submit a tax return with acknowledgment number."""
        from datetime import datetime
        return self.update(return_id, {
            "status": TaxReturnStatus.SUBMITTED,
            "acknowledgment_number": acknowledgment_number,
            "filing_date": datetime.now(),
        })