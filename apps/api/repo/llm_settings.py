"""Repository for LLM settings management."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..db.models import LLMSettingsModel


class LLMSettingsRepository:
    """Repository for LLM settings CRUD operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_settings(self) -> Optional[LLMSettingsModel]:
        """Get current LLM settings (there should be only one record)."""
        return self.db.query(LLMSettingsModel).first()
    
    def create_settings(self, settings_data: Dict[str, Any]) -> LLMSettingsModel:
        """Create new LLM settings."""
        settings = LLMSettingsModel(**settings_data)
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def update_settings(self, settings_id: int, update_data: Dict[str, Any]) -> LLMSettingsModel:
        """Update existing LLM settings."""
        settings = self.db.query(LLMSettingsModel).filter(LLMSettingsModel.id == settings_id).first()
        
        if not settings:
            raise ValueError(f"LLM settings with id {settings_id} not found")
        
        for key, value in update_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def delete_settings(self, settings_id: int) -> bool:
        """Delete LLM settings."""
        settings = self.db.query(LLMSettingsModel).filter(LLMSettingsModel.id == settings_id).first()
        
        if not settings:
            return False
        
        self.db.delete(settings)
        self.db.commit()
        return True