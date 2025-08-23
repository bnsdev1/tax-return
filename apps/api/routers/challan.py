from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from decimal import Decimal
import os
import uuid
from pathlib import Path

from db.base import get_db
from db.models import TaxReturn, Challan
from ..schemas.challan import ChallanCreate, ChallanResponse, TaxPaymentSummary
from packages.core.src.core.compute.calculator import TaxCalculator

router = APIRouter(prefix="/challan", tags=["challan"])

# Configure upload directory
UPLOAD_DIR = Path("uploads/challans")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/payment-summary/{return_id}", response_model=TaxPaymentSummary)
async def get_payment_summary(return_id: int, db: Session = Depends(get_db)):
    """Get tax payment summary for a return"""
    tax_return = db.query(TaxReturn).filter(TaxReturn.id == return_id).first()
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    
    # Calculate tax using the tax engine
    import json
    return_data = json.loads(tax_return.return_data) if tax_return.return_data else {}
    calculator = TaxCalculator()
    result = calculator.compute_totals(return_data)
    
    # Get existing challan if any
    challan = db.query(Challan).filter(Challan.tax_return_id == return_id).first()
    
    # Calculate remaining balance
    challan_amount = challan.amount if challan else Decimal('0')
    remaining_balance = max(Decimal('0'), result.net_payable - challan_amount)
    
    # Extract values from computation result
    tax_liability = result.tax_liability
    computed_totals = result.computed_totals
    
    return TaxPaymentSummary(
        total_tax_liability=Decimal(str(tax_liability['total_tax_liability'])),
        tds_paid=Decimal(str(return_data.get('tds', {}).get('total_tds', 0))),
        advance_tax_paid=Decimal(str(return_data.get('advance_tax', 0))),
        net_payable=Decimal(str(computed_totals['refund_or_payable'])) if computed_totals['refund_or_payable'] > 0 else Decimal('0'),
        interest_234a=Decimal(str(tax_liability['interest_234a'])),
        interest_234b=Decimal(str(tax_liability['interest_234b'])),
        interest_234c=Decimal(str(tax_liability['interest_234c'])),
        total_interest=Decimal(str(tax_liability['total_interest'])),
        total_amount_due=Decimal(str(computed_totals['refund_or_payable'])) if computed_totals['refund_or_payable'] > 0 else Decimal('0'),
        challan_present=challan is not None,
        challan_amount=challan_amount if challan else None,
        remaining_balance=remaining_balance
    )

