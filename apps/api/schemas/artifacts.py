"""Artifact schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ArtifactType(str, Enum):
    """Artifact type enumeration."""
    PDF = "pdf"
    XML = "xml"
    JSON = "json"
    EXCEL = "excel"
    IMAGE = "image"
    OTHER = "other"


class ArtifactCreate(BaseModel):
    """Schema for creating artifact metadata."""
    
    name: str = Field(
        ...,
        description="Artifact name",
        example="ITR2_Form.pdf",
        max_length=255
    )
    artifact_type: ArtifactType = Field(
        ...,
        description="Type of artifact",
        example="pdf"
    )
    description: Optional[str] = Field(
        None,
        description="Artifact description",
        example="Generated ITR2 form for assessment year 2025-26"
    )
    tags: Optional[str] = Field(
        None,
        description="Comma-separated tags",
        example="form,pdf,itr2,generated"
    )
    
    # File metadata (for upload tracking)
    file_size: Optional[int] = Field(
        None,
        description="File size in bytes",
        example=1024000
    )
    mime_type: Optional[str] = Field(
        None,
        description="MIME type of the file",
        example="application/pdf"
    )
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata as key-value pairs"
    )


class ArtifactResponse(BaseModel):
    """Schema for artifact response."""
    
    id: int = Field(..., description="Unique artifact ID", example=1)
    tax_return_id: int = Field(..., description="Associated tax return ID", example=1)
    name: str = Field(..., description="Artifact name", example="ITR2_Form.pdf")
    artifact_type: ArtifactType = Field(..., description="Artifact type", example="pdf")
    
    # File information
    file_path: Optional[str] = Field(None, description="File storage path")
    file_size: Optional[int] = Field(None, description="File size in bytes", example=1024000)
    checksum: Optional[str] = Field(None, description="File checksum (SHA-256)")
    mime_type: Optional[str] = Field(None, description="MIME type", example="application/pdf")
    
    # Metadata
    description: Optional[str] = Field(None, description="Artifact description")
    tags: Optional[str] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Status
    upload_status: str = Field("pending", description="Upload status", example="completed")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ArtifactMetadata(BaseModel):
    """Schema for artifact metadata only (lightweight response)."""
    
    id: int = Field(..., description="Artifact ID", example=1)
    name: str = Field(..., description="Artifact name", example="ITR2_Form.pdf")
    artifact_type: ArtifactType = Field(..., description="Artifact type", example="pdf")
    file_size: Optional[int] = Field(None, description="File size in bytes", example=1024000)
    upload_status: str = Field("pending", description="Upload status", example="pending")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True