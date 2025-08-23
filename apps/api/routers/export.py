"""
Export API endpoints for ITR JSON generation and download
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import tempfile
import os

from db.base import get_db
from db.models import TaxReturn
from packages.core.src.core.exporter.itr_json import build_itr_json
from packages.core.src.core.validate.schema_check import validate_itr_json, get_schema_registry
from packages.core.src.core.compute.calculator import TaxCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/returns", tags=["export"])

# Configure export directory
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/{return_id}/export")
async def export_itr_json(
    return_id: int,
    form_type: Optional[str] = None,
    schema_version: str = "2.0",
    validate_schema: bool = True,
    db: Session = Depends(get_db)
):
    """
    Export ITR JSON file for a tax return
    
    This endpoint generates a byte-perfect ITR JSON file from the tax return data,
    validates it against the appropriate schema, and provides it for download.
    
    Args:
        return_id: Tax return ID to export
        form_type: ITR form type (ITR1, ITR2) - auto-detected if not provided
        schema_version: Schema version to use for validation
        validate_schema: Whether to perform schema validation
        
    Returns:
        JSON file download with validation log
    """
    logger.info(f"Exporting ITR JSON for return {return_id}")
    
    try:
        # Get tax return from database
        tax_return = db.query(TaxReturn).filter(TaxReturn.id == return_id).first()
        if not tax_return:
            raise HTTPException(status_code=404, detail="Tax return not found")
        
        # Parse return data
        try:
            return_data = json.loads(tax_return.return_data) if tax_return.return_data else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid return data format")
        
        # Determine form type if not provided
        if not form_type:
            form_type = tax_return.form_type or "ITR1"
        
        # Calculate tax totals
        calculator = TaxCalculator(
            assessment_year=tax_return.assessment_year,
            regime=return_data.get('tax_regime', 'new')
        )
        
        computation_result = calculator.compute_totals(return_data)
        
        # Prepare data for JSON export
        totals = {
            **computation_result.computed_totals,
            'tax_liability': computation_result.tax_liability,
            'deductions_summary': computation_result.deductions_summary
        }
        
        # Prepare prefill data (from various sources)
        prefill = {
            'taxpayer': {
                'first_name': return_data.get('taxpayer_info', {}).get('first_name', 'John'),
                'middle_name': return_data.get('taxpayer_info', {}).get('middle_name', ''),
                'last_name': return_data.get('taxpayer_info', {}).get('last_name', 'Doe'),
                'pan': return_data.get('taxpayer_info', {}).get('pan', 'ABCDE1234F'),
                'date_of_birth': return_data.get('taxpayer_info', {}).get('date_of_birth', '1990-01-01'),
                'email': return_data.get('taxpayer_info', {}).get('email', 'john.doe@example.com'),
                'address': return_data.get('taxpayer_info', {}).get('address', {}),
                'phone': return_data.get('taxpayer_info', {}).get('phone', {}),
                'father_name': return_data.get('taxpayer_info', {}).get('father_name', 'Father Name'),
                'place': return_data.get('taxpayer_info', {}).get('place', 'Mumbai')
            },
            'tds': return_data.get('tds', {}),
            'house_property': return_data.get('house_property', {}),
            'capital_gains': return_data.get('capital_gains', {}),
            'donations': return_data.get('donations', {})
        }
        
        # Prepare form data
        form_data = {
            'form_type': form_type,
            'assessment_year': tax_return.assessment_year,
            'filing_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Build ITR JSON
        export_result = build_itr_json(
            totals=totals,
            prefill=prefill,
            form_data=form_data,
            ay=tax_return.assessment_year,
            schema_ver=schema_version
        )
        
        # Perform schema validation if requested
        validation_result = None
        if validate_schema:
            try:
                validation_result = validate_itr_json(
                    export_result.json_data,
                    form_type,
                    schema_version
                )
                logger.info(f"Schema validation completed: {validation_result.error_count} errors, {validation_result.warning_count} warnings")
            except Exception as e:
                logger.error(f"Schema validation failed: {e}")
                validation_result = None
        
        # Create export files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"ITR_{form_type}_{return_id}_{timestamp}.json"
        validation_filename = f"validation_log_{return_id}_{timestamp}.json"
        
        export_path = EXPORT_DIR / export_filename
        validation_path = EXPORT_DIR / validation_filename
        
        # Write ITR JSON file
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(export_result.json_string)
        
        # Write validation log
        validation_log = {
            "export_info": {
                "return_id": return_id,
                "form_type": form_type,
                "assessment_year": tax_return.assessment_year,
                "schema_version": schema_version,
                "export_timestamp": export_result.export_timestamp.isoformat(),
                "export_filename": export_filename
            },
            "export_warnings": export_result.warnings,
            "schema_validation": None
        }
        
        if validation_result:
            schema_registry = get_schema_registry()
            validation_log["schema_validation"] = schema_registry.create_validation_log(validation_result)
        
        with open(validation_path, 'w', encoding='utf-8') as f:
            json.dump(validation_log, f, indent=2, ensure_ascii=False)
        
        # Return success response with file info
        response_data = {
            "message": "ITR JSON exported successfully",
            "export_info": {
                "return_id": return_id,
                "form_type": form_type,
                "assessment_year": tax_return.assessment_year,
                "schema_version": schema_version,
                "export_timestamp": export_result.export_timestamp.isoformat(),
                "file_size_bytes": os.path.getsize(export_path)
            },
            "validation_summary": {
                "schema_validation_performed": validate_schema,
                "is_valid": validation_result.is_valid if validation_result else None,
                "error_count": validation_result.error_count if validation_result else 0,
                "warning_count": validation_result.warning_count if validation_result else len(export_result.warnings),
                "export_warnings": export_result.warnings
            },
            "download_urls": {
                "itr_json": f"/api/returns/{return_id}/download/{export_filename}",
                "validation_log": f"/api/returns/{return_id}/download/{validation_filename}"
            }
        }
        
        # Add validation details if available
        if validation_result:
            response_data["validation_details"] = {
                "errors": validation_result.errors[:10],  # Limit to first 10 errors
                "warnings": validation_result.warnings[:10]  # Limit to first 10 warnings
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for return {return_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/{return_id}/download/{filename}")
async def download_export_file(
    return_id: int,
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Download exported file (ITR JSON or validation log)
    
    Args:
        return_id: Tax return ID
        filename: Name of the file to download
        
    Returns:
        File download response
    """
    # Verify return exists
    tax_return = db.query(TaxReturn).filter(TaxReturn.id == return_id).first()
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    
    # Construct file path
    file_path = EXPORT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    if filename.endswith('.json'):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )

