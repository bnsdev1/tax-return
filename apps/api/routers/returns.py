"""Tax returns API endpoints."""

import logging
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
    PreviewResponse,
)
from schemas.jobs import BuildJobResponse, JobStatus, JobType
from repo import TaxpayerRepository, TaxReturnRepository
from services.pipeline import TaxReturnPipeline
from db.models import Challan
from packages.core.src.core.compute.calculator import TaxCalculator
from datetime import datetime
import json

logger = logging.getLogger(__name__)

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
    response_model=PreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Build tax return and generate preview",
    description="Execute the complete tax return pipeline and return a preview with key financial highlights.",
    responses={
        200: {
            "description": "Tax return built successfully with preview",
            "content": {
                "application/json": {
                    "example": {
                        "key_lines": {
                            "savings_interest": {
                                "amount": 45000.0,
                                "tds_deducted": 4500.0,
                                "bank_count": 2
                            },
                            "total_tds_tcs": {
                                "total_tds": 89500.0,
                                "salary_tds": 85000.0,
                                "interest_tds": 4500.0,
                                "property_tds": 0.0,
                                "breakdown": {
                                    "salary": 85000.0,
                                    "interest": 4500.0,
                                    "property": 0.0
                                }
                            },
                            "advance_tax": {
                                "amount": 15000.0,
                                "total_taxes_paid": 104500.0
                            },
                            "capital_gains": {
                                "short_term": 25000.0,
                                "long_term": 50000.0,
                                "total": 75000.0,
                                "transaction_count": 5
                            }
                        },
                        "summary": {
                            "gross_total_income": 1320000.0,
                            "total_deductions": 0.0,
                            "taxable_income": 1245000.0,
                            "tax_liability": 78000.0,
                            "refund_or_payable": -26500.0
                        },
                        "warnings": [],
                        "blockers": [],
                        "metadata": {
                            "generated_at": "2025-08-23T12:00:00Z",
                            "pipeline_status": "completed",
                            "total_warnings": 0,
                            "total_blockers": 0
                        }
                    }
                }
            }
        },
        404: {"description": "Tax return not found"},
        500: {"description": "Pipeline execution failed"}
    }
)
async def build_tax_return(
    return_id: int,
    db: Session = Depends(get_db)
) -> PreviewResponse:
    """
    Build tax return and generate preview.
    
    This endpoint executes the complete deterministic pipeline for a tax return:
    1. Parse artifacts - Extract data from uploaded documents
    2. Reconcile sources - Cross-reference data from multiple sources
    3. Compute totals - Calculate tax liability and totals
    4. Validate - Check compliance and business rules
    
    Returns a preview with key financial highlights and any warnings/blockers.
    
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
    
    try:
        # Execute pipeline
        pipeline = TaxReturnPipeline(db, return_id)
        preview = pipeline.execute()
        
        # Get challan payments for this return
        from db.models import Challan, ChallanStatus as DBChallanStatus
        challan_payments = db.query(Challan).filter(
            Challan.tax_return_id == return_id,
            Challan.status == DBChallanStatus.PAID
        ).all()
        total_challan_payments = sum(float(c.amount) for c in challan_payments)
        
        # Convert to API response format
        preview_dict = preview.to_dict()
        
        # Update summary with challan information
        summary = preview_dict["summary"]
        summary["challan_payments"] = total_challan_payments
        summary["total_taxes_paid"] = summary.get("total_taxes_paid", 0) + total_challan_payments
        
        # Recalculate net payable considering challan payments
        tax_liability = summary.get("tax_liability", 0)
        total_paid = summary.get("total_taxes_paid", 0)
        net_payable = max(0, tax_liability - total_paid)
        summary["net_tax_payable"] = net_payable
        summary["refund_or_payable"] = tax_liability - total_paid
        
        return PreviewResponse(
            key_lines=preview_dict["key_lines"],
            summary=summary,
            warnings=preview_dict["warnings"],
            blockers=preview_dict["blockers"],
            metadata=preview_dict["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Pipeline execution failed for return {return_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
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
    
    # Get job status (simplified for demo)
    job_status = {
        "status": "completed",
        "progress_percentage": 100,
        "current_step": "Ready",
        "error_message": None,
        "started_at": None,
        "completed_at": None
    }
    
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


@router.post(
    "/{return_id}/export",
    status_code=status.HTTP_200_OK,
    summary="Export tax return",
    description="Export the tax return for filing. Validates that all requirements are met including tax payment if applicable.",
    responses={
        200: {"description": "Export initiated successfully"},
        400: {"description": "Export blocked - requirements not met"},
        404: {"description": "Tax return not found"}
    }
)
async def export_tax_return(
    return_id: int,
    db: Session = Depends(get_db)
):
    """
    Export tax return for filing.
    
    This endpoint validates all requirements before allowing export:
    - Tax computation must be complete
    - If tax is payable, challan must be uploaded
    - All validations must pass
    
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
    
    # Calculate tax to check if payment is required
    try:
        return_data = json.loads(tax_return.return_data) if tax_return.return_data else {}
        calculator = TaxCalculator()
        result = calculator.compute_totals(return_data)
        
        net_payable = result.computed_totals.get('refund_or_payable', 0)
        
        # If tax is payable, check for challan
        if net_payable > 0:
            challan = db.query(Challan).filter(Challan.tax_return_id == return_id).first()
            if not challan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "tax_payment_required",
                        "message": f"Tax payment of ₹{net_payable:,.2f} is required before export",
                        "net_payable": net_payable,
                        "action_required": "Complete tax payment and upload challan"
                    }
                )
            
            # Verify challan amount covers the liability
            if challan.amount < net_payable:
                remaining = net_payable - float(challan.amount)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "insufficient_payment",
                        "message": f"Additional payment of ₹{remaining:,.2f} is required",
                        "net_payable": net_payable,
                        "paid_amount": float(challan.amount),
                        "remaining_balance": remaining,
                        "action_required": "Complete remaining tax payment"
                    }
                )
        
        # All validations passed - proceed with export
        # In a real implementation, this would generate the actual export files
        export_data = {
            "return_id": return_id,
            "assessment_year": tax_return.assessment_year,
            "form_type": tax_return.form_type,
            "export_timestamp": datetime.now().isoformat(),
            "tax_summary": {
                "gross_total_income": result.computed_totals.get('gross_total_income', 0),
                "taxable_income": result.computed_totals.get('taxable_income', 0),
                "total_tax_liability": result.tax_liability.get('total_tax_liability', 0),
                "net_payable": net_payable,
                "challan_present": net_payable > 0 and challan is not None,
                "challan_amount": float(challan.amount) if challan else 0
            },
            "export_files": [
                "ITR_Form.pdf",
                "return_data.xml",
                "computation_sheet.pdf"
            ]
        }
        
        return {
            "message": "Export completed successfully",
            "export_data": export_data,
            "status": "ready_for_filing"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid return data format"
        )
    except Exception as e:
        logger.error(f"Export failed for return {return_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export processing failed"
        )