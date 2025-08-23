"""Review and confirmation API endpoints."""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.base import get_db
from schemas.returns import PreviewResponse
from schemas.review import (
    ReviewPreviewResponse,
    ConfirmationRequest,
    ConfirmationResponse,
    LineItemEdit,
    HeadVariance,
)
from repo import TaxReturnRepository
from services.pipeline import TaxReturnPipeline

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/returns",
    tags=["Review & Confirmations"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{return_id}/preview",
    response_model=ReviewPreviewResponse,
    summary="Get tax return preview for review",
    description="Get detailed preview with head-wise breakdown, variances, and confirmation requirements.",
    responses={
        200: {
            "description": "Preview retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "return_id": 1,
                        "heads": {
                            "salary": {
                                "head_name": "Salary Income",
                                "total_amount": 1200000.0,
                                "line_items": [
                                    {
                                        "id": "salary_gross",
                                        "label": "Gross Salary",
                                        "amount": 1200000.0,
                                        "source": "prefill",
                                        "needs_confirm": True,
                                        "editable": True,
                                        "variance": None
                                    }
                                ],
                                "variances": [],
                                "needs_confirm": True
                            }
                        },
                        "summary": {
                            "gross_total_income": 1320000.0,
                            "total_deductions": 0.0,
                            "taxable_income": 1320000.0,
                            "tax_liability": 108160.0,
                            "refund_or_payable": 18660.0
                        },
                        "confirmations": {
                            "total_items": 8,
                            "confirmed_items": 0,
                            "blocking_variances": 0,
                            "can_proceed": False
                        },
                        "metadata": {
                            "generated_at": "2025-08-23T12:00:00Z",
                            "pipeline_status": "completed"
                        }
                    }
                }
            }
        },
        404: {"description": "Tax return not found"},
        500: {"description": "Preview generation failed"}
    }
)
async def get_review_preview(
    return_id: int,
    db: Session = Depends(get_db)
) -> ReviewPreviewResponse:
    """
    Get tax return preview for review and confirmation.
    
    This endpoint provides a detailed breakdown of the tax return by heads
    with line items that require confirmation and any variances that need
    to be resolved before proceeding.
    
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
    
    try:
        # Execute pipeline to get latest data
        pipeline = TaxReturnPipeline(db, return_id)
        preview = pipeline.execute()
        
        # Convert to review format with head-wise breakdown
        review_preview = _convert_to_review_format(return_id, preview)
        
        return review_preview
        
    except Exception as e:
        logger.error(f"Preview generation failed for return {return_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )


@router.post(
    "/{return_id}/confirm",
    response_model=ConfirmationResponse,
    summary="Submit confirmations and edits",
    description="Submit user confirmations and any edits to line items.",
    responses={
        200: {
            "description": "Confirmations processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "return_id": 1,
                        "confirmations_processed": 5,
                        "edits_applied": 2,
                        "remaining_confirmations": 3,
                        "blocking_variances": 0,
                        "can_proceed": False,
                        "updated_summary": {
                            "gross_total_income": 1250000.0,
                            "taxable_income": 1250000.0,
                            "tax_liability": 112000.0,
                            "refund_or_payable": 22500.0
                        },
                        "message": "Confirmations processed successfully"
                    }
                }
            }
        },
        400: {"description": "Invalid confirmation data"},
        404: {"description": "Tax return not found"},
        500: {"description": "Confirmation processing failed"}
    }
)
async def submit_confirmations(
    return_id: int,
    confirmation_request: ConfirmationRequest,
    db: Session = Depends(get_db)
) -> ConfirmationResponse:
    """
    Submit confirmations and edits for tax return line items.
    
    This endpoint processes user confirmations and applies any edits
    to line items, then recalculates the tax return and returns
    updated status.
    
    - **return_id**: The unique identifier of the tax return
    - **confirmations**: List of confirmed line item IDs
    - **edits**: List of line item edits with new values
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
        # Process confirmations and edits
        result = _process_confirmations(
            return_id, 
            confirmation_request.confirmations,
            confirmation_request.edits,
            db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Confirmation processing failed for return {return_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Confirmation processing failed: {str(e)}"
        )


def _convert_to_review_format(return_id: int, preview: Any) -> ReviewPreviewResponse:
    """Convert pipeline preview to review format with head-wise breakdown."""
    from datetime import datetime
    
    preview_dict = preview.to_dict()
    key_lines = preview_dict['key_lines']
    summary = preview_dict['summary']
    
    # Create head-wise breakdown
    heads = {}
    
    # Salary Head
    salary_head = _create_salary_head(key_lines, summary)
    if salary_head:
        heads['salary'] = salary_head
    
    # Interest Income Head
    interest_head = _create_interest_head(key_lines)
    if interest_head:
        heads['interest'] = interest_head
    
    # Capital Gains Head
    capital_gains_head = _create_capital_gains_head(key_lines)
    if capital_gains_head:
        heads['capital_gains'] = capital_gains_head
    
    # TDS Head
    tds_head = _create_tds_head(key_lines)
    if tds_head:
        heads['tds'] = tds_head
    
    # Count confirmations needed
    total_items = sum(len(head['line_items']) for head in heads.values())
    confirmed_items = 0  # Would come from stored confirmations
    blocking_variances = sum(len([v for v in head['variances'] if v.get('blocking', False)]) for head in heads.values())
    
    can_proceed = confirmed_items == total_items and blocking_variances == 0
    
    return ReviewPreviewResponse(
        return_id=return_id,
        heads=heads,
        summary=summary,
        confirmations={
            'total_items': total_items,
            'confirmed_items': confirmed_items,
            'blocking_variances': blocking_variances,
            'can_proceed': can_proceed
        },
        metadata={
            'generated_at': datetime.utcnow().isoformat(),
            'pipeline_status': preview_dict['metadata']['pipeline_status']
        }
    )


def _create_salary_head(key_lines: Dict, summary: Dict) -> Dict[str, Any]:
    """Create salary head with line items."""
    salary_income = summary.get('income_breakdown', {}).get('salary', 0)
    
    if salary_income == 0:
        return None
    
    line_items = [
        {
            'id': 'salary_gross',
            'label': 'Gross Salary',
            'amount': salary_income,
            'source': 'prefill',
            'needs_confirm': True,
            'editable': True,
            'variance': None
        }
    ]
    
    # Add variance if there's a discrepancy (mock for demo)
    variances = []
    if salary_income > 1000000:  # Mock variance condition
        variances.append({
            'field': 'salary_gross',
            'description': 'High salary amount detected',
            'expected_range': '₹500,000 - ₹1,000,000',
            'actual_value': f'₹{salary_income:,.2f}',
            'severity': 'warning',
            'blocking': False
        })
    
    return {
        'head_name': 'Salary Income',
        'total_amount': salary_income,
        'line_items': line_items,
        'variances': variances,
        'needs_confirm': True
    }


def _create_interest_head(key_lines: Dict) -> Dict[str, Any]:
    """Create interest income head with line items."""
    savings_interest = key_lines.get('savings_interest', {})
    interest_amount = savings_interest.get('amount', 0)
    
    if interest_amount == 0:
        return None
    
    line_items = [
        {
            'id': 'interest_savings',
            'label': 'Savings Account Interest',
            'amount': interest_amount,
            'source': 'ais',
            'needs_confirm': True,
            'editable': True,
            'variance': None
        },
        {
            'id': 'interest_tds',
            'label': 'TDS on Interest',
            'amount': savings_interest.get('tds_deducted', 0),
            'source': 'ais',
            'needs_confirm': False,
            'editable': False,
            'variance': None
        }
    ]
    
    return {
        'head_name': 'Interest Income',
        'total_amount': interest_amount,
        'line_items': line_items,
        'variances': [],
        'needs_confirm': True
    }


def _create_capital_gains_head(key_lines: Dict) -> Dict[str, Any]:
    """Create capital gains head with line items."""
    capital_gains = key_lines.get('capital_gains', {})
    total_gains = capital_gains.get('total', 0)
    
    if total_gains == 0:
        return None
    
    line_items = [
        {
            'id': 'cg_short_term',
            'label': 'Short-term Capital Gains',
            'amount': capital_gains.get('short_term', 0),
            'source': 'manual',
            'needs_confirm': True,
            'editable': True,
            'variance': None
        },
        {
            'id': 'cg_long_term',
            'label': 'Long-term Capital Gains',
            'amount': capital_gains.get('long_term', 0),
            'source': 'manual',
            'needs_confirm': True,
            'editable': True,
            'variance': None
        }
    ]
    
    return {
        'head_name': 'Capital Gains',
        'total_amount': total_gains,
        'line_items': line_items,
        'variances': [],
        'needs_confirm': True
    }


def _create_tds_head(key_lines: Dict) -> Dict[str, Any]:
    """Create TDS head with line items."""
    tds_data = key_lines.get('total_tds_tcs', {})
    total_tds = tds_data.get('total_tds', 0)
    
    if total_tds == 0:
        return None
    
    line_items = [
        {
            'id': 'tds_salary',
            'label': 'TDS on Salary',
            'amount': tds_data.get('salary_tds', 0),
            'source': 'form16',
            'needs_confirm': True,
            'editable': True,
            'variance': None
        },
        {
            'id': 'tds_interest',
            'label': 'TDS on Interest',
            'amount': tds_data.get('interest_tds', 0),
            'source': 'ais',
            'needs_confirm': False,
            'editable': False,
            'variance': None
        }
    ]
    
    return {
        'head_name': 'Tax Deducted at Source',
        'total_amount': total_tds,
        'line_items': line_items,
        'variances': [],
        'needs_confirm': True
    }


def _process_confirmations(
    return_id: int,
    confirmations: List[str],
    edits: List[LineItemEdit],
    db: Session
) -> ConfirmationResponse:
    """Process user confirmations and edits."""
    from datetime import datetime
    import json
    
    # Get current tax return
    return_repo = TaxReturnRepository(db)
    tax_return = return_repo.get(return_id)
    
    # Load existing confirmations and edits
    return_data = json.loads(tax_return.return_data or '{}')
    stored_confirmations = return_data.get('confirmations', [])
    stored_edits = return_data.get('edits', {})
    
    # Update confirmations
    updated_confirmations = list(set(stored_confirmations + confirmations))
    
    # Apply edits
    for edit in edits:
        stored_edits[edit.line_item_id] = {
            'new_amount': edit.new_amount,
            'reason': edit.reason,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Save updated data
    return_data.update({
        'confirmations': updated_confirmations,
        'edits': stored_edits,
        'last_confirmation_update': datetime.utcnow().isoformat()
    })
    
    tax_return.return_data = json.dumps(return_data)
    tax_return.updated_at = datetime.utcnow()
    db.commit()
    
    # Recalculate with edits (simplified for demo)
    pipeline = TaxReturnPipeline(db, return_id)
    
    # Apply edits to pipeline data (this would be more sophisticated in production)
    updated_preview = pipeline.execute()
    updated_summary = updated_preview.to_dict()['summary']
    
    # Count remaining items
    total_items = 8  # Mock total
    confirmed_items = len(updated_confirmations)
    remaining_confirmations = max(0, total_items - confirmed_items)
    blocking_variances = 0  # Mock - would check actual variances
    
    can_proceed = remaining_confirmations == 0 and blocking_variances == 0
    
    return ConfirmationResponse(
        return_id=return_id,
        confirmations_processed=len(confirmations),
        edits_applied=len(edits),
        remaining_confirmations=remaining_confirmations,
        blocking_variances=blocking_variances,
        can_proceed=can_proceed,
        updated_summary=updated_summary,
        message="Confirmations processed successfully"
    )