@router.post("/upload/{return_id}", response_model=ChallanResponse)
async def upload_challan(
    return_id: int,
    cin_crn: str = Form(...),
    bsr_code: str = Form(...),
    bank_reference: str = Form(...),
    payment_date: date = Form(...),
    amount_paid: Decimal = Form(...),
    challan_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Upload challan details and file"""
    # Verify return exists
    tax_return = db.query(TaxReturn).filter(TaxReturn.id == return_id).first()
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    
    # Check if challan already exists
    existing_challan = db.query(Challan).filter(Challan.tax_return_id == return_id).first()
    if existing_challan:
        raise HTTPException(status_code=400, detail="Challan already exists for this return")
    
    # Handle file upload
    file_path = None
    if challan_file:
        if not challan_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate unique filename
        file_extension = Path(challan_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await challan_file.read()
            buffer.write(content)
        
        file_path = str(file_path)
    
    # Create challan record
    challan = Challan(
        tax_return_id=return_id,
        challan_type="self_assessment",
        cin_crn=cin_crn,
        bsr_code=bsr_code,
        bank_reference=bank_reference,
        payment_date=payment_date,
        amount=amount_paid,
        challan_file_path=file_path,
        assessment_year=tax_return.assessment_year
    )
    
    db.add(challan)
    db.commit()
    db.refresh(challan)
    
    return ChallanResponse.from_orm(challan)

@router.get("/{return_id}", response_model=Optional[ChallanResponse])
async def get_challan(return_id: int, db: Session = Depends(get_db)):
    """Get challan details for a return"""
    challan = db.query(Challan).filter(Challan.tax_return_id == return_id).first()
    if not challan:
        return None
    
    return ChallanResponse.from_orm(challan)

@router.delete("/{return_id}")
async def delete_challan(return_id: int, db: Session = Depends(get_db)):
    """Delete challan for a return"""
    challan = db.query(Challan).filter(Challan.tax_return_id == return_id).first()
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    # Delete file if exists
    if challan.challan_file_path and os.path.exists(challan.challan_file_path):
        os.remove(challan.challan_file_path)
    
    db.delete(challan)
    db.commit()
    
    return {"message": "Challan deleted successfully"}

@router.get("/download/{return_id}")
async def download_challan_file(return_id: int, db: Session = Depends(get_db)):
    """Download challan PDF file"""
    challan = db.query(Challan).filter(Challan.tax_return_id == return_id).first()
    if not challan or not challan.challan_file_path:
        raise HTTPException(status_code=404, detail="Challan file not found")
    
    if not os.path.exists(challan.challan_file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=challan.challan_file_path,
        filename=f"challan_{challan.cin_crn}.pdf",
        media_type="application/pdf"
    )"""Challan API endpoints for tax payment management."""

import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime

from db.base import get_db
from db.models import Challan, TaxReturn, ChallanStatus as DBChallanStatus
from schemas.challan import (
    ChallanCreate,
    ChallanResponse,
    ChallanUpdate,
    ChallanSummary,
    ChallanType,
    ChallanStatus
)
from repo import TaxReturnRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/challans",
    tags=["Challans"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/{return_id}",
    response_model=ChallanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new challan for tax payment",
    description="Create a new challan record for self-assessment tax payment with optional PDF upload.",
)
async def create_challan(
    return_id: int,
    challan_type: str = Form(...),
    amount: float = Form(...),
    cin_crn: str = Form(...),
    bsr_code: str = Form(...),
    bank_reference: str = Form(...),
    payment_date: str = Form(...),
    bank_name: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    challan_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
) -> ChallanResponse:
    """
    Create a new challan for tax payment.
    
    This endpoint creates a challan record and optionally stores the uploaded PDF file.
    The challan is linked to the specified tax return.
    
    - **return_id**: Tax return ID to associate the challan with
    - **challan_type**: Type of challan (self_assessment, advance_tax, etc.)
    - **amount**: Payment amount
    - **cin_crn**: 16-digit CIN/CRN number from the challan
    - **bsr_code**: 7-digit BSR code of the bank
    - **bank_reference**: Bank reference number
    - **payment_date**: Date of payment (ISO format)
    - **bank_name**: Name of the bank (optional)
    - **remarks**: Additional remarks (optional)
    - **challan_file**: PDF file of the challan (optional)
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
        
        # Parse payment date
        try:
            parsed_payment_date = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment_date format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
            )
        
        # Validate challan type
        try:
            challan_type_enum = ChallanType(challan_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid challan_type. Must be one of: {[e.value for e in ChallanType]}"
            )
        
        # Handle file upload if provided
        file_path = None
        if challan_file:
            if not challan_file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only PDF files are allowed for challan upload"
                )
            
            # Create uploads directory if it doesn't exist
            upload_dir = f"uploads/challans/{return_id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"challan_{timestamp}_{challan_file.filename}"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await challan_file.read()
                buffer.write(content)
            
            logger.info(f"Challan file saved: {file_path}")
        
        # Generate challan number
        challan_count = db.query(Challan).filter(Challan.tax_return_id == return_id).count()
        challan_number = f"CH{return_id:06d}{challan_count + 1:03d}"
        
        # Create challan record
        challan = Challan(
            tax_return_id=return_id,
            challan_number=challan_number,
            challan_type=challan_type_enum.value,
            amount=amount,
            cin_crn=cin_crn,
            bsr_code=bsr_code,
            bank_reference=bank_reference,
            payment_date=parsed_payment_date,
            bank_name=bank_name,
            assessment_year=tax_return.assessment_year,
            status=DBChallanStatus.PAID,  # Assume paid when created with details
            remarks=remarks,
            challan_file_path=file_path
        )
        
        db.add(challan)
        db.commit()
        db.refresh(challan)
        
        logger.info(f"Created challan {challan_number} for return {return_id}")
        
        return ChallanResponse(
            id=challan.id,
            tax_return_id=challan.tax_return_id,
            challan_number=challan.challan_number,
            challan_type=ChallanType(challan.challan_type),
            amount=float(challan.amount),
            cin_crn=challan.cin_crn,
            bsr_code=challan.bsr_code,
            bank_reference=challan.bank_reference,
            payment_date=challan.payment_date,
            bank_name=challan.bank_name,
            status=ChallanStatus(challan.status.value),
            assessment_year=challan.assessment_year,
            remarks=challan.remarks,
            challan_file_path=challan.challan_file_path,
            created_at=challan.created_at,
            updated_at=challan.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create challan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create challan"
        )