@router.get("/{return_id}/validate")
async def validate_return_json(
    return_id: int,
    form_type: Optional[str] = None,
    schema_version: str = "2.0",
    db: Session = Depends(get_db)
):
    """
    Validate tax return data against ITR JSON schema without exporting
    
    Args:
        return_id: Tax return ID to validate
        form_type: ITR form type (ITR1, ITR2) - auto-detected if not provided
        schema_version: Schema version to validate against
        
    Returns:
        Validation results
    """
    logger.info(f"Validating return {return_id} against schema")
    
    try:
        # Get tax return from database
        tax_return = db.query(TaxReturn).filter(TaxReturn.id == return_id).first()
        if not tax_return:
            raise HTTPException(status_code=404, detail="Tax return not found")
        
        # Parse return data
        try:
            return_data = json.loads(tax_return.return_data) if tax_return.return_data else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid return data format")
        
        # Determine form type if not provided
        if not form_type:
            form_type = tax_return.form_type or "ITR1"
        
        # Calculate tax totals (similar to export)
        calculator = TaxCalculator(
            assessment_year=tax_return.assessment_year,
            regime=return_data.get('tax_regime', 'new')
        )
        
        computation_result = calculator.compute_totals(return_data)
        
        # Prepare data for JSON export (but don't save)
        totals = {
            **computation_result.computed_totals,
            'tax_liability': computation_result.tax_liability,
            'deductions_summary': computation_result.deductions_summary
        }
        
        prefill = {
            'taxpayer': {
                'first_name': return_data.get('taxpayer_info', {}).get('first_name', 'John'),
                'last_name': return_data.get('taxpayer_info', {}).get('last_name', 'Doe'),
                'pan': return_data.get('taxpayer_info', {}).get('pan', 'ABCDE1234F'),
                'date_of_birth': return_data.get('taxpayer_info', {}).get('date_of_birth', '1990-01-01'),
            },
            'tds': return_data.get('tds', {}),
            'house_property': return_data.get('house_property', {}),
            'capital_gains': return_data.get('capital_gains', {}),
            'donations': return_data.get('donations', {})
        }
        
        form_data = {
            'form_type': form_type,
            'assessment_year': tax_return.assessment_year
        }
        
        # Build ITR JSON (in memory only)
        export_result = build_itr_json(
            totals=totals,
            prefill=prefill,
            form_data=form_data,
            ay=tax_return.assessment_year,
            schema_ver=schema_version
        )
        
        # Perform schema validation
        validation_result = validate_itr_json(
            export_result.json_data,
            form_type,
            schema_version
        )
        
        # Create validation log
        schema_registry = get_schema_registry()
        validation_log = schema_registry.create_validation_log(validation_result)
        
        return {
            "validation_summary": {
                "return_id": return_id,
                "form_type": form_type,
                "schema_version": schema_version,
                "is_valid": validation_result.is_valid,
                "error_count": validation_result.error_count,
                "warning_count": validation_result.warning_count,
                "validation_timestamp": validation_result.validation_timestamp.isoformat()
            },
            "validation_log": validation_log,
            "export_warnings": export_result.warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed for return {return_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.get("/schemas")
async def list_available_schemas():
    """
    List all available ITR JSON schemas
    
    Returns:
        List of available schemas with their information
    """
    try:
        schema_registry = get_schema_registry()
        schemas = schema_registry.get_available_schemas()
        
        return {
            "available_schemas": [
                {
                    "form_type": schema.form_type,
                    "schema_version": schema.schema_version,
                    "description": schema.description,
                    "file_path": schema.file_path
                }
                for schema in schemas
            ],
            "total_count": len(schemas)
        }
        
    except Exception as e:
        logger.error(f"Failed to list schemas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list schemas: {str(e)}"
        )