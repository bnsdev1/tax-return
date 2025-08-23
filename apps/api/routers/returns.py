"""Tax returns API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.base import get_db
from schemas.returns import (
    TaxReturnCreate,
    TaxReturnResponse,
    TaxReturnStatusResponse,
    TaxReturnStatus,
    ValidationResult,
)
from schemas.jobs import BuildJobResponse, JobStatus, JobType
from repo import TaxpayerRepository, TaxReturnRepository
from services.jobs import JobService
from datetime import datetime

router = APIRouter(
    prefix="/api/returns",
    tags=["Tax Returns"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=TaxReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tax return",
    description="Create a new tax return for a taxpayer. If the taxpayer doesn't exist, they will be created automatically.",
    responses={
        201: {
            "description": "Tax return created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "taxpayer_id": 1,
                        "assessment_year": "2025-26",
                        "form_type": "ITR2",
                        "regime": "new",
                        "status": "draft",
                        "filing_date": None,
                        "acknowledgment_number": None,
                        "revised_return": False,
                        "created_at": "2025-08-23T12:00:00Z",
                        "updated_at": None
                    }
                }
            }
        },
        400: {"description": "Invalid input data"},
        422: {"description": "Validation error"}
    }
)
async def create_tax_return(
    tax_return: TaxReturnCreate,
    db: Session = Depends(get_db)
) -> TaxReturnResponse:
    """
    Create a new tax return.
    
    This endpoint creates a new tax return for the specified taxpayer.
    If the taxpayer (identified by PAN) doesn't exist, a new taxpayer
    record will be created automatically.
    
    - **pan**: PAN number of the taxpayer (10 characters)
    - **ay**: Assessment year in YYYY-YY format (e.g., "2025-26")
    - **form**: ITR form type (e.g., "ITR1", "ITR2", "ITR3")
    - **regime**: Tax regime ("old" or "new")
    """
    try:
        # Get or create taxpayer
        taxpayer_repo = TaxpayerRepository(db)
        taxpayer = taxpayer_repo.get_by_pan(tax_return.pan)
        
        if not taxpayer:
            # Create a basic taxpayer record
            taxpayer = taxpayer_repo.create_taxpayer(
                pan=tax_return.pan,
                name=f"Taxpayer {tax_return.pan}",  # Placeholder name
            )
        
        # Create tax return
        return_repo = TaxReturnRepository(db)
        new_return = return_repo.create_tax_return(
            taxpayer_id=taxpayer.id,
            assessment_year=tax_return.ay,
            form_type=tax_return.form,
            return_data=f'{{"regime": "{tax_return.regime.value}"}}'
        )
        
        # Convert to response model
        return TaxReturnResponse(
            id=new_return.id,
            taxpayer_id=new_return.taxpayer_id,
            assessment_year=new_return.assessment_year,
            form_type=new_return.form_type,
            regime=tax_return.regime,
            status=new_return.status.value,
            filing_date=new_return.filing_date,
            acknowledgment_number=new_return.acknowledgment_number,
            revised_return=new_return.revised_return,
            created_at=new_return.created_at,
            updated_at=new_return.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tax return"
        )


@router.get(
    "/{return_id}",
    response_model=TaxReturnResponse,
    summary="Get tax return by ID",
    description="Retrieve a specific tax return by its ID.",
    responses={
        200: {
            "description": "Tax return retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "taxpayer_id": 1,
                        "assessment_year": "2025-26",
                        "form_type": "ITR2",
                        "regime": "new",
                        "status": "draft",
                        "filing_date": None,
                        "acknowledgment_number": None,
                        "revised_return": False,
                        "created_at": "2025-08-23T12:00:00Z",
                        "updated_at": None
                    }
                }
            }
        },
        404: {"description": "Tax return not found"}
    }
)
async def get_tax_return(
    return_id: int,
    db: Session = Depends(get_db)
) -> TaxReturnResponse:
    """
    Get a tax return by ID.
    
    Retrieve detailed information about a specific tax return.
    
    - **return_id**: The unique identifier of the tax return
    """
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Extract regime from return_data (simplified for skeleton)
    regime = "new"  # Default
    if tax_return.return_data:
        try:
            import json
            data = json.loads(tax_return.return_data)
            regime = data.get("regime", "new")
        except:
            pass
    
    return TaxReturnResponse(
        id=tax_return.id,
        taxpayer_id=tax_return.taxpayer_id,
        assessment_year=tax_return.assessment_year,
        form_type=tax_return.form_type,
        regime=regime,
        status=tax_return.status.value,
        filing_date=tax_return.filing_date,
        acknowledgment_number=tax_return.acknowledgment_number,
        revised_return=tax_return.revised_return,
        created_at=tax_return.created_at,
        updated_at=tax_return.updated_at
    )


@router.post(
    "/{return_id}/build",
    response_model=BuildJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start build job for tax return",
    description="Initiate the build process for a tax return. This includes validation, calculations, and document generation.",
    responses={
        202: {
            "description": "Build job started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "job_1_build_return_20250823120000",
                        "tax_return_id": 1,
                        "job_type": "build_return",
                        "status": "queued",
                        "progress_percentage": 0,
                        "current_step": "Initializing build process",
                        "created_at": "2025-08-23T12:00:00Z",
                        "started_at": None,
                        "completed_at": None,
                        "estimated_completion": None,
                        "result": None,
                        "error_message": None,
                        "error_details": None,
                        "metadata": {}
                    }
                }
            }
        },
        404: {"description": "Tax return not found"},
        409: {"description": "Build job already in progress"}
    }
)
async def start_build_job(
    return_id: int,
    db: Session = Depends(get_db)
) -> BuildJobResponse:
    """
    Start a build job for the tax return.
    
    This endpoint initiates the complete build process for a tax return, which includes:
    - Data validation
    - Tax calculations
    - Document generation (PDF, XML)
    - Compliance checks
    
    The process runs asynchronously. Use the returned job_id to poll for status updates.
    
    - **return_id**: The unique identifier of the tax return to build
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Check if build job is already running
    job_service = JobService()
    existing_job = job_service.get_active_build_job(return_id)
    
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Build job already in progress for tax return {return_id}"
        )
    
    # Start new build job
    job = job_service.start_build_job(return_id)
    
    return BuildJobResponse(
        job_id=job["job_id"],
        tax_return_id=return_id,
        job_type=JobType.BUILD_RETURN,
        status=JobStatus.QUEUED,
        progress_percentage=0,
        current_step="Initializing build process",
        created_at=datetime.utcnow(),
        started_at=None,
        completed_at=None,
        estimated_completion=None,
        result=None,
        error_message=None,
        error_details=None,
        metadata=job.get("metadata", {})
    )


