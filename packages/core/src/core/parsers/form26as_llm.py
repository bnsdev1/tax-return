"""Form 26AS LLM fallback parser using Step 13A router."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import pdfplumber

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "llm"))

from router import LLMRouter
from contracts import LLMTask
from .form26as import Form26ASExtract, ParseMiss

logger = logging.getLogger(__name__)


def parse_form26as_llm(text: str, router: LLMRouter) -> Form26ASExtract:
    """
    Parse Form 26AS using LLM when deterministic parsing fails.
    
    Args:
        text: Raw text extracted from Form 26AS PDF
        router: LLM router instance
        
    Returns:
        Form26ASExtract with parsed data
        
    Raises:
        RuntimeError: If LLM extraction fails
    """
    # Create LLM task for Form 26AS extraction
    task = LLMTask(
        name="form26as_extract",
        schema_name="Form26ASExtract",
        prompt=_get_form26as_prompt(),
        text=text
    )
    
    # Execute LLM extraction
    result = router.run(task)
    
    if not result.ok:
        raise RuntimeError(f"LLM Form 26AS extraction failed: {result.error}")
    
    # Validate and return structured data
    extracted = Form26ASExtract.model_validate(result.json)
    
    # Set source and confidence
    extracted.source = "LLM_FALLBACK"
    extracted.confidence = result.json.get("confidence", 0.7)
    
    # Post-validation checks
    _validate_form26as_data(extracted)
    
    return extracted


def parse_form26as_with_fallback(file_path: Path, router: Optional[LLMRouter] = None) -> Dict[str, Any]:
    """
    Parse Form 26AS with deterministic parser and LLM fallback.
    
    Args:
        file_path: Path to Form 26AS PDF file
        router: Optional LLM router for fallback
        
    Returns:
        Dictionary with parsed Form 26AS data
        
    Raises:
        RuntimeError: If both deterministic and LLM parsing fail
    """
    from .form26as import Form26ASParser
    
    # Try deterministic parsing first
    parser = Form26ASParser()
    
    try:
        return parser.parse(file_path)
    except ParseMiss as e:
        logger.info(f"Deterministic parsing failed, trying LLM fallback: {e}")
        
        if not router:
            raise RuntimeError("Deterministic parsing failed and no LLM router provided")
        
        # Extract text from PDF for LLM processing
        try:
            text = _extract_text_from_pdf(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")
        
        # Use LLM fallback
        try:
            llm_result = parse_form26as_llm(text, router)
            
            # Convert to expected format
            return {
                "form26as_data": llm_result.model_dump(),
                "metadata": {
                    "source": "form26as",
                    "parser": "llm_fallback",
                    "confidence": llm_result.confidence,
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "file_extension": file_path.suffix.lower(),
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"LLM fallback also failed: {e}")


def _extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text from PDF file for LLM processing.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        Exception: If text extraction fails
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            if not text_parts:
                raise Exception("No text could be extracted from PDF")
            
            return "\n\n".join(text_parts)
            
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        raise


def _get_form26as_prompt() -> str:
    """Get the LLM prompt for Form 26AS extraction."""
    return """
Extract data from Form 26AS (Tax Credit Statement) with these specific requirements:

SECTIONS TO DETECT:
1. TDS (Salary) - Part A or Section 192
2. TDS (Non-salary) - Part B or Sections 194/195/196
3. TCS (Tax Collected at Source) - Part C
4. Advance Tax/Self-Assessment Challans - Part D

EXTRACTION RULES:
- For TDS rows: Extract TAN, deductor name, section code, period dates, and amount
- For Challan rows: Extract BSR code, challan number, payment date, amount, and determine if ADVANCE or SELF_ASSESSMENT
- Convert all amounts to integers (₹1 rounding)
- Parse dates in DD/MM/YYYY format
- Extract section totals if displayed

DATA VALIDATION:
- All amounts must be positive integers
- Dates must be valid
- TAN codes should be 10 characters if present
- BSR codes should be numeric if present

CONFIDENCE SCORING:
- 1.0 for clear table structure with all fields
- 0.8 for partial table structure
- 0.6 for text-only extraction
- 0.4 for unclear or incomplete data

Return the data in the exact Form26ASExtract schema format.
"""


def _validate_form26as_data(data: Form26ASExtract) -> None:
    """
    Post-validation checks for Form 26AS data consistency.
    
    Args:
        data: Extracted Form 26AS data
        
    Raises:
        ValueError: If data fails consistency checks
    """
    # Check that all amounts are positive
    all_amounts = []
    all_amounts.extend([row.amount for row in data.tds_salary])
    all_amounts.extend([row.amount for row in data.tds_others])
    all_amounts.extend([row.amount for row in data.tcs])
    all_amounts.extend([row.amount for row in data.challans])
    
    for amount in all_amounts:
        if amount < 0:
            raise ValueError(f"Amount cannot be negative: {amount}")
    
    # Check TAN format if present
    for row in data.tds_salary + data.tds_others + data.tcs:
        if row.tan and len(row.tan) not in [0, 10]:
            logger.warning(f"TAN format may be incorrect: {row.tan}")
    
    # Check BSR code format if present
    for row in data.challans:
        if row.bsr_code and not row.bsr_code.isdigit():
            logger.warning(f"BSR code format may be incorrect: {row.bsr_code}")
    
    # Check confidence threshold
    if data.confidence < 0.4:
        raise ValueError(f"Extraction confidence ({data.confidence}) too low for reliable processing")
    
    # Validate challan kinds
    valid_kinds = {"ADVANCE", "SELF_ASSESSMENT"}
    for row in data.challans:
        if row.kind not in valid_kinds:
            raise ValueError(f"Invalid challan kind: {row.kind}")
    
    # Check for reasonable date ranges (within last 10 years)
    from datetime import date, timedelta
    min_date = date.today() - timedelta(days=10*365)
    max_date = date.today() + timedelta(days=365)
    
    for row in data.tds_salary + data.tds_others + data.tcs:
        for dt in [row.period_from, row.period_to]:
            if dt and not (min_date <= dt <= max_date):
                logger.warning(f"Date outside reasonable range: {dt}")
    
    for row in data.challans:
        if row.paid_on and not (min_date <= row.paid_on <= max_date):
            logger.warning(f"Payment date outside reasonable range: {row.paid_on}")


def enhance_form26as_parser(original_parser_func):
    """
    Decorator to enhance existing Form 26AS parser with LLM fallback.
    
    Args:
        original_parser_func: Original deterministic parser function
        
    Returns:
        Enhanced parser with LLM fallback
    """
    def enhanced_parser(file_path: Path, router: Optional[LLMRouter] = None) -> Dict[str, Any]:
        """Enhanced parser with LLM fallback."""
        try:
            # Try deterministic parsing first
            return original_parser_func(file_path)
        except ParseMiss:
            if not router:
                raise RuntimeError("Deterministic parsing failed and no LLM router provided")
            
            # Use LLM fallback
            return parse_form26as_with_fallback(file_path, router)
    
    return enhanced_parser