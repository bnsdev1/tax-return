"""Artifact repository with specific CRUD operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from db.models import Artifact
from .base import BaseRepository


class ArtifactRepository(BaseRepository[Artifact]):
    """Repository for artifact operations."""
    
    def __init__(self, db: Session):
        super().__init__(Artifact, db)
    
    def get_by_tax_return(self, tax_return_id: int) -> List[Artifact]:
        """Get all artifacts for a tax return."""
        return (
            self.db.query(Artifact)
            .filter(Artifact.tax_return_id == tax_return_id)
            .order_by(Artifact.created_at.desc())
            .all()
        )
    
    def get_by_type(self, tax_return_id: int, artifact_type: str) -> List[Artifact]:
        """Get artifacts by type for a tax return."""
        return (
            self.db.query(Artifact)
            .filter(
                Artifact.tax_return_id == tax_return_id,
                Artifact.artifact_type == artifact_type
            )
            .all()
        )
    
    def get_by_name(self, tax_return_id: int, name: str) -> Optional[Artifact]:
        """Get artifact by name for a tax return."""
        return (
            self.db.query(Artifact)
            .filter(
                Artifact.tax_return_id == tax_return_id,
                Artifact.name == name
            )
            .first()
        )
    
    def search_by_tags(self, tax_return_id: int, tag: str) -> List[Artifact]:
        """Search artifacts by tag."""
        return (
            self.db.query(Artifact)
            .filter(
                Artifact.tax_return_id == tax_return_id,
                Artifact.tags.ilike(f"%{tag}%")
            )
            .all()
        )
    
    def create_artifact(
        self,
        tax_return_id: int,
        name: str,
        artifact_type: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
    ) -> Artifact:
        """Create a new artifact."""
        artifact_data = {
            "tax_return_id": tax_return_id,
            "name": name,
            "artifact_type": artifact_type,
            "file_path": file_path,
            "content": content,
            "description": description,
            "tags": tags,
            "file_size": file_size,
            "checksum": checksum,
        }
        
        return self.create(artifact_data)
    
    def get_total_size_by_return(self, tax_return_id: int) -> int:
        """Get total size of all artifacts for a tax return."""
        from sqlalchemy import func
        result = (
            self.db.query(func.sum(Artifact.file_size))
            .filter(Artifact.tax_return_id == tax_return_id)
            .scalar()
        )
        return result or 0