"""Artifacts API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.base import get_db
from schemas.artifacts import (
    ArtifactCreate,
    ArtifactResponse,
    ArtifactMetadata,
    ArtifactType,
)
from repo import TaxReturnRepository, ArtifactRepository
from datetime import datetime

router = APIRouter(
    prefix="/api/returns/{return_id}/artifacts",
    tags=["Artifacts"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create artifact metadata",
    description="Create metadata for a new artifact associated with a tax return. This endpoint handles metadata only - actual file upload is handled separately.",
    responses={
        201: {
            "description": "Artifact metadata created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "tax_return_id": 1,
                        "name": "ITR2_Form.pdf",
                        "artifact_type": "pdf",
                        "file_path": None,
                        "file_size": 1024000,
                        "checksum": None,
                        "mime_type": "application/pdf",
                        "description": "Generated ITR2 form for assessment year 2025-26",
                        "tags": "form,pdf,itr2,generated",
                        "metadata": {
                            "generated_by": "system",
                            "template_version": "2.1"
                        },
                        "upload_status": "pending",
                        "created_at": "2025-08-23T12:00:00Z",
                        "updated_at": None
                    }
                }
            }
        },
        400: {"description": "Invalid input data"},
        404: {"description": "Tax return not found"},
        422: {"description": "Validation error"}
    }
)
async def create_artifact_metadata(
    return_id: int,
    artifact: ArtifactCreate,
    db: Session = Depends(get_db)
) -> ArtifactResponse:
    """
    Create artifact metadata for a tax return.
    
    This endpoint creates metadata for an artifact (document/file) associated with a tax return.
    The actual file content is not uploaded through this endpoint - this is metadata only.
    
    Typical workflow:
    1. Create artifact metadata (this endpoint)
    2. Upload file content (separate endpoint/service)
    3. Update artifact with file information
    
    - **return_id**: The tax return ID to associate the artifact with
    - **name**: Name of the artifact/file
    - **artifact_type**: Type of artifact (pdf, xml, json, excel, image, other)
    - **description**: Optional description of the artifact
    - **tags**: Optional comma-separated tags for categorization
    - **file_size**: Expected file size in bytes
    - **mime_type**: MIME type of the file
    - **metadata**: Additional key-value metadata
    """
    try:
        # Verify tax return exists
        return_repo = TaxReturnRepository(db)
        tax_return = return_repo.get(return_id)
        
        if not tax_return:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tax return with ID {return_id} not found"
            )
        
        # Create artifact metadata
        artifact_repo = ArtifactRepository(db)
        new_artifact = artifact_repo.create_artifact(
            tax_return_id=return_id,
            name=artifact.name,
            artifact_type=artifact.artifact_type.value,
            description=artifact.description,
            tags=artifact.tags,
            file_size=artifact.file_size,
        )
        
        # Return response
        return ArtifactResponse(
            id=new_artifact.id,
            tax_return_id=new_artifact.tax_return_id,
            name=new_artifact.name,
            artifact_type=ArtifactType(new_artifact.artifact_type),
            file_path=new_artifact.file_path,
            file_size=new_artifact.file_size,
            checksum=new_artifact.checksum,
            mime_type=artifact.mime_type,
            description=new_artifact.description,
            tags=new_artifact.tags,
            metadata=artifact.metadata,
            upload_status="pending",
            created_at=new_artifact.created_at,
            updated_at=new_artifact.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create artifact metadata"
        )


@router.get(
    "/",
    response_model=List[ArtifactMetadata],
    summary="List artifacts for tax return",
    description="Get a list of all artifacts associated with a tax return.",
    responses={
        200: {
            "description": "Artifacts retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "ITR2_Form.pdf",
                            "artifact_type": "pdf",
                            "file_size": 1024000,
                            "upload_status": "completed",
                            "created_at": "2025-08-23T12:00:00Z"
                        },
                        {
                            "id": 2,
                            "name": "return_data.xml",
                            "artifact_type": "xml",
                            "file_size": 45000,
                            "upload_status": "completed",
                            "created_at": "2025-08-23T12:01:00Z"
                        }
                    ]
                }
            }
        },
        404: {"description": "Tax return not found"}
    }
)
async def list_artifacts(
    return_id: int,
    db: Session = Depends(get_db)
) -> List[ArtifactMetadata]:
    """
    List all artifacts for a tax return.
    
    Returns a lightweight list of artifact metadata for the specified tax return.
    
    - **return_id**: The tax return ID to get artifacts for
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Get artifacts
    artifact_repo = ArtifactRepository(db)
    artifacts = artifact_repo.get_by_tax_return(return_id)
    
    # Convert to metadata response
    return [
        ArtifactMetadata(
            id=artifact.id,
            name=artifact.name,
            artifact_type=ArtifactType(artifact.artifact_type),
            file_size=artifact.file_size,
            upload_status="completed" if artifact.file_path else "pending",
            created_at=artifact.created_at
        )
        for artifact in artifacts
    ]


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Get artifact by ID",
    description="Get detailed information about a specific artifact.",
    responses={
        200: {
            "description": "Artifact retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "tax_return_id": 1,
                        "name": "ITR2_Form.pdf",
                        "artifact_type": "pdf",
                        "file_path": "/storage/artifacts/2025/1/ITR2_Form.pdf",
                        "file_size": 1024000,
                        "checksum": "sha256:abc123...",
                        "mime_type": "application/pdf",
                        "description": "Generated ITR2 form",
                        "tags": "form,pdf,itr2",
                        "metadata": {"version": "1.0"},
                        "upload_status": "completed",
                        "created_at": "2025-08-23T12:00:00Z",
                        "updated_at": "2025-08-23T12:01:00Z"
                    }
                }
            }
        },
        404: {"description": "Artifact not found"}
    }
)
async def get_artifact(
    return_id: int,
    artifact_id: int,
    db: Session = Depends(get_db)
) -> ArtifactResponse:
    """
    Get detailed information about a specific artifact.
    
    - **return_id**: The tax return ID
    - **artifact_id**: The artifact ID
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Get artifact
    artifact_repo = ArtifactRepository(db)
    artifact = artifact_repo.get(artifact_id)
    
    if not artifact or artifact.tax_return_id != return_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID {artifact_id} not found for tax return {return_id}"
        )
    
    return ArtifactResponse(
        id=artifact.id,
        tax_return_id=artifact.tax_return_id,
        name=artifact.name,
        artifact_type=ArtifactType(artifact.artifact_type),
        file_path=artifact.file_path,
        file_size=artifact.file_size,
        checksum=artifact.checksum,
        mime_type="application/pdf",  # Simplified for skeleton
        description=artifact.description,
        tags=artifact.tags,
        metadata={},  # Simplified for skeleton
        upload_status="completed" if artifact.file_path else "pending",
        created_at=artifact.created_at,
        updated_at=artifact.updated_at
    )


@router.delete(
    "/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete artifact",
    description="Delete an artifact and its associated file.",
    responses={
        204: {"description": "Artifact deleted successfully"},
        404: {"description": "Artifact not found"}
    }
)
async def delete_artifact(
    return_id: int,
    artifact_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an artifact.
    
    This will remove the artifact metadata and associated file (if any).
    
    - **return_id**: The tax return ID
    - **artifact_id**: The artifact ID to delete
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Get and delete artifact
    artifact_repo = ArtifactRepository(db)
    artifact = artifact_repo.get(artifact_id)
    
    if not artifact or artifact.tax_return_id != return_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID {artifact_id} not found for tax return {return_id}"
        )
    
    # Delete artifact (file deletion would be handled by a background service)
    success = artifact_repo.delete(artifact_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete artifact"
        )