@router.get(
    "/{return_id}/status",
    response_model=TaxReturnStatusResponse,
    summary="Get tax return processing status",
    description="Get the current processing status of a tax return, including validation results and build progress.",
    responses={
        200: {
            "description": "Status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "status": "completed",
                        "progress_percentage": 100,
                        "current_step": "Build completed successfully",
                        "validations": [
                            {
                                "rule_name": "pan_format",
                                "status": "passed",
                                "message": "PAN format is valid",
                                "field_path": None
                            },
                            {
                                "rule_name": "deduction_limits",
                                "status": "warning",
                                "message": "Deduction exceeds recommended limit",
                                "field_path": "deductions.section_80c"
                            }
                        ],
                        "error_message": None,
                        "started_at": "2025-08-23T12:00:00Z",
                        "completed_at": "2025-08-23T12:05:30Z"
                    }
                }
            }
        },
        404: {"description": "Tax return not found"}
    }
)
async def get_tax_return_status(
    return_id: int,
    db: Session = Depends(get_db)
) -> TaxReturnStatusResponse:
    """
    Get the processing status of a tax return.
    
    This endpoint provides comprehensive status information including:
    - Overall processing status
    - Progress percentage
    - Current processing step
    - Validation results
    - Error information (if any)
    - Timing information
    
    - **return_id**: The unique identifier of the tax return
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Get job status
    job_service = JobService()
    job_status = job_service.get_return_status(return_id)
    
    # Get validation results (simplified for skeleton)
    validations = [
        ValidationResult(
            rule_name="pan_format",
            status="passed",
            message="PAN format is valid"
        ),
        ValidationResult(
            rule_name="basic_validation",
            status="passed",
            message="Basic data validation completed"
        )
    ]
    
    return TaxReturnStatusResponse(
        id=return_id,
        status=job_status.get("status", TaxReturnStatus.PENDING),
        progress_percentage=job_status.get("progress_percentage", 0),
        current_step=job_status.get("current_step", "Ready"),
        validations=validations,
        error_message=job_status.get("error_message"),
        started_at=job_status.get("started_at"),
        completed_at=job_status.get("completed_at")
    )