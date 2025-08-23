"""Form 16B parser with LLM fallback for non-standard formats."""

from typing import Dict, Any, Optional
from packages.llm.router import LLMRouter
from packages.llm.contracts import LLMTask, Form16Extract


class ParseMiss(Exception):
    """Exception raised when deterministic parsing fails."""
    pass


def parse_form16b_llm(text: str, router: LLMRouter) -> Form16Extract:
    """
    Parse Form 16B using LLM when deterministic parsing fails.
    
    Args:
        text: Raw text extracted from Form 16B PDF
        router: LLM router instance
        
    Returns:
        Form16Extract with parsed data
        
    Raises:
        RuntimeError: If LLM extraction fails
    """
    # Create LLM task for Form 16B extraction
    task = LLMTask(
        name="form16_extract",
        schema_name="Form16Extract",
        prompt="Extract salary and tax details from Form 16B",
        text=text
    )
    
    # Execute LLM extraction
    result = router.run(task)
    
    if not result.ok:
        raise RuntimeError(f"LLM Form 16B extraction failed: {result.error}")
    
    # Validate and return structured data
    extracted = Form16Extract.model_validate(result.json)
    
    # Post-validation checks
    _validate_form16b_data(extracted)
    
    return extracted


def _validate_form16b_data(data: Form16Extract) -> None:
    """
    Post-validation checks for Form 16B data consistency.
    
    Args:
        data: Extracted Form 16B data
        
    Raises:
        ValueError: If data fails consistency checks
    """
    # Check that TDS doesn't exceed gross salary
    if data.gross_salary and data.tds:
        if data.tds > data.gross_salary:
            raise ValueError(f"TDS ({data.tds}) cannot exceed gross salary ({data.gross_salary})")
    
    # Check that exemptions don't exceed gross salary
    if data.gross_salary and data.exemptions:
        total_exemptions = sum(data.exemptions.values())
        if total_exemptions > data.gross_salary:
            raise ValueError(f"Total exemptions ({total_exemptions}) cannot exceed gross salary ({data.gross_salary})")
    
    # Check standard deduction limit (₹50,000 for AY 2025-26)
    if data.standard_deduction and data.standard_deduction > 50000:
        raise ValueError(f"Standard deduction ({data.standard_deduction}) exceeds maximum limit (₹50,000)")
    
    # Check confidence threshold
    if data.confidence < 0.5:
        raise ValueError(f"Extraction confidence ({data.confidence}) too low for reliable processing")


def enhance_form16b_parser(original_parser_func):
    """
    Decorator to enhance existing Form 16B parser with LLM fallback.
    
    Args:
        original_parser_func: Original deterministic parser function
        
    Returns:
        Enhanced parser with LLM fallback
    """
    def enhanced_parser(file_path: str, router: Optional[LLMRouter] = None) -> Dict[str, Any]:
        """Enhanced parser with LLM fallback."""
        try:
            # Try deterministic parsing first
            return original_parser_func(file_path)
        except ParseMiss:
            if not router:
                raise RuntimeError("Deterministic parsing failed and no LLM router provided")
            
            # Extract text from PDF (assuming text extraction utility exists)
            text = _extract_text_from_pdf(file_path)
            
            # Use LLM fallback
            llm_result = parse_form16b_llm(text, router)
            
            # Convert to expected format
            return {
                "source": "LLM_FALLBACK",
                "confidence": llm_result.confidence,
                "gross_salary": llm_result.gross_salary,
                "exemptions": llm_result.exemptions,
                "standard_deduction": llm_result.standard_deduction,
                "tds": llm_result.tds,
                "employer_name": llm_result.employer_name,
                "period_from": llm_result.period_from,
                "period_to": llm_result.period_to,
            }
    
    return enhanced_parser


def _extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    # Mock implementation - in production, use PyPDF2, pdfplumber, or similar
    return f"Mock text content from {file_path}"