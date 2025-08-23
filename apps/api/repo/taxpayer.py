"""Taxpayer repository with specific CRUD operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from db.models import Taxpayer
from .base import BaseRepository


class TaxpayerRepository(BaseRepository[Taxpayer]):
    """Repository for taxpayer operations."""
    
    def __init__(self, db: Session):
        super().__init__(Taxpayer, db)
    
    def get_by_pan(self, pan: str) -> Optional[Taxpayer]:
        """Get taxpayer by PAN number."""
        return self.db.query(Taxpayer).filter(Taxpayer.pan == pan).first()
    
    def get_by_email(self, email: str) -> Optional[Taxpayer]:
        """Get taxpayer by email address."""
        return self.db.query(Taxpayer).filter(Taxpayer.email == email).first()
    
    def search_by_name(self, name_pattern: str) -> List[Taxpayer]:
        """Search taxpayers by name pattern."""
        return (
            self.db.query(Taxpayer)
            .filter(Taxpayer.name.ilike(f"%{name_pattern}%"))
            .all()
        )
    
    def get_with_returns(self, taxpayer_id: int) -> Optional[Taxpayer]:
        """Get taxpayer with their tax returns."""
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(Taxpayer)
            .options(joinedload(Taxpayer.tax_returns))
            .filter(Taxpayer.id == taxpayer_id)
            .first()
        )
    
    def create_taxpayer(
        self,
        pan: str,
        name: str,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Taxpayer:
        """Create a new taxpayer with validation."""
        # Check if PAN already exists
        existing = self.get_by_pan(pan)
        if existing:
            raise ValueError(f"Taxpayer with PAN {pan} already exists")
        
        # Check if email already exists
        if email:
            existing_email = self.get_by_email(email)
            if existing_email:
                raise ValueError(f"Taxpayer with email {email} already exists")
        
        taxpayer_data = {
            "pan": pan,
            "name": name,
            "email": email,
            "mobile": mobile,
            "address": address,
        }
        
        if date_of_birth:
            from datetime import datetime
            taxpayer_data["date_of_birth"] = datetime.fromisoformat(date_of_birth)
        
        return self.create(taxpayer_data)