@router.get(
    "/{return_id}",
    response_model=List[ChallanResponse],
    summary="Get all challans for a tax return",
    description="Retrieve all challan records associated with a specific tax return.",
)
async def get_challans(
    return_id: int,
    db: Session = Depends(get_db)
) -> List[ChallanResponse]:
    """
    Get all challans for a tax return.
    
    - **return_id**: Tax return ID to get challans for
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Get all challans for this return
    challans = db.query(Challan).filter(Challan.tax_return_id == return_id).all()
    
    return [
        ChallanResponse(
            id=challan.id,
            tax_return_id=challan.tax_return_id,
            challan_number=challan.challan_number,
            challan_type=ChallanType(challan.challan_type),
            amount=float(challan.amount),
            cin_crn=challan.cin_crn,
            bsr_code=challan.bsr_code,
            bank_reference=challan.bank_reference,
            payment_date=challan.payment_date,
            bank_name=challan.bank_name,
            status=ChallanStatus(challan.status.value),
            assessment_year=challan.assessment_year,
            remarks=challan.remarks,
            challan_file_path=challan.challan_file_path,
            created_at=challan.created_at,
            updated_at=challan.updated_at
        )
        for challan in challans
    ]


@router.get(
    "/{return_id}/summary",
    response_model=ChallanSummary,
    summary="Get challan summary for a tax return",
    description="Get a summary of all challans for a tax return including totals and counts.",
)
async def get_challan_summary(
    return_id: int,
    db: Session = Depends(get_db)
) -> ChallanSummary:
    """
    Get challan summary for a tax return.
    
    - **return_id**: Tax return ID to get summary for
    """
    # Verify tax return exists
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    if not tax_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax return with ID {return_id} not found"
        )
    
    # Get challan statistics
    challans = db.query(Challan).filter(Challan.tax_return_id == return_id).all()
    
    total_challans = len(challans)
    total_amount = sum(float(c.amount) for c in challans)
    paid_challans = len([c for c in challans if c.status == DBChallanStatus.PAID])
    pending_challans = len([c for c in challans if c.status == DBChallanStatus.PENDING])
    
    latest_payment_date = None
    if challans:
        latest_payment_date = max(c.payment_date for c in challans if c.payment_date)
    
    return ChallanSummary(
        total_challans=total_challans,
        total_amount=total_amount,
        paid_challans=paid_challans,
        pending_challans=pending_challans,
        latest_payment_date=latest_payment_date
    )


@router.put(
    "/challan/{challan_id}",
    response_model=ChallanResponse,
    summary="Update a challan",
    description="Update challan status or remarks.",
)
async def update_challan(
    challan_id: int,
    challan_update: ChallanUpdate,
    db: Session = Depends(get_db)
) -> ChallanResponse:
    """
    Update a challan.
    
    - **challan_id**: Challan ID to update
    - **challan_update**: Fields to update
    """
    challan = db.query(Challan).filter(Challan.id == challan_id).first()
    
    if not challan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challan with ID {challan_id} not found"
        )
    
    # Update fields
    if challan_update.status is not None:
        challan.status = DBChallanStatus(challan_update.status.value)
    
    if challan_update.remarks is not None:
        challan.remarks = challan_update.remarks
    
    challan.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(challan)
    
    return ChallanResponse(
        id=challan.id,
        tax_return_id=challan.tax_return_id,
        challan_number=challan.challan_number,
        challan_type=ChallanType(challan.challan_type),
        amount=float(challan.amount),
        cin_crn=challan.cin_crn,
        bsr_code=challan.bsr_code,
        bank_reference=challan.bank_reference,
        payment_date=challan.payment_date,
        bank_name=challan.bank_name,
        status=ChallanStatus(challan.status.value),
        assessment_year=challan.assessment_year,
        remarks=challan.remarks,
        challan_file_path=challan.challan_file_path,
        created_at=challan.created_at,
        updated_at=challan.updated_at
    )


@router.delete(
    "/challan/{challan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a challan",
    description="Delete a challan record (soft delete by marking as cancelled).",
)
async def delete_challan(
    challan_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a challan.
    
    - **challan_id**: Challan ID to delete
    """
    challan = db.query(Challan).filter(Challan.id == challan_id).first()
    
    if not challan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challan with ID {challan_id} not found"
        )
    
    # Soft delete by marking as cancelled
    challan.status = DBChallanStatus.CANCELLED
    challan.updated_at = datetime.utcnow()
    
    db.commit()